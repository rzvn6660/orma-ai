import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure backend directory is in path for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ochr.retrievers.retriever_registry import RetrieverRegistry
from ochr.retrievers.medication_retriever import MedicationRetriever
from ochr.retrievers.planner_retriever import PlannerRetriever
from ochr.retrievers.health_record_retriever import HealthRecordRetriever
from ochr.retrievers.memory_retriever import MemoryRetriever
from ochr.retrievers.conversation_retriever import ConversationRetriever

def test_retriever_registry():
    med_retriever = MedicationRetriever()
    RetrieverRegistry.register("medication_retriever", med_retriever)
    
    assert RetrieverRegistry.get_retriever("medication_retriever") == med_retriever
    assert "medication_retriever" in RetrieverRegistry.get_all_registered_names()

@patch("ochr.retrievers.medication_retriever.SessionLocal")
def test_medication_retriever_empty(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.all.return_value = []
    
    retriever = MedicationRetriever()
    result = retriever.retrieve({"user_id": "test_empty_user_id"})
    
    assert isinstance(result, dict)
    assert "pending_medicines" in result
    assert "taken_medicines" in result
    assert "missed_medicines" in result
    assert "schedule" in result
    assert "medication_history" in result
    assert len(result["pending_medicines"]) == 0

@patch("ochr.retrievers.planner_retriever.SessionLocal")
def test_planner_retriever_empty(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.all.return_value = []
    
    retriever = PlannerRetriever()
    result = retriever.retrieve({"user_id": "test_empty_user_id"})
    
    assert isinstance(result, dict)
    assert "appointments" in result
    assert "exercise_plans" in result
    assert "vaccinations" in result
    assert "blood_tests" in result
    assert "daily_planner" in result
    assert len(result["daily_planner"]) == 0

@patch("ochr.retrievers.health_record_retriever.SessionLocal")
def test_health_record_retriever_empty(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.all.return_value = []
    
    retriever = HealthRecordRetriever()
    result = retriever.retrieve({"user_id": "test_empty_user_id"})
    
    assert isinstance(result, dict)
    assert "blood_pressure" in result
    assert "blood_sugar" in result
    assert "weight" in result
    assert "reports" in result
    assert "doctor_visits" in result
    assert len(result["blood_pressure"]) == 0

@patch("ochr.retrievers.memory_retriever.SessionLocal")
def test_memory_retriever_empty(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.all.return_value = []
    
    retriever = MemoryRetriever()
    result = retriever.retrieve({"user_id": "test_empty_user_id"})
    
    assert isinstance(result, dict)
    assert "stored_ai_memories" in result
    assert "important_events" in result
    assert "user_preferences" in result
    assert len(result["stored_ai_memories"]) == 0

def test_conversation_retriever_empty():
    retriever = ConversationRetriever()
    result = retriever.retrieve({"user_id": "test_empty_user_id"})
    
    assert isinstance(result, dict)
    assert "previous_conversations" in result
    assert "doctor_discussions" in result
    assert "recent_ai_interactions" in result
    assert len(result["previous_conversations"]) == 0
