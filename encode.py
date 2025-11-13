import os
import ffmpeg
import asyncio
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "columbia-stream-2bd40d5335f9.json"
import os
import tempfile
import subprocess
from google.cloud import storage
import functions_framework

# Config via env vars
OUTPUT_PREFIX = "encodings"  # where to write HLS
FFMPEG_PATH   = "ffmpeg"  # path to ffmpeg binary

storage_client = storage.Client()

@functions_framework.cloud_event
def encode(cloud_event):
    data = cloud_event.data
    bucket_name = data["bucket"]
    key = data["name"]                     # e.g., "12.mp4"

    # 1) Ignore non-mp4 and outputs (avoid loops)
    if not key.lower().endswith(".mp4"):
        print(f"Skip non-mp4: {key}")
        return
    if key.startswith(OUTPUT_PREFIX + "/"):
        print(f"Skip outputs path: {key}")
        return

    base = os.path.splitext(os.path.basename(key))[0]          # "12"
    out_prefix = f"{OUTPUT_PREFIX}/{base}/"                    # encodings/12/

    print(f"Encoding gs://{bucket_name}/{key} -> gs://{bucket_name}/{out_prefix}")

    in_bucket = storage_client.bucket(bucket_name)
    out_bucket = in_bucket  # same bucket

    with tempfile.TemporaryDirectory() as tmp:
        # 2) Download source to /tmp
        src_path = os.path.join(tmp, "input.mp4")
        in_bucket.blob(key).download_to_filename(src_path)

        # 3) FFmpeg -> HLS in /tmp
        playlist_path = os.path.join(tmp, "playlist.m3u8")
        segment_pattern = os.path.join(tmp, "seg_%04d.ts")

        cmd = [
            FFMPEG_PATH, "-hide_banner", "-y",
            "-i", src_path,
            "-c:v", "h264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-ar", "48000", "-b:a", "128k",
            "-g", "60",
            "-f", "hls",
            "-hls_time", "10",
            "-hls_playlist_type", "vod",
            "-hls_flags", "independent_segments",
            "-hls_segment_filename", segment_pattern,
            playlist_path,
        ]
        subprocess.run(cmd, check=True)

        # 4) Upload playlist + segments to encodings/12/
        # playlist
        out_blob = out_bucket.blob(out_prefix + "playlist.m3u8")
        out_blob.upload_from_filename(
            playlist_path, content_type="application/vnd.apple.mpegurl"
        )
        # segments
        for fname in sorted(os.listdir(tmp)):
            if fname.endswith(".ts"):
                seg_blob = out_bucket.blob(out_prefix + fname)
                seg_blob.upload_from_filename(
                    os.path.join(tmp, fname), content_type="video/mp2t"
                )

    print(f"Done: gs://{bucket_name}/{out_prefix} (playlist.m3u8 + segments)")