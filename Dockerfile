# ---- Base image ----
    FROM python:3.11-slim

    # Prevent Python from buffering stdout/stderr
    ENV PYTHONUNBUFFERED=1 \
        PIP_NO_CACHE_DIR=1 \
        # Functions Framework will listen on $PORT (Cloud Run/Functions sets it)
        PORT=8080 \
        # Where your HLS outputs go inside the bucket
        OUTPUT_PREFIX=encodings \
        # Path to your bundled ffmpeg binary inside the image
        FFMPEG_PATH=/workspace/ffmpeg
    
    # Optional: install minimal OS deps (ca-certificates, curl for debugging)
    RUN apt-get update && apt-get install -y --no-install-recommends \
          ca-certificates \
        && rm -rf /var/lib/apt/lists/*
    
    # ---- App code + ffmpeg ----
    WORKDIR /workspace
    
    # If you have a requirements.txt, copy & install first (better layer caching)
    COPY requirements.txt .
    RUN pip install --upgrade pip && pip install -r requirements.txt
    
    # Copy your function code (e.g., main.py) and the bundled ffmpeg
    # Make sure the ffmpeg file exists at repo root or adjust the path below.
    COPY . .
    
    # Ensure ffmpeg is executable (in case the exec bit wasn’t preserved by git)
    RUN chmod +x /workspace/ffmpeg || true
    
    # (Optional) quick sanity check; comment out if your binary isn’t static and this fails
    # RUN /workspace/ffmpeg -version
    
    # Cloud Functions/Run will send requests to $PORT
    EXPOSE 8080
    
    # Start the Functions Framework for a CloudEvent function
    # --target must match your function name in main.py (encode)
    # --signature-type=cloudevent is required for GCS triggers
    CMD ["functions-framework", "--target=encode", "--signature-type=cloudevent", "--port=8080"]