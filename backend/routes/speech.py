import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from models.user import User
from dependencies import get_current_user
from services.transcription_service import transcribe_audio
from services.emergency_service import analyze_text_for_emergency, trigger_alert
from utils.transcription_cleanup import normalize_transcription

router = APIRouter()

# Directory to temporarily store uploaded audio files
UPLOAD_DIR = "temp_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS = {".webm", ".wav", ".mp3", ".ogg", ".m4a", ".mp4", ".flac"}
MAX_AUDIO_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB max

@router.post("/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    language: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts an uploaded audio file from an authenticated user and returns the transcribed text.
    """
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file provided")

    raw_filename = audio.filename or "recording.webm"
    ext = os.path.splitext(raw_filename)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        ext = ".webm"

    # Generate cryptographically random secure filename to prevent path traversal
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        # Read content with size limit enforcement
        content = await audio.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")
        if len(content) > MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Audio file exceeds maximum size limit of 15 MB.")

        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        # Call the transcription service with language support (e.g., 'ml' for Malayalam)
        transcription_result = transcribe_audio(file_path, language=language)
        raw_text = transcription_result["text"]
        detected_language = transcription_result["detected_language"]
        
        # Apply normalization to fix common Whisper mistakes
        text = normalize_transcription(raw_text)
        
        # Analyze transcription text for emergencies
        emergency_status = analyze_text_for_emergency(text)
        if emergency_status["is_emergency"]:
            trigger_alert(
                user_id=current_user.id, 
                text=text, 
                triggered_keywords=emergency_status["triggered_keywords"]
            )
        
        return {
            "transcription": text,
            "detected_language": detected_language,
            "emergency_status": emergency_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
