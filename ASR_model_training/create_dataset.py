import json
import os


def encode_transcript(transcript, char_map):
    """Encodes a transcript string into a list of integers (same as above)."""
    encoded = [char_map[char] for char in transcript]
    return encoded


def create_jsonl_dataset(csv_file, char_map, output_file):
    """Creates a JSONL dataset from the CSV file.

    Args:
        csv_file: Path to the CSV file (train.csv or test.csv).
        char_map: Dictionary mapping characters to integers.
        output_file: Path to the output JSONL file (train.jsonl or test.jsonl).
    """

    dataset = []
    with open(csv_file, "r") as f:
        next(f)
        for line in f:
            wav_filename, _, transcript = line.strip().split(",")
            encoded = encode_transcript(transcript, char_map)
            audio_uri = os.path.join(
                "gs://YOUR_BUCKET_NAME", wav_filename.lstrip("/")
            )
            dataset.append({"audio_uri": audio_uri, "transcript": encoded})

    with open(output_file, "w") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")


def main():
    """Loads the character map and creates the datasets."""

    with open("char_map.json", "r") as f:
        char_map = json.load(f)

    create_jsonl_dataset("train.csv", char_map, "train.jsonl")
    create_jsonl_dataset("test.csv", char_map, "test.jsonl")


if __name__ == "__main__":
    main()
