from app.chat.utils.speech_recognition.speech_recognition import transcribe_audio, transcribe_fon, transcribe_yoruba
from app.extensions import celery_logger, celery_manager

# from celery import shared_task

celery_app = celery_manager.get_celery_app()


# @shared_task(name="transcribe_task", ignore_result=False)
def transcribe_task(audio_path: str, language: str):
    try:
        if language.lower() == "fon":
            celery_logger.info("Transcribing Fon audio")
            transcript = transcribe_fon(audio_path)
        elif language.lower() == "yoruba":
            celery_logger.info("Transcribing Yoruba audio")
            transcript = transcribe_yoruba(audio_path)
        else:
            celery_logger.info("Transcribing audio")
            transcript = transcribe_audio(audio_path, language=language)
        return transcript
    except Exception as e:
        celery_logger.error(f"Transcription error: {e}")
        return "Could not transcribe audio"
