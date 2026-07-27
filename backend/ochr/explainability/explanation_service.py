import logging
from ochr.reasoning.reasoning_types import ReasoningPlan
from ochr.knowledge.hybrid_context import HybridContext
from ochr.execution.execution_models import ExecutionResult
from .explanation_models import ExplanationResult
from .explanation_engine import ExplanationEngine

logger = logging.getLogger(__name__)

class ExplanationService:
    def __init__(self):
        self.engine = ExplanationEngine()
        logger.info("ExplanationService initialized.")

    def explain(self, plan: ReasoningPlan, context: HybridContext, execution_result: ExecutionResult) -> ExplanationResult:
        logger.info("Generating explanation for execution result.")
        return self.engine.generate_explanation(plan, context, execution_result)
