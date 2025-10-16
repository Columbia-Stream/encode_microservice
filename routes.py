import json
import os
from fastapi import APIRouter, HTTPException, requests
from fastapi import Query, Path
from typing import Optional
from encode import convert_to_hls, save_hls_gcs
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter()

@router.post("/encode", responses={200: {"playlist_url": "PLAYLIST URL ON GCS"}})
async def encode_video(url: str, video_id: int, segment_duration: Optional[int] = Query(10, description="Segment duration in seconds")):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    encoded_video_local = await convert_to_hls(url, video_id, segment_duration)
    encoded_video_gcs = save_hls_gcs(encoded_video_local, 'your-s3-bucket', 'your-s3-prefix')
    resp = {"playlist_url": encoded_video_gcs}
    return json.dumps(resp)
    
