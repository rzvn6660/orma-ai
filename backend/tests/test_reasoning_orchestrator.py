import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ochr.context.context_models import UnifiedContext
from ochr.reasoning.reasoning_service import ReasoningService
from ochr.reasoning.reasoning_types import ReasoningCategory, SafetyLevel

def test_medication_reasoning():
    service = ReasoningService()
    context = UnifiedContext()
    context.medications = [{"id": 1, "medicine_name": "Aspirin"}]
    
    plan = service.build_reasoning_plan("Did I take my pill?", "medication_query", context)
    
    assert plan.reasoning_type == ReasoningCategory.MEDICATION
    assert plan.safety_level == SafetyLevel.MEDIUM
    assert not plan.clarification_needed
    assert "medications" in plan.required_context_sections

def test_planner_reasoning():
    service = ReasoningService()
    context = UnifiedContext()
    context.planner = [{"id": 1, "title": "Doctor Visit"}]
    
    plan = service.build_reasoning_plan("When is my next visit?", "timeline_query", context)
    
    assert plan.reasoning_type == ReasoningCategory.PLANNER
    assert plan.safety_level == SafetyLevel.LOW
    assert not plan.clarification_needed
    assert "planner" in plan.required_context_sections

def test_emergency_reasoning():
    service = ReasoningService()
    context = UnifiedContext()
    
    plan = service.build_reasoning_plan("I have severe pain in my chest!", "emergency_query", context)
    
    assert plan.reasoning_type == ReasoningCategory.EMERGENCY
    assert plan.safety_level == SafetyLevel.CRITICAL

def test_missing_context_clarification():
    service = ReasoningService()
    context = UnifiedContext()
    # Missing medications context
    
    plan = service.build_reasoning_plan("Did I take my medicine?", "medication_query", context)
    
    assert plan.reasoning_type == ReasoningCategory.MEDICATION
    assert plan.clarification_needed == True
    assert plan.clarification_question is not None

def test_safety_classification_high():
    service = ReasoningService()
    context = UnifiedContext()
    context.medications = [{"id": 1, "medicine_name": "Aspirin"}]
    
    plan = service.build_reasoning_plan("I think I missed my dose.", "medication_query", context)
    
    assert plan.safety_level == SafetyLevel.HIGH

def test_prompt_selection():
    service = ReasoningService()
    context = UnifiedContext()
    
    plan = service.build_reasoning_plan("Hello", "general_query", context)
    
    assert plan.reasoning_type == ReasoningCategory.GENERAL
    assert "helpful assistant" in plan.selected_prompt_template
