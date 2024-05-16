import unittest
from unittest.mock import patch, mock_open
from utils.text_to_speech import TextToSpeechGenerator


class TestTextToSpeechGenerator(unittest.TestCase):
    @patch("text_to_speech.requests.post")
    @patch("builtins.open", new_callable=mock_open)
    def test_text_to_speech(self, mock_open, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"audio_data"]
        generator = TextToSpeechGenerator(voice_id="test_voice", api_key="test_key")
        generator.text_to_speech("Hello, world!", "output.mp3")
        mock_open.assert_called_with("output.mp3", "wb")
        mock_open.return_value.write.assert_called_with(b"audio_data")
