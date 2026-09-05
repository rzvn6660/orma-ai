import os
import sys
import datetime
import pytest
from unittest.mock import patch, MagicMock

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal, Base, engine
from models.user import User, CaregiverRelationship
from models.medicine import MedicineReminder
from models.notification import Notification
from routes.medicine import miss_medicine
from routes.notifications import get_notifications, mark_notification_read

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    try:
        db.query(Notification).filter(Notification.elder_id == "missed_test_elder").delete()
        db.query(MedicineReminder).filter(MedicineReminder.subject_id == "missed_test_elder").delete()
        db.query(User).filter(User.id == "missed_test_elder").delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(Notification).filter(Notification.elder_id == "missed_test_elder").delete()
        db.query(MedicineReminder).filter(MedicineReminder.subject_id == "missed_test_elder").delete()
        db.query(User).filter(User.id == "missed_test_elder").delete()
        db.commit()
    finally:
        db.close()

@pytest.mark.asyncio
async def test_missed_medicine_creates_notification_and_deduplicates():
    db = SessionLocal()
    try:
        elder = User(id="missed_test_elder", email="elder_missed@test.com", role="elderly", name="Elder Missed")
        db.add(elder)
        db.commit()

        reminder = MedicineReminder(
            id=9901,
            elder_id="missed_test_elder",
            subject_id="missed_test_elder",
            medicine_name="Metformin 500mg",
            dosage="1 tablet",
            reminder_time="08:00 AM",
            taken_status=False,
            created_at=datetime.datetime.utcnow()
        )
        db.add(reminder)
        db.commit()

        ctx = {
            "authenticated_user": elder,
            "resolved_subject": {"id": "missed_test_elder", "name": "Elder Missed", "role": "elderly"}
        }

        # 1. Mark medicine as missed
        await miss_medicine(id=9901, db=db, ctx=ctx)

        # 2. Check notification in DB
        notifs = get_notifications(current_user=elder, db=db)
        assert len(notifs) == 1
        missed_notif = notifs[0]
        assert "Metformin 500mg" in missed_notif["title"]
        assert missed_notif["is_read"] is False
        assert missed_notif["priority"] == "high"

        # 3. Mark as read
        read_res = mark_notification_read(notification_id=missed_notif["id"], current_user=elder, db=db)
        assert read_res["status"] == "success"

        updated_notifs = get_notifications(current_user=elder, db=db)
        assert updated_notifs[0]["is_read"] is True

        # 4. Duplicate event / retry: Calling miss_medicine again must NOT create a duplicate notification
        await miss_medicine(id=9901, db=db, ctx=ctx)
        dedup_notifs = get_notifications(current_user=elder, db=db)
        assert len(dedup_notifs) == 1, "Duplicate notification must be prevented by deduplication window"

    finally:
        db.close()
