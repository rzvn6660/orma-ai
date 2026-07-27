import logging
from typing import List
from memory.memory_models import OCMEMemory
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextBuilder:
    """
    Converts raw memory objects into structured conversational context for the LLM.
    """
    def __init__(self):
        pass

    def build_context_string(self, memories: List[OCMEMemory]) -> str:
        """
        Converts a list of OCMEMemory objects into a concise string format.
        """
        if not memories:
            return ""
            
        logger.info(f"[ContextBuilder] Building context for {len(memories)} memories.")
        
        context_lines = ["\n[RELEVANT LONG-TERM MEMORY]"]
        now = datetime.utcnow()
        
        for mem in memories:
            # Calculate recency description
            recency = "recently"
            if mem.last_used:
                days_ago = (now - mem.last_used).days
                if days_ago == 0:
                    recency = "today"
                elif days_ago == 1:
                    recency = "yesterday"
                elif days_ago > 1:
                    recency = f"{days_ago} days ago"
                    
            # Build structured line
            line = f"- {mem.category}: {mem.title} is {mem.value}. (Last referenced {recency}, Confidence: {mem.confidence*100:.0f}%)"
            context_lines.append(line)
            
        context_str = "\n".join(context_lines)
        return context_str

context_builder = ContextBuilder()
