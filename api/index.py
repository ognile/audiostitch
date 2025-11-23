from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from pathlib import Path

# Configure FFmpeg BEFORE importing Pydub
import imageio_ffmpeg
from pydub import AudioSegment
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
print(f"Using FFmpeg binary from: {AudioSegment.converter}")

from api.audio_processor import AudioProcessor

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure temp directory exists (use /tmp for serverless environments)
TEMP_DIR = Path("/tmp")
TEMP_DIR.mkdir(exist_ok=True)


# Lazy initialization to avoid cold start overhead
_processor = None

def get_processor():
    global _processor
    if _processor is None:
        _processor = AudioProcessor()
    return _processor

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
        processed_audio = get_processor().process_audio(
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
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR in process_audio: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/")
def read_root():
    return {"message": "SmoothFlow API is running"}
