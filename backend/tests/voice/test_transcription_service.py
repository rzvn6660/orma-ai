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
            assert kwargs["data"]["model"] in ("whisper-large-v3", "whisper-large-v3-turbo")

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

def test_malayalam_auto_with_dravidian_disambiguation_retry(temp_audio_file):
    """
    Simulates real microphone Malayalam utterance ('എന്റെ അടുത്ത മരുന്ന് എന്താണ്?')
    where Groq Whisper initially misclassifies as Tamil with phonetic marker 'என்தானு'.
    Verifies automatic retry with language='ml' and final Malayalam resolution.
    """
    initial_ta_resp = MagicMock()
    initial_ta_resp.status_code = 200
    initial_ta_resp.json.return_value = {
        "text": "என்றி அடுத்த மருந்து என்தானு?",
        "language": "tamil",
        "segments": [{"avg_logprob": -0.425, "no_speech_prob": 0.001}]
    }

    retry_ml_resp = MagicMock()
    retry_ml_resp.status_code = 200
    retry_ml_resp.json.return_value = {
        "text": "എന്റെ അടുത്ത മരുന്ന് എന്താണ്?",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.287, "no_speech_prob": 0.001}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.side_effect = [initial_ta_resp, retry_ml_resp]

            result = ts.transcribe_audio(temp_audio_file)

            assert result["detected_language"] == "malayalam"
            assert result["text"] == "എന്റെ അടുത്ത മരുന്ന് എന്താണ്?"
            # Exactly 2 calls made: initial auto + single retry
            assert mock_client_instance.post.call_count == 2
            # Verify retry request explicitly sent language='ml'
            retry_call_args = mock_client_instance.post.call_args_list[1]
            assert retry_call_args[1]["data"]["language"] == "ml"

def test_malayalam_explicit_selection_no_override(temp_audio_file):
    """
    Verifies that when Voice Language = Malayalam is explicitly selected,
    language='ml' is forced, no retry is triggered, and Tamil never overrides it.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.25}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio_file, language="ml-IN")

            assert result["detected_language"] == "malayalam"
            assert result["text"] == "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?"
            assert mock_client_instance.post.call_count == 1
            call_kwargs = mock_client_instance.post.call_args[1]
            assert call_kwargs["data"]["language"] == "ml"

def test_tamil_auto_pure_tamil_no_retry(temp_audio_file):
    """
    Verifies that genuine Tamil speech ('என் அடுத்த மருந்து என்ன')
    containing pure Tamil interrogatives ('என்ன') is recognized as Tamil WITHOUT retrying.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "என் அடுத்த மருந்து என்ன",
        "language": "tamil",
        "segments": [{"avg_logprob": -0.136, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio_file)

            assert result["detected_language"] == "tamil"
            assert result["text"] == "என் அடுத்த மருந்து என்ன"
            # Exactly 1 call (no wasteful retry on genuine Tamil)
            assert mock_client_instance.post.call_count == 1

def test_english_auto_no_retry(temp_audio_file):
    """Verifies English AUTO request is transcribed directly without retrying."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "What is my next medicine?",
        "language": "english",
        "segments": [{"avg_logprob": -0.274}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio_file)

            assert result["detected_language"] == "english"
            assert result["text"] == "What is my next medicine?"
            assert mock_client_instance.post.call_count == 1

def test_hindi_auto_no_retry(temp_audio_file):
    """Verifies Hindi AUTO request is transcribed directly without retrying."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "मेरी अगली दवा कौन सी है?",
        "language": "hindi",
        "segments": [{"avg_logprob": -0.041}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio_file)

            assert result["detected_language"] == "hindi"
            assert result["text"] == "मेरी अगली दवा कौन सी है?"
            assert mock_client_instance.post.call_count == 1

def test_short_malayalam_utterance_auto(temp_audio_file):
    """Verifies short Malayalam utterance ('അടുത്തത്' / 'മരുന്ന്') misclassified as Tamil is retried."""
    initial_resp = MagicMock()
    initial_resp.status_code = 200
    initial_resp.json.return_value = {
        "text": "மருன்னு",  # 'marunnu' transliterated into Tamil
        "language": "tamil",
        "segments": [{"avg_logprob": -0.40}]
    }
    ml_resp = MagicMock()
    ml_resp.status_code = 200
    ml_resp.json.return_value = {
        "text": "മരുന്ന്",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.22}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.side_effect = [initial_resp, ml_resp]

            result = ts.transcribe_audio(temp_audio_file)

            assert result["detected_language"] == "malayalam"
            assert result["text"] == "മരുന്ന്"
            assert mock_client_instance.post.call_count == 2

def test_code_switched_manglish_medication_question(temp_audio_file):
    """
    Verifies code-switched / Latin Malayalam ('en adutha marunnu enthaanu')
    is correctly classified as Malayalam even when Whisper assigns language='english'.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "en adutha marunnu enthaanu",
        "language": "english",
        "segments": [{"avg_logprob": -0.45}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio_file)

            assert result["detected_language"] == "malayalam"
            assert result["text"] == "en adutha marunnu enthaanu"
            assert mock_client_instance.post.call_count == 1

def test_no_previous_conversation_language_leakage(temp_audio_file):
    """
    Verifies that when in AUTO mode, no language hint is passed in the initial API request,
    preventing any leakage from previous conversation turns.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "Hello, how can I help you?",
        "language": "english",
        "segments": [{"avg_logprob": -0.2}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            mock_client_instance = MockClient.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_resp

            # Explicitly call AUTO mode with language=None
            ts.transcribe_audio(temp_audio_file, language=None)

            call_kwargs = mock_client_instance.post.call_args[1]
            # Must NOT contain 'language' in post data
            assert "language" not in call_kwargs["data"]
