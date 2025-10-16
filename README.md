# Encode Microservice

## Overview

Upload a video → Stored temporarily or uploaded directly to S3.

Encode to HLS → Convert MP4 to .m3u8 playlist + .ts segments.

Stream content → Client (e.g. browser video player) fetches playlist and segments via /stream-segment.

## Endpoints
```/encode```

**Purpose:** Convert an MP4 file into HLS format for adaptive streaming.

**Method:** POST

**Args:**

```input_mp4_path``` – Path or URL to input MP4/MOV video.

```video_id``` - ID of video in database

```segment_duration (optional)``` – Duration (in seconds) for each .ts segment (default: 10s).

**Implementation:**
Uses ffmpeg to generate a .m3u8 playlist file and ultiple .ts video segment files. Save to local directory then uploads to GCS.

**Returns:**
Path to .m3u8 playlist file on GCP

---
### Upload Helper
upload_to_s3(file_path, bucket_name, object_name)

Purpose: Uploads encoded files or segments to Google Cloud Storage

venv: encode_service