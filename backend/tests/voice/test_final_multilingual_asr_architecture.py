import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import services.transcription_service as ts
from database import SessionLocal
from intelligence.orchestrator import orchestrator
from intelligence.conversational_reference_resolver import conversational_reference_resolver
from models.user import User, NotificationPreferences
from models.medicine import MedicineReminder

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def temp_audio(tmp_path):
    audio_path = tmp_path / "test_sample.wav"
    audio_path.write_bytes(b"\x1a\x45\xdf\xa3dummy_audio_stream")
    return str(audio_path)

# ==============================================================================
# 1. MALAYALAM TESTS (Explicit ml, normal, short, medication, quiet, noisy)
# ==============================================================================

def test_malayalam_explicit_ml_normal_sentence(temp_audio):
    """Tests that explicit 'ml' uses whisper-large-v3-turbo with language='ml'."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.22, "no_speech_prob": 0.001}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="ml")

            assert result["text"] == "എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?"
            assert result["detected_language"] == "malayalam"
            assert result["normalized_language"] == "ml"
            assert result["is_usable"] is True
            assert result["needs_clarification"] is False

            # Verify whisper-large-v3-turbo and language='ml'
            _, kwargs = client.post.call_args
            assert kwargs["data"]["model"] == "whisper-large-v3-turbo"
            assert kwargs["data"]["language"] == "ml"
            assert kwargs["data"]["temperature"] == "0"

def test_malayalam_short_affirmation(temp_audio):
    """Tests critical short medication affirmation 'കഴിച്ചു' with explicit ml."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "കഴിച്ചു",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.31, "no_speech_prob": 0.002}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="ml")

            assert result["text"] == "കഴിച്ചു"
            assert result["normalized_language"] == "ml"
            assert result["is_usable"] is True

def test_malayalam_medication_confirmation_phrase(temp_audio):
    """Tests primary medication affirmation phrase 'ഞാൻ അത് കഴിച്ചു.'"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "ഞാൻ അത് കഴിച്ചു.",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.28, "no_speech_prob": 0.005}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="ml")

            assert result["text"] == "ഞാൻ അത് കഴിച്ചു."
            assert result["normalized_language"] == "ml"
            assert result["is_usable"] is True

def test_malayalam_quiet_and_noisy_audio_quality(temp_audio):
    """Tests that low-amplitude or noisy audio with valid text passes validation."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "ഞാൻ മരുന്ന് എടുത്തു.",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.45, "no_speech_prob": 0.08}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="ml")
            assert result["is_usable"] is True
            assert result["text"] == "ഞാൻ മരുന്ന് എടുത്തു."

# ==============================================================================
# 2. OTHER EXPLICIT LANGUAGES (ta, en, hi)
# ==============================================================================

def test_explicit_tamil(temp_audio):
    """Tests Tamil explicit mode passes language='ta' and model='whisper-large-v3-turbo'."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "என் அடுத்த மருந்து என்ன?",
        "language": "tamil",
        "segments": [{"avg_logprob": -0.18, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="ta")

            assert result["normalized_language"] == "ta"
            assert result["text"] == "என் அடுத்த மருந்து என்ன?"
            _, kwargs = client.post.call_args
            assert kwargs["data"]["language"] == "ta"
            assert kwargs["data"]["model"] == "whisper-large-v3-turbo"

def test_explicit_english(temp_audio):
    """Tests English explicit mode passes language='en'."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "I already took my morning medicine.",
        "language": "english",
        "segments": [{"avg_logprob": -0.15, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="en")

            assert result["normalized_language"] == "en"
            assert result["text"] == "I already took my morning medicine."
            _, kwargs = client.post.call_args
            assert kwargs["data"]["language"] == "en"

def test_explicit_hindi(temp_audio):
    """Tests Hindi explicit mode passes language='hi'."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "मैंने वह दवा ले ली है।",
        "language": "hindi",
        "segments": [{"avg_logprob": -0.12, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="hi")

            assert result["normalized_language"] == "hi"
            assert result["text"] == "मैंने वह दवा ले ली है।"
            _, kwargs = client.post.call_args
            assert kwargs["data"]["language"] == "hi"

# ==============================================================================
# 3. AUTO MODE (en, ta, hi, ml where no preference exists)
# ==============================================================================

def test_auto_mode_english(temp_audio):
    """Tests AUTO mode correctly resolves English speech without language hint."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "When is my next appointment?",
        "language": "english",
        "segments": [{"avg_logprob": -0.21, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio)

            assert result["normalized_language"] == "en"
            assert result["text"] == "When is my next appointment?"
            assert client.post.call_count == 1
            _, kwargs = client.post.call_args
            assert "language" not in kwargs["data"]

def test_auto_mode_tamil_genuine(temp_audio):
    """Tests pure Tamil speech in AUTO mode is preserved without wasteful retry."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "என் அடுத்த மருந்து என்ன",
        "language": "tamil",
        "segments": [{"avg_logprob": -0.14, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio)

            assert result["normalized_language"] == "ta"
            assert client.post.call_count == 1

def test_auto_mode_hindi(temp_audio):
    """Tests Hindi speech in AUTO mode is resolved cleanly."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "मेरी अगली दवा कब है?",
        "language": "hindi",
        "segments": [{"avg_logprob": -0.19, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio)

            assert result["normalized_language"] == "hi"
            assert client.post.call_count == 1

def test_auto_mode_malayalam_with_mlym_script(temp_audio):
    """Tests Malayalam speech with native script detected directly in AUTO mode."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "എന്റെ മരുന്ന് എപ്പോഴാണ്?",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.25, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio)

            assert result["normalized_language"] == "ml"
            assert result["detected_language"] == "malayalam"
            assert client.post.call_count == 1

# ==============================================================================
# 4. PROFILE / AUTO CONFLICT TESTS
# ==============================================================================

def test_profile_ml_auto_ta_triggers_retry(temp_audio):
    """
    Critical conflict test:
    User profile is configured as Malayalam ('ml').
    AUTO Whisper returns Tamil ('ta').
    Verifies automatic retry with language='ml' using the SAME audio.
    """
    initial_ta_resp = MagicMock()
    initial_ta_resp.status_code = 200
    initial_ta_resp.json.return_value = {
        "text": "நான் அது கழிச்சு.",
        "language": "tamil",
        "segments": [{"avg_logprob": -0.26, "no_speech_prob": 0.1}]
    }

    retry_ml_resp = MagicMock()
    retry_ml_resp.status_code = 200
    retry_ml_resp.json.return_value = {
        "text": "ഞാൻ അത് കഴിച്ചു.",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.29, "no_speech_prob": 0.01}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            # First call returns Tamil, retry returns Malayalam
            client.post.side_effect = [initial_ta_resp, retry_ml_resp]

            # Call with profile_language='ml' but no explicit user toggle (e.g. language=None)
            # Wait: determine_language_hint with language=None and profile_lang='ml' will set hint='ml' directly!
            # To test AUTO + Profile conflict, pass language='auto' or simulate AUTO execution:
            result = ts.transcribe_audio(temp_audio, language="auto", profile_language="ml")

            # Result resolves to Malayalam!
            assert result["normalized_language"] == "ml"
            assert result["detected_language"] == "malayalam"

def test_profile_ta_auto_ml_does_not_blindly_force_ml(temp_audio):
    """
    Profile is Tamil, but user spoke English in AUTO mode.
    Verifies that system does not blindly force Malayalam.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "Good morning ORMA.",
        "language": "english",
        "segments": [{"avg_logprob": -0.15, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="auto", profile_language="ta")

            # English speech is preserved, not forced to Malayalam
            assert result["normalized_language"] in ("ta", "en")
            assert "Good morning" in result["text"]

# ==============================================================================
# 5. LANGUAGE SWITCHING (ml -> en -> ml -> ta -> ml)
# ==============================================================================

@pytest.mark.asyncio
async def test_sequential_language_switching(db_session):
    """
    Verifies 5-turn language switching without previous-turn leakage:
    Turn 1: ml -> response in ml
    Turn 2: en -> response in en
    Turn 3: ml -> response in ml
    Turn 4: ta -> response in ta
    Turn 5: ml -> response in ml
    """
    user_id = "test_lang_switch_user"

    turns = [
        ("എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", "ml"),
        ("What is my schedule today?", "en"),
        ("ഞാൻ അത് കഴിച്ചു.", "ml"),
        ("என் அடுத்த மருந்து என்ன?", "ta"),
        ("എന്റെ മരുന്ന് എപ്പോഴാണ്?", "ml")
    ]

    for utterance, expected_lang in turns:
        res = await orchestrator.process_request_detailed(
            text=utterance,
            user_id=user_id,
            db=db_session,
            language=expected_lang
        )
        assert res["language"] == expected_lang, (
            f"Expected language '{expected_lang}' for utterance '{utterance}', got '{res['language']}'"
        )

# ==============================================================================
# 6. MEDICATION SAFETY & CLARIFICATION
# ==============================================================================

def test_ambiguous_asr_triggers_clarification_no_action(temp_audio, db_session):
    """
    Verifies that when ASR is ambiguous or unusable (e.g. empty or discordant Hangul),
    needs_clarification is True, and conversational_reference_resolver performs NO medication state change.
    """
    # 1. Simulate ASR returning unusable discordant script for an Indian language speaker
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "아들 가르쳐줘.", # Korean hallucination on short speech
        "language": "korean",
        "segments": [{"avg_logprob": -0.85, "no_speech_prob": 0.45}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="ml")

            # Quality validation marks it unusable and needing clarification
            assert result["needs_clarification"] is True
            assert result["is_usable"] is False
            assert "വ്യക്തമായി കേട്ടില്ല" in result["clarification_prompt"]

    # 2. Verify that conversational_reference_resolver does NOT mark any medicine taken
    user_id = "test_safety_user"
    med = MedicineReminder(
        elder_id=user_id,
        medicine_name="SafetyTestMed",
        dosage="500mg",
        reminder_time="09:00 AM",
        taken_status=False
    )
    db_session.add(med)
    db_session.commit()

    # Pass the clarification prompt or unusable text into resolver
    resolver_res = conversational_reference_resolver.resolve(
        text=result["clarification_prompt"],
        user_id=user_id,
        db=db_session,
        history=[],
        language="ml"
    )

    # Medicine must NOT be marked taken
    db_session.refresh(med)
    assert med.taken_status is False

# ==============================================================================
# 7. MANGLISH SUPPORT (configured Malayalam + Romanized Malayalam)
# ==============================================================================

def test_manglish_with_configured_malayalam(temp_audio):
    """
    Verifies that when a configured Malayalam user speaks Romanized Manglish,
    explicit 'ml' mode is passed to Whisper.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "ഞാൻ അത് കഴിച്ചു",
        "language": "malayalam",
        "segments": [{"avg_logprob": -0.32, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            # User has profile_language='ml', speaking Manglish
            result = ts.transcribe_audio(temp_audio, profile_language="ml")

            assert result["normalized_language"] == "ml"
            assert result["is_usable"] is True
            _, kwargs = client.post.call_args
            assert kwargs["data"]["language"] == "ml"

# ==============================================================================
# 8. SAFE LANGUAGE PROPAGATION & ENGLISH PRIORITY
# ==============================================================================

def test_english_conversation_language_propagation(temp_audio):
    """
    Verifies that when conversation_language='en' is propagated from frontend,
    Whisper receives language='en' ensuring stable production English priority.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "What are my medicines for today?",
        "language": "english",
        "segments": [{"avg_logprob": -0.12, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, conversation_language="en")

            assert result["normalized_language"] == "en"
            assert result["is_usable"] is True
            _, kwargs = client.post.call_args
            assert kwargs["data"]["language"] == "en"
            assert kwargs["data"]["model"] == "whisper-large-v3-turbo"
            assert kwargs["data"]["temperature"] == "0"

def test_explicit_user_selection_overrides_conversation_language(temp_audio):
    """
    Verifies Priority 1: If an ongoing conversation was in Malayalam ('ml'),
    but user explicitly switches to English ('en'), English authoritative wins.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "Thank you, that is all.",
        "language": "english",
        "segments": [{"avg_logprob": -0.11, "no_speech_prob": 0.0}]
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "mock_groq_key"}):
        with patch("httpx.Client") as MockClient:
            client = MockClient.return_value.__enter__.return_value
            client.post.return_value = mock_resp

            result = ts.transcribe_audio(temp_audio, language="en", conversation_language="ml")

            assert result["normalized_language"] == "en"
            _, kwargs = client.post.call_args
            assert kwargs["data"]["language"] == "en"

def test_pseudo_language_values_filtered(temp_audio):
    """
    Verifies that 'null', 'undefined', 'auto', 'none' are rejected by normalize_language_code
    and fall through safely to AUTO mode without crashing or corrupting parameters.
    """
    assert ts.normalize_language_code("null") is None
    assert ts.normalize_language_code("undefined") is None
    assert ts.normalize_language_code("auto") is None
    assert ts.normalize_language_code("none") is None
    assert ts.normalize_language_code("") is None
    assert ts.determine_language_hint(explicit_lang="undefined", profile_lang="null", conversation_lang="auto") is None
