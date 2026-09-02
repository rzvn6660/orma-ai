import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from database import Base
from pydantic import BaseModel
from typing import Optional

# SQLAlchemy DB Model
class OCMEMemory(Base):
    __tablename__ = "ocme_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    
    category = Column(String(50), index=True)
    title = Column(String(255))
    value = Column(String(1024))
    
    importance = Column(Integer, default=50)
    confidence = Column(Float, default=1.0)
    visibility = Column(String(50), default="private")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    verified = Column(Boolean, default=False)
    pinned = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    
    trust_score = Column(Float, default=50.0)
    source = Column(String(100), default="system")
    expires_at = Column(DateTime, nullable=True)

class OCMEAudit(Base):
    __tablename__ = "ocme_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, index=True) # Logical foreign key
    action = Column(String(50)) # created, updated, merged, pinned, shared, explained, deleted, archived
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    source = Column(String(50)) # AI, User, Caregiver
    details = Column(String(512), nullable=True)

# Pydantic Schemas
class OCMEMemoryCreate(BaseModel):
    category: str
    title: str
    value: str
    importance: int = 50
    confidence: float = 1.0
    visibility: str = "private"
    source: str = "system"
    trust_score: float = 50.0
    expires_at: Optional[datetime.datetime] = None

class OCMEMemoryResponse(OCMEMemoryCreate):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_used: Optional[datetime.datetime]
    usage_count: int
    verified: bool
    pinned: bool
    archived: bool
    trust_score: float

    class Config:
        from_attributes = True
