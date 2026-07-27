import logging
from typing import Dict, Any, List, Optional
from memory.memory_models import OCMEMemory

logger = logging.getLogger(__name__)

class MergeEngine:
    """
    Merges complementary memories.
    Example: 
    Memory 1: Emily -> Daughter
    Memory 2 (Candidate): Emily lives in Dubai
    Result: One enriched Family memory -> Emily is Daughter, lives in Dubai.
    """
    
    def detect_merge(self, candidate: Dict[str, Any], existing_memories: List[OCMEMemory]) -> Optional[Dict[str, Any]]:
        """
        Returns action='MERGE' if complementary info is found.
        """
        title = candidate.get("title", "").lower()
        new_value = candidate.get("value", "")
        
        for mem in existing_memories:
            # We look for related entities. For a simple rule-based approach:
            # If titles are identical but values differ (and aren't direct conflicts),
            # or if the title is mentioned in an existing memory.
            # E.g. title: "Emily", value: "lives in Dubai". Existing title: "Emily", value: "Daughter".
            if mem.title.lower() == title:
                # If they are different, we can merge them
                if mem.value.lower() != new_value.lower():
                    # Check if it's already merged (basic string check)
                    if new_value.lower() not in mem.value.lower():
                        merged_value = f"{mem.value}, {new_value}"
                        logger.info(f"[MergeEngine] Merge opportunity detected for '{mem.title}'. Merging values.")
                        return {
                            "action": "MERGE",
                            "reason": "Complementary information merged.",
                            "existing_memory": mem,
                            "updates": {
                                "value": merged_value,
                                "confidence": min(1.0, mem.confidence + 0.1)
                            }
                        }
        return None

merge_engine = MergeEngine()
