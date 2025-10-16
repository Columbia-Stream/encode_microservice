import os
from fastapi import APIRouter, HTTPException, requests
from fastapi import Query, Path
from typing import Optional
from encode import convert_to_hls, save_hls_gcs
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter()

@router.post("/encode")
async def encode_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    encoded_video_local = await convert_to_hls(url)
    encoded_video_gcs = save_hls_gcs(encoded_video_local, 'your-s3-bucket', 'your-s3-prefix')
    return {"message": f"Playlist file saved at {encoded_video_gcs}"}
    

def fetch_file(url: str, chunk_size: int = 4096):
    # For any object storage (public/presigned/private URLs)
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size):
        if chunk:
            yield chunk
            
def guess_mime_type(filename: str) -> str:
    # Types for HLS streaming
    if filename.endswith('.m3u8'):
        return 'application/vnd.apple.mpegurl'
    elif filename.endswith('.ts'):
        return 'video/mp2t'
    return 'application/octet-stream'

@router.get("/stream-segment")
def stream_ts_segment(url: str = Query(..., description="URL to m3u8 file in object storage")):
    mime_type = guess_mime_type(url)
    return StreamingResponse(fetch_file(url), media_type=mime_type)
