import pytest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ochr.context.context_models import UnifiedContext
from ochr.knowledge.medical_sources import MockMedicalProvider
from ochr.knowledge.medical_retriever import MedicalRetriever
from ochr.knowledge.knowledge_router import KnowledgeRouter
from ochr.knowledge.hybrid_context import HybridContext
from ochr.knowledge.medical_context import MedicalContext

def test_drug_info_retrieval():
    retriever = MedicalRetriever(MockMedicalProvider())
    context = retriever.retrieve([{"type": "drug", "query": "aspirin"}])
    
    assert len(context.drugs) == 1
    assert context.drugs[0].query == "aspirin"
    assert "upset stomach" in context.drugs[0].content["side_effects"]

def test_condition_info_retrieval():
    retriever = MedicalRetriever(MockMedicalProvider())
    context = retriever.retrieve([{"type": "condition", "query": "hypertension"}])
    
    assert len(context.conditions) == 1
    assert context.conditions[0].query == "hypertension"
    assert "guidance" in context.conditions[0].content

def test_hybrid_context_creation():
    uc = UnifiedContext()
    mc = MedicalContext()
    
    hybrid = HybridContext(personal_context=uc, medical_context=mc)
    assert hybrid.personal_context == uc
    assert hybrid.medical_context == mc

def test_source_tracking():
    retriever = MedicalRetriever(MockMedicalProvider())
    context = retriever.retrieve([{"type": "drug", "query": "aspirin"}])
    
    item = context.drugs[0]
    assert item.metadata.provider == "mock_medical_provider"
    assert item.metadata.confidence == 1.0

def test_medical_retrieval_bypass():
    router = KnowledgeRouter()
    
    # Simple personal queries
    assert not router.requires_medical_knowledge("Did I take my pill?", "medication_query")
    assert not router.requires_medical_knowledge("What is my schedule?", "timeline_query")
    
    # Knowledge intensive queries
    assert router.requires_medical_knowledge("What are the side effects of Aspirin?", "medication_query")
    assert router.requires_medical_knowledge("Can I take this with blood thinners? interaction", "medication_query")