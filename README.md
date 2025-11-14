# Encode Microservice

## Overview

Encode to HLS → Convert MP4 to .m3u8 playlist + .ts segments. → Upload to ```hls-encodings``` GCS bucket 


## Endpoints
```/encode```

**Purpose:** Tool to encode mp4/mov to HLS format. Executed as Cloud Run function whenever raw video is uploaded to ```columbia_stream_video_storage``` bucket. Updates Videos DB with playlist path on GCS.

**Implementation:**
Uses ffmpeg to generate a .m3u8 playlist file and ultiple .ts video segment files. Save to local directory then uploads to GCS.


Deploy trigger function to encode video:
```
gcloud functions deploy encode \                                      
  --gen2 \
  --runtime=python311 \
  --entry-point=encode \
  --trigger-bucket=columbia_stream_video_storage \
  --set-env-vars=OUTPUT_PREFIX=encodings,FFMPEG_PATH=/workspace/ffmpeg \
  --memory=2048MB \
  --timeout=540s

```

Update CORS:
```
gcloud storage buckets update gs://<BUCKET_NAME> --cors-file=cors.json
```