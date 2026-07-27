import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from voice.voice_service import VoiceService
from ochr.execution.execution_models import ExecutionResult

def test_stt_input():
    service = VoiceService()
    text = service.pipeline.process_stt(b"audio")
    assert text == "Hello ORMA"

def test_tts_output():
    service = VoiceService()
    audio = service.pipeline.process_tts("Hi there")
    assert audio == b"fake_audio_stream"

def test_interrupt_handling():
    service = VoiceService()
    service.stream.start_stream()
    assert service.stream.is_streaming == True
    
    interrupted = service.interrupt()
    assert interrupted == True
    assert service.stream.is_streaming == False
    assert service.manager.state.interrupted == True

def test_conversation_continuity():
    service = VoiceService()
    service.manager.wake_word_detected()
    assert service.manager.state.is_active == True
    
    # Process silence
    service.manager.process_silence(1000)
    assert service.manager.state.is_active == True
    
    # Process more silence
    service.manager.process_silence(2500)
    assert service.manager.state.is_active == False
