import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.transcription_service import transcribe_audio
from services.emergency_service import analyze_text_for_emergency, trigger_alert
from utils.transcription_cleanup import normalize_transcription

router = APIRouter()

# Directory to temporarily store uploaded audio files
UPLOAD_DIR = "temp_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/transcribe")
async def transcribe_speech(audio: UploadFile = File(...), language: str = Form(None)):
    """
    Accepts an uploaded audio file and returns the transcribed text.
    """
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file provided")
        
    # Save the uploaded file temporarily
    file_path = os.path.join(UPLOAD_DIR, audio.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
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
                user_id="default_user", 
                text=text, 
                triggered_keywords=emergency_status["triggered_keywords"]
            )
        
        return {
            "transcription": text,
            "detected_language": detected_language,
            "emergency_status": emergency_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
