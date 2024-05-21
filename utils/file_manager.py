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


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print(
            "  To split: python file_manager.py split "
            "path/to/largefile.pt [chunk_size_in_MB]"
        )
        print(
            "  To join: python file_manager.py join path/to/output.pt part0 part1 ..."
        )
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "split":
        if len(sys.argv) < 3:
            print(
                "Usage: python file_manager.py split "
                "path/to/largefile.pt [chunk_size_in_MB]"
            )
            sys.exit(1)
        file_path = sys.argv[2]
        chunk_size = (
            int(sys.argv[3]) * 1024 * 1024
            if len(sys.argv) > 3
            else 2 * 1024 * 1024 * 1024
        )
        split_file(file_path, chunk_size)
    elif mode == "join":
        if len(sys.argv) < 4:
            print(
                "Usage: python file_manager.py join path/to/output.pt part0 part1 ..."
            )
            sys.exit(1)
        output_path = sys.argv[2]
        input_paths = sys.argv[3:]
        join_files(output_path, input_paths)
    else:
        print("Invalid mode. Use 'split' or 'join'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
