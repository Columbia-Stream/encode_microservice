import argparse
import mimetypes
from pathlib import Path
from google.cloud import storage
import mysql.connector


def upload(bucket_name: str, local_file: str, object_name: str | None = None) -> str:
    client = storage.Client()  # uses ADC (gcloud or GOOGLE_APPLICATION_CREDENTIALS)
    bucket = client.bucket(bucket_name)

    src = Path(local_file)
    if not src.exists():
        raise FileNotFoundError(f"Local file not found: {src}")

    if object_name is None:
        object_name = src.name 

    content_type, _ = mimetypes.guess_type(src.as_posix())
    blob = bucket.blob(object_name)
    blob.upload_from_filename(src.as_posix(), content_type=content_type or "application/octet-stream")

    print(f"✅ Uploaded {src} → gs://{bucket_name}/{object_name}")
    return f"gs://{bucket_name}/{object_name}"


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Upload a file to GCS to trigger the encoder.")
    p.add_argument("--bucket", required=True, help="GCS bucket name (e.g., columbia_stream_video_storage)")
    p.add_argument("--file", required=True, help="Local path to MP4 (e.g., ./test.mp4)")
    p.add_argument("--object", help="Object name in bucket (default: basename of --file, e.g., 12.mp4)")
    args = p.parse_args()

    upload(args.bucket, args.file, args.object)

    