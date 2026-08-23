from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from .identity_mixin import IdentityMixin

class AuditLog(Base, IdentityMixin):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String) # e.g. 'read', 'create', 'delete'
    resource = Column(String) # e.g. 'memory', 'health_record'
    outcome = Column(String) # e.g. 'success', 'denied'
    reason = Column(String, nullable=True) # e.g. 'insufficient_permissions'
