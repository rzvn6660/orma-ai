from typing import Any, Dict
from sqlalchemy.orm import Session
from database import SessionLocal
from models.health_event import HealthEvent
from .retriever_base import BaseRetriever

class PlannerRetriever(BaseRetriever):
    """Retrieves planned health events (appointments, exercises, etc.)."""
    
    def retrieve(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = query_context.get("user_id")
        
        db: Session = SessionLocal()
        try:
            query = db.query(HealthEvent)
            if user_id:
                query = query.filter(HealthEvent.subject_id == user_id)
                
            events = query.all()
            
            appointments = []
            exercises = []
            vaccinations = []
            blood_tests = []
            daily_planner = []
            
            for e in events:
                event_dict = {
                    "id": e.id,
                    "title": e.title,
                    "type": e.event_type,
                    "time": e.reminder_time,
                    "date": e.event_date,
                    "status": "completed" if e.status else "pending",
                    "location": e.location,
                    "contact_number": e.contact_number
                }
                
                daily_planner.append(event_dict)
                
                if e.event_type == "doctor_appointment":
                    appointments.append(event_dict)
                elif e.event_type == "exercise":
                    exercises.append(event_dict)
                elif e.event_type == "vaccination":
                    vaccinations.append(event_dict)
                elif e.event_type == "blood_test":
                    blood_tests.append(event_dict)

            return {
                "appointments": appointments,
                "exercise_plans": exercises,
                "vaccinations": vaccinations,
                "blood_tests": blood_tests,
                "daily_planner": daily_planner
            }
        finally:
            db.close()
