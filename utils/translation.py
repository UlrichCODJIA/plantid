"""
This module provides a translation service using the MMTAfrica model.

It allows translating text between various languages, including English, Swahili,
Fon, Igbo, Kinyarwanda, Xhosa, Yoruba, and French.
"""

import logging
from mmtafrica.mmtafrica import translate
from functools import lru_cache
from flask import current_app

from .utils_func import validate_text, handle_translation_error
from logger import configure_logger

logger = configure_logger(log_level=logging.DEBUG, log_file="translation.log")

language_map = {
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
    A service class for handling translation between languages using the MMTAfrica model.
    """

    @classmethod
    @lru_cache(maxsize=128)
    def get_translation(cls, source_lang, target_lang, source_sentence=None):
        """
        Translates a given sentence from the source language to the target language.
        This method is cached using an LRU (Least Recently Used) cache to improve performance.

        Args:
            source_lang (str): The source language code (e.g., 'en', 'fr', 'sw').
            target_lang (str): The target language code (e.g., 'en', 'fr', 'sw').
            source_sentence (str, optional): The sentence to be translated. If not provided,
                an empty string will be returned.

        Returns:
            str: The translated sentence, or an error message if the translation fails.
        """
        try:
            validate_text(source_sentence)
        except ValueError as e:
            return handle_translation_error(e)

        source_lang_ = language_map[source_lang]
        target_lang_ = language_map[target_lang]

        try:
            pred = translate(
                current_app.mmt_params,
                source_sentence,
                source_lang=source_lang_,
                target_lang=target_lang_,
            )
            if pred == "":
                return "Could not find translation"
            else:
                return pred
        except Exception as error:
            logger.error(f"Issue with translation: {error}")
            return f"Issue with translation: {error}"
