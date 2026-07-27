from .metrics import MetricsTracker

class APIMonitor:
    def __init__(self):
        self.metrics = MetricsTracker()
        
    def log_request(self, latency: int, tokens: int = 0):
        self.metrics.record_latency(latency)
        self.metrics.record_tokens(tokens)
