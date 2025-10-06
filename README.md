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

```input_mp4_path``` – Path or URL to input MP4 video.

```output_name``` – Desired output filename (e.g. movie.m3u8).

```segment_duration (optional)``` – Duration (in seconds) for each .ts segment (default: 10s).

**Implementation:**
Uses ffmpeg to generate a .m3u8 playlist file and ultiple .ts video segment files. Save to output directory: local_encodings/

---
```/stream-segment```

**Purpose:** Stream .m3u8 playlists or .ts video segments directly to clients.

**Method:** GET

**Query Parameter:**

url – Public or presigned URL of the HLS file (either .m3u8 or .ts).

**Implementation:**
<ul>
<li>Uses guess_mime_type() to determine content type.</li>
<li>Streams data chunk-by-chunk with StreamingResponse(fetch_file(url)).</li>
</ul>

Supported types:

.m3u8 → application/vnd.apple.mpegurl

.ts → video/mp2t

---
### Upload Helper
upload_to_s3(file_path, bucket_name, object_name)

Purpose: Uploads encoded files or segments to S3 storage (AWS or compatible).