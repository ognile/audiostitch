from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid

# Configure FFmpeg
import imageio_ffmpeg
from pydub import AudioSegment
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

# Import processor (after pydub config)
import sys
sys.path.insert(0, '/var/task')  # Vercel path
from api.audio_processor import AudioProcessor

app = FastAPI()

# Init processor
processor = AudioProcessor()

@app.post("/")
async def handler(
    file: UploadFile = File(...),
    padding: int = Form(150),
    crossfade: int = Form(50)
):
    try:
        file_bytes = await file.read()
        processed = processor.process_audio(file_bytes, padding, crossfade)
        
        filepath = Path(f"/tmp/{uuid.uuid4()}.mp3")
        processed.export(filepath, format="mp3")
        
        return FileResponse(filepath, media_type="audio/mpeg", filename="processed.mp3")
    except Exception as e:
        import traceback
        print(f"ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
