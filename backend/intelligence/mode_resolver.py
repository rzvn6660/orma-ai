import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExecutionMode:
    DIRECT = "DIRECT"
    TOOL_ONLY = "TOOL_ONLY"
    LLM_WITH_TOOL = "LLM_WITH_TOOL"
    CONVERSATIONAL = "CONVERSATIONAL"
    SAFETY_DETERMINISTIC = "SAFETY_DETERMINISTIC"
    RAG_WITH_LLM = "RAG_WITH_LLM"
    FALLBACK = "FALLBACK"

class ModeResolver:
    """
    Resolves the exact execution mode for ORMA AI requests (Part 1, Requirement #2).
    Distinguishes DIRECT, TOOL_ONLY, LLM_WITH_TOOL, CONVERSATIONAL, SAFETY_DETERMINISTIC, RAG_WITH_LLM, and FALLBACK.
    """
    
    @staticmethod
    def resolve_execution_mode(
        intent: str, 
        text: str, 
        llm_available: bool,
        has_next_med_query: bool = False
    ) -> Dict[str, Any]:
        
        low = text.lower().strip()

        # 1. SAFETY_DETERMINISTIC: Emergency, SOS, Pain, Caregiver Call, Medication Mutation
        if intent == "Emergency" or any(w in low for w in ["call my caregiver", "call caregiver", "ambulance", "hospital", "fell and", "i fell"]):
            return {
                "mode": ExecutionMode.SAFETY_DETERMINISTIC,
                "llm_required": False,
                "tool_required": True,
                "tool": "emergency_service",
                "reason": "Safety-critical emergency operation requires deterministic execution."
            }

        # 2. TOOL_ONLY: Authoritative direct lookup queries (e.g. "What is my next medicine?", "What medicine do I take tonight?")
        has_schedule_word = any(w in low for w in ["next", "tonight", "today", "morning", "afternoon", "evening", "night", "now", "അടുത്ത", "अगली", "التالي"])
        has_med_word = any(w in low for w in ["medicine", "medicines", "dose", "tablet", "tablets", "scheduled", "മരുന്ന്", "ദവാ", "दवा"])
        is_simple_next_med = has_next_med_query or (has_schedule_word and has_med_word and any(q in low for q in ["what", "which", "when", "next"])) or any(p in low for p in [
            "what medicine do i take", "what medicines do i take", "what medicine do i take tonight", "what medicine do i take today",
            "what is my next medicine", "what's my next medicine", "next medicine", "what is next", "next dose"
        ])
        if is_simple_next_med:
            return {
                "mode": ExecutionMode.TOOL_ONLY,
                "llm_required": False,
                "tool_required": True,
                "tool": "medication_schedule",
                "reason": "Authoritative database lookup answers query directly without LLM."
            }

        # 3. DIRECT: Simple direct deterministic responses requiring neither LLM nor database
        if low in ["hello", "hi", "hey"] and len(low.split()) == 1 and not llm_available:
            return {
                "mode": ExecutionMode.DIRECT,
                "llm_required": False,
                "tool_required": False,
                "tool": "none",
                "reason": "Direct deterministic response without LLM or external data."
            }

        # 4. RAG_WITH_LLM: Questions about uploaded documents, discharge summaries, medical reports, doctor's notes
        rag_intents = ["DOCUMENT_QUERY", "HealthRecordDocument", "RAG"]
        if intent in rag_intents:
            if llm_available:
                return {
                    "mode": ExecutionMode.RAG_WITH_LLM,
                    "llm_required": True,
                    "tool_required": True,
                    "tool": "rag_document_retriever",
                    "reason": "Document knowledge query requires RAG semantic retrieval and LLM synthesis."
                }
            else:
                return {
                    "mode": ExecutionMode.FALLBACK,
                    "llm_required": True,
                    "tool_required": True,
                    "tool": "rag_document_retriever",
                    "reason": "LLM provider unavailable for document synthesis. Graceful fallback active."
                }

        # Determine baseline execution mode assuming LLM is available
        med_tool_intents = ["MEDICATION_SCHEDULE", "MEDICATION_STATUS", "MEDICATION_SUMMARY", "MEDICATION_INFORMATION", "Medicine"]
        cal_tool_intents = ["Appointment", "Calendar"]

        if intent in med_tool_intents or intent in cal_tool_intents:
            baseline_mode = ExecutionMode.LLM_WITH_TOOL
            if intent == "MEDICATION_SCHEDULE":
                tool_name = "medication_schedule"
            elif intent == "MEDICATION_STATUS":
                tool_name = "medication_status"
            elif intent == "MEDICATION_SUMMARY":
                tool_name = "daily_adherence"
            elif intent in cal_tool_intents:
                tool_name = "calendar_events"
            else:
                tool_name = "medication_status"
            tool_req = True
            reason_str = f"Natural language request requires '{tool_name}' tool data and LLM synthesis."
        elif intent in ["GREETING", "GENERAL_CONVERSATION", "Memory"]:
            baseline_mode = ExecutionMode.CONVERSATIONAL
            tool_name = "none"
            tool_req = False
            reason_str = "Open-ended natural conversation without database query."
        else:
            baseline_mode = ExecutionMode.CONVERSATIONAL
            tool_name = "none"
            tool_req = False
            reason_str = "Default conversational mode."

        # 5. FALLBACK: When LLM is required but unavailable
        if not llm_available and baseline_mode in [ExecutionMode.LLM_WITH_TOOL, ExecutionMode.CONVERSATIONAL]:
            return {
                "mode": ExecutionMode.FALLBACK,
                "llm_required": True,
                "tool_required": tool_req,
                "tool": tool_name,
                "reason": "LLM provider unavailable. Graceful tool/deterministic fallback active."
            }

        return {
            "mode": baseline_mode,
            "llm_required": True,
            "tool_required": tool_req,
            "tool": tool_name,
            "reason": reason_str
        }

mode_resolver = ModeResolver()
