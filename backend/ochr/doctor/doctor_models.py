from pydantic import BaseModel, Field
from typing import List

class RiskSummary(BaseModel):
    high_risks: List[str] = Field(default_factory=list)
    medium_risks: List[str] = Field(default_factory=list)

class PatientSnapshot(BaseModel):
    current_medications: List[str] = Field(default_factory=list)
    recent_symptoms: List[str] = Field(default_factory=list)
    missed_medications: List[str] = Field(default_factory=list)
    upcoming_appointments: List[str] = Field(default_factory=list)
    important_memories: List[str] = Field(default_factory=list)
    recent_reports: List[str] = Field(default_factory=list)
    blood_pressure_trend: str = "No data"
    blood_sugar_trend: str = "No data"
    weight_trend: str = "No data"

class DoctorSummary(BaseModel):
    snapshot: PatientSnapshot
    questions_to_ask: List[str] = Field(default_factory=list)
    risk_summary: RiskSummary
