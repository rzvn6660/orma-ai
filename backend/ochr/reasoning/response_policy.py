from ochr.context.context_models import UnifiedContext
from .reasoning_types import ReasoningCategory, SafetyLevel

class ResponsePolicy:
    """Determines safety level and required context sections based on category and query."""
    
    def determine_safety_level(self, category: ReasoningCategory, query: str) -> SafetyLevel:
        query_lower = query.lower()
        
        # Immediate critical flags
        if category == ReasoningCategory.EMERGENCY or "pain" in query_lower or "blood" in query_lower or "emergency" in query_lower:
            return SafetyLevel.CRITICAL
            
        # High priority flags
        if category in [ReasoningCategory.MEDICATION, ReasoningCategory.HEALTH]:
            if "missed" in query_lower or "overdose" in query_lower or "wrong" in query_lower:
                return SafetyLevel.HIGH
            return SafetyLevel.MEDIUM
            
        return SafetyLevel.LOW

    def get_required_sections(self, category: ReasoningCategory) -> list[str]:
        mapping = {
            ReasoningCategory.MEDICATION: ["medications", "health_records"],
            ReasoningCategory.HEALTH: ["health_records", "medications"],
            ReasoningCategory.PLANNER: ["planner"],
            ReasoningCategory.MEMORY: ["memories"],
            ReasoningCategory.CONVERSATION: ["conversations"],
            ReasoningCategory.EMERGENCY: ["health_records", "medications", "planner"],
            ReasoningCategory.GENERAL: []
        }
        return mapping.get(category, [])
