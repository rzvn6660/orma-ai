import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from memory.memory_models import OCMEMemoryCreate, OCMEMemory
from memory.memory_candidate_extractor import memory_candidate_extractor
from memory.reasoning.reasoning_engine import reasoning_engine
from memory.memory_store import memory_store

logger = logging.getLogger(__name__)

class OCMEService:
    """
    The core service for the ORMA Cognitive Memory Engine.
    Handles the orchestration of memory extraction, validation, and storage.
    """
    def __init__(self):
        pass

    async def process_conversation_turn(self, db: Session, user_id: int, user_text: str, ai_response: str, context_intent: str) -> List[Dict[str, Any]]:
        """
        Main entry point for analyzing a conversation turn and extracting memories.
        """
        logger.info(f"--- [OCME] Processing turn for user {user_id} ---")
        
        # 1. Extraction (which internally classifies, scores importance and confidence)
        candidates = await memory_candidate_extractor.extract_candidates(user_text, ai_response, context_intent)
        
        if not candidates:
            logger.info("[OCME] No memory candidates extracted.")
            return []
            
        existing_memories = memory_store.get_all_memories(db, user_id)
        saved_memories = []
        
        # 2. Reasoning Layer Evaluation
        for candidate in candidates:
            decision = reasoning_engine.evaluate(candidate, existing_memories)
            action = decision.get("action")
            candidate["reasoning_action"] = action
            candidate["reasoning_reason"] = decision.get("reason")
            
            if action == "IGNORE":
                continue
                
            elif action == "ASK_USER":
                candidate["conflict_data"] = decision.get("conflict_data")
                candidate["recommendation"] = "ASK_CONFIRMATION"
                
            elif action == "SAVE":
                # Apply policy expiration if any
                policy = candidate.get("policy", {})
                expires_days = policy.get("expires_in_days")
                
                from datetime import datetime, timedelta
                expires_at = None
                if expires_days:
                    expires_at = datetime.utcnow() + timedelta(days=expires_days)
                    
                mem_data = OCMEMemoryCreate(
                    category=candidate["category"],
                    title=candidate["title"],
                    value=candidate["value"],
                    importance=candidate["importance"],
                    confidence=candidate["confidence"],
                    source=candidate["source"],
                    trust_score=candidate.get("trust_score", 50.0),
                    expires_at=expires_at
                )
                saved = memory_store.save_memory(db, user_id, mem_data)
                
                # Audit Trail
                from memory.reasoning.audit_engine import audit_engine
                audit_engine.log_action(db, saved.id, "created", "AI", decision.get("reason"))
                
                candidate["saved_id"] = saved.id
                saved_memories.append(candidate)
                
            elif action in ["UPDATE", "MERGE"]:
                mem = decision["existing_memory"]
                updates = decision.get("updates", {})
                
                for key, val in updates.items():
                    setattr(mem, key, val)
                
                db.commit()
                
                # Audit Trail
                from memory.reasoning.audit_engine import audit_engine
                audit_engine.log_action(db, mem.id, action.lower(), "AI", decision.get("reason"))
                
                candidate["saved_id"] = mem.id
                saved_memories.append(candidate)
                
        logger.info(f"--- [OCME] Turn processing complete. Saved/Updated/Merged {len(saved_memories)} memories ---")
        return candidates

ocme_service = OCMEService()
