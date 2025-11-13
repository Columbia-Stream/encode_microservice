import os
import tempfile
import subprocess
from google.cloud import storage
import functions_framework

# Config via env vars
OUTPUT_PREFIX = "encodings"  # where to write HLS
FFMPEG_PATH   = "ffmpeg"  # path to ffmpeg binary


_storage_client = None
def storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()  # uses Cloud Run/Functions ADC
    return _storage_client


@functions_framework.cloud_event
def encode(cloud_event):
    data = cloud_event.data
    in_bucket_name = data["bucket"]
    key = data["name"]   
    out_bucket_name = "hls-encodings"         

    # 1) Ignore non-mp4 and outputs (avoid loops)
    if not key.lower().endswith(".mp4"):
        print(f"Skip non-mp4: {key}")
        return
    if key.startswith(OUTPUT_PREFIX + "/"):
        print(f"Skip outputs path: {key}")
        return

    base = os.path.splitext(os.path.basename(key))[0]          # "12"
    out_prefix = f"{OUTPUT_PREFIX}/{base}/"                    # encodings/12/

    print(f"Encoding gs://{in_bucket_name}/{key} -> gs://{out_bucket_name}/{out_prefix}")

    client = storage_client()
    in_bucket  = client.bucket(in_bucket_name)
    out_bucket = client.bucket(out_bucket_name)

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

        # 4) Upload playlist + segments to encodings/
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

    print(f"Done: gs://{out_bucket_name}/{out_prefix} (playlist.m3u8 + segments)")