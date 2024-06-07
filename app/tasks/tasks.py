from datetime import datetime, timedelta
import logging
import os
from celery import Celery
from celery.schedules import crontab

from multilingual_webapp.app.chatbot.utils.speech_recognition.speech_recognition import (
    transcribe_audio,
    transcribe_fon,
    transcribe_yoruba,
)
from multilingual_webapp.app.chatbot.utils.text_to_image.text_to_image import (
    TextToImageGenerator,
)
from multilingual_webapp.app.extensions import db
from multilingual_webapp.app.models.Conversation import Conversation
from multilingual_webapp.logger import configure_logger

logger = configure_logger(log_level=logging.DEBUG, log_file="logs/chatbot.log")

celery_app = Celery(__name__)


@celery_app.task(name="transcribe_task")
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
@celery_app.task(name="generate_image_task")
def generate_image_task(prompt):
    response = TextToImageGenerator.generate_image_from_text_stability(prompt=prompt)
    return response["image_url"]


# Schedule a task to delete old images
@celery_app.task(name="delete_old_images_task")
def delete_old_images_task():
    """Deletes image files associated with conversations older than a certain time."""
    try:
        image_expiry_time = datetime.utcnow() - timedelta(
            days=7
        )  # Set the desired expiry time (e.g., 7 days)

        old_conversations = Conversation.query.filter(
            # Filter conversations with image paths
            Conversation.image_path is not None,
            Conversation.timestamp < image_expiry_time,
        ).all()

        for conversation in old_conversations:
            if os.path.exists(conversation.image_path):
                os.remove(conversation.image_path)
                conversation.image_path = None  # Clear the path in the database
        db.session.commit()

        logger.info("Deleted old images successfully.")
    except Exception as e:
        logger.error(f"Error deleting old images: {e}")


# Schedule the cleanup task to run periodically
celery_app.conf.beat_schedule = {
    "delete_old_images": {
        "task": "delete_old_images_task",
        "schedule": crontab(minute=0, hour=0),  # Run daily at midnight
    }
}
