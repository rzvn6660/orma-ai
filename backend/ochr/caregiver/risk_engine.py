from ochr.context.context_models import UnifiedContext
from .caregiver_models import RiskAnalysis

class RiskEngine:
    def analyze(self, adherence_data: dict, context: UnifiedContext) -> RiskAnalysis:
        reasons = []
        level = "LOW"
        
        if adherence_data["medication_percentage"] < 50.0:
            reasons.append("Severe medication non-adherence.")
            level = "CRITICAL"
        elif adherence_data["medication_percentage"] < 80.0:
            reasons.append("Moderate medication non-adherence.")
            level = "HIGH" if level not in ["CRITICAL"] else level
            
        emergencies = sum(1 for m in context.health_records if "emergency" in str(m.get("type", "")).lower())
        if emergencies > 0:
            reasons.append(f"{emergencies} recent emergency events detected.")
            level = "CRITICAL"
            
        if not reasons:
            reasons.append("All metrics appear stable.")
            
        return RiskAnalysis(risk_level=level, reasons=reasons)
