import os
import ffmpeg
import boto3
import asyncio

def save_hls_s3(local_hls_dir, s3_bucket, s3_prefix):
    s3 = boto3.client('s3')
    for filename in os.listdir(local_hls_dir):
        local_file = os.path.join(local_hls_dir, filename)
        s3_key = os.path.join(s3_prefix, filename)
        s3.upload_file(local_file, s3_bucket, s3_key)
        print(f"Uploaded {local_file} to s3://{s3_bucket}/{s3_key}")
    

async def convert_mp4_to_hls(input_mp4_path: str, output_name: str, segment_duration: int = 10):
    """
    Convert MP4 -> HLS (m3u8 + .ts) asynchronously.
    Returns the path to the generated .m3u8 playlist.
    """
    os.makedirs("local_encodings", exist_ok=True)

    if not output_name.endswith(".m3u8"):
        output_name += ".m3u8"

    playlist_path = os.path.join("local_encodings", output_name)
    segment_pattern = os.path.join("local_encodings", output_name.replace(".m3u8", "_%04d.ts"))

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
        .global_args("-hide_banner", "-y")
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