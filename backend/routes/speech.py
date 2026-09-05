import os
import shutil
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from dependencies import get_current_user
from services.transcription_service import transcribe_audio, normalize_language_code, get_tts_lang_code
from services.emergency_service import analyze_text_for_emergency, trigger_alert
from utils.transcription_cleanup import normalize_transcription

logger = logging.getLogger(__name__)
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
    conversation_language: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts an uploaded audio file from an authenticated user and returns the transcribed text.
    Applies authoritative language determination (Priority 1: Explicit, Priority 2: Profile, Priority 3: Conversation, Priority 4: AUTO).
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
            
        # Development-only diagnostic metadata (safe: no private audio/speech or medical content logged)
        try:
            from services.audio_preprocessor import analyze_audio
            meta = analyze_audio(file_path)
            logger.info(
                f"[AUDIO DIAGNOSTIC] format='{meta.get('format')}' | codec='{meta.get('codec')}' | "
                f"sr={meta.get('sample_rate')}Hz | ch={meta.get('channels')} | dur={meta.get('duration_s')}s | "
                f"peak={meta.get('peak_amplitude')} | rms={meta.get('rms_amplitude')} | "
                f"clip_pct={meta.get('clipping_pct')}% | lead_silence={meta.get('leading_silence_s')}s | "
                f"trail_silence={meta.get('trailing_silence_s')}s"
            )
        except Exception as diag_err:
            logger.debug(f"[AUDIO DIAGNOSTIC] Analysis skipped: {diag_err}")

        # Resolve user's configured profile voice language (Priority 2)
        profile_lang = None
        try:
            from services.notification_preference_service import get_user_notification_preferences
            prefs = get_user_notification_preferences(db, current_user)
            if prefs and prefs.voice_language and prefs.voice_language.lower() not in ("auto", "none", ""):
                profile_lang = prefs.voice_language
        except Exception as pref_err:
            logger.debug(f"[SPEECH] Notification preferences lookup skipped: {pref_err}")

        if not profile_lang:
            try:
                from models.ale import BehaviourProfile
                bprof = db.query(BehaviourProfile).filter(BehaviourProfile.user_id == str(current_user.id)).first()
                if bprof and bprof.preferred_language and bprof.preferred_language.lower() not in ("auto", "none", ""):
                    profile_lang = bprof.preferred_language
            except Exception as ale_err:
                logger.debug(f"[SPEECH] Behaviour profile lookup skipped: {ale_err}")

        # Call the transcription service with full language hierarchy
        transcription_result = transcribe_audio(
            file_path,
            language=language,
            profile_language=profile_lang,
            conversation_language=conversation_language
        )
        raw_text = transcription_result.get("text", "")
        detected_language = transcription_result.get("detected_language", "english")
        norm_lang = transcription_result.get("normalized_language") or normalize_language_code(detected_language) or "en"
        is_usable = transcription_result.get("is_usable", True)
        needs_clarification = transcription_result.get("needs_clarification", False)
        clarification_prompt = transcription_result.get("clarification_prompt")
        
        # Apply normalization to fix common Whisper mistakes
        text = normalize_transcription(raw_text) if raw_text else ""
        
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
            "normalized_language": norm_lang,
            "effective_language": norm_lang,
            "is_usable": is_usable,
            "needs_clarification": needs_clarification,
            "clarification_prompt": clarification_prompt,
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
