from pydub import AudioSegment
import functools
import tenacity


@functools.lru_cache(maxsize=None)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
def split_audio(audio_path, chunk_size=60):
    """
    Split the audio file into smaller segments.

    Args:
        audio_path (str): The path to the audio file.
        chunk_size (int, optional): The size of each segment in seconds. Defaults to 60.

    Returns:
        list: A list of audio segments.
    """
    try:
        audio = AudioSegment.from_wav(audio_path)
        segments = []
        for i in range(0, len(audio), chunk_size * 1000):
            segment = audio[i : i + chunk_size * 1000]
            segments.append(segment)
        return segments
    except Exception as e:
        print(f"Error splitting audio: {e}")
        raise


def convert_to_wav(audio_segment):
    """
    Convert an audio segment to WAV format.

    Args:
        audio_segment (pydub.AudioSegment): The audio segment to convert.

    Returns:
        pydub.AudioSegment: The converted audio segment in WAV format.
    """
    try:
        wav_segment = audio_segment.export(format="wav")
        return wav_segment
    except Exception as e:
        print(f"Error converting audio to WAV: {e}")
        raise
