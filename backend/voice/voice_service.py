from .voice_pipeline import VoicePipeline
from .stream_handler import StreamHandler
from .conversation_manager import ConversationManager
from ochr.execution.execution_models import ExecutionResult
from .voice_models import VoiceResponse

class VoiceService:
    def __init__(self):
        self.pipeline = VoicePipeline()
        self.stream = StreamHandler()
        self.manager = ConversationManager()
        
    def handle_voice_interaction(self, execution_result: ExecutionResult, lang="en") -> VoiceResponse:
        self.stream.start_stream()
        return self.pipeline.build_response(execution_result, lang)
        
    def interrupt(self):
        self.manager.state.interrupted = True
        return self.stream.handle_interrupt()
