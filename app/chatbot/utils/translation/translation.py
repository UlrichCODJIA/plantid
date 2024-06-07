import logging
from mmtafrica.mmtafrica import translate
from functools import lru_cache
from flask import current_app

from multilingual_webapp.logger import configure_logger
from multilingual_webapp.utils.utils import handle_translation_error, validate_text

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/translation.log")

LANGUAGE_MAP = {
    "English": "en",
    "Swahili": "sw",
    "Fon": "fon",
    "Igbo": "ig",
    "Kinyarwanda": "rw",
    "Xhosa": "xh",
    "Yoruba": "yo",
    "French": "fr",
}


class TranslationService:
    """
    A service class for handling translation between languages using the MMTAFRICA model.
    """

    @classmethod
    def load_model(cls):
        """
        Load the MMTAFRICA translation model.

        Returns:
            dict: The loaded model parameters.
        """
        try:
            checkpoint = "multilingual_webapp/ai_models/mmt_translation.pt"
            params = translate.load_params({"checkpoint": checkpoint, "device": "cpu"})
            return params
        except Exception as e:
            raise Exception(f"Failed to load MMTAFRICA model: {e}") from e

    @classmethod
    @lru_cache(maxsize=128)
    def get_translation(cls, source_lang, target_lang, source_text):
        """
        Translate the given source text from the source language to the target language.

        Args:
            source_lang (str): The source language code.
            target_lang (str): The target language code.
            source_text (str): The source text to translate.

        Returns:
            str: The translated text.
        """
        try:
            validate_text(source_text)
        except ValueError as e:
            return handle_translation_error(e)

        try:
            source_lang_code = LANGUAGE_MAP[source_lang]
            target_lang_code = LANGUAGE_MAP[target_lang]
            translated_text = translate(
                current_app.mmt_params, source_text, source_lang_code, target_lang_code
            )
            return translated_text
        except Exception as e:
            logger.error(f"Issue with translation: {e}")
            raise Exception(f"Failed to translate text: {e}") from e
