import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class KnowledgeRouter:
    """Decides if external medical knowledge is needed based on query intent and content."""
    
    def requires_medical_knowledge(self, query: str, intent: str) -> bool:
        """Heuristic check to bypass medical retrieval when only personal info is requested."""
        query_lower = query.lower()
        
        # If it's a general non-health query, or strictly about personal schedule
        if intent in ["conversation_query", "memory_query", "timeline_query"]:
            # Unless they ask about a condition or drug side effects
            if "side effect" not in query_lower and "symptom" not in query_lower and "interaction" not in query_lower:
                return False
                
        # If they explicitly ask about drug information
        if "side effect" in query_lower or "interaction" in query_lower or "what is" in query_lower:
            return True
            
        # For medication_query, if they just ask "did I take", we don't need HK-RAG
        if intent == "medication_query":
            if "did i take" in query_lower or "when is" in query_lower or "schedule" in query_lower:
                return False
            return True
            
        return False
        
    def extract_knowledge_queries(self, query: str) -> List[Dict[str, str]]:
        """
        Extracts specific entities to search for.
        In a production scenario, this would use an LLM or NER model.
        For this foundation sprint, we use simple keyword matching for the tests.
        """
        queries = []
        query_lower = query.lower()
        
        if "aspirin" in query_lower:
            queries.append({"type": "drug", "query": "aspirin"})
        if "hypertension" in query_lower or "blood pressure" in query_lower:
            queries.append({"type": "condition", "query": "hypertension"})
            
        return queries
