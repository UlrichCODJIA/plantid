import json


def encode_transcript(transcript, char_map):
    """Encodes a transcript string into a list of integers.

    Args:
        transcript: The Fongbe transcript string.
        char_map: A dictionary mapping characters to integers.

    Returns:
        A list of integers representing the encoded transcript.
    """

    encoded = [char_map[char] for char in transcript]
    return encoded


def main():
    """Loads the character map and encodes example transcripts."""

    with open("char_map.json", "r") as f:
        char_map = json.load(f)

    transcripts = [
        "mεɖe ɖu nu bɔ mεɖe ɔ nu sin",
        "gbɔsu donu gbɔsi",
        "a yi gbɔjε kpεɖe a",
    ]

    for transcript in transcripts:
        encoded = encode_transcript(transcript, char_map)
        print(f"Transcript: {transcript}")
        print(f"Encoded: {encoded}\n")


if __name__ == "__main__":
    main()
