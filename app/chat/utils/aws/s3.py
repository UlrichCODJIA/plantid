import os

from app.extensions import s3


def upload_file_to_s3(file_path, bucket_name, folder, object_name=None):
    if object_name is None:
        object_name = file_path

    file_name = os.path.basename(file_path)
    s3_object_key = f"{folder}/{file_name}"

    s3.upload_file(file_path, bucket_name, s3_object_key)

    file_url = f"https://{bucket_name}.s3.amazonaws.com/{bucket_name}/{s3_object_key}"
    return file_url, object_name
