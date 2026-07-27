class CacheService:
    def __init__(self):
        self.store = {}
        
    def get(self, key: str):
        return self.store.get(key)
        
    def set(self, key: str, value, ttl: int = 3600):
        self.store[key] = value
