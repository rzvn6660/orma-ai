import time
from .exceptions import RateLimitError

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.timestamps = []

    def acquire(self):
        now = time.time()
        
        # Remove timestamps older than 60 seconds
        self.timestamps = [t for t in self.timestamps if now - t < 60.0]
        
        if len(self.timestamps) >= self.requests_per_minute:
            raise RateLimitError("Rate limit exceeded. Try again later.")
            
        self.timestamps.append(now)
