import unittest
from unittest.mock import patch
from utils.translation import TranslationService


class TestTranslationService(unittest.TestCase):
    @patch("translation.translate")
    def test_get_translation(self, mock_translate):
        mock_translate.return_value = "Translated text"
        service = TranslationService()
        source_sentence = "Hello, world!"
        translation = service.get_translation("English", "French", source_sentence)
        self.assertEqual(translation, "Translated text")

    @patch("translation.translate")
    def test_get_translation_empty_input(self, mock_translate):
        service = TranslationService()
        translation = service.get_translation("English", "French", "")
        self.assertEqual(
            translation,
            "Input text cannot be empty or contain only whitespace characters.",
        )
