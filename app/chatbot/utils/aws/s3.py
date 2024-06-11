from app.extensions import s3


def upload_file_to_s3(file_path, bucket_name, folder, object_name=None):
    if object_name is None:
        object_name = file_path

    # Upload the file
    s3.upload_file(file_path, bucket_name, object_name)

    # Construct the S3 file URL
    file_url = f"https://{bucket_name}.s3.amazonaws.com/{folder}/{object_name}"
    return file_url, object_name
