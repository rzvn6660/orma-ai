import sys
import os
import asyncio
import re
import pytest
from datetime import datetime, date
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from main import app
from database import SessionLocal
from models.user import User
from models.medicine import MedicineReminder
from models.health_event import HealthEvent
from intelligence.orchestrator import orchestrator
from intelligence.conversation_manager import conversation_manager
from intelligence.tools import healthcare_tools
from services.auth_service import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_test_state():
    """Clean session state before and after each test."""
    db = SessionLocal()
    try:
        for uid in ["test_med_elder_1", "test_med_elder_2"]:
            conversation_manager.clear_session(uid)
            db.query(MedicineReminder).filter(
                (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
            ).delete()
            db.query(HealthEvent).filter(
                (HealthEvent.elder_id == uid) | (HealthEvent.subject_id == uid)
            ).delete()
            user = db.query(User).filter(User.id == uid).first()
            if not user:
                user = User(
                    id=uid,
                    email=f"{uid}@orma.ai",
                    name=f"Test Elder {uid[-1]}",
                    role="elderly",
                    timezone="Asia/Kolkata"
                )
                db.add(user)
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        for uid in ["test_med_elder_1", "test_med_elder_2"]:
            conversation_manager.clear_session(uid)
            db.query(MedicineReminder).filter(
                (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
            ).delete()
            db.query(HealthEvent).filter(
                (HealthEvent.elder_id == uid) | (HealthEvent.subject_id == uid)
            ).delete()
        db.commit()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_1_conversational_creation_routes_to_medicine_reminders_not_health_events():
    """
    Test 1: Conversational medicine creation routes to medicine_reminders, not health_events.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Turn 1: User says time
        res1 = await orchestrator.process_request("My medicine is at 8 PM.", uid, db, language="en")
        assert "What is the name of the medicine?" in res1

        # Turn 2: User provides name
        res2 = await orchestrator.process_request("Test Medicine", uid, db, language="en")
        assert "Would you like me to add this to your medicines?" in res2
        assert "Test Medicine" in res2

        # Turn 3: User confirms
        res3 = await orchestrator.process_request("yes", uid, db, language="en")
        assert "I have added Test Medicine" in res3

        # Verification: Exactly one MedicineReminder in canonical table
        meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds) == 1
        assert meds[0].medicine_name == "Test Medicine"
        assert meds[0].reminder_time == "08:00 PM"

        # Verification: ZERO HealthEvent records created
        events = db.query(HealthEvent).filter(
            (HealthEvent.elder_id == uid) | (HealthEvent.subject_id == uid)
        ).all()
        assert len(events) == 0, f"Expected 0 health_events but found {len(events)}"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_2_providing_name_and_time_does_not_create_db_record_before_confirmation():
    """
    Test 2: Providing medicine name + time does NOT create the DB record before confirmation.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Turn 1: User provides time
        res1 = await orchestrator.process_request("My medicine is at 8 PM.", uid, db, language="en")
        assert "What is the name of the medicine?" in res1

        # Turn 2: User provides name
        res2 = await orchestrator.process_request("Aspirin", uid, db, language="en")
        assert "Would you like me to add this to your medicines?" in res2

        # Critical Check: At this point, pending confirmation state is active, but DB MUST be empty!
        meds_before = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds_before) == 0, "MedicineReminder was prematurely created before explicit confirmation!"

        events_before = db.query(HealthEvent).filter(
            (HealthEvent.elder_id == uid) | (HealthEvent.subject_id == uid)
        ).all()
        assert len(events_before) == 0, "HealthEvent was prematurely created before explicit confirmation!"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_3_positive_confirmation_creates_exactly_one_medicine_reminder():
    """
    Test 3: Positive confirmation creates exactly one MedicineReminder.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # User provides name and time in multi-turn
        await orchestrator.process_request("My medicine is at 8 PM.", uid, db, language="en")
        await orchestrator.process_request("Metformin", uid, db, language="en")

        # Explicit confirmation: "confirm"
        res_confirm = await orchestrator.process_request("confirm", uid, db, language="en")
        assert "I have added Metformin" in res_confirm

        meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds) == 1
        assert meds[0].medicine_name == "Metformin"
        assert meds[0].frequency.lower() == "once daily"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_4_cancellation_creates_no_medicine_reminder():
    """
    Test 4: Cancellation creates no MedicineReminder.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Scenario A: Cancel at confirmation summary
        await orchestrator.process_request("My medicine is at 9 PM.", uid, db, language="en")
        await orchestrator.process_request("Amoxicillin", uid, db, language="en")

        res_cancel = await orchestrator.process_request("no, cancel", uid, db, language="en")
        assert "cancelled" in res_cancel.lower()

        meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds) == 0

        # Scenario B: Cancel during clarification
        await orchestrator.process_request("My medicine is at 10 PM.", uid, db, language="en")
        res_cancel2 = await orchestrator.process_request("cancel", uid, db, language="en")
        assert "cancelled" in res_cancel2.lower()

        meds2 = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds2) == 0
    finally:
        db.close()


@pytest.mark.asyncio
async def test_5_conversation_created_medicine_appears_through_get_api_medicines():
    """
    Test 5: Conversation-created medicine appears through GET /api/medicines.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Conversational creation + confirmation
        await orchestrator.process_request("My medicine is at 8 PM.", uid, db, language="en")
        await orchestrator.process_request("Thyroxine", uid, db, language="en")
        await orchestrator.process_request("yes", uid, db, language="en")

        # API Call as the elder user
        token = create_access_token(data={"sub": uid, "role": "elderly", "ver": 1})
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/medicines", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        matched = [m for m in data if m["medicine_name"] == "Thyroxine"]
        assert len(matched) == 1
        assert matched[0]["reminder_time"] == "08:00 PM"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_6_newly_created_medicine_can_subsequently_be_marked_taken():
    """
    Test 6: The newly created medicine can subsequently be marked taken through the existing voice/UI flow.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Create conversationally
        await orchestrator.process_request("My medicine is at 8 PM.", uid, db, language="en")
        await orchestrator.process_request("Atorvastatin", uid, db, language="en")
        await orchestrator.process_request("yes", uid, db, language="en")

        med = db.query(MedicineReminder).filter(
            MedicineReminder.medicine_name == "Atorvastatin",
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).first()
        assert med is not None
        assert not med.taken_status

        # Part A: Voice flow adherence logging ("I took Atorvastatin")
        voice_res = await orchestrator.process_request("I took Atorvastatin", uid, db, language="en")
        assert "Atorvastatin" in voice_res
        assert any(w in voice_res.lower() for w in ["taken", "marked", "recorded", "great"])

        db.refresh(med)
        assert med.taken_status is True

        # Part B: UI endpoint PUT /api/medicines/{id}/taken works consistently
        token = create_access_token(data={"sub": uid, "role": "elderly", "ver": 1})
        headers = {"Authorization": f"Bearer {token}"}
        ui_res = client.put(f"/api/medicines/{med.id}/taken", headers=headers)
        assert ui_res.status_code == 200
        assert ui_res.json()["taken_status"] is True
    finally:
        db.close()


@pytest.mark.asyncio
async def test_7_user_elder_isolation_remains_enforced():
    """
    Test 7: User/elder isolation remains enforced.
    """
    db = SessionLocal()
    uid_a = "test_med_elder_1"
    uid_b = "test_med_elder_2"
    try:
        # User A creates medicine conversationally
        await orchestrator.process_request("My medicine is at 8 PM.", uid_a, db, language="en")
        await orchestrator.process_request("SecretMedA", uid_a, db, language="en")
        await orchestrator.process_request("yes", uid_a, db, language="en")

        # User B queries via API
        token_b = create_access_token(data={"sub": uid_b, "role": "elderly", "ver": 1})
        headers_b = {"Authorization": f"Bearer {token_b}"}

        resp_b = client.get("/api/medicines", headers=headers_b)
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert not any(m["medicine_name"] == "SecretMedA" for m in data_b), "Tenant isolation breached: User B saw User A's medicine!"

        # User B queries via Conversational schedule
        conv_b = await orchestrator.process_request("What are my medicines?", uid_b, db, language="en")
        assert "SecretMedA" not in conv_b
    finally:
        db.close()


@pytest.mark.asyncio
async def test_8_existing_medication_date_scoping_behavior_remains_unchanged():
    """
    Test 8: Existing medication date-scoping behavior remains unchanged.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Create medicine conversationally
        await orchestrator.process_request("My medicine is at 8 PM.", uid, db, language="en")
        await orchestrator.process_request("Lisinopril", uid, db, language="en")
        await orchestrator.process_request("yes", uid, db, language="en")

        # Check date-scoped schedule tool
        today_sched = healthcare_tools.get_medication_schedule(db, uid, time_period="today")
        med_names = [m["name"] for m in today_sched.get("medications", [])]
        assert "Lisinopril" in med_names

        # Check daily adherence tool
        adherence = healthcare_tools.get_daily_adherence(db, uid)
        assert adherence["total_scheduled"] >= 1
    finally:
        db.close()


@pytest.mark.asyncio
async def test_9_existing_multilingual_malayalam_confirmation_handling():
    """
    Test 9: Existing multilingual/English confirmation handling remains intact.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Turn 1: Malayalam creation statement
        res1 = await orchestrator.process_request("എന്റെ മരുന്ന് രാത്രി 8 മണിക്കാണ്", uid, db, language="ml")
        assert "ഏതാണ് മരുന്നിന്റെ പേര്?" in res1

        # Turn 2: Malayalam medicine name
        res2 = await orchestrator.process_request("പാരാസിറ്റമോൾ", uid, db, language="ml")
        assert "പാരാസിറ്റമോൾ" in res2
        assert "ചേർക്കണോ?" in res2

        # Verify DB is still empty before confirmation
        meds_pre = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds_pre) == 0

        # Turn 3: Malayalam affirmative confirmation ("അതെ")
        res3 = await orchestrator.process_request("അതെ", uid, db, language="ml")
        assert "പാരാസിറ്റമോൾ" in res3
        assert "ചേർത്തു" in res3

        # Verify record in DB
        meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds) == 1
        assert meds[0].medicine_name == "പാരാസിറ്റമോൾ"

        # Test Malayalam cancellation flow
        conversation_manager.clear_session(uid)
        await orchestrator.process_request("എന്റെ മരുന്ന് രാത്രി 9 മണിക്കാണ്", uid, db, language="ml")
        await orchestrator.process_request("ക്രോസിൻ", uid, db, language="ml")
        res_cancel = await orchestrator.process_request("വേണ്ട", uid, db, language="ml")
        assert "ഒഴിവാക്കിയിട്ടുണ്ട്" in res_cancel

        # Verify no second record was created
        meds_post = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).all()
        assert len(meds_post) == 1
    finally:
        db.close()


@pytest.mark.asyncio
async def test_10_no_duplicate_medicine_reminder_if_confirmation_repeated():
    """
    Test 10: No duplicate medicine/reminder is created if the confirmation is repeated.
    """
    db = SessionLocal()
    uid = "test_med_elder_1"
    try:
        # Creation flow
        await orchestrator.process_request("My medicine is at 8 PM.", uid, db, language="en")
        await orchestrator.process_request("DuplicateTestMed", uid, db, language="en")
        res_conf1 = await orchestrator.process_request("yes", uid, db, language="en")
        assert "I have added DuplicateTestMed" in res_conf1

        count_1 = db.query(MedicineReminder).filter(
            MedicineReminder.medicine_name == "DuplicateTestMed",
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).count()
        assert count_1 == 1

        # User says "yes" again in next turn (confirmation repeated)
        res_conf2 = await orchestrator.process_request("yes", uid, db, language="en")
        # Should be handled as pure conversational acknowledgment, not another creation
        assert "DuplicateTestMed" not in res_conf2

        count_2 = db.query(MedicineReminder).filter(
            MedicineReminder.medicine_name == "DuplicateTestMed",
            (MedicineReminder.elder_id == uid) | (MedicineReminder.subject_id == uid)
        ).count()
        assert count_2 == 1, "Duplicate MedicineReminder was created upon repeated confirmation!"
    finally:
        db.close()
