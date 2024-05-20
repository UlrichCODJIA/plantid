from pydub import AudioSegment
import functools
import tenacity


@functools.lru_cache(maxsize=None)
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
def split_audio(audio_path, chunk_size=60):
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
    try:
        wav_segment = audio_segment.export(format="wav")
        return wav_segment
    except Exception as e:
        print(f"Error converting audio to WAV: {e}")
        raise
