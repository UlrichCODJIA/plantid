import functools
from multiprocessing import Pool

import tenacity
from app.chat.utils.speech_recognition.audio_processing import convert_to_wav, split_audio
from app.extensions import logger
from flask import current_app


@functools.lru_cache(maxsize=None)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
def transcribe_audio(audio_path: str, language: str) -> str:
    """Transcribes an audio segment using the Whisper model.

    Args:
        audio_path (str): Path to the audio segment.
        language (str): Language of the audio

    Returns:
        str: The transcribed text.

    Raises:
        Exception: If the transcription process encounters an error.
    """
    try:
        logger.info(f"Transcribing audio: {audio_path}")
        transcript = current_app.whisper_base_model.transcribe(audio_path, language=language)
        logger.info(f"Transcription complete: {transcript['text'][:50]}")
        return transcript["text"]
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        raise


@functools.lru_cache(maxsize=None)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
def transcribe_yoruba(audio_path: str) -> str:
    """Transcribes a Yoruba audio segment.

    Args:
        audio_path (str): Path to the audio segment.

    Returns:
        str: The transcribed text.

    Raises:
        Exception: If the transcription process encounters an error.
    """
    try:
        logger.info(f"Transcribing Yoruba audio: {audio_path}")
        transcript = current_app.whisper_yoruba_model(audio_path)["text"]
        return transcript
    except Exception as e:
        logger.error(f"Error transcribing Yoruba audio: {e}")
        raise


@functools.lru_cache(maxsize=None)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
def transcribe_fon(audio_path: str) -> str:
    """Transcribes a Fon audio segment.

    Args:
        audio_path (str): Path to the audio segment.

    Returns:
        str: The transcribed text.

    Raises:
        Exception: If the transcription process encounters an error.
    """
    try:
        logger.info(f"Transcribing Fon audio: {audio_path}")
        transcript = current_app.whisper_fon_model(audio_path)["text"]
        return transcript
    except Exception as e:
        logger.error(f"Error transcribing Fon audio: {e}")
        raise


def transcribe(audio_path: str, language: str) -> str:
    """Transcribes an audio file by splitting it into segments
    and transcribing each segment in parallel.

    Args:
        audio_path (str): Path to the audio file.
        language (str): Language of the audio

    Returns:
        str: The complete transcribed text.

    Raises:
        Exception: If the transcription process encounters an error.
    """
    try:
        logger.info(f"Transcribing audio: {audio_path}")
        segments = split_audio(audio_path)
        logger.info(f"Audio split into {len(segments)} segments")
        wav_segments = [convert_to_wav(segment) for segment in segments]
        logger.info(f"Converted {len(wav_segments)} segments to WAV format")
        with Pool() as pool:
            transcripts = pool.map(transcribe_audio, wav_segments)
            logger.info(f"Transcribed {len(transcripts)} segments")

        return " ".join(transcripts)
    except Exception as e:
        logger.errorr(f"Error transcribing audio: {e}")
        raise
