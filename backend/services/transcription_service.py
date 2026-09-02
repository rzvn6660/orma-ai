import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"
DEFAULT_TIMEOUT = 25.0

# Module-level cache for lazy local fallback model (never loaded at startup)
_cached_local_model = None

def _get_local_model():
    """
    Lazy-loads Faster-Whisper 'tiny' model only when local fallback is invoked.
    Never loads during startup or module import.
    """
    global _cached_local_model
    if _cached_local_model is None:
        logger.info("[TRANSCRIPTION] Initializing lazy local Faster-Whisper 'tiny' model fallback...")
        from faster_whisper import WhisperModel
        _cached_local_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _cached_local_model

def _transcribe_groq(file_path: str, api_key: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Submits audio to Groq hosted Whisper API.
    Zero local RAM overhead, fast cloud inference on LPU.
    """
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_content = f.read()

    files = {"file": (filename, file_content, "audio/webm")}
    data = {
        "model": GROQ_MODEL,
        "response_format": "verbose_json"
    }
    if language:
        data["language"] = language

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(GROQ_TRANSCRIPTION_URL, headers=headers, files=files, data=data)
    except httpx.TimeoutException as e:
        logger.error("[GROQ TRANSCRIPTION ERROR] Request timed out")
        raise RuntimeError("Speech transcription service timed out.") from e
    except Exception as e:
        logger.error(f"[GROQ TRANSCRIPTION ERROR] Network error: {type(e).__name__}")
        raise RuntimeError("Failed to connect to speech transcription service.") from e

    if resp.status_code != 200:
        logger.error(f"[GROQ TRANSCRIPTION ERROR] HTTP {resp.status_code}")
        raise RuntimeError(f"Cloud speech transcription failed with status {resp.status_code}")

    try:
        payload = resp.json()
    except Exception as e:
        logger.error("[GROQ TRANSCRIPTION ERROR] Malformed JSON response")
        raise RuntimeError("Received invalid response from speech transcription service.") from e

    text = (payload.get("text") or "").strip()
    detected_language = payload.get("language") or language or "en"

    return {
        "text": text,
        "detected_language": detected_language
    }

def _transcribe_local(file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Offline local transcription using lazy-loaded Faster-Whisper 'tiny'.
    """
    try:
        model = _get_local_model()
        kwargs = {"beam_size": 1}
        if language:
            kwargs["language"] = language

        segments, info = model.transcribe(file_path, **kwargs)
        transcription = "".join(segment.text for segment in segments).strip()

        return {
            "text": transcription,
            "detected_language": info.language
        }
    except Exception as e:
        logger.error(f"[LOCAL TRANSCRIPTION ERROR] Local fallback failed: {e}")
        raise RuntimeError(f"Local speech transcription failed: {e}") from e

def transcribe_audio(file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribes an audio file.
    Primary: Groq Cloud Whisper API (whisper-large-v3-turbo, 0 MB local RAM overhead).
    Fallback: Lazy-loaded local Faster-Whisper ('tiny') when GROQ_API_KEY is unset or cloud fails.

    Args:
        file_path (str): Local path to the temporary audio file.
        language (str, optional): Language code (e.g. 'ml' for Malayalam).

    Returns:
        dict: {"text": str, "detected_language": str}
    """
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if groq_api_key:
        try:
            return _transcribe_groq(file_path, groq_api_key, language=language)
        except Exception as cloud_err:
            logger.warning(
                f"[TRANSCRIPTION] Cloud Groq transcription failed ({type(cloud_err).__name__}). "
                "Attempting lazy local fallback."
            )
            try:
                return _transcribe_local(file_path, language=language)
            except Exception as local_err:
                logger.error(f"[TRANSCRIPTION] Both cloud and local transcription failed: {local_err}")
                raise RuntimeError("Speech transcription failed across both cloud and local providers.") from cloud_err
    else:
        return _transcribe_local(file_path, language=language)
