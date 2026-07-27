from ochr.context.context_models import UnifiedContext
from .doctor_models import DoctorSummary, RiskSummary, PatientSnapshot
from .health_summary import HealthSummaryEngine
from .question_generator import QuestionGenerator

class DoctorSummaryEngine:
    def __init__(self):
        self.health_summary = HealthSummaryEngine()
        self.question_generator = QuestionGenerator()
        
    def _detect_risks(self, snapshot: PatientSnapshot, context: UnifiedContext) -> RiskSummary:
        risks = RiskSummary()
        
        if len(snapshot.missed_medications) >= 3:
            risks.high_risks.append(f"Frequent missed medications: {', '.join(snapshot.missed_medications)}")
        elif len(snapshot.missed_medications) > 0:
            risks.medium_risks.append(f"Some missed medications: {', '.join(snapshot.missed_medications)}")
            
        # Mock threshold check for foundational sprint
        import re
        bp_match = re.search(r"(\d{3})/", snapshot.blood_pressure_trend)
        if "High" in snapshot.blood_pressure_trend or (bp_match and int(bp_match.group(1)) >= 140):
            risks.high_risks.append("High Blood Pressure detected in trend.")
            
        if len(snapshot.recent_symptoms) >= 3:
            risks.medium_risks.append("Repeated symptoms reported.")
            
        return risks

    def generate(self, context: UnifiedContext) -> DoctorSummary:
        snapshot = self.health_summary.build_snapshot(context)
        risks = self._detect_risks(snapshot, context)
        questions = self.question_generator.generate_questions(snapshot, risks)
        
        return DoctorSummary(
            snapshot=snapshot,
            risk_summary=risks,
            questions_to_ask=questions
        )
