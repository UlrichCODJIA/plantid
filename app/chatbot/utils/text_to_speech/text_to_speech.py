import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024


class TextToSpeechGenerator:
    """
    A class for generating speech from text using the Eleven Labs API.
    """

    def __init__(self, voice_id=None, api_key=None):
        self.voice_id = voice_id or current_app.config["ELEVEN_LABS_VOICE_ID"]
        self.api_key = api_key or current_app.config["ELEVEN_LABS_API_KEY"]
        if not self.voice_id or not self.api_key:
            raise ValueError("Missing voice ID or API key")

    def text_to_speech(self, text, output_file):
        """
        Generates an audio file from a given text using
        the ElevenLabs Text-to-Speech API.

        Args:
            text (str): The text to be converted to speech.
            output_file (str): The path to the output audio file.

        Returns:
            None
        """
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Audio file '{output_file}' generated successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
