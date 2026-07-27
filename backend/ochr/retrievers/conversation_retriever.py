from typing import Any, Dict
from .retriever_base import BaseRetriever
from intelligence.conversation_manager import conversation_manager
from ai.conversation import conversation_service

class ConversationRetriever(BaseRetriever):
    """Retrieves previous conversations from in-memory session managers."""
    
    def retrieve(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = query_context.get("user_id", "default_user")
        
        # Get from ConversationManager (task states)
        history_cm = conversation_manager.get_history(user_id)
        
        # Get from SessionMemoryManager (short term chat context)
        # Note: direct access to sessions dict
        history_ai = conversation_service.session_manager.sessions.get(user_id, [])
        
        # We consolidate them as previous conversations
        merged_history = []
        for msg in history_ai:
            merged_history.append({
                "role": msg.get("role"),
                "content": msg.get("content")
            })
            
        # Simplistic example classification (as there's no persistent DB table for granular topics)
        doctor_discussions = [m for m in merged_history if m["content"] and "doctor" in m["content"].lower()]
        
        return {
            "previous_conversations": merged_history,
            "doctor_discussions": doctor_discussions,
            "recent_ai_interactions": merged_history[-5:] if merged_history else []
        }
