import os
import re
import tempfile
import subprocess
from google.cloud import storage
import functions_framework
import mysql.connector
   
# Config via env vars
FFMPEG_PATH   = "ffmpeg"  # path to ffmpeg binary
host = '34.123.117.250'
port = 3306
user = 'root'
password = "Columbiacc@123"
db_name = "microservice-upload-db"
out_bucket_name = "hls_encodings"

_storage_client = None
def storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()  # uses Cloud Run/Functions ADC
    return _storage_client

def insert_gcs_path_db(video_id: int, gcs_path: str):
    mydb = mysql.connector.connect(
           host=host, 
           user=user,
           password=password,
           database=db_name 
    )
    cursor = mydb.cursor()
    cursor.execute("UPDATE Videos SET gcs_path = %s WHERE video_id = %s", (gcs_path, video_id))
    cursor.execute("UPDATE Videos SET status = %s WHERE video_id = %s", ("Completed", video_id))
    mydb.commit()
    
    print(f"Inserted into DB: {gcs_path}")
    cursor.close()
    mydb.close()
    
@functions_framework.cloud_event
def encode(cloud_event):
    data = cloud_event.data
    in_bucket_name = data["bucket"]
    key = data["name"]   # e.g., "raw/12/output_12.mp4"

    # Only accept keys like raw/<ID>/output_<ID>.mp4
    m = re.match(r'^raw/(?P<vid>[^/]+)/upload_(?P=vid)\.(?P<ext>mp4|mov)$', key, re.IGNORECASE)
    if not m:
        print(f"Skip (key does not match expected pattern): {key}")
        return

    video_id = m.group("vid")
    filetype = m.group("ext").lower()
    out_prefix = f"{video_id}/"
    print(f"Encoding gs://{in_bucket_name}/{key} -> gs://{out_bucket_name}/{out_prefix}")

    client = storage_client()
    in_bucket  = client.bucket(in_bucket_name)
    out_bucket = client.bucket(out_bucket_name)

    with tempfile.TemporaryDirectory() as tmp:
        # 2) Download source to /tmp
        src_path = os.path.join(tmp, f"input.{filetype}")
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
                
    insert_gcs_path_db(video_id, f"https://storage.googleapis.com/{out_bucket_name}/{out_prefix}playlist.m3u8")

    print(f"Done: gs://{out_bucket_name}/{out_prefix} (playlist.m3u8 + segments)")