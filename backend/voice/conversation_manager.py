from .voice_models import ConversationState

class ConversationManager:
    def __init__(self):
        self.state = ConversationState()
        
    def process_silence(self, duration_ms: int):
        self.state.silence_duration_ms += duration_ms
        if self.state.silence_duration_ms > 3000:
            self.state.is_active = False
            
    def wake_word_detected(self):
        self.state.is_active = True
        self.state.silence_duration_ms = 0
        self.state.interrupted = False
