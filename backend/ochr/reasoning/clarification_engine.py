from typing import Optional
from ochr.context.context_models import UnifiedContext
from .reasoning_types import ReasoningCategory

class ClarificationEngine:
    """Determines if the provided context is sufficient for the reasoning request."""
    
    def check_clarification_needed(self, category: ReasoningCategory, context: UnifiedContext, query: str) -> tuple[bool, Optional[str]]:
        """Returns a boolean indicating if clarification is needed, and an optional question."""
        # If medication query but no medication records found
        if category == ReasoningCategory.MEDICATION:
            if not context.medications:
                return True, "I couldn't find any medication records in your context. Which medicine are you asking about?"
        
        # If planner query but no planner data found
        if category == ReasoningCategory.PLANNER:
            if not context.planner:
                return True, "I don't see any upcoming events or appointments in your planner. What date are you checking?"

        return False, None
