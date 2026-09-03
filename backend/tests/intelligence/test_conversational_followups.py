import pytest
import datetime
from unittest.mock import patch
from database import SessionLocal
from models.medicine import MedicineReminder
from models.user import User
from intelligence.orchestrator import orchestrator
from intelligence.conversation_manager import conversation_manager

USER_CF = "test_user_conversational_followup"

@pytest.fixture(autouse=True)
def clean_test_data():
    conversation_manager.clear_session(USER_CF)
    db = SessionLocal()
    try:
        db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == USER_CF) | (MedicineReminder.subject_id == USER_CF)
        ).delete()
        db.query(User).filter(User.id == USER_CF).delete()
        db.commit()

        # Create test user in UTC
        u = User(id=USER_CF, email="followup@test.local", name="Elderly Followup", role="elderly", timezone="UTC")
        db.add(u)
        db.commit()
    finally:
        db.close()

    yield

    conversation_manager.clear_session(USER_CF)
    db = SessionLocal()
    try:
        db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == USER_CF) | (MedicineReminder.subject_id == USER_CF)
        ).delete()
        db.query(User).filter(User.id == USER_CF).delete()
        db.commit()
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_a_tomorrow_followup():
    """Scenario A: Previous 'When is the next medicine?' -> Follow-up 'What about tomorrow?'"""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Test Medicine (10)", dosage="standard dose", reminder_time="02:04 PM",
            frequency="Daily", taken_status=True
        )
        db.add(m)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            # Turn 1: Next medicine query
            res1 = await orchestrator.process_request("When is the next medicine?", USER_CF, db)
            assert "Test Medicine (10)" in res1
            assert "02:04 PM" in res1
            assert "tomorrow" in res1.lower()

            # Turn 2: Follow-up asking about tomorrow
            res2 = await orchestrator.process_request("What about tomorrow?", USER_CF, db)
            assert "Tomorrow you have" in res2
            assert "Test Medicine (10)" in res2
            assert "02:04 PM" in res2
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_b_identity_followup():
    """Scenario B: Previous 'When is the next medicine?' -> Follow-up 'What medicine is that?'"""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Test Medicine (10)", dosage="standard dose", reminder_time="02:04 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            # Turn 1
            res1 = await orchestrator.process_request("When is the next medicine?", USER_CF, db)
            assert "Test Medicine (10)" in res1

            # Turn 2: Follow-up asking for medicine identity
            res2 = await orchestrator.process_request("What medicine is that?", USER_CF, db)
            assert "That medicine is Test Medicine (10)" in res2
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_c_time_followup():
    """Scenario C: Previous 'When is the next medicine?' -> Follow-up 'What time?'"""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Test Medicine (10)", dosage="standard dose", reminder_time="02:04 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            # Turn 1
            res1 = await orchestrator.process_request("When is the next medicine?", USER_CF, db)
            assert "02:04 PM" in res1

            # Turn 2: Follow-up asking what time
            res2 = await orchestrator.process_request("What time?", USER_CF, db)
            assert "02:04 PM" in res2
            assert "Test Medicine (10)" in res2
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_d_status_followup_pending_and_taken():
    """Scenario D: Previous 'When is the next medicine?' -> Follow-up 'Did I already take that one?'"""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Test Medicine (10)", dosage="standard dose", reminder_time="02:04 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            # Turn 1: Ask for next medicine
            res1 = await orchestrator.process_request("When is the next medicine?", USER_CF, db)
            assert "Test Medicine (10)" in res1

            # Turn 2: Ask if already taken while pending
            res2 = await orchestrator.process_request("Did I already take that one?", USER_CF, db)
            assert "No, you have not taken Test Medicine (10) yet" in res2

            # Now mark as taken in DB
            m.taken_status = True
            db.commit()

            # Turn 3: Ask again after taking
            res3 = await orchestrator.process_request("Did I already take that one?", USER_CF, db)
            assert "Yes, you have already taken Test Medicine (10)" in res3
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_e_ambiguous_reference_clarification():
    """Scenario E: Ambiguous reference with two medicines mentioned -> Asks clarification."""
    db = SessionLocal()
    try:
        m1 = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Medicine A", dosage="10 mg", reminder_time="10:00 AM",
            frequency="Daily", taken_status=False
        )
        m2 = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Medicine B", dosage="20 mg", reminder_time="06:00 PM",
            frequency="Daily", taken_status=False
        )
        db.add_all([m1, m2])
        db.commit()

        # Seed interaction context with two medicines mentioned in previous turn
        conversation_manager.save_interaction_context(USER_CF, {
            "intent": "MEDICATION_SCHEDULE",
            "medications": [
                {"name": "Medicine A", "scheduled_time": "10:00 AM", "dosage": "10 mg"},
                {"name": "Medicine B", "scheduled_time": "06:00 PM", "dosage": "20 mg"}
            ]
        })
        conversation_manager.add_message(USER_CF, "user", "What is my medicine schedule?")
        conversation_manager.add_message(USER_CF, "assistant", "You have Medicine A at 10:00 AM and Medicine B at 06:00 PM.")

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            res = await orchestrator.process_request("What time is that?", USER_CF, db)
            # Must ask clarification rather than picking one arbitrarily
            assert "Do you mean Medicine A at 10:00 AM or Medicine B at 06:00 PM?" in res
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_f_medication_name_dosage_safety():
    """Scenario F: 'Test Medicine (10)' must NOT be assumed to mean '10 mg' unless dosage explicitly says 10 mg."""
    db = SessionLocal()
    try:
        # Case 1: Dosage is unknown / empty in DB
        m1 = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Test Medicine (10)", dosage=None, reminder_time="02:04 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m1)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            # Turn 1
            await orchestrator.process_request("When is the next medicine?", USER_CF, db)

            # Turn 2: User asks if the 10 means 10 mg
            res2 = await orchestrator.process_request("Why the 10 is the 10 mg you mean?", USER_CF, db)
            # Must refuse to assume 10 mg
            assert "I don't want to assume that the '10' in the medicine name means 10 mg" in res2

        # Case 2: DB record explicitly has dosage = "10 mg"
        m1.dosage = "10 mg"
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            await orchestrator.process_request("When is the next medicine?", USER_CF, db)
            res3 = await orchestrator.process_request("Is that 10 mg?", USER_CF, db)
            assert "prescribed dosage for Test Medicine (10) is 10 mg" in res3
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_g_existing_upcoming_medicine_offline():
    """Scenario G: Existing 'Which is my upcoming medicine?' continues to resolve deterministically."""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Metformin", dosage="500 mg", reminder_time="08:00 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            res = await orchestrator.process_request("Which is my upcoming medicine?", USER_CF, db)
            assert "Metformin" in res
            assert "500 mg" in res
            assert "08:00 PM" in res
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_h_natural_language_variations():
    """Scenario H: Test natural phrasing variations for follow-ups."""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_CF, subject_id=USER_CF,
            medicine_name="Test Medicine (10)", dosage="standard dose", reminder_time="02:04 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        with patch("intelligence.orchestrator.ai_manager.check_health", return_value={"available": False, "provider": "none"}):
            # 1. "What about the one tomorrow?"
            await orchestrator.process_request("When is the next medicine?", USER_CF, db)
            r1 = await orchestrator.process_request("What about the one tomorrow?", USER_CF, db)
            assert "Tomorrow you have" in r1
            assert "Test Medicine (10)" in r1

            # 2. "Which one is that?"
            r2 = await orchestrator.process_request("Which one is that?", USER_CF, db)
            assert "That medicine is Test Medicine (10)" in r2

            # 3. "Did I take it already?"
            r3 = await orchestrator.process_request("Did I take it already?", USER_CF, db)
            assert "No, you have not taken Test Medicine (10) yet" in r3

            # 4. "What medicine do you mean?"
            r4 = await orchestrator.process_request("What medicine do you mean?", USER_CF, db)
            assert "That medicine is Test Medicine (10)" in r4
    finally:
        db.close()
