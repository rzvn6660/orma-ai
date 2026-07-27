from ochr.context.context_models import UnifiedContext
from .caregiver_models import CaregiverReport, AdherenceScore
from .adherence_engine import AdherenceEngine
from .risk_engine import RiskEngine
from .analytics import AnalyticsEngine

class CaregiverEngine:
    def __init__(self):
        self.adherence = AdherenceEngine()
        self.risk = RiskEngine()
        self.analytics = AnalyticsEngine()
        
    def generate_report(self, context: UnifiedContext, report_type: str = "weekly") -> CaregiverReport:
        adherence_data = self.adherence.calculate(context)
        risk_analysis = self.risk.analyze(adherence_data, context)
        health_score = self.analytics.compute_health_score(context)
        
        return CaregiverReport(
            report_type=report_type,
            health_score=health_score,
            adherence_score=AdherenceScore(**adherence_data),
            risk_analysis=risk_analysis,
            recent_events=[]
        )
