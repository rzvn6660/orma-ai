import os
import sys
import uuid
import pytest
from unittest.mock import patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal
from models.user import User, AuditLog, NotificationPreferences
from services.auth_service import verify_password
from scripts.seed_test_user import seed_qa_test_user

def test_seed_qa_user_missing_env_vars():
    """Fails safely if required environment variables are absent."""
    with patch.dict(os.environ, {"ORMA_TEST_EMAIL": "", "ORMA_TEST_PASSWORD": ""}):
        created = seed_qa_test_user()
        assert created is False

def test_seed_qa_user_success_and_idempotency():
    """Successfully provisions verified test account, then refuses to duplicate."""
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"qa_test_{unique_id}@orma.internal"
    test_password = "SecureTestPassword123!"

    db = SessionLocal()
    created_user_id = None
    try:
        with patch.dict(os.environ, {
            "ORMA_TEST_EMAIL": test_email,
            "ORMA_TEST_PASSWORD": test_password
        }):
            # 1. First run: user should be created
            success = seed_qa_test_user()
            assert success is True

            # Verify in DB
            user = db.query(User).filter(User.email == test_email).first()
            assert user is not None
            created_user_id = user.id
            assert user.email == test_email
            assert user.email_verified is True
            assert user.role == "elderly"
            assert user.name == "ORMA QA Test Account"
            assert user.token_version == 1
            assert verify_password(test_password, user.hashed_password) is True

            # Verify NotificationPreferences created
            prefs = db.query(NotificationPreferences).filter(NotificationPreferences.user_id == user.id).first()
            assert prefs is not None
            assert prefs.medication_reminder_notifications is True

            # Verify AuditLog created
            audit = db.query(AuditLog).filter(
                AuditLog.user_id == user.id,
                AuditLog.action == "qa_seed_user"
            ).first()
            assert audit is not None
            assert audit.outcome == "success"

            # 2. Second run: idempotency check, should return False and not duplicate
            success_again = seed_qa_test_user()
            assert success_again is False

            # Verify still only 1 user with this email
            user_count = db.query(User).filter(User.email == test_email).count()
            assert user_count == 1

    finally:
        # Clean up test user
        if created_user_id:
            db.query(AuditLog).filter(AuditLog.user_id == created_user_id).delete()
            db.query(NotificationPreferences).filter(NotificationPreferences.user_id == created_user_id).delete()
            db.query(User).filter(User.id == created_user_id).delete()
            db.commit()
        db.close()
