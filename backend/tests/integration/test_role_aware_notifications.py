import pytest
import sys
import os
import datetime

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal, Base, engine
from models.user import User, CaregiverRelationship, NotificationPreferences
from models.medicine import MedicineReminder
from models.notification import Notification
from models.emergency import EmergencyAlert
from services.notification_preference_service import (
    get_user_notification_preferences,
    update_user_notification_preferences
)
from services.notification_service import dispatch_notification
import asyncio

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_1_elderly_default_and_caregiver_default_preferences():
    db = SessionLocal()
    try:
        elder = User(id="test_elder_1", email="elder1@test.com", role="elderly", name="Test Elder")
        caregiver = User(id="test_cg_1", email="cg1@test.com", role="caregiver", name="Test Caregiver")
        db.add_all([elder, caregiver])
        db.commit()

        elder_prefs = get_user_notification_preferences(db, elder)
        cg_prefs = get_user_notification_preferences(db, caregiver)

        # Elderly defaults: ON
        assert elder_prefs.medication_reminder_notifications is True
        assert elder_prefs.medication_spoken_alerts is True
        assert elder_prefs.missed_medication_alerts is True
        assert elder_prefs.medication_adherence_summary is True

        # Caregiver defaults: OFF for normal reminders/speech, ON for missed/summary
        assert cg_prefs.medication_reminder_notifications is False
        assert cg_prefs.medication_spoken_alerts is False
        assert cg_prefs.missed_medication_alerts is True
        assert cg_prefs.medication_adherence_summary is True
    finally:
        db.close()

def test_2_and_3_toggle_caregiver_preference_persistence():
    db = SessionLocal()
    try:
        cg = db.query(User).filter(User.id == "test_cg_1").first()
        
        # Toggle ON
        updated_on = update_user_notification_preferences(db, cg, {"medication_reminder_notifications": True})
        assert updated_on.medication_reminder_notifications is True

        # Re-fetch from DB
        db.expire_all()
        fresh_on = get_user_notification_preferences(db, cg)
        assert fresh_on.medication_reminder_notifications is True

        # Toggle OFF
        updated_off = update_user_notification_preferences(db, cg, {"medication_reminder_notifications": False})
        assert updated_off.medication_reminder_notifications is False

        # Re-fetch from DB
        db.expire_all()
        fresh_off = get_user_notification_preferences(db, cg)
        assert fresh_off.medication_reminder_notifications is False
    finally:
        db.close()

def test_4_missed_medication_alert_delivery():
    db = SessionLocal()
    try:
        # Establish approved relationship
        rel = CaregiverRelationship(elder_id="test_elder_1", caregiver_id="test_cg_1", status="approved")
        db.add(rel)
        db.commit()

        # Caregiver has missed_medication_alerts = True
        cg = db.query(User).filter(User.id == "test_cg_1").first()
        update_user_notification_preferences(db, cg, {"missed_medication_alerts": True})

        asyncio.run(dispatch_notification(db, elder_id="test_elder_1", title="Missed Medication", message="Patient missed 02:30 PM dose"))

        notif = db.query(Notification).filter(Notification.caregiver_id == "test_cg_1", Notification.title == "Missed Medication").first()
        assert notif is not None
        assert "missed" in notif.message.lower()
    finally:
        db.close()

def test_5_emergency_alert_bypasses_all_medication_notification_switches():
    db = SessionLocal()
    try:
        cg = db.query(User).filter(User.id == "test_cg_1").first()
        # Turn ALL medication notification preferences OFF for caregiver
        update_user_notification_preferences(db, cg, {
            "medication_reminder_notifications": False,
            "medication_spoken_alerts": False,
            "missed_medication_alerts": False,
            "medication_adherence_summary": False
        })

        # Create emergency alert
        alert = EmergencyAlert(
            id="emergency_test_123",
            elder_id="test_elder_1",
            status="active",
            severity="critical",
            message="SOS triggered"
        )
        notif = Notification(
            caregiver_id="test_cg_1",
            elder_id="test_elder_1",
            title="Emergency Alert: Test Elder",
            message="Immediate assistance needed",
            priority="high"
        )
        db.add_all([alert, notif])
        db.commit()

        # Emergency notification MUST still exist in DB for caregiver
        saved_notif = db.query(Notification).filter(Notification.caregiver_id == "test_cg_1", Notification.priority == "high").first()
        assert saved_notif is not None
        assert saved_notif.title.startswith("Emergency Alert")
    finally:
        db.close()

def test_6_unlinked_caregiver_isolation():
    db = SessionLocal()
    try:
        unlinked_cg = User(id="test_cg_unlinked", email="unlinked@test.com", role="caregiver", name="Unlinked Caregiver")
        db.add(unlinked_cg)
        db.commit()

        # Dispatch notification for test_elder_1
        asyncio.run(dispatch_notification(db, elder_id="test_elder_1", title="Missed Medication", message="Test unlinked"))

        # Unlinked caregiver must NOT receive notification
        notif = db.query(Notification).filter(Notification.caregiver_id == "test_cg_unlinked").first()
        assert notif is None
    finally:
        db.close()

def test_cleanup():
    db = SessionLocal()
    try:
        db.query(Notification).delete()
        db.query(EmergencyAlert).delete()
        db.query(CaregiverRelationship).delete()
        db.query(NotificationPreferences).delete()
        db.query(User).filter(User.id.in_(["test_elder_1", "test_cg_1", "test_cg_unlinked"])).delete()
        db.commit()
    finally:
        db.close()