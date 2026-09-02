"""
ORMA AI — Controlled QA Test User Provisioning Script

Purpose:
  Safely provisions a single verified QA/test user in the configured database
  (SQLite local or Supabase PostgreSQL) without bypassing, weakening, or
  modifying the production signup, OTP, or email verification flows.

Security Invariants:
  1. Credentials must NEVER be hardcoded into source code or Git.
  2. Reads credentials exclusively from environment variables:
     - ORMA_TEST_EMAIL
     - ORMA_TEST_PASSWORD
  3. Uses production bcrypt password hashing (auth_service.get_password_hash).
  4. Never prints passwords, connection strings, or sensitive API keys.
  5. Idempotent: Refuses to overwrite existing accounts or modify existing user data.
  6. Records an audit trail log in the audit_logs table.
"""

import os
import sys
import logging

# Ensure backend root is on Python sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal
from models.user import User, AuditLog
from services.auth_service import get_password_hash
from services.notification_preference_service import get_user_notification_preferences

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_test_user")

def seed_qa_test_user() -> bool:
    """
    Provisions a verified QA test user using environment variables.
    Returns True if user was created, False if user already exists or configuration is missing.
    """
    test_email = (os.getenv("ORMA_TEST_EMAIL") or "").strip().lower()
    test_password = os.getenv("ORMA_TEST_PASSWORD") or ""

    if not test_email or not test_password:
        logger.error(
            "Missing required environment variables. "
            "Both ORMA_TEST_EMAIL and ORMA_TEST_PASSWORD must be set."
        )
        return False

    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            logger.warning(
                f"Account with email '{test_email}' already exists (ID: {existing_user.id}). "
                "Skipping creation to avoid overwriting existing user data."
            )
            return False

        # Hash password with production bcrypt
        hashed_pw = get_password_hash(test_password)

        new_user = User(
            email=test_email,
            hashed_password=hashed_pw,
            role="elderly",
            name="ORMA QA Test Account",
            timezone="UTC",
            token_version=1,
            email_verified=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Seed default notification preferences
        get_user_notification_preferences(db, new_user)

        # Record audit log
        audit_entry = AuditLog(
            user_id=new_user.id,
            action="qa_seed_user",
            resource="user",
            outcome="success",
            details="Controlled QA test account provisioned via seed script"
        )
        db.add(audit_entry)
        db.commit()

        logger.info(
            f"Successfully provisioned verified QA test account: '{test_email}' "
            f"(User ID: {new_user.id}, Role: {new_user.role}, Verified: {new_user.email_verified})"
        )
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed QA test user: {type(e).__name__}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    success = seed_qa_test_user()
    sys.exit(0 if success else 1)
