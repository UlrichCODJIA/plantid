"""
This module provides a translation service using the MMTAfrica model.

It allows translating text between various languages, including English, Swahili,
Fon, Igbo, Kinyarwanda, Xhosa, Yoruba, and French.
"""

import logging
import torch
from mmtafrica.mmtafrica import load_params, translate
from functools import lru_cache

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

    def __init__(self):
        """
        Initializes the TranslationService by downloading the MMTAfrica model checkpoint
        and loading the model parameters.
        """

        checkpoint_path = "models/mmt_translation.pt"
        device = "cpu"
        if torch.cuda.is_available():
            device = "gpu"
        print('1')
        self.checkpoint = torch.load(checkpoint_path, map_location=torch.device(device))
        print('2')
        self.params = load_params({"checkpoint": self.checkpoint, "device": device})

    @lru_cache(maxsize=128)
    def get_translation(self, source_language, target_language, source_sentence=None):
        """
        Translates a given sentence from the source language to the target language.
        This method is cached using an LRU (Least Recently Used) cache to improve performance.

        Args:
            source_language (str): The source language code (e.g., 'en', 'fr', 'sw').
            target_language (str): The target language code (e.g., 'en', 'fr', 'sw').
            source_sentence (str, optional): The sentence to be translated. If not provided,
                an empty string will be returned.

        Returns:
            str: The translated sentence, or an error message if the translation fails.
        """
        try:
            validate_text(source_sentence)
        except ValueError as e:
            return handle_translation_error(e)

        source_language_ = language_map[source_language]
        target_language_ = language_map[target_language]

        try:
            print('ok')
            pred = translate(
                self.params,
                source_sentence,
                source_lang=source_language_,
                target_lang=target_language_,
            )
            if pred == "":
                return "Could not find translation"
            else:
                return pred
        except Exception as error:
            logger.error(f"Issue with translation: {error}")
            return f"Issue with translation: {error}"
