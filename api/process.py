from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
from pathlib import Path

# Configure FFmpeg BEFORE importing Pydub
import imageio_ffmpeg
from pydub import AudioSegment
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

from api.audio_processor import AudioProcessor

app = FastAPI()

# Lazy initialization
_processor = None

def get_processor():
    global _processor
    if _processor is None:
        _processor = AudioProcessor()
    return _processor

@app.post("/")
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
        filepath = Path(f"/tmp/processed_{uuid.uuid4()}.mp3")
        
        # Export
        processed_audio.export(filepath, format="mp3")
        
        # Return file
        return FileResponse(filepath, media_type="audio/mpeg", filename="processed.mp3")
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

# Vercel handler
handler = app
