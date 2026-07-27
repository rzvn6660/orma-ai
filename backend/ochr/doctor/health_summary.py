from typing import List, Dict, Any
from ochr.context.context_models import UnifiedContext
from .doctor_models import PatientSnapshot

class HealthSummaryEngine:
    def _calculate_trend(self, records: List[Dict[str, Any]], record_type: str) -> str:
        # Simple string-based trend heuristic for foundational sprint
        filtered = [r for r in records if r.get("type", "").lower() == record_type.lower()]
        if not filtered:
            return "No data"
        if len(filtered) == 1:
            return f"Latest: {filtered[0].get('value', 'Unknown')}"
        return f"Trend available across {len(filtered)} records. Latest: {filtered[-1].get('value', 'Unknown')}"

    def build_snapshot(self, context: UnifiedContext) -> PatientSnapshot:
        snapshot = PatientSnapshot()
        
        # Current and Missed Medications
        for med in context.medications:
            status = med.get("_medication_status", "pending")
            name = med.get("medicine_name", "Unknown Pill")
            if status == "taken" or status == "pending":
                if name not in snapshot.current_medications:
                    snapshot.current_medications.append(name)
            elif status == "missed":
                if name not in snapshot.missed_medications:
                    snapshot.missed_medications.append(name)
                    
        # Symptoms / Health Records / Reports
        for record in context.health_records:
            r_type = record.get("type", "").lower()
            if r_type == "symptom":
                snapshot.recent_symptoms.append(record.get("value", ""))
            elif r_type == "report":
                snapshot.recent_reports.append(record.get("value", ""))
                
        snapshot.blood_pressure_trend = self._calculate_trend(context.health_records, "blood_pressure")
        snapshot.blood_sugar_trend = self._calculate_trend(context.health_records, "blood_sugar")
        snapshot.weight_trend = self._calculate_trend(context.health_records, "weight")
        
        # Planner
        for plan in context.planner:
            title = plan.get("title", "")
            if "visit" in title.lower() or "appointment" in title.lower():
                snapshot.upcoming_appointments.append(title)
                
        # Memories
        for mem in context.memories:
            snapshot.important_memories.append(mem.get("content", ""))
            
        return snapshot
