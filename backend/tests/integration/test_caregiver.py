import pytest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ochr.context.context_models import UnifiedContext
from ochr.caregiver.caregiver_engine import CaregiverEngine

def test_empty_patient():
    engine = CaregiverEngine()
    ctx = UnifiedContext()
    report = engine.generate_report(ctx, "weekly")
    assert report.adherence_score.medication_percentage == 100.0
    assert report.risk_analysis.risk_level == "LOW"

def test_adherence_calculation():
    engine = CaregiverEngine()
    ctx = UnifiedContext()
    ctx.medications = [
        {"_medication_status": "taken"},
        {"_medication_status": "taken"},
        {"_medication_status": "missed"},
        {"_medication_status": "missed"}
    ]
    report = engine.generate_report(ctx, "monthly")
    assert report.adherence_score.medication_percentage == 50.0

def test_risk_escalation():
    engine = CaregiverEngine()
    ctx = UnifiedContext()
    ctx.medications = [{"_medication_status": "missed"}] * 10
    report = engine.generate_report(ctx)
    assert report.risk_analysis.risk_level == "CRITICAL"
    
    ctx.health_records = [{"type": "emergency"}]
    report2 = engine.generate_report(ctx)
    assert report2.risk_analysis.risk_level == "CRITICAL"
    assert any("emergency" in r for r in report2.risk_analysis.reasons)