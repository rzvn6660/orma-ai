import pytest
import sys
import os

# Ensure backend directory is in path for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ochr.router.intent_definitions import IntentType, RetrieverType
from ochr.router.router_service import RouterService
from ochr.router.retrieval_router import RetrievalRouter

def test_medication_query():
    service = RouterService()
    decision = service.get_routing_decision("Did I take my medicine yesterday?")
    
    assert decision["intent"] == "medication_query"
    assert "medication_retriever" in decision["retrievers"]

def test_timeline_query():
    service = RouterService()
    decision = service.get_routing_decision("What happened before my surgery?")
    
    assert decision["intent"] == "timeline_query"
    assert "planner_retriever" in decision["retrievers"]
    assert "health_record_retriever" in decision["retrievers"]
    assert "memory_retriever" in decision["retrievers"]
    assert "conversation_retriever" in decision["retrievers"]

def test_empty_query():
    service = RouterService()
    decision = service.get_routing_decision("")
    
    assert decision["intent"] == "unknown"
    assert decision["retrievers"] == []

def test_general_query():
    service = RouterService()
    decision = service.get_routing_decision("What is the meaning of life?")
    
    assert decision["intent"] == "general_query"
    assert "memory_retriever" in decision["retrievers"]
    assert "conversation_retriever" in decision["retrievers"]

def test_emergency_query():
    service = RouterService()
    decision = service.get_routing_decision("I am bleeding and need an ambulance!")
    
    assert decision["intent"] == "emergency_query"
    assert "emergency_retriever" in decision["retrievers"]
    assert "health_record_retriever" in decision["retrievers"]
