FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    OUTPUT_PREFIX=encodings \
    FFMPEG_PATH=/workspace/ffmpeg \
    # Tell Functions Framework which module/file and function to load:
    FUNCTION_SOURCE=encode \
    FUNCTION_TARGET=encode

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your code (must include encode.py) and the ffmpeg binary
COPY . .
RUN chmod +x /workspace/ffmpeg || true

EXPOSE 8080

# CloudEvent function (GCS finalize trigger)
CMD ["functions-framework", "--signature-type=cloudevent", "--port=8080"]