import os
import sys
import asyncio
import datetime
import pytest
from unittest.mock import patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal
from models.user import User
from models.medicine import MedicineReminder
from memory.memory_models import OCMEMemory
from memory.memory_service import ocme_service
from intelligence.orchestrator import orchestrator
from intelligence.intent_detector import intent_detector
from intelligence.conversation_manager import conversation_manager
from intelligence.mode_resolver import ExecutionMode

USER_ENG_A = "test_engine_user_a"
USER_ENG_B = "test_engine_user_b"

@pytest.fixture(autouse=True)
def clean_engine_data():
    conversation_manager.clear_session(USER_ENG_A)
    conversation_manager.clear_session(USER_ENG_B)
    db = SessionLocal()
    try:
        db.query(OCMEMemory).filter(OCMEMemory.user_id.in_([USER_ENG_A, USER_ENG_B])).delete()
        db.query(MedicineReminder).filter(MedicineReminder.elder_id.in_([USER_ENG_A, USER_ENG_B])).delete()
        db.query(User).filter(User.id.in_([USER_ENG_A, USER_ENG_B])).delete()
        db.commit()

        # Create test users
        user_a = User(
            id=USER_ENG_A,
            email="engine_a@test.local",
            name="Alice Engine",
            role="elderly",
            timezone="UTC"
        )
        user_b = User(
            id=USER_ENG_B,
            email="engine_b@test.local",
            name="Bob Engine",
            role="elderly",
            timezone="UTC"
        )
        db.add_all([user_a, user_b])
        db.commit()
    finally:
        db.close()

    yield

    conversation_manager.clear_session(USER_ENG_A)
    conversation_manager.clear_session(USER_ENG_B)
    db = SessionLocal()
    try:
        db.query(OCMEMemory).filter(OCMEMemory.user_id.in_([USER_ENG_A, USER_ENG_B])).delete()
        db.query(MedicineReminder).filter(MedicineReminder.elder_id.in_([USER_ENG_A, USER_ENG_B])).delete()
        db.query(User).filter(User.id.in_([USER_ENG_A, USER_ENG_B])).delete()
        db.commit()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_a_greeting():
    """A. Greeting: 'Hello ORMA' produces a warm, non-repetitive greeting without medication dump."""
    db = SessionLocal()
    try:
        intent, conf, _ = await intent_detector.detect_intent_with_metadata("Hello ORMA")
        assert intent == "GREETING"

        res = await orchestrator.process_request("Hello ORMA", USER_ENG_A, db, language="en")
        assert any(w in res.lower() for w in ["hello", "hi", "nice to hear", "help", "orma"])
        assert "metformin" not in res.lower()
        assert "schedule" not in res.lower()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_b_acknowledgment():
    """B. Acknowledgment: 'Okay' / 'Yeah' produces a concise conversational response, not a capability description."""
    db = SessionLocal()
    try:
        intent, conf, _ = await intent_detector.detect_intent_with_metadata("Okay")
        assert intent == "ACKNOWLEDGMENT"

        # Prime conversation history with a medication turn
        conversation_manager.add_message(USER_ENG_A, "assistant", "Your next medicine is Metformin at 8 PM.")

        res = await orchestrator.process_request("Okay", USER_ENG_A, db, language="en")
        # Must be short natural acknowledgment
        assert any(w in res.lower() for w in ["alright", "okay", "here if you need"])
        assert "i am here to assist you with your medicines" not in res.lower()
        assert "metformin" not in res.lower()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_c_thanks():
    """C. Thanks: 'Thank you' produces a polite 'You're welcome!' response."""
    db = SessionLocal()
    try:
        intent, conf, _ = await intent_detector.detect_intent_with_metadata("Thank you")
        assert intent == "THANKS"

        res = await orchestrator.process_request("Thank you", USER_ENG_A, db, language="en")
        assert any(w in res.lower() for w in ["welcome", "pleasure", "glad", "anytime"])
        assert "i am here to assist you with your medicines" not in res.lower()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_d_follow_up_tomorrow():
    """D. Follow-up: 'What about tomorrow?' resolves topic to tomorrow's medication schedule from live DB."""
    db = SessionLocal()
    try:
        # User has Metformin scheduled tomorrow
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        tomorrow_date = (now_utc + datetime.timedelta(days=1)).date()

        med = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            frequency="Daily",
            taken_status=False
        )
        db.add(med)
        db.commit()

        # Prime previous assistant message
        conversation_manager.add_message(USER_ENG_A, "user", "What is my next medicine?")
        conversation_manager.add_message(USER_ENG_A, "assistant", "Your next medicine is Metformin at 8:00 PM.")

        res = await orchestrator.process_request("What about tomorrow?", USER_ENG_A, db, language="en")
        assert "tomorrow" in res.lower()
        assert "Metformin" in res
        assert "08:00 PM" in res or "8:00 PM" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_e_pronoun_resolution():
    """E. Pronoun: 'When should I take it?' resolves 'it' to the single active medicine from context."""
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Amlodipine",
            dosage="5mg",
            reminder_time="08:00 AM",
            frequency="Daily",
            taken_status=False
        )
        db.add(med)
        db.commit()

        # Previous turn discussed Amlodipine
        conversation_manager.add_message(USER_ENG_A, "user", "What is my blood pressure medicine?")
        conversation_manager.add_message(USER_ENG_A, "assistant", "Your blood pressure medicine is Amlodipine.")
        conversation_manager.save_interaction_context(USER_ENG_A, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"id": med.id, "name": "Amlodipine", "dosage": "5mg", "scheduled_time": "08:00 AM"}]
        })

        res = await orchestrator.process_request("When should I take it?", USER_ENG_A, db, language="en")
        assert "Amlodipine" in res
        assert "08:00 AM" in res or "8:00 AM" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_f_entity_reference_second_one():
    """F. Entity Reference: 'What about the second one?' resolves to the 2nd medicine mentioned in context."""
    db = SessionLocal()
    try:
        med1 = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Amlodipine",
            dosage="5mg",
            reminder_time="08:00 AM",
            taken_status=True
        )
        med2 = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add_all([med1, med2])
        db.commit()

        conversation_manager.add_message(USER_ENG_A, "assistant", "You have Amlodipine at 08:00 AM and Metformin at 08:00 PM.")
        conversation_manager.save_interaction_context(USER_ENG_A, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [
                {"id": med1.id, "name": "Amlodipine", "dosage": "5mg", "scheduled_time": "08:00 AM"},
                {"id": med2.id, "name": "Metformin", "dosage": "500mg", "scheduled_time": "08:00 PM"}
            ]
        })

        res = await orchestrator.process_request("What about the second one?", USER_ENG_A, db, language="en")
        assert "Metformin" in res
        assert "08:00 PM" in res or "8:00 PM" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_g_repetition_request():
    """G. Repeat: 'Can you tell me that again?' repeats the relevant previous assistant answer."""
    db = SessionLocal()
    try:
        previous_text = "Your evening medicine is Metformin 500mg scheduled at 8 PM."
        conversation_manager.add_message(USER_ENG_A, "assistant", previous_text)

        res = await orchestrator.process_request("Can you tell me that again?", USER_ENG_A, db, language="en")
        assert "Metformin" in res
        assert "8 PM" in res
        assert "Certainly:" in res or "Metformin" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_h_correction():
    """H. Correction: 'No, I meant the morning one.' updates focus and answers with morning medicine from DB."""
    db = SessionLocal()
    try:
        med_morn = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Thyroxine",
            dosage="25mcg",
            reminder_time="07:00 AM",
            taken_status=False
        )
        med_eve = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add_all([med_morn, med_eve])
        db.commit()

        # Prime conversation about evening medicine
        conversation_manager.add_message(USER_ENG_A, "assistant", "Your evening medicine is Metformin at 08:00 PM.")

        res = await orchestrator.process_request("No, I meant the morning one.", USER_ENG_A, db, language="en")
        assert "Thyroxine" in res
        assert "07:00 AM" in res or "7:00 AM" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_i_ambiguous_reference_clarification():
    """I. Ambiguous Reference: 'When should I take it?' with 2 candidate medicines asks a concise clarification."""
    db = SessionLocal()
    try:
        med1 = MedicineReminder(
            id=701,
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Amlodipine",
            dosage="5mg",
            reminder_time="08:00 AM",
            taken_status=False
        )
        med2 = MedicineReminder(
            id=702,
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add_all([med1, med2])
        db.commit()

        conversation_manager.add_message(USER_ENG_A, "assistant", "You have Amlodipine at 08:00 AM and Metformin at 08:00 PM.")
        conversation_manager.save_interaction_context(USER_ENG_A, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [
                {"id": 701, "name": "Amlodipine", "dosage": "5mg", "scheduled_time": "08:00 AM"},
                {"id": 702, "name": "Metformin", "dosage": "500mg", "scheduled_time": "08:00 PM"}
            ]
        })

        detailed = await orchestrator.process_request_detailed("When should I take it?", USER_ENG_A, db, language="en")
        res = detailed["response"]
        assert "Amlodipine" in res
        assert "Metformin" in res
        assert "or" in res.lower() or "which" in res.lower() or "mean" in res.lower()
        assert detailed["intent"] == "Clarification"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_j_conversation_recall():
    """J. Conversation Recall: 'What did I just tell you?' recalls the user's previous statement."""
    db = SessionLocal()
    try:
        conversation_manager.add_message(USER_ENG_A, "user", "I prefer walking in the evening.")
        conversation_manager.add_message(USER_ENG_A, "assistant", "That sounds like a wonderful habit.")

        res = await orchestrator.process_request("What did I just tell you?", USER_ENG_A, db, language="en")
        assert "walking in the evening" in res.lower()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_k_ocme_query():
    """K. OCME Query: 'What language do I prefer for reminders?' retrieves grounded OCME memory."""
    db = SessionLocal()
    try:
        # Insert explicit OCME memory record
        mem = OCMEMemory(
            user_id=USER_ENG_A,
            category="Preference",
            title="preferred_language",
            value="Malayalam",
            confidence=0.95,
            source="user_explicit",
            archived=False
        )
        db.add(mem)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            res = await orchestrator.process_request("What language do I prefer for reminders?", USER_ENG_A, db, language="en")
            assert "Malayalam" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_l_explicit_memory():
    """L. Explicit Memory: 'Remember that I prefer Malayalam.' confirms persistence."""
    db = SessionLocal()
    try:
        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            res = await orchestrator.process_request("Remember that I prefer Malayalam for my medication alerts.", USER_ENG_A, db, language="en")
            assert any(w in res.lower() for w in ["remember", "noted", "note", "malayalam"])

            # Verify memory was persisted to DB
            saved = db.query(OCMEMemory).filter(OCMEMemory.user_id == USER_ENG_A).all()
            assert len(saved) > 0
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_m_medication_grounding():
    """M. Medication Grounding: Actual fixture medication data (dosage, time, status) is truthfully reflected."""
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Atorvastatin",
            dosage="20mg",
            reminder_time="09:30 PM",
            taken_status=False
        )
        db.add(med)
        db.commit()

        res = await orchestrator.process_request("What medicine do I take tonight?", USER_ENG_A, db, language="en")
        assert "Atorvastatin" in res
        assert "20mg" in res or "20 mg" in res
        assert "09:30 PM" in res or "9:30 PM" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_n_language_switching():
    """N. Language Switching: English -> Malayalam -> English preserves context and matches user language."""
    db = SessionLocal()
    try:
        # Turn 1: English
        t1 = await orchestrator.process_request("Hello ORMA", USER_ENG_A, db, language="en")
        assert any(w in t1.lower() for w in ["hello", "hi", "hear from you", "help"])

        # Turn 2: Malayalam
        t2 = await orchestrator.process_request("ശരി, ഇന്ന് സുഖമാണോ?", USER_ENG_A, db, language="ml")
        assert any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in t2)

        # Turn 3: English
        t3 = await orchestrator.process_request("Thank you, how are you?", USER_ENG_A, db, language="en")
        assert not any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in t3)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_o_malayalam_acknowledgment():
    """O. Malayalam Acknowledgment: 'ശരി' produces a concise Malayalam acknowledgment."""
    db = SessionLocal()
    try:
        res = await orchestrator.process_request("ശരി", USER_ENG_A, db, language="ml")
        assert "ശരി" in res
        assert len(res) < 60
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_p_malayalam_followup():
    """P. Malayalam Follow-Up: 'അത് എപ്പോഴാണ്?' resolves time in Malayalam."""
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add(med)
        db.commit()

        conversation_manager.add_message(USER_ENG_A, "assistant", "നിങ്ങളുടെ അടുത്ത മരുന്ന് Metformin ആണ്.")
        conversation_manager.save_interaction_context(USER_ENG_A, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"id": med.id, "name": "Metformin", "scheduled_time": "08:00 PM"}]
        })

        res = await orchestrator.process_request("അത് എപ്പോഴാണ്?", USER_ENG_A, db, language="ml")
        assert "Metformin" in res
        assert "08:00 PM" in res or "8:00 PM" in res
        assert any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in res)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_q_malayalam_repeat():
    """Q. Malayalam Repeat: 'ഒന്ന് കൂടി പറയാമോ?' repeats previous assistant message."""
    db = SessionLocal()
    try:
        prev_ml = "നിങ്ങളുടെ അടുത്ത മരുന്ന് മെറ്റ്ഫോർമിൻ ആണ്, സമയം രാത്രി 8 മണി."
        conversation_manager.add_message(USER_ENG_A, "assistant", prev_ml)

        res = await orchestrator.process_request("ഒന്ന് കൂടി പറയാമോ?", USER_ENG_A, db, language="ml")
        assert "മെറ്റ്ഫോർമിൻ" in res or "8 മണി" in res or "തീർച്ചയായും" in res
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_r_new_chat_isolation():
    """R. New Chat Isolation: Clearing conversation session isolates new turns completely."""
    db = SessionLocal()
    try:
        conversation_manager.add_message(USER_ENG_A, "assistant", "We were discussing Metformin.")
        conversation_manager.save_interaction_context(USER_ENG_A, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"name": "Metformin"}]
        })

        # Clear session (Simulating New Chat / Clear button)
        conversation_manager.clear_session(USER_ENG_A)

        assert len(conversation_manager.get_history(USER_ENG_A)) == 0
        assert conversation_manager.get_last_interaction_context(USER_ENG_A) is None
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_s_cross_user_isolation():
    """S. Cross-User Isolation: User A's context never bleeds into User B's turns."""
    db = SessionLocal()
    try:
        med_a = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Med_Secret_A",
            dosage="10mg",
            reminder_time="08:00 AM"
        )
        med_b = MedicineReminder(
            elder_id=USER_ENG_B,
            subject_id=USER_ENG_B,
            medicine_name="Med_Secret_B",
            dosage="20mg",
            reminder_time="09:00 PM"
        )
        db.add_all([med_a, med_b])
        db.commit()

        conversation_manager.add_message(USER_ENG_A, "assistant", "Your medicine is Med_Secret_A.")
        conversation_manager.save_interaction_context(USER_ENG_A, {
            "medications": [{"name": "Med_Secret_A"}]
        })

        # User B queries their next medicine
        res_b = await orchestrator.process_request("What is my next medicine?", USER_ENG_B, db, language="en")
        assert "Med_Secret_A" not in res_b
        assert "Med_Secret_B" in res_b
    finally:
        db.close()


@pytest.mark.asyncio
async def test_case_t_emergency_safety_regression():
    """T. Emergency Safety Regression: 'Help me!' triggers emergency alert, casual 'I don't feel well' does not."""
    db = SessionLocal()
    try:
        # 1. Critical Emergency Trigger
        det_em = await orchestrator.process_request_detailed("Help me!", USER_ENG_A, db, language="en")
        assert det_em["execution_mode"] == ExecutionMode.SAFETY_DETERMINISTIC
        assert "alerted" in det_em["response"].lower() or "help is on the way" in det_em["response"].lower()

        # 2. Casual Health Concern (NOT emergency alert)
        det_casual = await orchestrator.process_request_detailed("I don't feel well today", USER_ENG_A, db, language="en")
        assert det_casual["execution_mode"] != ExecutionMode.SAFETY_DETERMINISTIC
    finally:
        db.close()


@pytest.mark.asyncio
async def test_continuous_conversation_sequence():
    """Part 15 continuous conversation sequence test without generic capability loops."""
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_ENG_A,
            subject_id=USER_ENG_A,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            frequency="Daily",
            taken_status=False
        )
        db.add(med)
        db.commit()

        # Turn 1: Next medicine
        r1 = await orchestrator.process_request("What is my next medicine?", USER_ENG_A, db, language="en")
        assert "Metformin" in r1
        assert "08:00 PM" in r1 or "8:00 PM" in r1

        # Turn 2: User acknowledges
        r2 = await orchestrator.process_request("Okay.", USER_ENG_A, db, language="en")
        assert any(w in r2.lower() for w in ["alright", "okay"])
        assert "metformin" not in r2.lower()
        assert "assist you with your medicines" not in r2.lower()

        # Turn 3: Follow-up question
        r3 = await orchestrator.process_request("When should I take it?", USER_ENG_A, db, language="en")
        assert "Metformin" in r3
        assert "08:00 PM" in r3 or "8:00 PM" in r3

        # Turn 4: User asks to repeat
        r4 = await orchestrator.process_request("Can you tell me that again?", USER_ENG_A, db, language="en")
        assert "Metformin" in r4

        # Turn 5: User thanks
        r5 = await orchestrator.process_request("Okay, thanks.", USER_ENG_A, db, language="en")
        assert any(w in r5.lower() for w in ["welcome", "pleasure", "anytime", "alright"])
        assert "assist you with your medicines" not in r5.lower()
    finally:
        db.close()
