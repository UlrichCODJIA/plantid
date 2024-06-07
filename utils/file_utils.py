import os
import sys


def split_file(file_path, chunk_size=2 * 1024 * 1024 * 1024):
    """Splits a large file into smaller parts."""
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        part_num = 0
        while file_size > 0:
            part_size = min(file_size, chunk_size)
            part_file_name = f"{file_path}.part{part_num}"
            with open(part_file_name, "wb") as chunk_file:
                chunk_file.write(f.read(part_size))
            print(f"Created part: {part_file_name}")
            file_size -= part_size
            part_num += 1


def join_files(output_path, input_paths):
    """Joins smaller parts into the original file."""
    with open(output_path, "wb") as output_file:
        for file_path in input_paths:
            with open(file_path, "rb") as input_file:
                output_file.write(input_file.read())
            print(f"Added part: {file_path} to {output_path}")


def find_and_split_large_files(folder_path, chunk_size=2 * 1024 * 1024 * 1024):
    """Finds and splits all large files in the specified folder."""
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) >= chunk_size:
                split_file(file_path, chunk_size)
                os.remove(file_path)


def find_and_join_parts(folder_path):
    """Finds and joins all file parts in the specified folder."""
    parts_dict = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if ".part" in file:
                base_name = file.split(".part")[0]
                if base_name not in parts_dict:
                    parts_dict[base_name] = []
                parts_dict[base_name].append(os.path.join(root, file))

    for base_name, parts in parts_dict.items():
        parts.sort()  # Ensure the parts are in the correct order
        join_files(base_name, parts)
        for part in parts:
            os.remove(part)


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python file_manager.py <split|join> "
            "[folder_path] [chunk_size_in_MB]"
        )
        sys.exit(1)

    mode = sys.argv[1]
    folder_path = sys.argv[2] if len(sys.argv) > 2 else "."

    if mode == "split":
        chunk_size = (
            int(sys.argv[3]) * 1024 * 1024
            if len(sys.argv) > 3
            else 2 * 1024 * 1024 * 1024
        )
        find_and_split_large_files(folder_path, chunk_size)
    elif mode == "join":
        find_and_join_parts(folder_path)
    else:
        print("Invalid mode. Use 'split' or 'join'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
