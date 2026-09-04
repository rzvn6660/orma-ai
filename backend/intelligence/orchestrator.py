import logging
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from intelligence.conversation_manager import conversation_manager
from intelligence.intent_detector import intent_detector
from intelligence.entity_extractor import entity_extractor
from intelligence.safety_validator import safety_validator
from intelligence.task_planner import task_planner
from intelligence.response_coordinator import response_coordinator
from intelligence.tools import healthcare_tools
from intelligence.mode_resolver import mode_resolver, ExecutionMode
from memory.memory_retriever import memory_retriever
from memory.context_builder import context_builder
from memory.memory_service import ocme_service
from context.context_resolver import ContextResolver
from models.user import User
from intelligence.agent_router import agent_router
from llm.ai_manager import ai_manager
from rag.rag_service import rag_service
from rag.grounded_synthesizer import get_empty_retrieval_response
from intelligence.conversational_reference_resolver import conversational_reference_resolver

logger = logging.getLogger(__name__)

class IntelligenceOrchestrator:
    """
    The central intelligence layer for ORMA AI's Conversational Brain.
    Integrates Gemini primary + Groq failover, Database-first facts, provider health checks,
    execution mode routing, controlled tool calls, multi-turn context, and telemetry.
    """
    def __init__(self):
        pass

    async def process_request(self, text: str, user_id: str, db: Session, language: str = "en", active_subject_id: str = None) -> str:
        res = await self.process_request_detailed(text, user_id, db, language=language, active_subject_id=active_subject_id)
        return res["response"]

    async def process_request_detailed(self, text: str, user_id: str, db: Session, language: str = "en", active_subject_id: str = None) -> Dict[str, Any]:
        """
        Main Conversational Brain Pipeline with High-Precision Telemetry:
        Captures T0..T10 timestamps for latency forensic analysis.
        """
        t0 = time.perf_counter()
        req_id = str(uuid.uuid4())[:8]
        logger.info(f"--- [ORMA BRAIN req_{req_id}] Processing request for user {user_id} ---")

        # T1: Transcription starts | T2: Transcription completed (STT)
        t1 = time.perf_counter()
        t2 = t1 

        # 1. Non-blocking LLM Capability & Health Check
        llm_health = await ai_manager.check_health()
        
        # 2. Maintain Conversation History & Multi-turn Context
        history = list(conversation_manager.get_history(user_id))
        conversation_manager.add_message(user_id, "user", text)

        # 2b. Conversational Reference & Follow-Up Resolution (Phase A)
        followup_res = conversational_reference_resolver.resolve(
            text=text,
            user_id=user_id,
            db=db,
            history=history,
            language=language
        )
        if followup_res.get("is_followup") and followup_res.get("direct_response"):
            response_text = followup_res["direct_response"]
            conversation_manager.add_message(user_id, "assistant", response_text)
            if followup_res.get("referenced_medications"):
                conversation_manager.save_interaction_context(user_id, {
                    "intent": followup_res.get("intent", "FOLLOW_UP"),
                    "medications": followup_res["referenced_medications"],
                    "response_text": response_text
                })
            t3 = time.perf_counter()
            t4 = t3
            t5 = t4
            t6 = t5
            t7 = t6
            t8 = time.perf_counter()
            t9 = t8
            t10 = t9
            return {
                "response": response_text,
                "intent": followup_res.get("intent", "FOLLOW_UP"),
                "execution_mode": ExecutionMode.TOOL_ONLY,
                "llm_called": False,
                "llm_required": False,
                "tool_required": True,
                "tool_name": "conversational_reference_resolver",
                "language": language,
                "gen_meta": {"resolver": "conversational_reference"},
                "timestamps": {
                    "T0": t0, "T1": t1, "T2": t2, "T3": t3, "T4": t4,
                    "T5": t5, "T6": t6, "T7": t7, "T8": t8, "T9": t9, "T10": t10
                }
            }

        # 3. Context Resolution
        user_obj = db.query(User).filter(User.id == str(user_id)).first()
        if not user_obj and str(user_id).isdigit():
            user_obj = db.query(User).filter(User.id == int(user_id)).first()
        if not user_obj:
            class MockUser:
                id = str(user_id)
                name = "User"
                role = "elderly"
            user_obj = MockUser()
            
        ctx = ContextResolver.resolve(user_obj, text, db, active_subject_id=active_subject_id)
        
        if ctx.requires_clarification:
            logger.info("[ORMA BRAIN] CMCE requires clarification.")
            conversation_manager.add_message(user_id, "assistant", ctx.clarification_message)
            t3 = time.perf_counter()
            t4 = t3
            t5 = t4
            t6 = t5
            t7 = t6
            t8 = t7
            t9 = t8
            t10 = t9
            return {
                "response": ctx.clarification_message,
                "intent": "Clarification",
                "execution_mode": "CLARIFICATION",
                "llm_called": False,
                "llm_required": False,
                "tool_required": False,
                "tool_name": "none",
                "language": language,
                "gen_meta": {},
                "timestamps": {"T0": t0, "T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5, "T6": t6, "T7": t7, "T8": t8, "T9": t9, "T10": t10}
            }

        low_text = text.lower()

        # 4. Semantic NLU Intent & Time-Period Detection
        intent, confidence, meta = await intent_detector.detect_intent_with_metadata(text)
        time_period = meta.get("time_period", "today")
        t3 = time.perf_counter() # Language & Intent detection completed

        is_next_med_query = any(p in low_text for p in ["next medicine", "next dose", "upcoming medicine", "upcoming", "what is my next medicine", "what's my next medicine", "next scheduled medicine"])

        # 5. Resolve Execution Mode
        mode_data = mode_resolver.resolve_execution_mode(
            intent=intent,
            text=text,
            llm_available=llm_health["available"],
            has_next_med_query=is_next_med_query
        )
        
        exec_mode = mode_data["mode"]
        llm_required = mode_data["llm_required"]
        tool_required = mode_data["tool_required"]
        selected_tool_name = mode_data["tool"]
        t4 = time.perf_counter() # Brain routing completed

        # 6. Extract Entities
        new_entities = await entity_extractor.extract(text, intent)
        conversation_manager.save_entities(user_id, new_entities)
        all_entities = conversation_manager.get_entities(user_id)

        # 7. Memory Retrieval (Fast SQL DB lookup without LLM candidate extraction during pre-synthesis tool phase)
        subject_uid = ctx.subject_id or user_id
        conflict = None
        retrieved_memories = []

        try:
            retrieved_memories = memory_retriever.retrieve(db, subject_uid, intent)
        except Exception as mem_err:
            logger.warning(f"[ORMA BRAIN] OCME memory retrieval warning: {mem_err}")

        # 8. Controlled Tool Execution
        target_uid = str(ctx.subject_id) if ctx.subject_id else str(user_id)
        tool_start = time.time()
        tool_result = {}
        med_context_lines = []

        if tool_required:
            if selected_tool_name == "medication_schedule":
                tool_result = healthcare_tools.get_medication_schedule(db, target_uid, time_period=time_period)
                meds = tool_result.get("medications", [])
                med_context_lines.append(f"\n[STRUCTURED MEDICATION SCHEDULE FOR TIME PERIOD: {time_period.upper()}]")
                if meds:
                    for m in meds:
                        stat = m.get('status', 'TAKEN' if m.get('taken') else 'PENDING')
                        med_context_lines.append(f"- {m['name']} ({m['dosage']}): Scheduled at {m['scheduled_time']} [Status: {stat}]")
                else:
                    med_context_lines.append(f"- No medicines scheduled for {time_period}.")

            elif selected_tool_name == "medication_status":
                tool_result = healthcare_tools.get_medication_status(db, target_uid, time_period=time_period)
                meds = tool_result.get("medications", [])
                med_context_lines.append(f"\n[STRUCTURED MEDICATION STATUS FOR TIME PERIOD: {time_period.upper()}]")
                if meds:
                    for m in meds:
                        med_context_lines.append(f"- {m['name']} ({m['dosage']}) scheduled at {m['scheduled_time']}: Status = {m['status']}")
                    med_context_lines.append(f"\nTime Period Summary: Total = {tool_result['total_count']}, Taken = {tool_result['taken_count']}, Pending = {tool_result['pending_count']}, All Taken = {tool_result['all_taken']}")
                else:
                    med_context_lines.append(f"- No medicines scheduled for {time_period}.")

            elif selected_tool_name == "daily_adherence":
                tool_result = healthcare_tools.get_daily_adherence(db, target_uid)
                med_context_lines.append(f"\n[DAILY MEDICATION ADHERENCE SUMMARY FOR TODAY]")
                med_context_lines.append(f"- Total Scheduled Today: {tool_result['total_scheduled']}")
                med_context_lines.append(f"- Taken Today: {tool_result['taken_count']}")
                med_context_lines.append(f"- Pending Today: {tool_result['pending_count']}")
                med_context_lines.append(f"- Adherence Percentage: {tool_result['adherence_percentage']}%")

            elif selected_tool_name == "calendar_events":
                tool_result = healthcare_tools.get_calendar_events(db, target_uid)
                events = tool_result.get("events", [])
                med_context_lines.append("\n[USER CALENDAR & APPOINTMENTS]")
                if events:
                    for e in events:
                        loc = f" at {e['location']}" if e.get('location') else ""
                        med_context_lines.append(f"- {e['title']} ({e['type']}) on {e['date']} at {e['time']}{loc}")
                else:
                    med_context_lines.append("- No calendar events found.")

            elif selected_tool_name == "rag_document_retriever":
                chunks, total_docs, ret_lat = rag_service.retrieve_context(db, target_uid, text)
                grounded_str = rag_service.synthesizer.build_grounded_context(chunks)
                med_context_lines.append(grounded_str if grounded_str else "\n[NO MATCHING USER DOCUMENTS FOUND]")
        else:
            med_context_lines.append("\n[NO EXTERNAL DATABASE RECORDS REQUIRED FOR THIS QUERY]")

        t5 = time.perf_counter() # Database / tool lookup completed

        # Multi-Turn History String for Coreference
        history_lines = []
        if history:
            history_lines.append("\nRECENT CONVERSATION HISTORY:")
            for turn in history[-4:]:
                role_label = "User" if turn["role"] == "user" else "Orma"
                history_lines.append(f"{role_label}: {turn['content']}")

        cmce_context_header = f"CONVERSATION CONTEXT:\nActor Speaking: {ctx.actor_name} ({ctx.actor_role})\nConversation Subject: {ctx.subject_name} ({ctx.subject_role})\n"
        memory_context = cmce_context_header + "\n".join(med_context_lines) + "\n" + "\n".join(history_lines) + "\n\n" + context_builder.build_context_string(retrieved_memories)

        # 9. Mode-Specific Execution Branching
        llm_called = False
        gen_meta = {}

        if exec_mode == ExecutionMode.SAFETY_DETERMINISTIC:
            logger.info(f"[ORMA BRAIN req_{req_id}] Executing SAFETY_DETERMINISTIC route for intent '{intent}'")
            await agent_router.route(intent, all_entities, user_id, db, raw_text=text)
            if intent == "Emergency":
                response_text = "I have alerted your caregiver and family immediately. Help is on the way."
            else:
                response_text = "Action executed safely through backend security service."
            conversation_manager.add_message(user_id, "assistant", response_text)
            t6 = t5
            t7 = t6
            t8 = time.perf_counter()

        elif exec_mode == ExecutionMode.TOOL_ONLY:
            logger.info(f"[ORMA BRAIN req_{req_id}] Executing TOOL_ONLY direct database response for query '{text}'")
            if is_next_med_query or any(w in low_text for w in ["next", "upcoming", "അടുത്ത", "अगली", "التالي"]):
                next_info = healthcare_tools.get_next_medication(db, target_uid, query_text=text, language=language)
                response_text = next_info["response_text"]
                if next_info.get("medication"):
                    conversation_manager.save_interaction_context(user_id, {
                        "intent": "MEDICATION_SCHEDULE",
                        "tool": "next_medication",
                        "medications": [next_info["medication"]],
                        "response_text": response_text
                    })
            else:
                meds = tool_result.get("medications", [])
                pending_meds = [m for m in meds if not m.get("taken")]
                if pending_meds:
                    next_m = pending_meds[0]
                    response_text = f"Your scheduled medicine for {time_period} is {next_m['name']} ({next_m['dosage']}) scheduled for {next_m['scheduled_time']}."
                elif meds:
                    response_text = f"All scheduled medicines for {time_period} have already been taken."
                else:
                    response_text = f"You have no medicines scheduled for {time_period}."
                if meds:
                    conversation_manager.save_interaction_context(user_id, {
                        "intent": "MEDICATION_SCHEDULE",
                        "tool": selected_tool_name or "medication_schedule",
                        "medications": meds,
                        "response_text": response_text
                    })
            conversation_manager.add_message(user_id, "assistant", response_text)
            t6 = t5
            t7 = t6
            t8 = time.perf_counter()

        elif exec_mode == ExecutionMode.DIRECT:
            logger.info(f"[ORMA BRAIN req_{req_id}] Executing DIRECT acknowledgment for text '{text}'")
            response_text = "Hello! I am Orma, your healthcare companion. How can I help you today?"
            conversation_manager.add_message(user_id, "assistant", response_text)
            t6 = t5
            t7 = t6
            t8 = time.perf_counter()

        elif exec_mode == ExecutionMode.RAG_WITH_LLM:
            logger.info(f"[ORMA BRAIN req_{req_id}] Executing RAG_WITH_LLM route for intent '{intent}'")
            t6 = time.perf_counter()
            rag_res = await rag_service.execute_rag_pipeline(
                db=db,
                user_id=target_uid,
                query=text,
                language=language,
                memory_context=memory_context,
                request_id=req_id
            )
            t7 = time.perf_counter()
            response_text = rag_res["response"]
            gen_meta = rag_res.get("gen_meta", {})
            llm_called = rag_res.get("telemetry", {}).get("llm_called", False)
            conversation_manager.add_message(user_id, "assistant", response_text)
            t8 = time.perf_counter()

        elif exec_mode == ExecutionMode.FALLBACK:
            logger.info(f"[ORMA BRAIN req_{req_id}] Executing FALLBACK mode because LLM provider is unavailable")
            if selected_tool_name == "medication_status":
                meds = tool_result.get("medications", [])
                pending = [m for m in meds if m.get("status") != "TAKEN"]
                if pending:
                    p_str = ", ".join(f"{m['name']} at {m['scheduled_time']}" for m in pending)
                    response_text = f"I can still check your schedule: You have pending medicines ({p_str})."
                else:
                    response_text = "I can still check your schedule: All scheduled medicines for this time are taken."
            elif selected_tool_name == "daily_adherence":
                response_text = f"I can still check your adherence: {tool_result.get('summary_text')}"
            elif selected_tool_name == "rag_document_retriever":
                chunks, _, _ = rag_service.retrieve_context(db, target_uid, text)
                if chunks:
                    response_text = f"According to your document ({chunks[0].document_title}): {chunks[0].text_content[:120]}... Please consult your doctor for detailed advice."
                else:
                    response_text = get_empty_retrieval_response(language)
            else:
                response_text = "I am currently running in offline tool mode. How can I assist you with your schedule?"
            conversation_manager.add_message(user_id, "assistant", response_text)
            t6 = t5
            t7 = t6
            t8 = time.perf_counter()

        else:
            # Modes = LLM_WITH_TOOL or CONVERSATIONAL
            is_ready, task_missing = task_planner.evaluate_task_readiness(intent, all_entities, raw_text=text)
            decision, reason, val_missing = safety_validator.validate(intent, all_entities, raw_text=text)
            missing_fields = list(set(task_missing + val_missing))
            
            if conflict:
                decision = "Conflict"
                reason = "Memory conflict detected."
            elif not is_ready and decision == "Continue":
                decision = "Clarify"
                reason = f"Task Planner requires more information: {', '.join(missing_fields)}"

            route_result = None
            if decision == "Continue":
                route_result = await agent_router.route(intent, all_entities, user_id, db, raw_text=text)
                conversation_manager.clear_current_task(user_id)

            t6 = time.perf_counter() # LLM request begins
            final_response, gen_meta = await response_coordinator.generate_response_with_meta(
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
            t7 = time.perf_counter() # LLM response received
            response_text = final_response
            conversation_manager.add_message(user_id, "assistant", response_text)
            t8 = time.perf_counter() # Response processing completed
            llm_called = gen_meta.get("llm_called", False)

            # Schedule memory extraction (await for explicit Memory intent, non-blocking background for general turns)
            if intent in ["Memory", "GENERAL_CONVERSATION", "Family", "Personal", "Reminder", "Appointment"]:
                try:
                    if intent == "Memory":
                        await self._async_extract_memory(str(target_uid), text, response_text, intent)
                    else:
                        asyncio.create_task(self._async_extract_memory(str(target_uid), text, response_text, intent))
                except Exception as e:
                    logger.warning(f"[ORMA BRAIN] Memory extraction scheduling warning: {e}")

        # 10. TTS Voice Resolution
        t9 = time.perf_counter() # TTS voice resolved
        t10 = t9 # TTS starts (marked NOT_TESTABLE in headless environment)

        total_latency_ms = int((t9 - t0) * 1000)
        tool_latency_ms = int((t5 - t4) * 1000)
        llm_lat_ms = gen_meta.get("latency_ms", int((t7 - t6) * 1000) if llm_called else 0)

        self._log_telemetry(
            req_id=req_id, user_id=user_id, language=language, intent=intent,
            exec_mode=exec_mode, llm_required=llm_required, llm_available=llm_health['available'],
            llm_called=llm_called, llm_provider=gen_meta.get("provider", "none"), llm_model=gen_meta.get("model", "none"),
            llm_latency_ms=llm_lat_ms, tool_required=tool_required, tool_used=selected_tool_name,
            tool_latency_ms=tool_latency_ms, fallback_used=gen_meta.get("fallback_used", False),
            fallback_from=gen_meta.get("fallback_from", None), response_mode=str(exec_mode).lower(), total_latency=total_latency_ms
        )

        return {
            "response": response_text,
            "intent": intent,
            "execution_mode": exec_mode,
            "llm_called": llm_called,
            "llm_required": llm_required,
            "tool_required": tool_required,
            "tool_name": selected_tool_name,
            "language": language,
            "gen_meta": gen_meta,
            "timestamps": {
                "T0": t0, "T1": t1, "T2": t2, "T3": t3, "T4": t4,
                "T5": t5, "T6": t6, "T7": t7, "T8": t8, "T9": t9, "T10": t10
            }
        }

    def _log_telemetry(self, req_id, user_id, language, intent, exec_mode, llm_required, llm_available, llm_called, llm_provider, llm_model, llm_latency_ms, tool_required, tool_used, tool_latency_ms, fallback_used, fallback_from, response_mode, total_latency):
        logger.info(f"""
========================================
[ORMA BRAIN TELEMETRY req_{req_id}]
request_id: {req_id}
user_id: {user_id}
language: {language}
intent: {intent}
execution_mode: {exec_mode}
llm_required: {llm_required}
llm_available: {llm_available}
llm_called: {llm_called}
llm_provider: {llm_provider}
llm_model: {llm_model}
llm_latency_ms: {llm_latency_ms}ms
tool_required: {tool_required}
tool_used: {tool_used}
tool_latency_ms: {tool_latency_ms}ms
fallback_used: {fallback_used}
fallback_from: {fallback_from}
response_mode: {response_mode}
total_latency_ms: {total_latency}ms
========================================
""")

    async def _async_extract_memory(self, user_id: str, user_text: str, response_text: str, intent: str):
        from database import SessionLocal
        from memory.memory_service import ocme_service
        db = SessionLocal()
        try:
            await ocme_service.process_conversation_turn(db, user_id, user_text, response_text, intent)
        except Exception as e:
            logger.warning(f"[ORMA BRAIN] Non-blocking background memory extraction warning: {e}")
        finally:
            db.close()

orchestrator = IntelligenceOrchestrator()
