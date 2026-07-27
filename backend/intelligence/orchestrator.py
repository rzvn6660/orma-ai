import logging
from sqlalchemy.orm import Session
from intelligence.conversation_manager import conversation_manager
from intelligence.intent_detector import intent_detector
from intelligence.entity_extractor import entity_extractor
from intelligence.safety_validator import safety_validator
from intelligence.task_planner import task_planner
from intelligence.response_coordinator import response_coordinator
from memory.memory_retriever import memory_retriever
from memory.context_builder import context_builder
from memory.memory_service import ocme_service
from context.context_resolver import ContextResolver
from models.user import User
from intelligence.agent_router import agent_router

logger = logging.getLogger(__name__)

class IntelligenceOrchestrator:
    """
    The main intelligence layer that orchestrates processing of user requests.
    Sits above the existing ORMA AI modules.
    """
    def __init__(self):
        pass

    async def process_request(self, text: str, user_id: str, db: Session, language: str = "en", active_subject_id: str = None) -> str:
        """
        Main pipeline: Intent -> Entity -> Memory -> Route -> Respond
        """
        logger.info(f"--- [Orchestrator] Processing request for user {user_id} ---")
        
        # 1. Maintain conversation session
        conversation_manager.add_message(user_id, "user", text)
        current_task = conversation_manager.get_current_task(user_id)
        
        # 1.5 CMCE Context Resolution Engine
        uid_int = int(user_id) if str(user_id).isdigit() else 1
        user_obj = db.query(User).filter(User.id == uid_int).first()
        if not user_obj:
            # Fallback mock user if not found in db
            class MockUser:
                id = uid_int
                name = "User"
                role = "elderly"
            user_obj = MockUser()
            
        ctx = ContextResolver.resolve(user_obj, text, db, active_subject_id=active_subject_id)
        
        logger.info(f"[Orchestrator] CMCE Context: Actor={ctx.actor_name}({ctx.actor_role}), Subject={ctx.subject_name}({ctx.subject_role})")
        
        # Clarification Engine
        if ctx.requires_clarification:
            logger.info("[Orchestrator] CMCE requires clarification.")
            conversation_manager.add_message(user_id, "assistant", ctx.clarification_message)
            return ctx.clarification_message

        
        # 2. Detect Intent
        if not current_task:
            intent, confidence = await intent_detector.detect_intent(text)
            logger.info(f"[Orchestrator] Intent detected: {intent} (Confidence: {confidence})")
            if intent not in ["GeneralChat", "Unknown"]:
                conversation_manager.set_current_task(user_id, intent)
        else:
            intent = current_task
            logger.info(f"[Orchestrator] Continuing existing task: {intent}")

        # 3. Extract Entities
        new_entities = await entity_extractor.extract(text, intent)
        conversation_manager.save_entities(user_id, new_entities)
        all_entities = conversation_manager.get_entities(user_id)
        logger.info(f"[Orchestrator] Entities extracted and merged: {all_entities}")

        # 3.5. OCME Memory Retrieval & Processing
        # Memory ownership logic applied using Subject
        subject_uid = int(ctx.subject_id) if str(ctx.subject_id).isdigit() else uid_int
        
        # Process turn to extract and save NEW memories passively
        # (This also checks for conflicts, but we won't interrupt the main flow for this sprint unless handled specially)
        memory_candidates = await ocme_service.process_conversation_turn(db, subject_uid, text, "", intent)
        conflict = next((c.get("conflict_data") for c in memory_candidates if c.get("conflict_data")), None)

        # Retrieve relevant context for the current turn using Subject
        retrieved_memories = memory_retriever.retrieve(db, subject_uid, intent)
        
        # Context enrichment with CMCE
        cmce_context_header = f"CONVERSATION CONTEXT:\nActor Speaking: {ctx.actor_name} ({ctx.actor_role})\nConversation Subject: {ctx.subject_name} ({ctx.subject_role})\n\n"
        memory_context = cmce_context_header + context_builder.build_context_string(retrieved_memories)

        # 4. Task Planner & Validation
        is_ready, task_missing = task_planner.evaluate_task_readiness(intent, all_entities)
        decision, reason, val_missing = safety_validator.validate(intent, all_entities)
        
        # Combine missing fields from both planner and validator
        missing_fields = list(set(task_missing + val_missing))
        
        if conflict:
            decision = "Conflict"
            reason = "Memory conflict detected."
            
        elif not is_ready and decision == "Continue":
            decision = "Clarify"
            reason = f"Task Planner requires more information: {', '.join(missing_fields)}"

        logger.info(f"[Orchestrator] Safety & Planning decision: {decision} | Reason: {reason}")
        
        route_result = None
        
        # 5. Route to Agents (only if Continue)
        if decision == "Continue":
            logger.info(f"[Orchestrator] Selecting Agent for intent: {intent}")
            route_result = await agent_router.route(intent, all_entities, user_id, db)
            
            # Log execution result with explainability
            if route_result and "explainability" in route_result:
                explain = route_result["explainability"]
                logger.info(f"[Orchestrator] Agent Execution Result: {explain.get('result')} | Reason: {explain.get('reason')} | Confidence: {explain.get('confidence')}")
                if explain.get("memory_updates"):
                    logger.info(f"[Orchestrator] Agent Memory Updates: {explain.get('memory_updates')}")
                
            # Task complete, clear context
            conversation_manager.clear_current_task(user_id)
        elif decision != "Conflict":
            # Task incomplete, track missing fields
            logger.info(f"[Orchestrator] Task incomplete. Missing fields tracked: {missing_fields}")
            conversation_manager.update_missing_info(user_id, missing_fields)
            
        # 6. Coordinate Response
        final_response = await response_coordinator.generate_response(
            text=text,
            intent=intent,
            validation_decision=decision,
            validation_reason=reason,
            missing_fields=missing_fields,
            route_result=route_result,
            language=language,
            memory_context=memory_context,
            conflict=conflict
        )
        
        logger.info(f"[Orchestrator] Final response generated: {final_response}")
        conversation_manager.add_message(user_id, "assistant", final_response)
        
        logger.info(f"--- [Orchestrator] Processing complete ---")
        return final_response

orchestrator = IntelligenceOrchestrator()
