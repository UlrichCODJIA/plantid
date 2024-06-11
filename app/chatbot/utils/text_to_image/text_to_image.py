import logging
import base64
import os
import requests
import replicate
from flask import current_app

from app import chat_logger
from app.utils.utils import get_temp_file_path
from app.chatbot.utils.aws.cloudwatch import create_cloudwatch_rule
from app.chatbot.utils.aws.s3 import upload_file_to_s3

logger = logging.getLogger(__name__)

IMAGE_SIZES = {
    "small": {"height": 512, "width": 512},
    "medium": {"height": 1024, "width": 1024},
    "big": {"height": 1536, "width": 1536},
    "landscape": {"height": 768, "width": 1024},
    "portrait": {"height": 1024, "width": 768},
}


class TextToImageGenerator:
    def __init__(self, stability_api_key=None, replicate_api_key=None):
        self.stability_api_key = (
            stability_api_key or current_app.config["STABILITY_API_KEY"]
        )
        self.replicate_api_key = (
            replicate_api_key or current_app.config["REPLICATE_API_KEY"]
        )
        if not self.stability_api_key or not self.replicate_api_key:
            raise ValueError("Missing Stability or Replicate API key")
        self.stability_api_host = current_app.config["STABILITY_API_HOST"]
        self.stability_engine_id = "stable-diffusion-v1-6"
        self.replicate_scheduler = "K_EULER"
        self.s3_bucket_name = os.environ.get("AWS_BUCKET_NAME")

    def generate_image_from_text_stability(
        self, prompt, user_id, size="medium", samples=1
    ):
        """
        Generate an image from text using the Stability AI API.

        Args:
            prompt (str): The text prompt for generating the image.
            size (str, optional): The size of the image. Default is 'medium'.
                Available options: 'small', 'medium', 'big', 'landscape', 'portrait'.
            samples (int, optional): Number of samples to generate. Default is 1.

        Returns:
            list of bytes: List of image data in bytes format.
        """

        if size not in IMAGE_SIZES:
            raise ValueError(
                "Invalid size. Please choose from:"
                " small, medium, big, landscape, portrait."
            )

        try:
            response = requests.post(
                f"{self.stability_api_host}"
                "/v1/generation/{self.stability_engine_id}/text-to-image",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.stability_api_key}",
                },
                json={
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": 7,
                    "height": IMAGE_SIZES[size]["height"],
                    "width": IMAGE_SIZES[size]["width"],
                    "samples": samples,
                    "steps": 30,
                },
            )

            if response.status_code != 200:
                try:
                    self.generate_image_from_text_replicate(prompt)
                except Exception:
                    raise Exception(f"Non-200 response: {response.text}")

            data = response.json()

            images = []
            for image in data["artifacts"]:
                images.append(base64.b64decode(image["base64"]))

            image_file_url = self.generate_image_link(images[0], user_id)

            return image_file_url

        except Exception as e:
            chat_logger.error(f"Error in generate_image_from_text_stability: {e}")
            raise Exception(f"Error generating image: {e}")

    def generate_image_from_text_replicate(self, prompt, user_id):
        """
        Generate an image using the Replicate API.

        Args:
            prompt (str): The text prompt for image generation.

        Returns:
            dict: The generated image data.
        """
        model = replicate.models.get("stability-ai/stable-diffusion")
        version = model.versions.get(
            "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf"
        )
        inputs = {
            "prompt": prompt,
            "image_dimensions": "512x512",
            "num_outputs": 1,
            "num_inference_steps": 50,
            "guidance_scale": 7.5,
        }
        output = version.predict(**inputs)
        try:
            response = requests.get(output[0], stream=True)
            response.raise_for_status()
            image_data = response.content

            image_file_url = self.generate_image_link(image_data, user_id)
            return image_file_url

        except Exception as e:
            chat_logger.error(f"Error in generate_image_from_text_replicate: {e}")
            raise Exception(f"Error generating image: {e}")

    def generate_image_link(self, image, user_id):
        try:
            temp_file_path = get_temp_file_path(suffix=".png")
            with open(temp_file_path, "wb") as f:
                f.write(image)
            image_file_url, image_object_key = upload_file_to_s3(
                temp_file_path, self.s3_bucket_name, f"images/{user_id}"
            )
            create_cloudwatch_rule(
                image_object_key, "plantid-chatbot-image-remover", delay_minutes=10080
            )
            return image_file_url

        except Exception as e:
            chat_logger.error(f"Error in generate_image_link: {e}")
            raise Exception(f"Error generating image: {e}")

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
