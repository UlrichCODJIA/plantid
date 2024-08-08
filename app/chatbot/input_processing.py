import os
from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename

from app import chat_logger
from app.chatbot.utils.translation.translation import TranslationService
from app.tasks.tasks import transcribe_task
from app.chatbot.utils.aws.s3 import upload_file_to_s3
from app.chatbot.utils.aws.cloudwatch import create_cloudwatch_rule
from app.utils.utils import get_temp_file_path


def process_input(audio_file, text_input, image_file, language, user_id):
    translated_text = None
    image_tensor = None
    inputs = None
    temp_file_path = None
    image_file_url = None
    audio_file_url = None
    s3_bucket_name = os.environ.get("AWS_BUCKET_NAME")

    try:
        if audio_file:
            temp_file_path = get_temp_file_path(suffix=".wav")
            audio_file.save(temp_file_path)
            audio_file_url, audio_object_key = upload_file_to_s3(
                temp_file_path, s3_bucket_name, f"audios/{user_id}"
            )
            create_cloudwatch_rule(
                audio_object_key, "plantid-chatbot-image-remover", delay_minutes=10080
            )
            transcription_result = transcribe_task.delay(temp_file_path, language)
            transcript = transcription_result.get()

            if language != "English":
                translated_text = TranslationService.get_translation(
                    source_lang=language,
                    target_lang="English",
                    source_text=transcript,
                )
            else:
                translated_text = transcript

        elif text_input:
            if language != "English":
                translated_text = TranslationService.get_translation(
                    source_lang=language,
                    target_lang="English",
                    source_sentence=text_input,
                )
            else:
                translated_text = text_input

        if image_file:
            filename = secure_filename(image_file.filename)
            temp_file_path = get_temp_file_path(
                suffix=f".{filename.rsplit('.', 1)[1].lower()}"
            )
            image_file.save(temp_file_path)
            image_file_url, image_object_key = upload_file_to_s3(
                temp_file_path, s3_bucket_name, f"images/{user_id}"
            )
            create_cloudwatch_rule(
                image_object_key, "plantid-chatbot-image-remover", delay_minutes=10080
            )
            image = Image.open(temp_file_path)

            image_tensor = current_app.llava_processor(
                images=image, return_tensors="pt"
            ).pixel_values.to(current_app.llava_model.device)

        if translated_text:
            text_input = (
                translated_text + "\n<image>" if image_tensor else translated_text
            )
        else:
            text_input = "<image>" if image_tensor else None

        if text_input:
            inputs = current_app.llava_processor(
                text=text_input, images=image_tensor, return_tensors="pt"
            ).to(current_app.llava_model.device)

    except Exception as e:
        chat_logger.error(f"Error in process_input: {e}")
        raise Exception("Error processing input")

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return inputs, translated_text, image_file_url, audio_file_url
