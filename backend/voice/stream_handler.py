class StreamHandler:
    def __init__(self):
        self.is_streaming = False
        
    def start_stream(self):
        self.is_streaming = True
        
    def stop_stream(self):
        self.is_streaming = False
        
    def handle_interrupt(self):
        if self.is_streaming:
            self.stop_stream()
            return True
        return False
