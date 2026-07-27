import logging
from typing import Dict, Any, List
from memory.memory_models import OCMEMemory

from .ownership_engine import ownership_engine
from .policy_engine import policy_engine
from .duplicate_engine import duplicate_engine
from .conflict_engine import conflict_engine
from .merge_engine import merge_engine
from .trust_engine import trust_engine

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """
    Orchestrates the Memory Reasoning Layer (MRL).
    Evaluates every memory candidate before it is written to the Memory Store.
    """
    
    def evaluate(self, candidate: Dict[str, Any], existing_memories: List[OCMEMemory]) -> Dict[str, Any]:
        """
        Receives: Memory Candidate
        Returns a decision object containing the action:
        SAVE, UPDATE, MERGE, ASK_USER, IGNORE, ARCHIVE, DELETE
        And an explainability string.
        """
        logger.info(f"[ReasoningEngine] Evaluating candidate: {candidate.get('title')}")
        
        decision = {
            "action": "SAVE",
            "reason": "Passed all evaluations.",
            "candidate": candidate,
            "conflict_data": None,
            "existing_memory": None,
            "updates": None
        }
        
        # 1. Ownership Check
        owner_status = ownership_engine.evaluate(candidate)
        if owner_status == "IGNORE":
            decision["action"] = "IGNORE"
            decision["reason"] = f"Information belongs to another subsystem."
            logger.info(f"[ReasoningEngine] Decision: IGNORE ({decision['reason']})")
            return decision

        # 2. Policy Check
        policy = policy_engine.apply_policy(candidate)
        if policy["action"] == "IGNORE":
            decision["action"] = "IGNORE"
            decision["reason"] = "Policy dictates ignoring this category."
            logger.info(f"[ReasoningEngine] Decision: IGNORE ({decision['reason']})")
            return decision
            
        candidate["policy"] = policy
            
        # 3. Duplicate Detection
        dup_result = duplicate_engine.detect(candidate, existing_memories)
        if dup_result:
            decision["action"] = dup_result["action"]
            decision["reason"] = dup_result["reason"]
            decision["existing_memory"] = dup_result["existing_memory"]
            decision["updates"] = dup_result["updates"]
            logger.info(f"[ReasoningEngine] Decision: {decision['action']} ({decision['reason']})")
            return decision
            
        # 4. Conflict Detection
        conflict_result = conflict_engine.detect(candidate, existing_memories)
        if conflict_result:
            decision["action"] = conflict_result["action"]
            decision["reason"] = conflict_result["reason"]
            decision["conflict_data"] = conflict_result["conflict_data"]
            logger.info(f"[ReasoningEngine] Decision: {decision['action']} ({decision['reason']})")
            return decision
            
        # 5. Merge Detection
        merge_result = merge_engine.detect_merge(candidate, existing_memories)
        if merge_result:
            decision["action"] = merge_result["action"]
            decision["reason"] = merge_result["reason"]
            decision["existing_memory"] = merge_result["existing_memory"]
            decision["updates"] = merge_result["updates"]
            logger.info(f"[ReasoningEngine] Decision: {decision['action']} ({decision['reason']})")
            return decision

        # 6. Trust Engine
        candidate["trust_score"] = trust_engine.calculate_score(candidate)

        logger.info(f"[ReasoningEngine] Final Decision: {decision['action']} ({decision['reason']})")
        return decision

reasoning_engine = ReasoningEngine()
