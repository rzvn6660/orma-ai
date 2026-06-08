import os
from faster_whisper import WhisperModel

# Initialize the Whisper model.
# Using 'medium' model for vastly improved Malayalam support.
# In a production setting with GPU, you would use 'cuda' and 'large-v3'.
MODEL_SIZE = "medium"
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def transcribe_audio(file_path: str, language: str = None) -> dict:
    """
    Transcribes an audio file using faster-whisper.
    
    Args:
        file_path (str): The local path to the audio file.
        language (str): Optional language code (e.g., 'ml' for Malayalam).
        
    Returns:
        dict: A dictionary containing 'text' and 'detected_language'.
    """
    try:
        kwargs = {"beam_size": 5}
        if language:
            kwargs["language"] = language
            
        segments, info = model.transcribe(file_path, **kwargs)
        
        transcription = ""
        for segment in segments:
            transcription += segment.text + " "
            
        return {
            "text": transcription.strip(),
            "detected_language": info.language
        }
    except Exception as e:
        print(f"Error during transcription: {e}")
        raise e
