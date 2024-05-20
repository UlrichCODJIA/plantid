from utils.audio_processing import split_audio, convert_to_wav
from multiprocessing import Pool
import functools
import tenacity
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
        transcript = current_app.whisper_base_model.transcribe(
            audio_path, language=language
        )
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
        transcript = current_app.whisper_yoruba_pipeline(audio_path)["text"]
        return transcript
    except Exception as e:
        print(f"Error transcribing Yoruba audio: {e}")
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
        transcript = current_app.whisper_fon_pipeline(audio_path)["text"]
        return transcript
    except Exception as e:
        print(f"Error transcribing Fon audio: {e}")
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
        # Split audio into segments
        segments = split_audio(audio_path)

        # Convert segments to WAV format
        wav_segments = [convert_to_wav(segment) for segment in segments]

        # Perform parallel transcription using multiprocessing
        with Pool() as pool:
            transcripts = pool.map(transcribe_audio, wav_segments)

        return " ".join(transcripts)
    except Exception as e:
        print(f"Error transcribing video: {e}")
        raise
