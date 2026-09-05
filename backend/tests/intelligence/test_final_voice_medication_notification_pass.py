import pytest
import os
import sys
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import Base, engine, get_db
from models.user import User
from models.medicine import MedicineReminder
from models.notification import Notification
from services import medicine_service
from services.notification_service import dispatch_notification
from intelligence.conversational_reference_resolver import ConversationalReferenceResolver
from intelligence.orchestrator import IntelligenceOrchestrator, orchestrator
from intelligence.response_coordinator import response_coordinator

@pytest.fixture
def db():
    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def test_user(db):
    user_id = f"test_user_final_{datetime.utcnow().timestamp()}"
    user = User(
        id=user_id,
        email=f"{user_id}@example.com",
        name="Test Patient",
        role="elder"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def _create_med(db, user_id, name, time_str="09:00", frequency="daily", taken=False):
    med = MedicineReminder(
        subject_id=user_id,
        owned_by=user_id,
        elder_id=user_id,
        medicine_name=name,
        dosage="1 tab",
        reminder_time=time_str,
        frequency=frequency,
        taken_status=taken
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return med

# ==============================================================================
# MEDICATION ACTION REGRESSION TESTS (Task 2 & Task 3)
# ==============================================================================

def test_explicit_taken_confirmation_it(db, test_user):
    """
    User says 'I already took it' after discussing Test Medicine.
    Must mark Test Medicine as taken for today and verify authoritative status.
    """
    med = _create_med(db, test_user.id, "Metformin", "09:00", frequency="daily")

    resolver = ConversationalReferenceResolver()
    history = [
        {"role": "assistant", "content": "Your next medicine is Metformin scheduled for 09:00 AM."}
    ]

    result = resolver.resolve("I already took it", test_user.id, db, history)

    assert result is not None
    reply = result.get("direct_response") or result.get("response") or ""
    assert "marked Metformin as taken for today" in reply

    # Verify authoritative database record
    db.refresh(med)
    assert med.taken_at is not None
    assert med.taken_at.date() == date.today()

def test_taken_confirmation_that_medicine(db, test_user):
    """User says 'I took that medicine'."""
    med = _create_med(db, test_user.id, "Aspirin", "14:00", frequency="daily")

    resolver = ConversationalReferenceResolver()
    history = [
        {"role": "assistant", "content": "You have Aspirin scheduled for 02:00 PM."}
    ]

    result = resolver.resolve("I took that medicine", test_user.id, db, history)
    assert result is not None
    reply = result.get("direct_response") or result.get("response") or ""
    assert "marked Aspirin as taken for today" in reply

    db.refresh(med)
    assert med.taken_status is True

def test_malayalam_taken_confirmation(db, test_user):
    """User confirms in Malayalam 'ഞാൻ അത് കഴിച്ചു'."""
    med = _create_med(db, test_user.id, "Paracetamol", "12:00", frequency="daily")

    resolver = ConversationalReferenceResolver()
    history = [
        {"role": "assistant", "content": "അടുത്ത മരുന്ന് Paracetamol ആണ്."}
    ]

    result = resolver.resolve("ഞാൻ അത് കഴിച്ചു", test_user.id, db, history)
    assert result is not None
    reply = result.get("direct_response") or result.get("response") or ""
    assert "Paracetamol" in reply
    assert "കഴിച്ചതായി" in reply

    db.refresh(med)
    assert med.taken_status is True

def test_manglish_taken_confirmation(db, test_user):
    """User confirms in Manglish 'marunnu kazhichu'."""
    med = _create_med(db, test_user.id, "Atorvastatin", "20:00", frequency="daily")

    resolver = ConversationalReferenceResolver()
    history = [
        {"role": "assistant", "content": "Your next medicine is Atorvastatin at 8:00 PM."}
    ]

    result = resolver.resolve("njan marunnu kazhichu", test_user.id, db, history)
    assert result is not None
    reply = result.get("direct_response") or result.get("response") or ""
    assert "marked Atorvastatin as taken" in reply

    db.refresh(med)
    assert med.taken_status is True

def test_did_i_take_it_status_inquiry_authoritative(db, test_user):
    """'Did I take it?' must query authoritative live DB status."""
    med = _create_med(db, test_user.id, "Thyroxine", "07:00", frequency="daily")

    resolver = ConversationalReferenceResolver()
    history = [
        {"role": "assistant", "content": "Thyroxine is scheduled for 7:00 AM."}
    ]

    # When pending:
    res_pending = resolver.resolve("Did I take it?", test_user.id, db, history)
    assert res_pending is not None
    reply_pending = res_pending.get("direct_response") or res_pending.get("response") or ""
    assert "Thyroxine" in reply_pending
    assert "haven't marked" in reply_pending or "pending" in reply_pending.lower()

    # Now mark it as taken:
    medicine_service.mark_taken(db, reminder_id=med.id, subject_id=test_user.id)
    db.refresh(med)

    # When taken:
    res_taken = resolver.resolve("Did I take that medicine?", test_user.id, db, history)
    assert res_taken is not None
    reply_taken = res_taken.get("direct_response") or res_taken.get("response") or ""
    assert "Yes" in reply_taken
    assert "is marked as taken for today" in reply_taken

def test_ambiguous_multiple_medicines_asks_clarification(db, test_user):
    """If multiple medicines are pending and context is ambiguous, do NOT mark taken; ask clarification."""
    _create_med(db, test_user.id, "Med A", "10:00")
    _create_med(db, test_user.id, "Med B", "10:00")

    resolver = ConversationalReferenceResolver()
    # Empty history: which medicine does 'it' refer to?
    result = resolver.resolve("I already took it", test_user.id, db, [])
    assert result is not None
    reply = result.get("direct_response") or result.get("response") or ""
    assert "Which" in reply or "Med A" in reply or "Med B" in reply
    assert result.get("action") is None  # Must NOT mark anything taken!

def test_question_does_not_mark_taken(db, test_user):
    """Asking 'When should I take it?' must NOT mark the medication taken."""
    med = _create_med(db, test_user.id, "Vitamins", "11:00")

    resolver = ConversationalReferenceResolver()
    history = [{"role": "assistant", "content": "Your next medicine is Vitamins."}]

    result = resolver.resolve("When should I take that medicine?", test_user.id, db, history)
    if result and result.get("is_followup"):
        reply = result.get("direct_response") or result.get("response") or ""
        assert "marked" not in reply or "as taken" not in reply

    db.refresh(med)
    assert med.taken_status is False

def test_already_taken_medicine_confirmation(db, test_user):
    """If already taken for today, state that it's already marked taken."""
    med = _create_med(db, test_user.id, "Calcitriol", "08:00")
    medicine_service.mark_taken(db, reminder_id=med.id, subject_id=test_user.id)
    db.refresh(med)

    resolver = ConversationalReferenceResolver()
    history = [{"role": "assistant", "content": "Calcitriol was scheduled for 8:00 AM."}]

    result = resolver.resolve("I already took Calcitriol", test_user.id, db, history)
    assert result is not None
    reply = result.get("direct_response") or result.get("response") or ""
    assert "already marked as taken for today" in reply

def test_recurring_medicine_today_vs_tomorrow(db, test_user):
    """If the medicine discussed is for tomorrow, do not mark it taken today."""
    med = _create_med(db, test_user.id, "Insulin", "07:00", frequency="daily")

    resolver = ConversationalReferenceResolver()
    history = [
        {"role": "assistant", "content": "You have Insulin scheduled for tomorrow at 07:00 AM."}
    ]

    # When context has tomorrow's medicine
    with patch.object(resolver, "_extract_referenced_medications", return_value=[{
        "id": med.id, "name": "Insulin", "scheduled_time": "07:00 AM", "day": "tomorrow"
    }]):
        result = resolver.resolve("I already took that medicine", test_user.id, db, history)
        assert result is not None
        reply = result.get("direct_response") or result.get("response") or ""
        assert "scheduled for tomorrow" in reply

        db.refresh(med)
        assert med.taken_status is False

def test_authoritative_action_failure(db, test_user):
    """If authoritative mark_taken action fails or cannot be verified, do NOT claim marked taken."""
    med = _create_med(db, test_user.id, "Lisinopril", "10:00")

    resolver = ConversationalReferenceResolver()
    history = [{"role": "assistant", "content": "Your medicine is Lisinopril."}]

    with patch("services.medicine_service.mark_taken", return_value=None), \
         patch("intelligence.conversational_reference_resolver.resolve_medication_daily_status", return_value=False):
        result = resolver.resolve("I already took it", test_user.id, db, history)
        assert result is not None
        reply = result.get("direct_response") or result.get("response") or ""
        assert "unable to update" in reply or "Please try again" in reply
        assert "marked Lisinopril as taken for today" not in reply

def test_successful_action_followed_by_authoritative_verification(db, test_user):
    """After mark_taken succeeds, live DB verification confirms it before confirming to user."""
    med = _create_med(db, test_user.id, "Omega3", "13:00")

    resolver = ConversationalReferenceResolver()
    history = [{"role": "assistant", "content": "Your next medicine is Omega3 at 1:00 PM."}]

    result = resolver.resolve("Yes, I already took that", test_user.id, db, history)
    assert result is not None
    reply = result.get("direct_response") or ""
    assert "marked Omega3 as taken for today" in reply

    db.refresh(med)
    assert med.taken_status is True
    assert med.taken_at is not None

# ==============================================================================
# NOTIFICATION DEDUPLICATION & SUPPRESSION TESTS (Task 4 & Task 5)
# ==============================================================================

@pytest.mark.asyncio
async def test_same_occurrence_duplicate(db, test_user):
    """Same medication + same scheduled occurrence + same date: exactly ONE notification."""
    title = "Missed Medication: Test Med 1"
    msg = "Medication Test Med 1 scheduled for 09:00 AM was marked as missed."

    await dispatch_notification(db=db, elder_id=test_user.id, title=title, message=msg, priority="high")
    count1 = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title).count()
    assert count1 == 1

    # Repeat dispatch (e.g. from polling, reconnect, re-render)
    await dispatch_notification(db=db, elder_id=test_user.id, title=title, message=msg, priority="high")
    count2 = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title).count()
    assert count2 == 1

@pytest.mark.asyncio
async def test_same_medicine_two_times_same_day(db, test_user):
    """Same medication + DIFFERENT scheduled occurrence on SAME date: TWO separate notifications."""
    title = "Missed Medication: Test Med 1"
    msg_morning = "Medication Test Med 1 scheduled for 09:00 AM was marked as missed."
    msg_evening = "Medication Test Med 1 scheduled for 08:00 PM was marked as missed."

    # 09:00 AM occurrence missed
    await dispatch_notification(db=db, elder_id=test_user.id, title=title, message=msg_morning, priority="high")
    
    # 08:00 PM occurrence missed on the same day
    await dispatch_notification(db=db, elder_id=test_user.id, title=title, message=msg_evening, priority="high")

    all_notifs = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title).all()
    assert len(all_notifs) == 2
    messages = {n.message for n in all_notifs}
    assert msg_morning in messages
    assert msg_evening in messages

@pytest.mark.asyncio
async def test_same_medicine_different_day(db, test_user):
    """Same recurring medication + same occurrence on a NEW DATE: new notification."""
    title = "Missed Medication: Recurring Med"
    msg = "Medication Recurring Med scheduled for 09:00 AM was marked as missed."

    # Create yesterday's missed occurrence
    yesterday = datetime.utcnow() - timedelta(days=1)
    yesterday_notif = Notification(
        elder_id=test_user.id,
        subject_id=test_user.id,
        title=title,
        message=msg,
        priority="high",
        is_read=True,
        created_at=yesterday
    )
    db.add(yesterday_notif)
    db.commit()

    # Dispatch today's missed occurrence
    await dispatch_notification(db=db, elder_id=test_user.id, title=title, message=msg, priority="high")

    all_notifs = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title).all()
    assert len(all_notifs) == 2

    # Today's notification is new and unread
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_notif = db.query(Notification).filter(
        Notification.elder_id == test_user.id,
        Notification.title == title,
        Notification.created_at >= today_start
    ).first()
    assert today_notif is not None
    assert today_notif.is_read is False

@pytest.mark.asyncio
async def test_different_medicine_same_day(db, test_user):
    """Different medication + same date: separate notifications."""
    title_a = "Missed Medication: Med A"
    msg_a = "Medication Med A scheduled for 10:00 AM was marked as missed."
    title_b = "Missed Medication: Med B"
    msg_b = "Medication Med B scheduled for 10:00 AM was marked as missed."

    await dispatch_notification(db=db, elder_id=test_user.id, title=title_a, message=msg_a, priority="high")
    await dispatch_notification(db=db, elder_id=test_user.id, title=title_b, message=msg_b, priority="high")

    count_a = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title_a).count()
    count_b = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title_b).count()
    assert count_a == 1
    assert count_b == 1

@pytest.mark.asyncio
async def test_read_notification_duplicate_suppression(db, test_user):
    """Read notification duplicate suppression: read status strictly preserved and no duplicate created."""
    title = "Missed Medication: ReadTest"
    msg = "Medication ReadTest scheduled for 12:00 PM was marked as missed."

    await dispatch_notification(db=db, elder_id=test_user.id, title=title, message=msg, priority="high")

    notif = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title).first()
    assert notif is not None
    assert notif.is_read is False

    # User reads notification:
    notif.is_read = True
    db.commit()

    # Re-dispatch / poll:
    await dispatch_notification(db=db, elder_id=test_user.id, title=title, message=msg, priority="high")

    db.refresh(notif)
    assert notif.is_read is True  # MUST REMAIN TRUE!

    # Exactly one record in DB:
    total_count = db.query(Notification).filter(Notification.elder_id == test_user.id, Notification.title == title).count()
    assert total_count == 1


# ==============================================================================
# LANGUAGE PROPAGATION & NO CROSS-TURN LEAKAGE TESTS (Task 1)
# ==============================================================================

@pytest.mark.asyncio
async def test_malayalam_response_language_propagation_and_no_leakage(db, test_user):
    """
    User speaks Malayalam: 'എന്റെ അടുത്ത മരുന്ന് എന്താണ്?'.
    Response language must be 'ml'.
    Crucially, if the previous turn in history was Tamil or English,
    the current turn must NOT inherit Tamil or English.
    """
    from intelligence.conversation_manager import conversation_manager
    conversation_manager.add_message(test_user.id, "user", "வணக்கம், என் மருந்து என்ன?")
    conversation_manager.add_message(test_user.id, "assistant", "உங்கள் அடுத்த மருந்து Metformin.")

    # 1. Next medicine question in Malayalam (resolved via Phase A reference resolver)
    result = await orchestrator.process_request_detailed(
        text="എന്റെ അടുത്ത മരുന്ന് എന്താണ്?",
        user_id=test_user.id,
        db=db,
        language="auto"
    )
    assert result["language"] == "ml"

    # 2. General utterance in Malayalam (goes through response coordinator)
    with patch.object(response_coordinator, "generate_response_with_meta", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ("നമസ്കാരം! എനിക്ക് സുഖമാണ്.", {"llm_called": True})

        res2 = await orchestrator.process_request_detailed(
            text="നമസ്കാരം, സുഖമാണോ?",
            user_id=test_user.id,
            db=db,
            language="auto"
        )
        assert res2["language"] == "ml"
        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs["language"] == "ml"  # Orchestrator passed ml to response generator!

@pytest.mark.asyncio
async def test_language_detection_auto_for_all_languages(db, test_user):
    """
    English -> en
    Tamil -> ta
    Hindi -> hi
    Malayalam -> ml
    """
    with patch.object(response_coordinator, "generate_response_with_meta", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ("ok", {"llm_called": True})

        # 1. English
        r_en = await orchestrator.process_request_detailed(
            text="What is my next medicine?",
            user_id=test_user.id,
            db=db,
            language="auto"
        )
        assert r_en["language"] == "en"

        # 2. Malayalam script
        r_ml = await orchestrator.process_request_detailed(
            text="എന്റെ അടുത്ത മരുന്ന് ഏതാണ്?",
            user_id=test_user.id,
            db=db,
            language="auto"
        )
        assert r_ml["language"] == "ml"

        # 3. Tamil script
        r_ta = await orchestrator.process_request_detailed(
            text="என் அடுத்த மருந்து எது?",
            user_id=test_user.id,
            db=db,
            language="auto"
        )
        assert r_ta["language"] == "ta"

        # 4. Hindi script
        r_hi = await orchestrator.process_request_detailed(
            text="मेरी अगली दवाई कौन सी है?",
            user_id=test_user.id,
            db=db,
            language="auto"
        )
        assert r_hi["language"] == "hi"
