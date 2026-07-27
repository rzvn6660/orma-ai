from pydantic import BaseModel, Field
from typing import List

class HealthScore(BaseModel):
    overall_score: int
    bp_trend: str
    sugar_trend: str

class AdherenceScore(BaseModel):
    medication_percentage: float
    exercise_percentage: float
    appointment_percentage: float

class RiskAnalysis(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    reasons: List[str]

class CaregiverReport(BaseModel):
    report_type: str  # daily, weekly, monthly
    health_score: HealthScore
    adherence_score: AdherenceScore
    risk_analysis: RiskAnalysis
    recent_events: List[str]
