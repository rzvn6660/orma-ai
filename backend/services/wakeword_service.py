import numpy as np
import openwakeword
from openwakeword.model import Model
import os
import traceback

class WakeWordService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, "models", "hey_orma.onnx")
        self.model_name = "hey_orma"
        self.is_ready = False
        self.oww_model = None
        self.file_exists = False
        self.load_error = None
        
        print(f"Model path: {self.model_path}")
        try:
            self.file_exists = os.path.exists(self.model_path)
            
            if self.file_exists:
                self.oww_model = Model(wakeword_models=[self.model_path])
                self.is_ready = True
                print("Wake word model loaded successfully")
            else:
                print(f"Model file not found at {self.model_path}. Custom wake word detection will be disabled.")
                self.load_error = "Model file missing"
        except Exception as e:
            self.load_error = str(e)
            print(f"Model load error: {self.load_error}")

    def process_audio_chunk(self, audio_data: bytes, threshold: float = 0.5) -> dict:
        if not self.is_ready or not self.oww_model:
            return {"detected": False, "confidence": 0.0}
            
        try:
            # OpenWakeWord expects 16-bit 16kHz mono audio
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            # Predict
            predictions = self.oww_model.predict(audio_np)
            
            # Since there's only one model loaded, we grab its score
            score = 0.0
            for mdl, s in predictions.items():
                score = s
                
            if score >= threshold:
                print(f"Wake word detected! Confidence: {score:.2f}")
                return {"detected": True, "confidence": score}
                
            return {"detected": False, "confidence": score}
        except Exception as e:
            # Silently ignore chunk errors
            return {"detected": False, "confidence": 0.0}

wakeword_service = WakeWordService()
