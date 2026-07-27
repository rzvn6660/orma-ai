from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from database import Base
from .identity_mixin import IdentityMixin

class WellnessLog(Base, IdentityMixin):
    __tablename__ = "wellness_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    text = Column(String)
    emotion = Column(String) # sadness, stress, anxiety, loneliness, calmness
    confusion_flag = Column(Boolean, default=False)
    repeated_question = Column(Boolean, default=False)
    intent_category = Column(String)
