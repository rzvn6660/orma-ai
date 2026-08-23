import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class WakeWordService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        custom_path = os.environ.get("WAKEWORD_MODEL_PATH")
        self.model_path = custom_path if custom_path else os.path.join(base_dir, "models", "hey_orma.onnx")
        self.model_name = "hey_orma"
        self.mode = "DISABLED" # "ENABLED", "FALLBACK", "DISABLED"
        self.is_ready = False
        self.oww_model = None
        self.file_exists = False
        self.load_error = None
        
        self.file_exists = os.path.exists(self.model_path)
        
        try:
            from openwakeword.model import Model
            if self.file_exists:
                self.oww_model = Model(wakeword_models=[self.model_path])
                self.is_ready = True
                self.mode = "ENABLED"
                logger.info(f"[WAKEWORD] ENABLED - Using custom model: {self.model_path}")
            else:
                # Attempt fallback to openwakeword default model if available
                try:
                    self.oww_model = Model(wakeword_models=["hey_jarvis"])
                    self.is_ready = True
                    self.mode = "FALLBACK"
                    self.model_name = "hey_jarvis (fallback)"
                    logger.info("[WAKEWORD] FALLBACK MODE - Custom model missing, using default model: hey_jarvis")
                except Exception as fallback_err:
                    self.mode = "DISABLED"
                    self.is_ready = False
                    self.load_error = f"Model file not found at {self.model_path}. Fallback attempt failed: {fallback_err}"
                    logger.warning(f"[WAKEWORD] DISABLED - Model not found at {self.model_path}")
        except Exception as e:
            self.mode = "DISABLED"
            self.is_ready = False
            self.load_error = str(e)
            logger.warning(f"[WAKEWORD] DISABLED - OpenWakeWord error: {self.load_error}")

    def process_audio_chunk(self, audio_data: bytes, threshold: float = 0.5) -> dict:
        if not self.is_ready or not self.oww_model:
            return {"detected": False, "confidence": 0.0, "mode": self.mode}
            
        try:
            # OpenWakeWord expects 16-bit 16kHz mono audio
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            # Predict
            predictions = self.oww_model.predict(audio_np)
            
            score = 0.0
            for mdl, s in predictions.items():
                score = float(s)
                
            if score >= threshold:
                logger.info(f"[WAKEWORD] Detected! Confidence: {score:.2f} (Mode: {self.mode})")
                return {"detected": True, "confidence": score, "mode": self.mode}
                
            return {"detected": False, "confidence": score, "mode": self.mode}
        except Exception as e:
            logger.debug(f"[WAKEWORD] Chunk processing error: {e}")
            return {"detected": False, "confidence": 0.0, "mode": self.mode}

wakeword_service = WakeWordService()

