import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ochr.reasoning.reasoning_types import ReasoningPlan, ReasoningCategory, SafetyLevel
from ochr.context.context_models import UnifiedContext
from ochr.knowledge.medical_context import MedicalContext
from ochr.knowledge.hybrid_context import HybridContext
from ochr.execution.context_window_manager import ContextWindowManager
from ochr.execution.prompt_builder import PromptBuilder
from ochr.execution.model_adapter import ModelAdapter
from ochr.execution.execution_engine import ExecutionEngine
from ochr.execution.provider_interface import LLMProvider
from ochr.execution.execution_models import FormattedPrompt, LLMResponse

class MockProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "mock_provider"

    def generate(self, prompt: FormattedPrompt, **kwargs) -> LLMResponse:
        return LLMResponse(
            text=f"Mock response to: {prompt.user_query}",
            metadata={"model": "mock-llm-1.0"}
        )

def get_dummy_hybrid_context():
    uc = UnifiedContext()
    uc.medications = [{"id": 1, "medicine_name": "Aspirin"}] * 15 # To test truncation
    mc = MedicalContext()
    return HybridContext(personal_context=uc, medical_context=mc)

def test_context_window_manager():
    manager = ContextWindowManager(max_items=5)
    ctx = get_dummy_hybrid_context()
    
    assert len(ctx.personal_context.medications) == 15
    optimized = manager.optimize(ctx)
    assert len(optimized.personal_context.medications) == 5

def test_prompt_builder():
    builder = PromptBuilder()
    ctx = get_dummy_hybrid_context()
    
    plan = ReasoningPlan(
        reasoning_type=ReasoningCategory.MEDICATION,
        selected_prompt_template="Base Prompt",
        required_context_sections=["medications"],
        safety_level=SafetyLevel.MEDIUM,
        clarification_needed=True,
        clarification_question="Which pill?"
    )
    
    prompt = builder.build("Did I take it?", plan, ctx)
    assert "Base Prompt" in prompt.system_instruction
    assert "Which pill?" in prompt.system_instruction
    assert "Aspirin" in prompt.personal_context
    assert "No relevant medical context" in prompt.medical_context

def test_execution_engine():
    engine = ExecutionEngine(provider=MockProvider())
    ctx = get_dummy_hybrid_context()
    plan = ReasoningPlan(
        reasoning_type=ReasoningCategory.GENERAL,
        selected_prompt_template="Answer me",
        required_context_sections=[],
        safety_level=SafetyLevel.LOW
    )
    
    result = engine.execute("Hello", plan, ctx)
    
    assert result.is_successful
    assert "Mock response to: Hello" in result.response_text
    assert result.confidence == 0.95

def test_execution_engine_no_provider():
    engine = ExecutionEngine() # No provider
    ctx = get_dummy_hybrid_context()
    plan = ReasoningPlan(
        reasoning_type=ReasoningCategory.GENERAL,
        selected_prompt_template="Answer me",
        required_context_sections=[],
        safety_level=SafetyLevel.LOW
    )
    
    result = engine.execute("Hello", plan, ctx)
    
    assert not result.is_successful
    assert result.response_text == "No AI provider is configured."
    assert result.validation_status == "not_configured"
