import os
import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock
import httpx

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import services.transcription_service as ts

@pytest.fixture
def temp_audio_file(tmp_path):
    audio_path = tmp_path / "sample.webm"
    audio_path.write_bytes(b"\x1a\x45\xdf\xa3fake_audio_stream")
    return str(audio_path)

def test_faster_whisper_not_instantiated_at_import():
    """Confirms WhisperModel is NOT instantiated when the module is imported."""
    with patch("faster_whisper.WhisperModel") as mock_whisper:
        importlib.reload(ts)
        # Verify WhisperModel was never called upon import
        assert mock_whisper.call_count == 0
        assert ts._cached_local_model is None

def test_groq_transcription_success(temp_audio_file):
    """Tests successful cloud transcription with Groq Whisper."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "Good morning, doctor.",
        "language": "english",
        "duration": 2.5
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_api_key_123"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio_file)

            assert result == {
                "text": "Good morning, doctor.",
                "detected_language": "english"
            }

            # Verify call endpoint and headers
            mock_client_instance.post.assert_called_once()
            args, kwargs = mock_client_instance.post.call_args
            assert args[0] == "https://api.groq.com/openai/v1/audio/transcriptions"
            assert kwargs["headers"]["Authorization"] == "Bearer mock_groq_api_key_123"
            assert kwargs["data"]["model"] == "whisper-large-v3-turbo"
            assert kwargs["data"]["response_format"] == "verbose_json"
            assert "language" not in kwargs["data"]

def test_groq_transcription_with_language_hint(temp_audio_file):
    """Tests that language parameter (e.g. Malayalam 'ml') is sent to Groq."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "എനിക്ക് സുഖമാണ്",
        "language": "malayalam",
        "duration": 3.1
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_api_key_123"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio_file, language="ml")

            assert result == {
                "text": "എനിക്ക് സുഖമാണ്",
                "detected_language": "malayalam"
            }

            _, kwargs = mock_client_instance.post.call_args
            assert kwargs["data"]["language"] == "ml"
            assert kwargs["data"]["model"] == "whisper-large-v3-turbo"

def test_groq_missing_key_uses_lazy_local_fallback(temp_audio_file):
    """Confirms local fallback is used lazily when GROQ_API_KEY is not configured."""
    mock_segment = MagicMock()
    mock_segment.text = "Local offline fallback transcript."
    mock_info = MagicMock()
    mock_info.language = "en"

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
        with patch.object(ts, "_get_local_model", return_value=mock_model) as mock_get_model:
            result = ts.transcribe_audio(temp_audio_file, language="en")

            assert mock_get_model.called
            assert result == {
                "text": "Local offline fallback transcript.",
                "detected_language": "en"
            }

def test_groq_http_error_falls_back_to_local(temp_audio_file):
    """Tests that when Groq returns HTTP 500, it falls back to local transcription."""
    mock_groq_resp = MagicMock()
    mock_groq_resp.status_code = 500
    mock_groq_resp.text = "Internal Server Error"

    mock_segment = MagicMock()
    mock_segment.text = "Fallback text after cloud failure"
    mock_info = MagicMock()
    mock_info.language = "en"

    mock_local_model = MagicMock()
    mock_local_model.transcribe.return_value = ([mock_segment], mock_info)

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_api_key_123"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_groq_resp

            with patch.object(ts, "_get_local_model", return_value=mock_local_model):
                result = ts.transcribe_audio(temp_audio_file)
                assert result["text"] == "Fallback text after cloud failure"

def test_groq_timeout_error_falls_back_to_local(temp_audio_file):
    """Tests that a cloud timeout triggers local fallback."""
    mock_segment = MagicMock()
    mock_segment.text = "Fallback text after timeout"
    mock_info = MagicMock()
    mock_info.language = "ml"

    mock_local_model = MagicMock()
    mock_local_model.transcribe.return_value = ([mock_segment], mock_info)

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_api_key_123"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.side_effect = httpx.TimeoutException("Read timed out")

            with patch.object(ts, "_get_local_model", return_value=mock_local_model):
                result = ts.transcribe_audio(temp_audio_file, language="ml")
                assert result["text"] == "Fallback text after timeout"
                assert result["detected_language"] == "ml"

def test_transcribe_nonexistent_file():
    """Verifies proper error when audio file does not exist."""
    with pytest.raises(FileNotFoundError):
        ts.transcribe_audio("nonexistent_recording_path.webm")
