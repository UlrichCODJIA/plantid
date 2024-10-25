from functools import lru_cache

from app.extensions import logger
from app.utils.utils import handle_translation_error, validate_text
from flask import current_app
from mmtafrica.mmtafrica import load_params, translate

LANGUAGE_MAP = {
    "english": "en",
    "swahili": "sw",
    "fon": "fon",
    "igbo": "ig",
    "kinyarwanda": "rw",
    "xhosa": "xh",
    "yoruba": "yo",
    "french": "fr",
}


class TranslationService:
    """
    A service class for handling translation between languages using the MMTAFRICA model.
    """

    @classmethod
    def load_model(cls, device):
        """
        Load the MMTAFRICA translation model.

        Returns:
            dict: The loaded model parameters.
        """
        try:
            checkpoint = "ai_models/mmt_translation.pt"
            params = load_params({"checkpoint": checkpoint, "device": device})
            return params
        except Exception as e:
            raise Exception(f"Failed to load MMTAFRICA model: {e}") from e

    @classmethod
    @lru_cache(maxsize=128)
    def get_translation(cls, source_lang: str, target_lang: str, source_text):
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
            source_lang_code = LANGUAGE_MAP[source_lang.lower()]
            target_lang_code = LANGUAGE_MAP[target_lang.lower()]
            translated_text = translate(current_app.mmt_params, source_text, source_lang_code, target_lang_code)
            return translated_text
        except Exception as e:
            logger.error(f"Issue with translation: {e}")
            raise Exception(f"Failed to translate text: {e}") from e
