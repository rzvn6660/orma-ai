from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from datetime import datetime
import uuid
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # 'elderly' or 'caregiver'
    name = Column(String)
    timezone = Column(String, default="UTC")
    timezone_offset = Column(String, nullable=True)
    country = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CaregiverRelationship(Base):
    __tablename__ = "caregiver_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(String, ForeignKey("users.id"))
    caregiver_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="pending") # pending, approved, revoked
    connected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConnectionCode(Base):
    __tablename__ = "connection_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    elder_id = Column(String, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)

class RateLimit(Base):
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    action = Column(String)
    attempts = Column(Integer, default=0)
    window_start = Column(DateTime, default=datetime.utcnow)
