from typing import Any, Dict
from sqlalchemy.orm import Session
from database import SessionLocal
from models.medicine import MedicineReminder
from .retriever_base import BaseRetriever

class MedicationRetriever(BaseRetriever):
    """Retrieves medication data for the user."""
    
    def retrieve(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = query_context.get("user_id")
        
        db: Session = SessionLocal()
        try:
            query = db.query(MedicineReminder)
            if user_id:
                query = query.filter(MedicineReminder.subject_id == user_id)
                
            all_reminders = query.all()
            
            pending = []
            taken = []
            
            for r in all_reminders:
                med_dict = {
                    "id": r.id,
                    "medicine_name": r.medicine_name,
                    "dosage": r.dosage,
                    "reminder_time": r.reminder_time,
                    "purpose": r.purpose,
                    "frequency": r.frequency
                }
                if r.taken_status:
                    med_dict["taken_at"] = r.taken_at.isoformat() if r.taken_at else None
                    taken.append(med_dict)
                else:
                    pending.append(med_dict)

            # Map missing medicines to pending for simplicity in this sprint
            return {
                "pending_medicines": pending,
                "taken_medicines": taken,
                "missed_medicines": pending, 
                "schedule": [r.reminder_time for r in all_reminders if r.reminder_time],
                "medication_history": taken
            }
        finally:
            db.close()
