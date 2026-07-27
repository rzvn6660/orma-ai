from ochr.context.context_models import UnifiedContext

class AdherenceEngine:
    def calculate(self, context: UnifiedContext) -> dict:
        # Medication adherence
        meds = context.medications
        taken = sum(1 for m in meds if m.get("_medication_status") == "taken")
        missed = sum(1 for m in meds if m.get("_medication_status") == "missed")
        total = taken + missed
        med_pct = (taken / total * 100) if total > 0 else 100.0

        return {
            "medication_percentage": med_pct,
            "exercise_percentage": 100.0, # Placeholder
            "appointment_percentage": 100.0 # Placeholder
        }
