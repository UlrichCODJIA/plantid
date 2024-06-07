from flask import current_app
import requests
from PIL import Image

from multilingual_webapp.app.chatbot.utils.translation.translation import (
    TranslationService,
)
from multilingual_webapp.app.tasks.tasks import transcribe_task
from multilingual_webapp.utils.utils import get_temp_file_path


def process_input(audio_file, text_input, image_url, image_file, language):
    translated_text = None
    image_tensor = None
    inputs = None
    temp_file_path = None

    if audio_file:
        temp_file_path = get_temp_file_path(suffix=".wav")
        audio_file.save(temp_file_path)
        transcription_result = transcribe_task.delay(temp_file_path, language)
        transcript = transcription_result.get()

        if language != "English":
            translated_text = TranslationService.get_translation(
                source_lang=language,
                target_lang="English",
                source_sentence=transcript,
            )
        else:
            translated_text = transcript

        inputs = current_app.llava_processor(
            text=translated_text, return_tensors="pt"
        ).to(current_app.llava_model.device)

    elif text_input:
        if language != "English":
            translated_text = TranslationService.get_translation(
                source_lang=language,
                target_lang="English",
                source_sentence=text_input,
            )
        else:
            translated_text = text_input

        inputs = current_app.llava_processor(
            text=translated_text, return_tensors="pt"
        ).to(current_app.llava_model.device)

    if image_file or image_url:
        if image_file:
            temp_file_path = get_temp_file_path(suffix=".jpg")
            image_file.save(temp_file_path)
            image = Image.open(temp_file_path)
        elif image_url:
            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                temp_file_path = get_temp_file_path(suffix=".jpg")
                with open(temp_file_path, "wb") as f:
                    f.write(response.content)
                image = Image.open(temp_file_path)
            except requests.exceptions.RequestException as e:
                raise Exception(f"Error downloading image: {e}")

        try:
            image_tensor = current_app.llava_processor(
                images=image, return_tensors="pt"
            ).pixel_values.to(current_app.llava_model.device)
        except Exception as e:
            raise Exception(f"Error processing image: {e}")

        if translated_text:
            text_input = translated_text + "\n<image>"
        else:
            text_input = "<image>"

        inputs = current_app.llava_processor(
            text=text_input, images=image_tensor, return_tensors="pt"
        ).to(current_app.llava_model.device)

    return inputs, translated_text, temp_file_path
