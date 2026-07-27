import logging
from ochr.context.context_models import UnifiedContext
from .reasoning_types import ReasoningPlan
from .reasoning_orchestrator import ReasoningOrchestrator

logger = logging.getLogger(__name__)

class ReasoningService:
    """Service layer for Reasoning Orchestration."""
    
    def __init__(self):
        self.orchestrator = ReasoningOrchestrator()
        logger.info("ReasoningService initialized.")

    def build_reasoning_plan(self, query: str, router_intent: str, context: UnifiedContext) -> ReasoningPlan:
        """
        Creates a structured plan describing how the LLM should respond to the user.
        Returns a ReasoningPlan model.
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to ReasoningService.")
            
        return self.orchestrator.orchestrate(query, router_intent, context)
