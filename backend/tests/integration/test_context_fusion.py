import pytest
import sys
import os

# Ensure backend directory is in path for tests
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ochr.context.context_models import UnifiedContext
from ochr.context.fusion_service import FusionService
from ochr.context.context_ranker import ContextRanker

def test_single_retriever_fusion():
    service = FusionService()
    
    data = {
        "medication_retriever": {
            "pending_medicines": [{"id": 1, "medicine_name": "Aspirin", "dosage": "100mg", "reminder_time": "08:00 AM"}]
        }
    }
    
    unified = service.build_context(data)
    
    assert len(unified.medications) == 1
    assert unified.medications[0]["medicine_name"] == "Aspirin"
    assert unified.medications[0]["_source"] == "medication_retriever"
    assert unified.medications[0]["_medication_status"] == "pending"
    assert "medication_retriever" in unified.retrieval_sources

def test_multiple_retrievers_fusion():
    service = FusionService()
    
    data = {
        "medication_retriever": {
            "taken_medicines": [{"id": 2, "medicine_name": "Lisinopril", "taken_at": "09:00 AM"}]
        },
        "health_record_retriever": {
            "blood_pressure": [{"id": 1, "type": "blood_pressure", "value": "120/80", "date": "2023-10-10"}]
        }
    }
    
    unified = service.build_context(data)
    
    assert len(unified.medications) == 1
    assert len(unified.health_records) == 1
    assert "medication_retriever" in unified.retrieval_sources
    assert "health_record_retriever" in unified.retrieval_sources
    assert unified.health_records[0]["value"] == "120/80"

def test_duplicate_handling():
    service = FusionService()
    
    data = {
        "memory_retriever": {
            "stored_ai_memories": [
                {"id": 10, "content": "User likes tea."},
                {"id": 10, "content": "User likes tea."} # Duplicate
            ]
        }
    }
    
    unified = service.build_context(data)
    
    assert len(unified.memories) == 1
    assert unified.memories[0]["content"] == "User likes tea."

def test_missing_or_empty_outputs():
    service = FusionService()
    
    data = {
        "medication_retriever": {},
        "planner_retriever": {"appointments": []},
        "health_record_retriever": None
    }
    
    unified = service.build_context(data)
    
    assert len(unified.medications) == 0
    assert len(unified.planner) == 0
    assert len(unified.health_records) == 0
    assert unified.retrieval_sources == []

def test_source_tracking():
    service = FusionService()
    
    data = {
        "conversation_retriever": {
            "previous_conversations": [{"role": "user", "content": "Hello"}]
        }
    }
    
    unified = service.build_context(data)
    
    assert len(unified.conversations) == 1
    assert unified.conversations[0]["_source"] == "conversation_retriever"

def test_context_ranking():
    ranker = ContextRanker()
    
    items = [
        {"id": 1, "_source": "memory_retriever", "confidence": 0.8}, # Score: 0.8
        {"id": 2, "_source": "medication_retriever", "reminder_time": "10:00 AM"}, # Score: 1.0 + 2.0 (priority) + 0.5 (time) = 3.5
        {"id": 3, "_source": "planner_retriever"}, # Score: 1.0 + 2.0 (priority) = 3.0
    ]
    
    context = UnifiedContext()
    # Let's put them all in 'planner' just to sort and verify ranker logic works as expected
    context.planner = items
    
    ranked = ranker.rank(context)
    
    assert ranked.planner[0]["id"] == 2 # Highest score
    assert ranked.planner[1]["id"] == 3
    assert ranked.planner[2]["id"] == 1
    assert ranked.metadata["ranked"] == True