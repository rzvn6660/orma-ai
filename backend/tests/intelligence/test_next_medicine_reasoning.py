import pytest
import datetime
import pytz
from database import SessionLocal
from models.medicine import MedicineReminder
from models.user import User
from intelligence.orchestrator import orchestrator
from intelligence.tools import healthcare_tools

USER_A = "test_user_next_med_a"
USER_B = "test_user_next_med_b"

@pytest.fixture(autouse=True)
def clean_test_data():
    db = SessionLocal()
    try:
        db.query(MedicineReminder).filter(
            MedicineReminder.elder_id.in_([USER_A, USER_B]) | 
            MedicineReminder.subject_id.in_([USER_A, USER_B])
        ).delete()
        db.query(User).filter(User.id.in_([USER_A, USER_B])).delete()
        db.commit()

        # Create test users with timezone
        u_a = User(id=USER_A, email="next_med_a@test.local", name="Elderly Alice", role="elderly", timezone="Asia/Kolkata")
        u_b = User(id=USER_B, email="next_med_b@test.local", name="Elderly Bob", role="elderly", timezone="UTC")
        db.add_all([u_a, u_b])
        db.commit()
    finally:
        db.close()
    
    yield

    db = SessionLocal()
    try:
        db.query(MedicineReminder).filter(
            MedicineReminder.elder_id.in_([USER_A, USER_B]) | 
            MedicineReminder.subject_id.in_([USER_A, USER_B])
        ).delete()
        db.query(User).filter(User.id.in_([USER_A, USER_B])).delete()
        db.commit()
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_1_one_medicine_pending():
    """Scenario 1: One medicine today + pending -> returns that medicine."""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Amlodipine", dosage="5 mg", reminder_time="10:00 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        res = await orchestrator.process_request("What is my next medicine?", USER_A, db)
        assert "Amlodipine" in res
        assert "5 mg" in res
        assert "10:00 PM" in res
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_2_one_medicine_taken():
    """Scenario 2: One medicine today + TAKEN -> does NOT return it as next medicine."""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Test Medicine", dosage="10", reminder_time="02:04 PM",
            frequency="Daily", taken_status=True, taken_at=datetime.datetime.utcnow()
        )
        db.add(m)
        db.commit()

        res = await orchestrator.process_request("What is the next medicine to take for me today?", USER_A, db)
        # Must clearly state no more medicines today, and announce tomorrow's dose
        assert "no more medicines scheduled for today" in res.lower()
        assert "tomorrow" in res.lower()
        # Must NOT claim Test Medicine is scheduled for today at 02:04 PM
        assert "scheduled for 02:04 pm" not in res.lower() or "tomorrow at 02:04 pm" in res.lower()
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_3_multiple_medicines_first_taken_second_pending():
    """Scenario 3: Multiple medicines today (first taken, second pending) -> returns second medicine."""
    db = SessionLocal()
    try:
        m1 = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Metformin", dosage="500 mg", reminder_time="08:00 AM",
            frequency="Daily", taken_status=True, taken_at=datetime.datetime.utcnow()
        )
        m2 = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Atorvastatin", dosage="20 mg", reminder_time="09:00 PM",
            frequency="Daily", taken_status=False
        )
        db.add_all([m1, m2])
        db.commit()

        res = await orchestrator.process_request("What is my next medicine?", USER_A, db)
        assert "Atorvastatin" in res
        assert "20 mg" in res
        assert "09:00 PM" in res
        assert "Metformin" not in res
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_4_earlier_taken_later_pending():
    """Scenario 4: Earlier dose taken, later dose pending -> returns later dose."""
    db = SessionLocal()
    try:
        m1 = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Aspirin", dosage="75 mg", reminder_time="07:00 AM",
            frequency="Daily", taken_status=True, taken_at=datetime.datetime.utcnow()
        )
        m2 = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Vitamin D3", dosage="1000 IU", reminder_time="01:00 PM",
            frequency="Daily", taken_status=False
        )
        db.add_all([m1, m2])
        db.commit()

        res = await orchestrator.process_request("What is the next medicine to take for me today?", USER_A, db)
        assert "Vitamin D3" in res
        assert "Aspirin" not in res
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_5_all_medicines_taken_today():
    """Scenario 5: All medicines today taken -> returns 'no more medicines today' behavior."""
    db = SessionLocal()
    try:
        m1 = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Morning Pill", dosage="10 mg", reminder_time="08:00 AM",
            frequency="Daily", taken_status=True, taken_at=datetime.datetime.utcnow()
        )
        m2 = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Evening Pill", dosage="20 mg", reminder_time="08:00 PM",
            frequency="Daily", taken_status=True, taken_at=datetime.datetime.utcnow()
        )
        db.add_all([m1, m2])
        db.commit()

        res = await orchestrator.process_request("What is my next medicine to take today?", USER_A, db)
        assert "no more medicines scheduled for today" in res.lower()
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_6_future_recurring_tomorrow():
    """Scenario 6: Recurring medicine exists -> correctly identifies next future occurrence tomorrow."""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Glipizide", dosage="5 mg", reminder_time="09:00 AM",
            frequency="Daily", taken_status=True, taken_at=datetime.datetime.utcnow()
        )
        db.add(m)
        db.commit()

        res = await orchestrator.process_request("What is my next medicine?", USER_A, db)
        assert "tomorrow" in res.lower()
        assert "Glipizide" in res
        assert "09:00 AM" in res
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_7_no_future_medicines():
    """Scenario 7: No future medicines -> does not invent a medicine; reports no upcoming medicines."""
    db = SessionLocal()
    try:
        # SOS medicine taken today, no recurring schedule
        m = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Painkiller", dosage="500 mg", reminder_time="12:00 PM",
            frequency="SOS (As Needed)", taken_status=True, taken_at=datetime.datetime.utcnow()
        )
        db.add(m)
        db.commit()

        res = await orchestrator.process_request("What is my next medicine?", USER_A, db)
        assert "no more medicines scheduled for today" in res.lower() or "no medicines currently scheduled" in res.lower()
        # Must not fabricate an imaginary tomorrow dose
        assert "tomorrow" not in res.lower()
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_8_timezone_handling():
    """Scenario 8: Timezone handling uses user's timezone correctly."""
    db = SessionLocal()
    try:
        # User A is Asia/Kolkata (UTC+5:30)
        m = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Thyroxine", dosage="50 mcg", reminder_time="06:30 AM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        res = await orchestrator.process_request("What is my next dose?", USER_A, db)
        assert "Thyroxine" in res
        assert "06:30 AM" in res
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_9_query_phrasing_variations():
    """Scenario 9: Supports varied phrasing ('next dose', 'upcoming medicine', 'what is the next medicine to take for me today?')."""
    db = SessionLocal()
    try:
        m = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Lisinopril", dosage="10 mg", reminder_time="07:00 PM",
            frequency="Daily", taken_status=False
        )
        db.add(m)
        db.commit()

        for q in [
            "What is my next medicine?",
            "What is my next dose?",
            "What is the next medicine to take for me today?",
            "Which is my upcoming medicine?"
        ]:
            res = await orchestrator.process_request(q, USER_A, db)
            assert "Lisinopril" in res, f"Failed for query: {q}"
    finally:
        db.close()

@pytest.mark.asyncio
async def test_scenario_10_subject_isolation():
    """Scenario 10: User A's medicine cannot affect User B's next medicine."""
    db = SessionLocal()
    try:
        # User A has Insulin
        ma = MedicineReminder(
            elder_id=USER_A, subject_id=USER_A,
            medicine_name="Insulin Glargine", dosage="15 units", reminder_time="09:00 PM",
            frequency="Daily", taken_status=False
        )
        # User B has no medicines
        db.add(ma)
        db.commit()

        res_b = await orchestrator.process_request("What is my next medicine?", USER_B, db)
        assert "Insulin" not in res_b
        assert "no medicines" in res_b.lower()

        res_a = await orchestrator.process_request("What is my next medicine?", USER_A, db)
        assert "Insulin Glargine" in res_a
    finally:
        db.close()
