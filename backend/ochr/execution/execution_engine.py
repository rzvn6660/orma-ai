import logging
from typing import Optional
from ochr.reasoning.reasoning_types import ReasoningPlan
from ochr.knowledge.hybrid_context import HybridContext
from .execution_models import ExecutionResult
from .context_window_manager import ContextWindowManager
from .prompt_builder import PromptBuilder
from .model_adapter import ModelAdapter
from .provider_interface import LLMProvider
from .response_validator import ResponseValidator
from ochr.explainability.explanation_service import ExplanationService

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.context_manager = ContextWindowManager()
        self.prompt_builder = PromptBuilder()
        self.model_adapter = ModelAdapter(default_provider=provider)
        self.validator = ResponseValidator()
        self.explainer = ExplanationService()
        
    def execute(self, query: str, plan: ReasoningPlan, context: HybridContext) -> ExecutionResult:
        logger.info(f"Executing query: '{query}' with ReasoningPlan: {plan.reasoning_type.value}")
        
        # 1. Optimize Context Window
        optimized_context = self.context_manager.optimize(context)
        
        # 2. Build Prompt
        prompt = self.prompt_builder.build(query, plan, optimized_context)
        
        # 3. Handle No Provider scenario cleanly
        if not self.model_adapter.has_provider():
            return ExecutionResult(
                is_successful=False,
                response_text="No AI provider is configured.",
                validation_status="not_configured",
                confidence=0.0,
                metadata={"provider": None, "status": "not_configured"}
            )
            
        # 4. Call LLM
        llm_response = self.model_adapter.generate_response(prompt)
        
        # 5. Validate Response
        is_valid, validation_status, confidence = self.validator.validate(llm_response, optimized_context)
        
        if not is_valid:
            return ExecutionResult(
                is_successful=False,
                response_text="Validation failed: Unsafe response.",
                validation_status=validation_status,
                confidence=0.0
            )
            
        # 5. Return structured result
        result = ExecutionResult(
            is_successful=is_valid,
            response_text=llm_response.text,
            validation_status=validation_status,
            confidence=confidence,
            metadata={
                "provider": llm_response.metadata.get("provider", "unknown"),
                "model": llm_response.metadata.get("model", "unknown"),
                "usage": llm_response.metadata.get("usage", {}),
                "generation_time_ms": llm_response.metadata.get("generation_time_ms", 0),
                "safety_level": plan.safety_level.value
            }
        )
        
        # 6. Explainability
        explanation = self.explainer.explain(plan, optimized_context, result)
        result.explanation = explanation
        
        logger.info(f"Execution finished with status: {validation_status}")
        return result
