import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ochr.context.context_models import UnifiedContext
from ochr.doctor.doctor_service import DoctorService

def test_empty_records():
    service = DoctorService()
    ctx = UnifiedContext()
    
    summary = service.generate_summary(ctx)
    assert len(summary.snapshot.current_medications) == 0
    assert summary.snapshot.blood_pressure_trend == "No data"
    assert len(summary.questions_to_ask) == 1
    assert "daily routine" in summary.questions_to_ask[0]

def test_multiple_medicines():
    service = DoctorService()
    ctx = UnifiedContext()
    ctx.medications = [
        {"id": 1, "medicine_name": "Aspirin", "_medication_status": "taken"},
        {"id": 2, "medicine_name": "Metformin", "_medication_status": "taken"},
        {"id": 3, "medicine_name": "Lisinopril", "_medication_status": "taken"}
    ]
    
    summary = service.generate_summary(ctx)
    assert len(summary.snapshot.current_medications) == 3
    # Check question generation for >2 meds
    assert any("reduced or stopped" in q for q in summary.questions_to_ask)

def test_trend_generation():
    service = DoctorService()
    ctx = UnifiedContext()
    ctx.health_records = [
        {"id": 1, "type": "blood_pressure", "value": "120/80"},
        {"id": 2, "type": "blood_pressure", "value": "125/82"}
    ]
    
    summary = service.generate_summary(ctx)
    assert "Trend available across 2 records" in summary.snapshot.blood_pressure_trend
    assert "Latest: 125/82" in summary.snapshot.blood_pressure_trend

def test_risk_detection_high_bp():
    service = DoctorService()
    ctx = UnifiedContext()
    ctx.health_records = [
        {"id": 1, "type": "blood_pressure", "value": "145/90"}
    ]
    
    summary = service.generate_summary(ctx)
    assert any("High Blood Pressure" in r for r in summary.risk_summary.high_risks)
    assert any("blood pressure abnormal" in q for q in summary.questions_to_ask)

def test_risk_detection_missed_meds():
    service = DoctorService()
    ctx = UnifiedContext()
    ctx.medications = [
        {"id": 1, "medicine_name": "Aspirin", "_medication_status": "missed"},
        {"id": 2, "medicine_name": "Metformin", "_medication_status": "missed"},
        {"id": 3, "medicine_name": "Lisinopril", "_medication_status": "missed"}
    ]
    
    summary = service.generate_summary(ctx)
    assert any("Frequent missed medications" in r for r in summary.risk_summary.high_risks)
    assert any("missing my medication" in q for q in summary.questions_to_ask)
