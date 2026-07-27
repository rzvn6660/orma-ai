from ochr.knowledge.hybrid_context import HybridContext

class ContextWindowManager:
    """Trims or summarizes context to fit within typical LLM token limits."""
    
    def __init__(self, max_items: int = 10):
        self.max_items = max_items

    def optimize(self, context: HybridContext) -> HybridContext:
        """
        Naive trimming approach for the foundational sprint.
        Ensures we do not pass more than `max_items` per list to the LLM.
        """
        # Truncate personal context
        context.personal_context.medications = context.personal_context.medications[:self.max_items]
        context.personal_context.planner = context.personal_context.planner[:self.max_items]
        context.personal_context.health_records = context.personal_context.health_records[:self.max_items]
        context.personal_context.memories = context.personal_context.memories[:self.max_items]
        context.personal_context.conversations = context.personal_context.conversations[:self.max_items]
        
        # Truncate medical context
        context.medical_context.drugs = context.medical_context.drugs[:self.max_items]
        context.medical_context.conditions = context.medical_context.conditions[:self.max_items]
        
        return context
