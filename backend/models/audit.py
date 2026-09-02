from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from .identity_mixin import IdentityMixin

class AuditLog(Base, IdentityMixin):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    action = Column(String) # e.g. 'read', 'create', 'delete', 'signup', 'login'
    resource = Column(String, nullable=True) # e.g. 'memory', 'health_record', 'auth'
    outcome = Column(String, nullable=True) # e.g. 'success', 'denied'
    reason = Column(String, nullable=True) # e.g. 'insufficient_permissions'
    details = Column(String, nullable=True)
