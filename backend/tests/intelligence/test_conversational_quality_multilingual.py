import pytest
import os
import sys
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal
from models.user import User
from intelligence.orchestrator import orchestrator
from intelligence.conversation_manager import conversation_manager
from llm.providers.fallback_provider import FallbackProvider
from services.transcription_service import normalize_language_code, transcribe_audio

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_stt_language_normalization():
    """Verify that language codes are properly normalized to 2-letter ISO codes."""
    assert normalize_language_code("ml-IN") == "ml"
    assert normalize_language_code("ml_in") == "ml"
    assert normalize_language_code("en-US") == "en"
    assert normalize_language_code("en-IN") == "en"
    assert normalize_language_code("auto") is None
    assert normalize_language_code("none") is None
    assert normalize_language_code(None) is None
    assert normalize_language_code("") is None

@pytest.mark.asyncio
async def test_fallback_natural_greetings():
    """Confirms greetings return warm, human greetings and avoid the repetitive generic sentence."""
    fb = FallbackProvider()
    
    # English greeting
    res_en = await fb.generate_response("User: Hello ORMA")
    assert res_en["success"] is True
    assert "assist you with your medicines, health reminders, and daily schedule" not in res_en["text"]
    assert any(w in res_en["text"] for w in ["Hello", "Orma", "Hi", "help", "hear from you"])

    # Malayalam greeting
    res_ml = await fb.generate_response("User: ഹലോ ഓർമ")
    assert res_ml["success"] is True
    assert "assist you with your medicines" not in res_ml["text"]
    assert any(w in res_ml["text"] for w in ["നമസ്കാരം", "ഹലോ", "സഹായിക്കാൻ", "സന്തോഷം"])

@pytest.mark.asyncio
async def test_fallback_answers_user_name():
    """Confirms 'What is my name?' retrieves the user's name from context."""
    fb = FallbackProvider()
    prompt = "Actor Speaking: QA User Test (elderly)\nUser: What is my name?"
    res = await fb.generate_response(prompt)
    assert res["success"] is True
    assert "QA User Test" in res["text"]
    assert "assist you with your medicines" not in res["text"]

@pytest.mark.asyncio
async def test_fallback_coreference_resolution():
    """Confirms 'What did I just tell you?' recalls the previous user statement."""
    fb = FallbackProvider()
    prompt = (
        "Actor Speaking: Elderly Patient (elderly)\n"
        "RECENT CONVERSATION HISTORY:\n"
        "User: My favorite drink is tender coconut water.\n"
        "Orma: That sounds healthy and refreshing!\n"
        "User: What did I just tell you?"
    )
    res = await fb.generate_response(prompt)
    assert res["success"] is True
    assert "tender coconut water" in res["text"].lower()

@pytest.mark.asyncio
async def test_fallback_repeat_request():
    """Confirms 'Can you repeat that?' recalls the immediately previous assistant statement."""
    fb = FallbackProvider()
    prompt = (
        "RECENT CONVERSATION HISTORY:\n"
        "User: How are you?\n"
        "Orma: I am feeling great and ready to assist you.\n"
        "User: Can you repeat that?"
    )
    res = await fb.generate_response(prompt)
    assert res["success"] is True
    assert "ready to assist you" in res["text"]

@pytest.mark.asyncio
async def test_fallback_medication_grounding_malayalam():
    """Confirms Malayalam medication questions return actual medication data in Malayalam."""
    fb = FallbackProvider()
    prompt = (
        "User: എന്റെ മരുന്ന് എപ്പോഴാണ് കഴിക്കേണ്ടത്?\n"
        "- Amlodipine 5mg scheduled at 09:00 AM: Status = SCHEDULED"
    )
    res = await fb.generate_response(prompt)
    assert res["success"] is True
    # Must preserve exact medication name and dosage
    assert "Amlodipine 5mg" in res["text"]
    assert "09:00 AM" in res["text"]
    # Must contain Malayalam response words
    assert "മരുന്ന്" in res["text"] or "സമയം" in res["text"]

@pytest.mark.asyncio
async def test_generic_fallback_avoidance_unknown_intent():
    """Confirms unknown/unrecognized queries ask polite clarification, not generic schedule sentences."""
    fb = FallbackProvider()
    res = await fb.generate_response("User: Quasar blip florp")
    assert res["success"] is True
    assert "assist you with your medicines, health reminders, and daily schedule" not in res["text"]
    assert any(w in res["text"].lower() for w in ["catch that", "rephrase", "understood", "tell me what you need", "help with"])

@pytest.mark.asyncio
async def test_orchestrator_multilingual_language_switching(db_session):
    """Confirms language switching works dynamically between English and Malayalam."""
    test_uid = "test_lang_switch_user_123"
    
    # 1. User starts in English
    reply_en = await orchestrator.process_request("Hello ORMA", test_uid, db_session, language="en")
    assert any(w in reply_en.lower() for w in ["hello", "hi", "help", "hear from you", "orma", "companion"])

    # 2. User switches to Malayalam
    reply_ml = await orchestrator.process_request("ഹലോ! സുഖമാണോ?", test_uid, db_session, language="ml")
    # Response must contain Malayalam script
    assert any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in reply_ml)

    # 3. User switches back to English
    reply_en2 = await orchestrator.process_request("Thank you, what is my schedule today?", test_uid, db_session, language="en")
    assert "schedule" in reply_en2.lower() or "medicine" in reply_en2.lower() or "appointment" in reply_en2.lower() or "clear" in reply_en2.lower()
