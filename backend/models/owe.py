import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from database import Base
from .identity_mixin import IdentityMixin

class WorkflowAuditLog(Base, IdentityMixin):
    """
    Records workflow executions, steps, failures, and completions.
    """
    __tablename__ = "owe_workflow_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), index=True) # E.g., 'medicine_creation_flow'
    idempotency_key = Column(String(100), index=True, unique=True, nullable=True)
    
    status = Column(String(50), default="started") # started, completed, failed, pending_approval
    actor = Column(String(50), default="system") # AI, User, Caregiver
    
    steps_executed = Column(JSON, default=list)
    failures = Column(JSON, default=list)
    retries = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ApprovalRequest(Base, IdentityMixin):
    """
    Actions requiring confirmation before execution.
    """
    __tablename__ = "owe_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    workflow_log_id = Column(Integer)
    
    action_type = Column(String(100)) # e.g., 'reschedule_appointment', 'delete_memory'
    payload = Column(JSON)
    
    status = Column(String(50), default="pending") # pending, approved, rejected
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
