import logging
import base64
import requests
import replicate
from flask import current_app

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

    def generate_image_from_text_stability(self, prompt, size="medium", samples=1):
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

        return images

    def generate_image_from_text_replicate(self, prompt):
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
        return {"image_url": output[0]}
