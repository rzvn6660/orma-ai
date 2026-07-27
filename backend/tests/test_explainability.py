import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ochr.reasoning.reasoning_types import ReasoningPlan, ReasoningCategory, SafetyLevel
from ochr.context.context_models import UnifiedContext
from ochr.knowledge.medical_context import MedicalContext, MedicalKnowledgeItem, MedicalSourceMetadata
from ochr.knowledge.hybrid_context import HybridContext
from ochr.execution.execution_models import ExecutionResult
from ochr.explainability.explanation_service import ExplanationService

def test_explanation_generation():
    service = ExplanationService()
    
    uc = UnifiedContext()
    uc.medications = [{"id": 1, "medicine_name": "Aspirin", "_source": "medication_retriever", "confidence": 0.9}]
    
    mc = MedicalContext()
    mc.drugs = [
        MedicalKnowledgeItem(
            query="Aspirin",
            category="drug",
            content={"side_effects": ["nausea"]},
            metadata=MedicalSourceMetadata(source_name="OpenFDA", provider="mock", confidence=0.95)
        )
    ]
    
    context = HybridContext(personal_context=uc, medical_context=mc)
    
    plan = ReasoningPlan(
        reasoning_type=ReasoningCategory.MEDICATION,
        selected_prompt_template="Test",
        required_context_sections=["medications"],
        safety_level=SafetyLevel.MEDIUM
    )
    
    exec_result = ExecutionResult(
        is_successful=True,
        response_text="You might feel nauseous.",
        validation_status="passed",
        confidence=0.9
    )
    
    explanation = service.explain(plan, context, exec_result)
    
    assert explanation.reasoning_category == "medication"
    assert len(explanation.evidence_items) == 2
    assert explanation.medical_sources == ["OpenFDA"]
    assert "medications" in explanation.contributing_context_sections
    assert "OpenFDA" in explanation.explanation_summary
    
    medical_evidence = [e for e in explanation.evidence_items if e.is_medical]
    assert len(medical_evidence) == 1
    assert medical_evidence[0].source_name == "OpenFDA"
