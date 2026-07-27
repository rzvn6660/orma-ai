from typing import Dict, Any
from .context_models import UnifiedContext

class ContextRanker:
    """
    Ranks context items based on simple heuristics like source priority, recency, etc.
    """
    def __init__(self):
        # Priority sources get a higher base score
        self.priority_sources = ["emergency_retriever", "medication_retriever", "planner_retriever"]
        
    def score_item(self, item: Dict[str, Any]) -> float:
        score = 1.0
        
        # Source Priority
        source = item.get("_source", "")
        if source in self.priority_sources:
            score += 2.0
            
        # Confidence multiplier if available
        confidence = item.get("confidence", 1.0)
        score *= confidence
        
        # Simple recency heuristic: items with temporal fields get a small boost
        if any(key in item for key in ["date", "time", "taken_at", "reminder_time"]):
            score += 0.5
            
        return score

    def rank(self, unified_context: UnifiedContext) -> UnifiedContext:
        """
        Sorts items in each category of the unified context by relevance score in descending order.
        """
        # Sort in place
        unified_context.medications.sort(key=self.score_item, reverse=True)
        unified_context.planner.sort(key=self.score_item, reverse=True)
        unified_context.health_records.sort(key=self.score_item, reverse=True)
        unified_context.memories.sort(key=self.score_item, reverse=True)
        unified_context.conversations.sort(key=self.score_item, reverse=True)
        
        # Store some metadata about the ranking
        unified_context.metadata["ranked"] = True
        
        return unified_context
