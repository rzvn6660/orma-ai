from sqlalchemy import Column, String, DateTime
from datetime import datetime

class IdentityMixin:
    """
    Universal Actor-Subject Identity Framework (ASIF) Mixin.
    Every action-based entity inherits this.
    """
    actor_id = Column(String, index=True, nullable=True)     # Who performed the action
    subject_id = Column(String, index=True, nullable=True)   # Who the action is about
    created_by = Column(String, nullable=True)               # Original creator
    owned_by = Column(String, index=True, nullable=True)     # The primary owner
    role = Column(String, nullable=True)                     # Role of the actor
    permission_scope = Column(String, nullable=True)         # Scope used for creation
    organization_id = Column(String, index=True, nullable=True) # Future-ready
    session_id = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
