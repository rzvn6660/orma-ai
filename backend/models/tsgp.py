import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from database import Base
from .identity_mixin import IdentityMixin

class TSGPAuditLog(Base, IdentityMixin):
    """
    Immutable audit trail for all sensitive requests evaluated by the Governance Platform.
    """
    __tablename__ = "tsgp_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    
    intent = Column(String(100))
    request_text = Column(Text, nullable=True)
    
    risk_score = Column(String(50)) # Low, Medium, High, Critical
    action_taken = Column(String(50)) # allowed, blocked, escalated, clarification_required
    
    policies_applied = Column(JSON, default=list) # Which rules were checked
    explainability = Column(Text) # Why it was allowed or blocked
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PolicyConfiguration(Base):
    """
    Configurable healthcare safety policies. Avoids hardcoded values.
    """
    __tablename__ = "tsgp_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    severity_level = Column(String(50), default="High") # If violated, what is the risk?
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
