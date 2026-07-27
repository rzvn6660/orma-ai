from typing import Any, Dict
from sqlalchemy.orm import Session
from database import SessionLocal
from models.health_record import HealthRecord
from .retriever_base import BaseRetriever

class HealthRecordRetriever(BaseRetriever):
    """Retrieves health records (vitals, reports)."""
    
    def retrieve(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = query_context.get("user_id")
        
        db: Session = SessionLocal()
        try:
            query = db.query(HealthRecord)
            if user_id:
                query = query.filter(HealthRecord.user_id == user_id)
                
            records = query.all()
            
            bp = []
            sugar = []
            weight = []
            reports = []
            visits = []
            
            for r in records:
                record_dict = {
                    "id": r.id,
                    "type": r.vital_type,
                    "value": r.value,
                    "unit": r.unit,
                    "date": r.date,
                    "time": r.time,
                    "notes": r.notes
                }
                
                if r.vital_type == "blood_pressure":
                    bp.append(record_dict)
                elif r.vital_type == "blood_sugar":
                    sugar.append(record_dict)
                elif r.vital_type == "weight":
                    weight.append(record_dict)
                elif r.vital_type == "report":
                    reports.append(record_dict)
                elif r.vital_type == "doctor_visit":
                    visits.append(record_dict)

            return {
                "blood_pressure": bp,
                "blood_sugar": sugar,
                "weight": weight,
                "reports": reports,
                "doctor_visits": visits
            }
        finally:
            db.close()
