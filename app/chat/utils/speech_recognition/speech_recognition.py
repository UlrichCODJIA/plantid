import functools
from multiprocessing import Pool

import librosa
import tenacity
import torch
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
        transcription = current_app.whisper_base_model.transcribe(audio_path, language=language)
        transcription = transcription["text"] if isinstance(transcription, dict) else transcription
        logger.info(f"Transcription complete: {transcription[:50]}")
        return transcription
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
        # Load and preprocess the audio
        speech_array, sampling_rate = librosa.load(audio_path, sr=16000)
        logger.info(f"Loaded Yoruba audio: {audio_path}")
        inputs = current_app.whisper_yoruba_processor(speech_array, sampling_rate=16000, return_tensors="pt")
        logger.info(f"Preprocessed Yoruba audio: {audio_path}")
        # Generate transcription
        generated_ids = current_app.whisper_yoruba_model.generate(
            inputs.input_features,
            forced_decoder_ids=current_app.whisper_yoruba_processor.get_decoder_prompt_ids(
                language="yo", task="transcribe"
            ),
        )
        logger.info("Generated Yoruba transcription")
        transcription = current_app.whisper_yoruba_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        logger.info(f"Transcription complete: {transcription[:50]}")
        return transcription
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
        # Load and preprocess the audio
        speech_array, sampling_rate = librosa.load(audio_path, sr=16000)
        logger.info(f"Loaded Fon audio: {audio_path}")
        inputs = current_app.whisper_fon_processor(speech_array, sampling_rate=16000, return_tensors="pt")
        logger.info(f"Preprocessed Fon audio: {audio_path}")
        # Generate transcription
        with torch.no_grad():
            logits = current_app.whisper_fon_model(inputs.input_values).logits
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = current_app.whisper_fon_processor.batch_decode(predicted_ids)[0]
        logger.info("Generated Fon transcription")
        logger.info(f"Transcription complete: {transcription[:50]}")
        return transcription
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
