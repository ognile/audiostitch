from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from pathlib import Path
from api.audio_processor import AudioProcessor
from pydub import AudioSegment

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure temp directory exists
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

import imageio_ffmpeg

# Configure Pydub to use imageio-ffmpeg's binary
# This works cross-platform (local Mac, Vercel Linux) automatically
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
print(f"Using FFmpeg binary from: {AudioSegment.converter}")

processor = AudioProcessor()

@app.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    padding: int = Form(150),
    crossfade: int = Form(50)
):
    try:
        # Read file
        file_bytes = await file.read()
        
        # Process
        processed_audio = processor.process_audio(
            file_bytes, 
            padding_ms=padding, 
            crossfade_ms=crossfade
        )
        
        # Save to temp file
        filename = f"processed_{uuid.uuid4()}.mp3"
        filepath = TEMP_DIR / filename
        
        # Export
        processed_audio.export(filepath, format="mp3")
        
        # Return file
        return FileResponse(filepath, media_type="audio/mpeg", filename="processed.mp3")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "SmoothFlow API is running"}
