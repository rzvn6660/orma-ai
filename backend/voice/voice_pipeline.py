from ochr.execution.execution_models import ExecutionResult
from .voice_models import VoiceResponse, SpeechMetadata, ConversationState

class VoicePipeline:
    def process_stt(self, audio_data: bytes) -> str:
        # Mock STT translation
        return "Hello ORMA"
        
    def process_tts(self, text: str, lang: str = "en") -> bytes:
        # Mock TTS generation
        return b"fake_audio_stream"
        
    def build_response(self, execution_result: ExecutionResult, lang="en") -> VoiceResponse:
        return VoiceResponse(
            audio_stream_url="/api/v1/voice/stream/xyz",
            text_fallback=execution_result.response_text,
            metadata=SpeechMetadata(duration_ms=1500, confidence=0.98, language=lang),
            state=ConversationState(is_active=True)
        )
