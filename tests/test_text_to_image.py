import functools
import unittest
from unittest.mock import patch
from utils.text_to_image import TextToImageGenerator


class TestTextToImageGenerator(unittest.TestCase):
    @patch("text_to_image.requests.post")
    @functools.lru_cache(maxsize=128)
    def test_generate_image_from_text_stability(self, mock_post):
        """
        Generate an image from text using the Stability AI API.
        This method is cached using an LRU (Least Recently Used) cache to improve performance.
        """
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "artifacts": [
                {
                    "base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEEQEDbavnbwAAAABJRU5ErkJggg=="
                }
            ]
        }
        generator = TextToImageGenerator(api_key="test_key")
        images = generator.generate_image_from_text_stability("A lighthouse on a cliff")
        self.assertEqual(len(images), 1)

    def test_generate_image_from_text_stability_invalid_size(self):
        generator = TextToImageGenerator(api_key="test_key")
        with self.assertRaises(ValueError):
            generator.generate_image_from_text_stability(
                "A lighthouse on a cliff", size="invalid_size"
            )
