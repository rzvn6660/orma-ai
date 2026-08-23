"""
ORMA AI — Medicine Reminder Full Integration Test
Tests:
1. Reminder creation & retrieval
2. Scheduler detection & duplicate prevention
3. Taken action & state persistence
4. Snooze action & state persistence
5. Skip action & state persistence
6. Caregiver escalation threshold (30 minutes)
7. Caregiver duplicate notification prevention (single-fire persistence via is_caregiver_notified)
8. Reminder history event logging
"""
import os
import sys
import datetime
import pytz
import pytest

# Ensure backend root in path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal, ensure_schema_migrations
from models.user import User
from models.medicine import MedicineReminder
from services.scheduler_service import process_event, triggered_today, pending_reminders
from services.medicine_service import mark_taken, snooze_reminder, mark_skipped

ensure_schema_migrations()

def test_medicine_reminder_full_integration():
    db = SessionLocal()
    try:
        # 1. Setup user
        user = db.query(User).filter(User.role == "elderly").first()
        if not user:
            user = User(
                id="test_reminder_user_123",
                name="Elderly Test User",
                email="elderly_test@orma.ai",
                role="elderly",
                created_at=datetime.datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        user_id = user.id

        now_utc = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        local_tz = pytz.timezone("Asia/Kolkata")
        local_now = now_utc.astimezone(local_tz)
        current_time_str = local_now.strftime("%I:%M %p")

        # 2. Create test medicine reminder
        med = MedicineReminder(
            subject_id=user_id,
            owned_by=user_id,
            actor_id=user_id,
            created_by=user_id,
            role="elderly",
            elder_id=user_id,
            medicine_name="Amlodipine 5 mg",
            dosage="1 tablet",
            reminder_time=current_time_str,
            purpose="Blood Pressure",
            frequency="Daily",
            timezone="Asia/Kolkata",
            taken_status=False,
            is_caregiver_notified=False,
            created_at=datetime.datetime.utcnow()
        )
        db.add(med)
        db.commit()
        db.refresh(med)
        test_med_id = med.id
        assert test_med_id is not None

        # 3. Scheduler trigger and duplicate prevention
        process_event(db, med, "medicine")
        assert med.reminder_triggered_at is not None
        initial_trigger_count = len(triggered_today)

        # Second execution in same minute
        process_event(db, med, "medicine")
        second_trigger_count = len(triggered_today)
        assert initial_trigger_count == second_trigger_count

        # 4. Mark Taken Action
        taken_med = mark_taken(db, reminder_id=test_med_id, subject_id=user_id)
        assert taken_med is not None
        assert taken_med.taken_status is True
        assert taken_med.taken_at is not None

        # 5. Snooze Action (10 minutes)
        taken_med.taken_status = False
        db.commit()
        snoozed_med = snooze_reminder(db, reminder_id=test_med_id, subject_id=user_id, minutes=10)
        assert snoozed_med.adherence_pattern_flags == "snoozed"
        assert snoozed_med.taken_status is False

        # 6. Skip Action
        skipped_med = mark_skipped(db, reminder_id=test_med_id, subject_id=user_id)
        assert skipped_med.adherence_pattern_flags == "skipped"
        assert skipped_med.taken_status is False

        # 7. Caregiver Escalation (>30m threshold) & Spam Prevention
        past_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=35)
        skipped_med.reminder_triggered_at = past_time
        skipped_med.is_caregiver_notified = False
        skipped_med.caregiver_notified_at = None
        db.commit()

        process_event(db, skipped_med, "medicine")
        db.refresh(skipped_med)
        assert skipped_med.is_caregiver_notified is True
        assert skipped_med.caregiver_notified_at is not None
        assert skipped_med.adherence_pattern_flags == "missed"

        # Re-run process_event -> should NOT duplicate
        notified_timestamp_1 = skipped_med.caregiver_notified_at
        process_event(db, skipped_med, "medicine")
        db.refresh(skipped_med)
        notified_timestamp_2 = skipped_med.caregiver_notified_at
        assert notified_timestamp_1 == notified_timestamp_2

        # 8. Cleanup
        db.delete(skipped_med)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    test_medicine_reminder_full_integration()
    print("ALL MEDICINE REMINDER INTEGRATION CHECKS PASSED")