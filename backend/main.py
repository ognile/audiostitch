from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from pathlib import Path
from audio_processor import AudioProcessor

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

# Check for FFmpeg
if shutil.which("ffmpeg"):
    print("FFmpeg found in system path.")
else:
    # Check for local ffmpeg binary (common in some deployments)
    local_ffmpeg = Path("ffmpeg")
    if local_ffmpeg.exists():
        print("Found local ffmpeg binary.")
        AudioSegment.converter = str(local_ffmpeg.absolute())
    else:
        print("WARNING: FFmpeg not found! Audio processing will fail.")

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
