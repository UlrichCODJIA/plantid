import os
from typing import Optional, Tuple

from app.chat.utils.aws.cloudwatch import create_cloudwatch_rule
from app.chat.utils.aws.s3 import upload_file_to_s3
from app.chat.utils.translation.translation import TranslationService
from app.extensions import chat_logger
from app.tasks.tasks import transcribe_task
from app.utils.utils import get_temp_file_path

# from celery.result import AsyncResult


def process_input(audio_file, text_input: str, language: str, user_id: str) -> Tuple[Optional[str], Optional[str]]:
    translated_text = None
    audio_file_url = None
    temp_file_path = None
    s3_bucket_name = os.environ.get("AWS_BUCKET_NAME")

    chat_logger.info(f"Processing input for user {user_id} in language: {language}")

    print("audio_file", audio_file)

    try:
        if audio_file:
            filename = audio_file.filename
            file_ext = os.path.splitext(filename)[1].lower()
            temp_file_path = get_temp_file_path(suffix=file_ext)
            chat_logger.debug(f"Temporary file path: {temp_file_path}")
            audio_file.save(temp_file_path)

            audio_file_url, audio_object_key = upload_file_to_s3(temp_file_path, s3_bucket_name, f"audios/{user_id}")
            chat_logger.info(f"Audio file uploaded: {audio_file_url}")

            create_cloudwatch_rule(audio_object_key, "plantid-chatbot-image-remover", delay_minutes=10080)
            chat_logger.debug(f"CloudWatch rule created for: {audio_object_key}")

            try:
                transcript = transcribe_task(temp_file_path, language)

                # try:
                #     async_result = AsyncResult(transcription_result.id)
                #     transcript = async_result.get(timeout=300)  # 5 minutes timeout

                #     if async_result.successful():
                #         chat_logger.info(f"Transcription completed successfully: {transcript[:50]}...")
                #     elif async_result.failed():
                #         chat_logger.error(f"Transcription task failed: {async_result.result}")
                #         raise Exception("Transcription task failed")
                #     else:
                #         chat_logger.warning(f"Transcription task ended with unexpected status: {async_result.status}")
                #         raise Exception("Transcription task ended with unexpected status")

                # except TimeoutError:
                #     chat_logger.error("Transcription task timed out after 5 minutes")
                #     raise Exception("Transcription took too long to complete")

                translated_text = (
                    TranslationService.get_translation(
                        source_lang=language,
                        target_lang="English",
                        source_text=transcript,
                    )
                    if language != "English"
                    else transcript
                )

                chat_logger.info(f"Translation completed: {translated_text[:50]}...")

            except Exception as e:
                chat_logger.error(f"Error during transcription or translation: {str(e)}", exc_info=True)
                raise

        elif text_input:
            translated_text = (
                TranslationService.get_translation(
                    source_lang=language,
                    target_lang="English",
                    source_text=text_input,
                )
                if language != "English"
                else text_input
            )

            chat_logger.info(f"Text input processed: {translated_text[:50]}...")

        return translated_text, audio_file_url

    except Exception as e:
        chat_logger.error(f"Error in process_input: {str(e)}", exc_info=True)
        raise

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            chat_logger.debug(f"Temporary file removed: {temp_file_path}")
