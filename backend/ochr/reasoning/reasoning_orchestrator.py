import logging
from ochr.context.context_models import UnifiedContext
from .reasoning_types import ReasoningCategory, ReasoningPlan
from .prompt_selector import PromptSelector
from .clarification_engine import ClarificationEngine
from .response_policy import ResponsePolicy

logger = logging.getLogger(__name__)

class ReasoningOrchestrator:
    """Core logic for preparing a ReasoningPlan from the UnifiedContext and User Query."""
    
    def __init__(self):
        self.prompt_selector = PromptSelector()
        self.clarification_engine = ClarificationEngine()
        self.response_policy = ResponsePolicy()
        
    def _map_intent_to_category(self, intent: str) -> ReasoningCategory:
        """Mapping from router intent to reasoning category."""
        mapping = {
            "medication_query": ReasoningCategory.MEDICATION,
            "timeline_query": ReasoningCategory.PLANNER,
            "health_record_query": ReasoningCategory.HEALTH,
            "memory_query": ReasoningCategory.MEMORY,
            "conversation_query": ReasoningCategory.CONVERSATION,
            "emergency_query": ReasoningCategory.EMERGENCY,
            "general_query": ReasoningCategory.GENERAL
        }
        return mapping.get(intent, ReasoningCategory.GENERAL)

    def orchestrate(self, query: str, router_intent: str, context: UnifiedContext) -> ReasoningPlan:
        logger.info(f"Orchestrating reasoning plan for intent: {router_intent}")
        category = self._map_intent_to_category(router_intent)
        
        clarification_needed, clarification_q = self.clarification_engine.check_clarification_needed(category, context, query)
        
        safety_level = self.response_policy.determine_safety_level(category, query)
        required_sections = self.response_policy.get_required_sections(category)
        
        template = self.prompt_selector.select(category)
        
        # Calculate some simple metadata
        item_count = len(context.medications) + len(context.planner) + len(context.health_records) + len(context.memories) + len(context.conversations)
        
        plan = ReasoningPlan(
            reasoning_type=category,
            selected_prompt_template=template,
            required_context_sections=required_sections,
            safety_level=safety_level,
            clarification_needed=clarification_needed,
            clarification_question=clarification_q,
            explanation_metadata={
                "intent_mapped": router_intent,
                "context_items_count": str(item_count)
            }
        )
        
        logger.info(f"Generated Reasoning Plan: {plan.model_dump_json()}")
        return plan
