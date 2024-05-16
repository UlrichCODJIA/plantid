# text_to_image.py
import logging
import os
import base64
import requests
import replicate

logger = logging.getLogger(__name__)


class TextToImageGenerator:
    def __init__(self, stability_api_key=None, replicate_api_key=None):
        self.stability_api_key = stability_api_key or os.environ.get(
            "STABILITY_API_KEY"
        )
        self.replicate_api_key = replicate_api_key or os.environ.get(
            "REPLICATE_API_KEY"
        )
        if not self.stability_api_key or not self.replicate_api_key:
            raise ValueError("Missing Stability or Replicate API key")
        self.stability_api_host = os.getenv("API_HOST", "https://api.stability.ai")
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
        sizes = {
            "small": {"height": 512, "width": 512},
            "medium": {"height": 1024, "width": 1024},
            "big": {"height": 1536, "width": 1536},
            "landscape": {"height": 768, "width": 1024},
            "portrait": {"height": 1024, "width": 768},
        }

        if size not in sizes:
            raise ValueError(
                "Invalid size. Please choose from: small, medium, big, landscape, portrait."
            )

        response = requests.post(
            f"{self.stability_api_host}/v1/generation/{self.stability_engine_id}/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.stability_api_key}",
            },
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": sizes[size]["height"],
                "width": sizes[size]["width"],
                "samples": samples,
                "steps": 30,
            },
        )

        if response.status_code != 200:
            try:
                self.generate_image_from_text_replicate(prompt)
            except Exception as e:
                raise Exception(f"Non-200 response: {response.text}")

        data = response.json()

        images = []
        for image in data["artifacts"]:
            images.append(base64.b64decode(image["base64"]))

        return images

    def generate_image_from_text_replicate(self, prompt):
        input = {"prompt": prompt, "scheduler": self.replicate_scheduler}

        output = replicate.run(
            "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
            input=input,
        )
        return output
