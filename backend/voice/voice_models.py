from pydantic import BaseModel, Field
from typing import Optional

class SpeechMetadata(BaseModel):
    duration_ms: int
    confidence: float
    language: str

class ConversationState(BaseModel):
    is_active: bool = False
    last_interaction: str = ""
    silence_duration_ms: int = 0
    interrupted: bool = False

class VoiceResponse(BaseModel):
    audio_stream_url: Optional[str] = None
    text_fallback: str
    metadata: SpeechMetadata
    state: ConversationState
