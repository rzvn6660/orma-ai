class MetricsTracker:
    def __init__(self):
        self.latency_ms = []
        self.token_usage = 0
        
    def record_latency(self, ms: int):
        self.latency_ms.append(ms)
        
    def record_tokens(self, count: int):
        self.token_usage += count
