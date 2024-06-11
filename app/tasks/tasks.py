from datetime import datetime
import logging
from celery import shared_task
from flask import current_app

from app.chatbot.utils.speech_recognition.speech_recognition import (
    transcribe_audio,
    transcribe_fon,
    transcribe_yoruba,
)
from app.chatbot.utils.text_to_image.text_to_image import (
    TextToImageGenerator,
)
from app.extensions import celery_manager
from app.models.Conversation import Conversation
from logger import configure_logger

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/chat.log")

celery_app = celery_manager.get_celery_app()


@shared_task(name="transcribe_task", ignore_result=False)
def transcribe_task(audio_path, language):
    try:
        if language == "yoruba":
            transcript = transcribe_yoruba(audio_path)
        elif language == "fon":
            transcript = transcribe_fon(audio_path)
        else:
            transcript = transcribe_audio(audio_path, language=language)
        return transcript
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return "Could not transcribe audio"


# Image generation task
@shared_task(name="generate_image_task", ignore_result=False)
def generate_image_task(prompt, conversation_id):
    with current_app.app_context():
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation:
            return

        conversation.image_task_status = "STARTED"
        conversation.image_task_started_at = datetime.utcnow()
        conversation.save()

        try:
            generate_image_data = (
                TextToImageGenerator.generate_image_from_text_stability(prompt=prompt)
            )
            conversation.image_task_status = "SUCCESS"
            conversation.image_task_completed_at = datetime.utcnow()
            return generate_image_data[0]["image_url"]
        except Exception as e:
            conversation.image_task_status = "FAILURE"
        finally:
            conversation.save()
