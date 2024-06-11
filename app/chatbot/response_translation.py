from app.chatbot.utils.translation.translation import (
    TranslationService,
)


def translate_response(response, target_language):
    if target_language != "English":
        translated_response = TranslationService.get_translation(
            source_lang="English",
            target_lang=target_language,
            source_sentence=response,
        )
    else:
        translated_response = response
    return translated_response
