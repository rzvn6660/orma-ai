"""
ORMA AI — Adversarial Human Conversation QA Test Suite
Comprehensive parameterized tests for natural human language, incomplete utterances,
code-switching, pronoun coreference, entity selection, ambiguity clarification,
corrections, memory vs. conversation distinctions, and false-positive protections.
"""

import pytest
from unittest.mock import patch
from database import SessionLocal
from models.user import User
from models.medicine import MedicineReminder
from memory.memory_models import OCMEMemory
from intelligence.orchestrator import orchestrator
from intelligence.conversation_manager import conversation_manager
from intelligence.intent_detector import intent_detector
from intelligence.mode_resolver import ExecutionMode

USER_QA = "adv_user_qa_101"
USER_QA_B = "adv_user_qa_102"


@pytest.fixture(autouse=True)
def setup_teardown_db():
    db = SessionLocal()
    try:
        # Clean up test users & reminders & memories
        db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id.in_([USER_QA, USER_QA_B])) | 
            (MedicineReminder.subject_id.in_([USER_QA, USER_QA_B]))
        ).delete(synchronize_session=False)
        db.query(OCMEMemory).filter(OCMEMemory.user_id.in_([USER_QA, USER_QA_B])).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_([USER_QA, USER_QA_B])).delete(synchronize_session=False)

        user1 = User(id=USER_QA, name="Mary", role="elderly", phone="+19998887771", timezone="UTC")
        user2 = User(id=USER_QA_B, name="John", role="elderly", phone="+19998887772", timezone="UTC")
        db.add_all([user1, user2])
        db.commit()

        conversation_manager.clear_session(USER_QA)
        conversation_manager.clear_session(USER_QA_B)
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id.in_([USER_QA, USER_QA_B])) | 
            (MedicineReminder.subject_id.in_([USER_QA, USER_QA_B]))
        ).delete(synchronize_session=False)
        db.query(OCMEMemory).filter(OCMEMemory.user_id.in_([USER_QA, USER_QA_B])).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_([USER_QA, USER_QA_B])).delete(synchronize_session=False)
        db.commit()
        conversation_manager.clear_session(USER_QA)
        conversation_manager.clear_session(USER_QA_B)
    finally:
        db.close()


# =============================================================================
# PART 1 — GREETING ROBUSTNESS
# =============================================================================
GREETING_VARIATIONS = [
    ("Hello", "en"),
    ("Hi", "en"),
    ("Hey ORMA", "en"),
    ("Hello ORMA", "en"),
    ("Good morning", "en"),
    ("Good evening", "en"),
    ("Hi dear", "en"),
    ("Are you there?", "en"),
    ("ORMA?", "en"),
    ("ഹലോ", "ml"),
    ("നമസ്കാരം", "ml"),
    ("ഹായ്", "ml"),
    ("ഹലോ ഓർമ", "ml"),
    ("സുഖമാണോ ഓർമ?", "ml"),
    ("Hello ORMA, സുഖമാണോ?", "ml"),
    ("Hi ORMA, എങ്ങനെയുണ്ട്?", "ml"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("greeting_phrase,lang", GREETING_VARIATIONS)
async def test_part1_greeting_robustness(greeting_phrase, lang):
    db = SessionLocal()
    try:
        res = await orchestrator.process_request(greeting_phrase, USER_QA, db, language=lang)
        assert len(res) > 3
        assert "i am here to assist you with your medicines, health reminders, and daily schedule" not in res.lower()
        if lang == "ml":
            assert any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in res)
    finally:
        db.close()


# =============================================================================
# PART 2 — ACKNOWLEDGMENT ROBUSTNESS
# =============================================================================
ACKNOWLEDGMENT_VARIATIONS = [
    ("Okay", "en"),
    ("OK", "en"),
    ("Yeah", "en"),
    ("Yes", "en"),
    ("Alright", "en"),
    ("Right", "en"),
    ("Got it", "en"),
    ("Fine", "en"),
    ("That's fine", "en"),
    ("Okay then", "en"),
    ("Yeah okay", "en"),
    ("Ah okay", "en"),
    ("Hmm okay", "en"),
    ("Okay, thanks", "en"),
    ("ശരി", "ml"),
    ("ആ ശരി", "ml"),
    ("അതെ", "ml"),
    ("ഓക്കെ", "ml"),
    ("ശരി ഓർമ", "ml"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("ack_phrase,lang", ACKNOWLEDGMENT_VARIATIONS)
async def test_part2_acknowledgment_robustness(ack_phrase, lang):
    db = SessionLocal()
    try:
        # Prime with assistant turn
        conversation_manager.add_message(USER_QA, "assistant", "Your next medicine is Metformin at 8 PM.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"name": "Metformin", "scheduled_time": "08:00 PM"}]
        })

        detailed = await orchestrator.process_request_detailed(ack_phrase, USER_QA, db, language=lang)
        res = detailed["response"]
        
        # Must be short, acknowledging, without regurgitating medication list
        assert len(res) < 70
        assert "metformin at 8 pm" not in res.lower()
        assert "assist you with your medicines" not in res.lower()
        if lang == "ml":
            assert any(w in res for w in ["ശരി", "തീർച്ചയായും", "സന്തോഷം", "ഓക്കെ"])
        else:
            assert any(w in res.lower() for w in ["alright", "okay", "welcome", "got it"])
    finally:
        db.close()


# =============================================================================
# PART 3 — THANKS / GRATITUDE
# =============================================================================
THANKS_VARIATIONS = [
    ("Thanks", "en"),
    ("Thank you", "en"),
    ("Thanks ORMA", "en"),
    ("Thank you so much", "en"),
    ("That's helpful, thanks", "en"),
    ("നന്ദി", "ml"),
    ("വളരെ നന്ദി", "ml"),
    ("നന്ദി ഓർമ", "ml"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("thanks_phrase,lang", THANKS_VARIATIONS)
async def test_part3_thanks_robustness(thanks_phrase, lang):
    db = SessionLocal()
    try:
        detailed = await orchestrator.process_request_detailed(thanks_phrase, USER_QA, db, language=lang)
        res = detailed["response"]
        assert len(res) < 80
        if lang == "ml":
            assert any(w in res for w in ["സന്തോഷം", "തീർച്ചയായും", "നന്ദി"])
        else:
            assert any(w in res.lower() for w in ["welcome", "pleasure", "anytime", "happy to help"])
    finally:
        db.close()


# =============================================================================
# PART 4 — FOLLOW-UP ROBUSTNESS (TOMORROW)
# =============================================================================
TOMORROW_VARIATIONS = [
    "What about tomorrow?",
    "And tomorrow?",
    "Tomorrow?",
    "What do I have tomorrow?",
    "How about tomorrow?",
    "What about the next day?",
    "And the day after?",
    "What happens tomorrow?",
    "Tomorrow then?"
]

@pytest.mark.asyncio
@pytest.mark.parametrize("phrase", TOMORROW_VARIATIONS)
async def test_part4_followup_tomorrow_robustness(phrase):
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Glipizide",
            dosage="5mg",
            reminder_time="09:00 AM",
            frequency="Daily",
            taken_status=False
        )
        db.add(med)
        db.commit()

        # Prime conversation with previous turn
        conversation_manager.add_message(USER_QA, "assistant", "Your next medicine is Metformin at 8 PM.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"name": "Metformin", "scheduled_time": "08:00 PM"}]
        })

        detailed = await orchestrator.process_request_detailed(phrase, USER_QA, db, language="en")
        res = detailed["response"]
        assert "Glipizide" in res
        assert "09:00 AM" in res or "9:00 AM" in res
        assert detailed["intent"] in ["MEDICATION_SCHEDULE", "FOLLOW_UP"]
    finally:
        db.close()


# =============================================================================
# PART 5 — PRONOUN ROBUSTNESS
# =============================================================================
PRONOUN_VARIATIONS = [
    "When do I take it?",
    "When should I take it?",
    "What time do I take it?",
    "When am I supposed to take it?",
    "When do I have to take that?",
    "What time is that?",
    "That medicine, when?",
    "And that one?"
]

@pytest.mark.asyncio
@pytest.mark.parametrize("phrase", PRONOUN_VARIATIONS)
async def test_part5_pronoun_robustness(phrase):
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add(med)
        db.commit()

        conversation_manager.add_message(USER_QA, "assistant", "Your next medicine is Metformin at 8 PM.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"id": med.id, "name": "Metformin", "scheduled_time": "08:00 PM"}]
        })

        res = await orchestrator.process_request(phrase, USER_QA, db, language="en")
        assert "Metformin" in res
        assert "08:00 PM" in res or "8:00 PM" in res
    finally:
        db.close()


# =============================================================================
# PART 6 — MULTIPLE ENTITY REFERENCES
# =============================================================================
MULTIPLE_ENTITY_VARIATIONS = [
    ("What about the second one?", "Metformin", "08:00 PM"),
    ("When do I take the second one?", "Metformin", "08:00 PM"),
    ("And the morning one?", "Amlodipine", "08:00 AM"),
    ("What about the evening one?", "Metformin", "08:00 PM"),
    ("The first one?", "Amlodipine", "08:00 AM"),
    ("The other one?", "Metformin", "08:00 PM"),
    ("What time is the second medicine?", "Metformin", "08:00 PM"),
    ("What about Metformin?", "Metformin", "08:00 PM")
]

@pytest.mark.asyncio
@pytest.mark.parametrize("phrase,expected_med,expected_time", MULTIPLE_ENTITY_VARIATIONS)
async def test_part6_multiple_entity_references(phrase, expected_med, expected_time):
    db = SessionLocal()
    try:
        med1 = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Amlodipine",
            dosage="5mg",
            reminder_time="08:00 AM",
            taken_status=False
        )
        med2 = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add_all([med1, med2])
        db.commit()

        conversation_manager.add_message(USER_QA, "assistant", "You have Amlodipine at 8 AM and Metformin at 8 PM.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [
                {"id": med1.id, "name": "Amlodipine", "dosage": "5mg", "scheduled_time": "08:00 AM"},
                {"id": med2.id, "name": "Metformin", "dosage": "500mg", "scheduled_time": "08:00 PM"}
            ]
        })

        res = await orchestrator.process_request(phrase, USER_QA, db, language="en")
        assert expected_med in res
        assert expected_time in res or expected_time.replace("08", "8") in res
    finally:
        db.close()


# =============================================================================
# PART 7 — AMBIGUITY ADVERSARIAL TEST
# =============================================================================
AMBIGUITY_VARIATIONS = [
    "When do I take it?",
    "When do I take that?",
    "What time is it?",
    "When should I take this?",
    "That medicine, when?",
    "When do I take the medicine?",
    "When?",
    "What time?"
]

@pytest.mark.asyncio
@pytest.mark.parametrize("phrase", AMBIGUITY_VARIATIONS)
async def test_part7_ambiguity_clarification(phrase):
    db = SessionLocal()
    try:
        med1 = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Amlodipine",
            dosage="5mg",
            reminder_time="08:00 AM",
            taken_status=False
        )
        med2 = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add_all([med1, med2])
        db.commit()

        # Both medicines in context, no single focus established
        conversation_manager.add_message(USER_QA, "assistant", "You have Amlodipine and Metformin.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [
                {"id": med1.id, "name": "Amlodipine", "dosage": "5mg", "scheduled_time": "08:00 AM"},
                {"id": med2.id, "name": "Metformin", "dosage": "500mg", "scheduled_time": "08:00 PM"}
            ]
        })

        detailed = await orchestrator.process_request_detailed(phrase, USER_QA, db, language="en")
        res = detailed["response"]
        
        # Must not hallucinate one medicine; must ask clarification naming both
        assert "Amlodipine" in res
        assert "Metformin" in res
        assert any(w in res.lower() for w in ["which", "mean", "or"])
        assert detailed["intent"] == "Clarification"
    finally:
        db.close()


# =============================================================================
# PART 8 — REPEAT REQUESTS
# =============================================================================
REPEAT_VARIATIONS = [
    ("Can you repeat that?", "en"),
    ("Say that again.", "en"),
    ("What did you say?", "en"),
    ("Tell me that again.", "en"),
    ("Could you repeat that?", "en"),
    ("I didn't hear you.", "en"),
    ("One more time.", "en"),
    ("Again please.", "en"),
    ("ഒന്ന് കൂടി പറയാമോ?", "ml"),
    ("വീണ്ടും പറയാമോ?", "ml"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("phrase,lang", REPEAT_VARIATIONS)
async def test_part8_repeat_requests(phrase, lang):
    db = SessionLocal()
    try:
        prev_statement = "നിങ്ങളുടെ അടുത്ത മരുന്ന് Metformin 8 PM ആണ്." if lang == "ml" else "Your evening medicine is Metformin at 8 PM."
        conversation_manager.add_message(USER_QA, "assistant", prev_statement)

        res = await orchestrator.process_request(phrase, USER_QA, db, language=lang)
        assert "Metformin" in res
        assert "8 PM" in res or "8 pm" in res or "രാത്രി" in res
    finally:
        db.close()


# =============================================================================
# PART 9 — CORRECTIONS
# =============================================================================
CORRECTION_VARIATIONS = [
    ("No, I meant the morning one.", "en"),
    ("Sorry, the morning medicine.", "en"),
    ("No, not that one.", "en"),
    ("I was asking about the other one.", "en"),
    ("I meant the first one.", "en"),
    ("അല്ല, രാവിലെ കഴിക്കുന്ന മരുന്നാണ്.", "ml"),
    ("അതല്ല, രാവിലെ ഉള്ളത്.", "ml"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("phrase,lang", CORRECTION_VARIATIONS)
async def test_part9_corrections(phrase, lang):
    db = SessionLocal()
    try:
        med_morn = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Thyroxine",
            dosage="25mcg",
            reminder_time="07:00 AM",
            taken_status=False
        )
        med_eve = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            taken_status=False
        )
        db.add_all([med_morn, med_eve])
        db.commit()

        conversation_manager.add_message(USER_QA, "assistant", "Your evening medicine is Metformin at 8 PM.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"id": med_eve.id, "name": "Metformin", "scheduled_time": "08:00 PM"}]
        })

        res = await orchestrator.process_request(phrase, USER_QA, db, language=lang)
        assert "Thyroxine" in res
        assert "07:00 AM" in res or "7:00 AM" in res
    finally:
        db.close()


# =============================================================================
# PART 10 — CONVERSATION RECALL
# =============================================================================
RECALL_VARIATIONS = [
    ("What did I just tell you?", "en"),
    ("What did I say?", "en"),
    ("What was I saying?", "en"),
    ("What did I tell you just now?", "en"),
    ("Do you remember what I said?", "en"),
    ("ഞാൻ എന്താണ് പറഞ്ഞത്?", "ml"),
    ("ഞാൻ ഇപ്പോൾ എന്താണ് പറഞ്ഞത്?", "ml"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("phrase,lang", RECALL_VARIATIONS)
async def test_part10_conversation_recall(phrase, lang):
    db = SessionLocal()
    try:
        prev_user_msg = "ഞാൻ ചായ കുടിക്കാൻ പോകുന്നു" if lang == "ml" else "I like drinking tea in the morning"
        conversation_manager.add_message(USER_QA, "user", prev_user_msg)
        conversation_manager.add_message(USER_QA, "assistant", "That sounds pleasant.")

        res = await orchestrator.process_request(phrase, USER_QA, db, language=lang)
        assert prev_user_msg.lower() in res.lower()
    finally:
        db.close()


# =============================================================================
# PART 11 — OCME DISTINCTION
# =============================================================================
@pytest.mark.asyncio
async def test_part11_ocme_explicit_vs_casual():
    db = SessionLocal()
    try:
        # 1. Explicit memory request
        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            res1 = await orchestrator.process_request("Remember that I prefer Malayalam.", USER_QA, db, language="en")
            assert any(w in res1.lower() for w in ["remember", "noted", "save", "malayalam"])

            # Verify saved in OCME
            mems = db.query(OCMEMemory).filter(OCMEMemory.user_id == USER_QA).all()
            assert len(mems) > 0

        # Clear session (simulating new session/chat)
        conversation_manager.clear_session(USER_QA)

        # 2. Query in new session
        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            res2 = await orchestrator.process_request("What language do I prefer?", USER_QA, db, language="en")
            assert "Malayalam" in res2

        # 3. Casual conversational statement
        conversation_manager.clear_session(USER_QA)
        count_before = db.query(OCMEMemory).filter(OCMEMemory.user_id == USER_QA).count()
        await orchestrator.process_request("I like tea.", USER_QA, db, language="en")
        count_after = db.query(OCMEMemory).filter(OCMEMemory.user_id == USER_QA).count()
        assert count_after == count_before
    finally:
        db.close()


# =============================================================================
# PART 12 — LANGUAGE SWITCHING
# =============================================================================
@pytest.mark.asyncio
async def test_part12_language_switching_flow():
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            frequency="Daily",
            taken_status=False
        )
        db.add(med)
        db.commit()

        # Turn 1: English greeting
        t1 = await orchestrator.process_request("Hello ORMA.", USER_QA, db, language="en")
        assert any(w in t1.lower() for w in ["hello", "hi", "how can i help"])

        # Turn 2: Malayalam next med query
        t2 = await orchestrator.process_request("എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", USER_QA, db, language="ml")
        assert "Metformin" in t2
        assert any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in t2)

        # Turn 3: Malayalam follow-up
        t3 = await orchestrator.process_request("അത് എപ്പോഴാണ് കഴിക്കേണ്ടത്?", USER_QA, db, language="ml")
        assert "Metformin" in t3
        assert "08:00 PM" in t3 or "8:00 PM" in t3

        # Turn 4: English follow-up
        t4 = await orchestrator.process_request("What about tomorrow?", USER_QA, db, language="en")
        assert "Metformin" in t4
        assert not any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in t4)

        # Turn 5: Malayalam acknowledgment
        t5 = await orchestrator.process_request("ശരി.", USER_QA, db, language="ml")
        assert "ശരി" in t5
        assert len(t5) < 60
    finally:
        db.close()


# =============================================================================
# PART 13 — MIXED LANGUAGE ROBUSTNESS
# =============================================================================
MIXED_LANGUAGE_INPUTS = [
    ("My medicine എപ്പോഴാണ് കഴിക്കേണ്ടത്?", "time"),
    ("Tomorrow എന്താണ്?", "tomorrow"),
    ("That medicine എപ്പോഴാ?", "time"),
    ("Okay, അത് മനസ്സിലായി.", "ack"),
    ("Morning medicine ഏതാണ്?", "morning"),
    ("എന്റെ next medicine ഏതാണ്?", "next"),
    ("Can you repeat അത്?", "repeat"),
    ("ശരി, what about tomorrow?", "tomorrow"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_type", MIXED_LANGUAGE_INPUTS)
async def test_part13_mixed_language_handling(query, expected_type):
    db = SessionLocal()
    try:
        med_morn = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Amlodipine",
            dosage="5mg",
            reminder_time="08:00 AM",
            frequency="Daily",
            taken_status=False
        )
        med_eve = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            frequency="Daily",
            taken_status=False
        )
        db.add_all([med_morn, med_eve])
        db.commit()

        conversation_manager.add_message(USER_QA, "assistant", "Your medicine is Metformin scheduled at 8:00 PM.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"id": med_eve.id, "name": "Metformin", "scheduled_time": "08:00 PM"}]
        })

        detailed = await orchestrator.process_request_detailed(query, USER_QA, db, language="ml")
        res = detailed["response"]
        assert len(res) > 2

        if expected_type == "time":
            assert "08:00 PM" in res or "8:00 PM" in res or "Metformin" in res
        elif expected_type == "tomorrow":
            assert "Amlodipine" in res or "Metformin" in res
        elif expected_type == "ack":
            assert len(res) < 70
        elif expected_type == "morning":
            assert "Amlodipine" in res
        elif expected_type == "next":
            assert "Amlodipine" in res or "Metformin" in res
        elif expected_type == "repeat":
            assert "Metformin" in res
    finally:
        db.close()


# =============================================================================
# PART 14 — HUMAN CONVERSATION SEQUENCE (ENGLISH)
# =============================================================================
@pytest.mark.asyncio
async def test_part14_human_conversation_sequence_english():
    db = SessionLocal()
    try:
        med_m = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Thyroxine",
            dosage="25mcg",
            reminder_time="07:00 AM",
            frequency="Daily",
            taken_status=False
        )
        med_e = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            frequency="Daily",
            taken_status=False
        )
        db.add_all([med_m, med_e])
        db.commit()

        # 1. Greeting
        r1 = await orchestrator.process_request("Hello ORMA.", USER_QA, db, language="en")
        assert any(w in r1.lower() for w in ["hello", "hi", "how can i help"])
        assert "i am here to assist you with your medicines" not in r1.lower()

        # 2. Next medicine
        r2 = await orchestrator.process_request("What is my next medicine?", USER_QA, db, language="en")
        assert any(m in r2 for m in ["Thyroxine", "Metformin"])

        # 3. Acknowledgment
        r3 = await orchestrator.process_request("Okay.", USER_QA, db, language="en")
        assert any(w in r3.lower() for w in ["alright", "okay"])
        assert "assist you with your medicines" not in r3.lower()

        # 4. Tomorrow follow-up
        r4 = await orchestrator.process_request("What about tomorrow?", USER_QA, db, language="en")
        assert "Thyroxine" in r4 or "Metformin" in r4

        # 5. Evening one
        r5 = await orchestrator.process_request("And the evening one?", USER_QA, db, language="en")
        assert "Metformin" in r5
        assert "08:00 PM" in r5 or "8:00 PM" in r5

        # 6. Acknowledgment
        r6 = await orchestrator.process_request("Okay, got it.", USER_QA, db, language="en")
        assert any(w in r6.lower() for w in ["alright", "okay", "got it"])

        # 7. Repeat request
        r7 = await orchestrator.process_request("Can you tell me that again?", USER_QA, db, language="en")
        assert "Metformin" in r7

        # 8. Correction
        r8 = await orchestrator.process_request("Actually no, I meant the morning one.", USER_QA, db, language="en")
        assert "Thyroxine" in r8
        assert "07:00 AM" in r8 or "7:00 AM" in r8

        # 9. Thanks
        r9 = await orchestrator.process_request("Thanks.", USER_QA, db, language="en")
        assert any(w in r9.lower() for w in ["welcome", "pleasure", "anytime", "happy"])
        assert "assist you with your medicines" not in r9.lower()
    finally:
        db.close()


# =============================================================================
# PART 15 — MALAYALAM COMPLETE SEQUENCE
# =============================================================================
@pytest.mark.asyncio
async def test_part15_malayalam_complete_sequence():
    db = SessionLocal()
    try:
        med_m = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Thyroxine",
            dosage="25mcg",
            reminder_time="07:00 AM",
            frequency="Daily",
            taken_status=False
        )
        med_e = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Metformin",
            dosage="500mg",
            reminder_time="08:00 PM",
            frequency="Daily",
            taken_status=False
        )
        db.add_all([med_m, med_e])
        db.commit()

        # 1. Greeting
        r1 = await orchestrator.process_request("ഹലോ ഓർമ.", USER_QA, db, language="ml")
        assert any(w in r1 for w in ["നമസ്കാരം", "ഹലോ", "സഹായിക്കണം", "ഇവിടെയുണ്ട്"])

        # 2. Next medicine
        r2 = await orchestrator.process_request("എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?", USER_QA, db, language="ml")
        assert "Thyroxine" in r2 or "Metformin" in r2

        # 3. Acknowledgment
        r3 = await orchestrator.process_request("ശരി.", USER_QA, db, language="ml")
        assert "ശരി" in r3
        assert len(r3) < 60

        # 4. Tomorrow
        r4 = await orchestrator.process_request("നാളെ എന്താണ്?", USER_QA, db, language="ml")
        assert "Thyroxine" in r4 or "Metformin" in r4

        # 5. Specific medicine time
        r5 = await orchestrator.process_request("ആ മരുന്ന് എപ്പോഴാണ്?", USER_QA, db, language="ml")
        assert "07:00 AM" in r5 or "08:00 PM" in r5 or "7:00 AM" in r5 or "8:00 PM" in r5

        # 6. Repeat
        r6 = await orchestrator.process_request("ഒന്ന് കൂടി പറയാമോ?", USER_QA, db, language="ml")
        assert len(r6) > 5

        # 7. Correction
        r7 = await orchestrator.process_request("അല്ല, രാവിലെ ഉള്ള മരുന്നാണ് ഞാൻ ചോദിച്ചത്.", USER_QA, db, language="ml")
        assert "Thyroxine" in r7

        # 8. Thanks
        r8 = await orchestrator.process_request("നന്ദി.", USER_QA, db, language="ml")
        assert any(w in r8 for w in ["സന്തോഷം", "തീർച്ചയായും", "നന്ദി"])
    finally:
        db.close()


# =============================================================================
# PART 16 — SHORT / INCOMPLETE HUMAN SPEECH
# =============================================================================
SHORT_INCOMPLETE_UTTERANCES = [
    ("Tomorrow?", "MEDICATION_SCHEDULE"),
    ("The morning one?", "MEDICATION_SCHEDULE"),
    ("Again?", "REPEAT_REQUEST"),
    ("Okay?", "ACKNOWLEDGMENT"),
    ("Hmm.", "ACKNOWLEDGMENT"),
    ("Yeah.", "ACKNOWLEDGMENT"),
    ("Right.", "ACKNOWLEDGMENT"),
    ("Tomorrow then?", "MEDICATION_SCHEDULE"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("utterance,expected_intent", SHORT_INCOMPLETE_UTTERANCES)
async def test_part16_short_incomplete_speech(utterance, expected_intent):
    db = SessionLocal()
    try:
        med = MedicineReminder(
            elder_id=USER_QA,
            subject_id=USER_QA,
            medicine_name="Amlodipine",
            dosage="5mg",
            reminder_time="08:00 AM",
            frequency="Daily",
            taken_status=False
        )
        db.add(med)
        db.commit()

        conversation_manager.add_message(USER_QA, "assistant", "Your morning medicine is Amlodipine at 08:00 AM.")
        conversation_manager.save_interaction_context(USER_QA, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [{"id": med.id, "name": "Amlodipine", "scheduled_time": "08:00 AM"}]
        })

        detailed = await orchestrator.process_request_detailed(utterance, USER_QA, db, language="en")
        assert detailed["intent"] == expected_intent or (expected_intent == "MEDICATION_SCHEDULE" and detailed["intent"] == "FOLLOW_UP")
        assert "assist you with your medicines, health reminders, and daily schedule" not in detailed["response"].lower()
    finally:
        db.close()


# =============================================================================
# PART 19 — FALSE POSITIVE CHECK
# =============================================================================
@pytest.mark.asyncio
async def test_part19_false_positive_protections():
    db = SessionLocal()
    try:
        # 1. Casual unwell should NOT trigger emergency alert
        det_unwell = await orchestrator.process_request_detailed("I don't feel well today", USER_QA, db, language="en")
        assert det_unwell["execution_mode"] != ExecutionMode.SAFETY_DETERMINISTIC
        assert det_unwell["intent"] != "Emergency"

        # 2. Historical fall mention should NOT trigger emergency alert
        det_past_fall = await orchestrator.process_request_detailed("Okay, I fell yesterday, but I am resting now", USER_QA, db, language="en")
        assert det_past_fall["execution_mode"] != ExecutionMode.SAFETY_DETERMINISTIC
        assert det_past_fall["intent"] != "Emergency"

        # 3. Informational question about emergency should NOT trigger emergency alert
        det_info_em = await orchestrator.process_request_detailed("Can you tell me about emergency support?", USER_QA, db, language="en")
        assert det_info_em["execution_mode"] != ExecutionMode.SAFETY_DETERMINISTIC
        assert det_info_em["intent"] != "Emergency"

        # 4. 'Good morning' is GREETING
        det_gm = await orchestrator.process_request_detailed("Good morning ORMA", USER_QA, db, language="en")
        assert det_gm["intent"] == "GREETING"

        # 5. 'Morning medicine' is MEDICATION, not greeting
        det_mm = await orchestrator.process_request_detailed("What is my morning medicine?", USER_QA, db, language="en")
        assert det_mm["intent"] in ["MEDICATION_SCHEDULE", "FOLLOW_UP"]

        # 6. 'Yes, I need my medicine' is MEDICATION, not pure acknowledgment
        det_need_med = await orchestrator.process_request_detailed("Yes, I need my medicine", USER_QA, db, language="en")
        assert det_need_med["intent"] in ["MEDICATION_SCHEDULE", "MEDICATION_STATUS"]
        assert det_need_med["intent"] != "ACKNOWLEDGMENT"

        # 7. Acute emergency triggers SAFETY_DETERMINISTIC
        det_acute = await orchestrator.process_request_detailed("Help me, I fell down and can't get up!", USER_QA, db, language="en")
        assert det_acute["execution_mode"] == ExecutionMode.SAFETY_DETERMINISTIC
        assert det_acute["intent"] == "Emergency"
    finally:
        db.close()
