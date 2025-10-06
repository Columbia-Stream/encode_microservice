from fastapi import FastAPI
import routes

app = FastAPI(
    title="Streaming Video API",
    description="Endpoints for encoding and streaming video segments",
    version="0.1.0",
)

app.include_router(routes.router, prefix="/videos", tags=["Videos"])

@app.get("/")
def read_root():
    return {"message": "Upload Video Microservice is running"}