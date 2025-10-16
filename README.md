# Encode Microservice

## Overview

Encode to HLS → Convert MP4 to .m3u8 playlist + .ts segments. → Upload to GCS 


## Endpoints
```/encode```

**Purpose:** Convert an MP4 file into HLS format for adaptive streaming.

**Method:** POST

**Args:**

```url``` – Path or URL to input MP4/MOV video.

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