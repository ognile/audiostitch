from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Configure FFmpeg BEFORE importing pydub
import imageio_ffmpeg
from pydub import AudioSegment
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

# Now import processor
from audio_processor import AudioProcessor

app = FastAPI()

# Initialize processor once
processor = AudioProcessor()

@app.post("/")
async def process_audio(
    file: UploadFile = File(...),
    padding: int = Form(150),
    crossfade: int = Form(50)
):
    try:
        print(f"Processing file: {file.filename}")
        
        # Read file
        file_bytes = await file.read()
        print(f"Read {len(file_bytes)} bytes")
        
        # Process
        print(f"Starting audio processing with padding={padding}, crossfade={crossfade}")
        processed_audio = processor.process_audio(file_bytes, padding, crossfade)
        print("Audio processing complete")
        
        # Save
        filepath = Path(f"/tmp/processed_{uuid.uuid4()}.mp3")
        print(f"Exporting to {filepath}")
        processed_audio.export(filepath, format="mp3")
        print("Export complete")
        
        return FileResponse(filepath, media_type="audio/mpeg", filename="processed.mp3")
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"FULL ERROR:\n{error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/")
def health():
    return {"status": "ok"}
