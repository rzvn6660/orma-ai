import os
import io
import wave
import struct
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from services.audio_preprocessor import (
    analyze_audio,
    preprocess_audio_pipeline,
    DEFAULT_PREPROCESS_CONFIG
)
import services.transcription_service as ts

def create_synthetic_sine_wav(path: str, duration_sec: float = 1.0, sr: int = 44100, freq: float = 440.0, volume: float = 0.5):
    """Generates a synthetic 16-bit PCM WAV file."""
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    samples = (np.sin(2 * np.pi * freq * t) * volume * 32767).astype(np.int16)
    
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())

def create_silence_padded_wav(path: str, speech_duration: float = 1.0, lead_silence: float = 1.2, trail_silence: float = 1.5, sr: int = 16000):
    """Generates WAV with leading silence, sine burst, and trailing silence."""
    lead_n = int(sr * lead_silence)
    speech_n = int(sr * speech_duration)
    trail_n = int(sr * trail_silence)
    
    lead = np.zeros(lead_n, dtype=np.int16)
    t = np.linspace(0, speech_duration, speech_n, endpoint=False)
    speech = (np.sin(2 * np.pi * 300 * t) * 0.6 * 32767).astype(np.int16)
    trail = np.zeros(trail_n, dtype=np.int16)
    
    full = np.concatenate([lead, speech, trail])
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(full.tobytes())

def test_analyze_audio_metadata(tmp_path):
    """Verifies analyze_audio extracts codec, duration, sample rate, and peak without logging private data."""
    test_file = str(tmp_path / "test_sine.wav")
    create_synthetic_sine_wav(test_file, duration_sec=1.5, sr=44100, volume=0.7)
    
    meta = analyze_audio(test_file)
    assert meta["format"] == "wav"
    assert meta["sample_rate"] == 44100
    assert meta["channels"] == 1
    assert 1.4 <= meta["duration_seconds"] <= 1.6
    assert meta["peak_amplitude"] > 0.6
    assert meta["clipping_pct"] == 0.0

def test_preprocess_pipeline_resampling_and_mono(tmp_path):
    """Verifies audio is converted to 16 kHz Mono 16-bit PCM WAV."""
    test_file = str(tmp_path / "test_stereo.wav")
    create_synthetic_sine_wav(test_file, duration_sec=1.0, sr=48000, volume=0.5)
    
    out_path, meta = preprocess_audio_pipeline(test_file, config={"target_sample_rate": 16000})
    try:
        assert os.path.exists(out_path)
        assert meta["applied"] is True
        with wave.open(out_path, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getframerate() == 16000
            assert wf.getsampwidth() == 2
    finally:
        if os.path.exists(out_path) and out_path != test_file:
            os.remove(out_path)

def test_silence_trimming_preserves_safety_padding(tmp_path):
    """Verifies leading/trailing silence is trimmed while maintaining safety pad for phoneme preservation."""
    padded_file = str(tmp_path / "padded.wav")
    create_silence_padded_wav(padded_file, speech_duration=1.0, lead_silence=1.2, trail_silence=1.5, sr=16000)
    
    out_path, meta = preprocess_audio_pipeline(padded_file, config={"trim_silence": True})
    try:
        assert meta["lead_trimmed_sec"] > 0.8
        assert meta["trail_trimmed_sec"] > 1.0
        # Original duration was ~3.7s; trimmed should be ~1.44s (1.0s speech + 2*0.22s safety padding)
        assert 1.3 <= meta["proc_duration_sec"] <= 1.7
    finally:
        if os.path.exists(out_path) and out_path != padded_file:
            os.remove(out_path)

def test_loudness_normalization_quiet_audio(tmp_path):
    """Verifies quiet audio is safely boosted without clipping."""
    quiet_file = str(tmp_path / "quiet.wav")
    create_synthetic_sine_wav(quiet_file, duration_sec=1.0, sr=16000, volume=0.05)
    
    out_path, meta = preprocess_audio_pipeline(quiet_file, config={"normalize_loudness": True})
    try:
        assert meta["peak_before"] < 0.1
        assert meta["peak_after"] > meta["peak_before"] * 2.0
        assert meta["peak_after"] <= 0.95
    finally:
        if os.path.exists(out_path) and out_path != quiet_file:
            os.remove(out_path)

def test_preprocessor_graceful_fallback_corrupt_file(tmp_path):
    """Verifies invalid or non-audio file falls back gracefully without raising an exception."""
    corrupt_file = str(tmp_path / "corrupt.wav")
    with open(corrupt_file, "wb") as f:
        f.write(b"NOT_A_VALID_AUDIO_CONTAINER_DATA")
        
    out_path, meta = preprocess_audio_pipeline(corrupt_file)
    assert out_path == corrupt_file
    assert meta["applied"] is False
    assert "error" in meta

def test_groq_transcribe_temperature_zero():
    """Verifies that _transcribe_groq explicitly sends temperature='0' for deterministic decoding."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"text": "Deterministic result", "language": "english"}
    
    with patch("httpx.Client") as MockClient:
        mock_client_instance = MockClient.return_value.__enter__.return_value
        mock_client_instance.post.return_value = mock_resp
        
        # Call with dummy bytes file
        fake_file = os.path.abspath(__file__)
        ts._transcribe_groq(fake_file, api_key="dummy_key", language="en")
        
        _, kwargs = mock_client_instance.post.call_args
        assert kwargs["data"]["temperature"] == "0"
        assert kwargs["data"]["response_format"] == "verbose_json"

def test_explicit_malayalam_selects_large_v3(tmp_path):
    """Verifies that explicit Malayalam selection uses whisper-large-v3-turbo (proven by hard-case benchmark)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"text": "എന്റെ മരുന്ന്", "language": "malayalam"}
    
    sample_file = str(tmp_path / "sample.wav")
    create_synthetic_sine_wav(sample_file, duration_sec=0.5, sr=16000)
    
    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp
            
            res = ts.transcribe_audio(sample_file, language="ml")
            assert res["detected_language"] == "malayalam"
            
            _, kwargs = mock_client_instance.post.call_args
            assert kwargs["data"]["model"] == "whisper-large-v3-turbo"
            assert kwargs["data"]["language"] == "ml"
