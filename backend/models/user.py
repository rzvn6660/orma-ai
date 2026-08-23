from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from datetime import datetime
import uuid
from database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # 'elderly' or 'caregiver'
    name = Column(String)
    timezone = Column(String, default="UTC")
    timezone_offset = Column(String, nullable=True)
    country = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    token_version = Column(Integer, default=1)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class CaregiverRelationship(Base):
    __tablename__ = "caregiver_relationships"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(String, ForeignKey("users.id"))
    caregiver_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="pending") # pending, approved, revoked
    connected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConnectionCode(Base):
    __tablename__ = "connection_codes"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    elder_id = Column(String, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)

class RateLimit(Base):
    __tablename__ = "rate_limits"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    action = Column(String)
    attempts = Column(Integer, default=0)
    window_start = Column(DateTime, default=datetime.utcnow)

class PasswordResetToken(Base):
    """Stores hashed, single-use, time-limited password reset tokens."""
    __tablename__ = "password_reset_tokens"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    token_hash = Column(String, unique=True, index=True)  # sha256 hex of the raw token
    expires_at = Column(DateTime)                          # 30 minutes from creation
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class NotificationPreferences(Base):
    """Stores role-aware notification, alert and language preferences per user."""
    __tablename__ = "notification_preferences"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, index=True)
    medication_reminder_notifications = Column(Boolean, default=True)
    medication_spoken_alerts = Column(Boolean, default=True)
    missed_medication_alerts = Column(Boolean, default=True)
    medication_adherence_summary = Column(Boolean, default=True)
    reminder_language = Column(String, default="en-IN")
    voice_language = Column(String, default="auto")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailVerificationOTP(Base):
    """Stores hashed, single-use, 10-minute email verification OTPs."""
    __tablename__ = "email_verification_otps"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    email = Column(String, index=True)
    otp_hash = Column(String, index=True)  # sha256 hex of the 6-digit numeric OTP
    expires_at = Column(DateTime)          # 10 minutes from creation
    attempts = Column(Integer, default=0)  # Max 5 attempts
    max_attempts = Column(Integer, default=5)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    last_sent_at = Column(DateTime, default=datetime.utcnow)
