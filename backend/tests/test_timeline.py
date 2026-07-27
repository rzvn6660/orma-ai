import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ochr.context.context_models import UnifiedContext
from ochr.timeline.timeline_service import TimelineService

def test_empty_timeline():
    service = TimelineService()
    ctx = UnifiedContext()
    
    result = service.generate_timeline(ctx)
    assert len(result.events) == 0
    assert "No health events" in result.summary

def test_mixed_event_fusion():
    service = TimelineService()
    ctx = UnifiedContext()
    ctx.medications = [{"id": 1, "medicine_name": "Aspirin", "date": "2023-10-01T10:00:00Z", "_source": "medication_retriever"}]
    ctx.planner = [{"id": 2, "title": "Doctor Visit", "date": "2023-10-05T14:00:00Z", "_source": "planner_retriever"}]
    ctx.health_records = [{"id": 3, "type": "Blood Pressure", "date": "2023-10-05T15:00:00Z", "_source": "health_record_retriever"}]
    
    result = service.generate_timeline(ctx)
    assert len(result.events) == 3
    assert result.statistics["medication"] == 1
    assert result.statistics["doctor_visit"] == 1
    assert result.statistics["lab_result"] == 1

def test_duplicate_removal():
    service = TimelineService()
    ctx = UnifiedContext()
    # Identical IDs and timestamps should be deduplicated
    ctx.medications = [
        {"id": 1, "medicine_name": "Aspirin", "date": "2023-10-01", "_source": "medication_retriever"},
        {"id": 1, "medicine_name": "Aspirin", "date": "2023-10-01", "_source": "medication_retriever"}
    ]
    
    result = service.generate_timeline(ctx)
    assert len(result.events) == 1

def test_date_sorting():
    service = TimelineService()
    ctx = UnifiedContext()
    ctx.planner = [
        {"id": 1, "title": "Event B", "date": "2023-10-02T10:00:00Z"},
        {"id": 2, "title": "Event C", "date": "2023-10-03T10:00:00Z"},
        {"id": 3, "title": "Event A", "date": "2023-10-01T10:00:00Z"}
    ]
    
    result = service.generate_timeline(ctx)
    assert result.events[0].title == "Event A"
    assert result.events[2].title == "Event C"
    
def test_timeline_summary():
    service = TimelineService()
    ctx = UnifiedContext()
    ctx.medications = [{"id": 1, "medicine_name": "Aspirin", "date": "2023-10-01T10:00:00Z", "_source": "medication_retriever"}]
    
    result = service.generate_timeline(ctx)
    assert "Timeline covers 1 events" in result.summary
    assert result.date_range["start"] == "2023-10-01T10:00:00Z"
