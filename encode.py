import os
import ffmpeg
import asyncio
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "columbia-stream-2bd40d5335f9.json"

def save_hls_gcs(local_encodings, bucket_name, video_id):
    
    temp_path = os.path.join(local_encodings, str(video_id))
    filenames = [f for f in os.listdir(temp_path)]
    
    storage_client = storage.Client(
        
    )
    bucket = storage_client.bucket(bucket_name)
    
    for filename in filenames:
        # Prepend video_id as a folder prefix in GCS path
        blob_name = f"{video_id}/{filename}"
        blob = bucket.blob(blob_name)
        
        try:
            file_path = os.path.join(temp_path, filename)
            blob.upload_from_filename(file_path)
            print(f"Successfully uploaded {filename} to gs://{bucket_name}/{blob_name}")
        except Exception as e:
            print(f"Failed to upload {filename}: {e}")
    return f"gs://{bucket_name}/{video_id}/playlist.m3u8"
            


async def convert_to_hls(input_mp4_path: str, video_id: int, segment_duration: int = 10):
    """
    Convert MP4 -> HLS (m3u8 + .ts) asynchronously.
    Returns the path to the generated .m3u8 playlist.
    """
    os.makedirs(f"local_encodings/{str(video_id)}", exist_ok=True)

    playlist_path = os.path.join("local_encodings", str(video_id), "playlist.m3u8")
    segment_pattern = os.path.join("local_encodings", str(video_id), "chunk_%04d.ts")

    # Build CLI args with ffmpeg-python, then run with asyncio
    stream = (
        ffmpeg
        .input(input_mp4_path)
        # Choose codecs (copy if already h264/aac and you want to avoid re-encode):
        .output(
            playlist_path,
            format="hls",
            hls_time=segment_duration,
            hls_list_size=0,              # keep all segments (VOD)
            hls_playlist_type="vod",
            hls_flags="independent_segments",
            hls_segment_filename=segment_pattern,
            **{
                "c:v": "h264",
                "preset": "veryfast",     # adjust as needed
                "crf": 20,                # quality target (lower=better)
                "c:a": "aac",
                "ar": 48000,
                "b:a": "128k",
                # optional GOP control: roughly 2s for typical 30fps -> g=60
                "g": 60,
            }
        )
    )

    cmd = stream.compile()
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        # surface ffmpeg errors
        raise RuntimeError(f"FFmpeg failed ({proc.returncode}):\n{stderr.decode('utf-8', 'ignore')}")

    return playlist_path

#asyncio.run(convert_to_hls("test.mov", 12))
save_hls_gcs("local_encodings", "columbiastream_video_storage", 12)