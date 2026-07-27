import logging
import json

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def info(self, msg: str, **kwargs):
        self.logger.info(json.dumps({"msg": msg, "level": "INFO", **kwargs}))
        
    def error(self, msg: str, **kwargs):
        self.logger.error(json.dumps({"msg": msg, "level": "ERROR", **kwargs}))
