from typing import Dict, List, Any
from .context_models import UnifiedContext

class ContextFusionEngine:
    """
    Fuses structured output from multiple retrievers into a single UnifiedContext object.
    Handles deduplication, source tracking, and schema normalization.
    """
    
    def _normalize_item(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Adds source tracking and standardizes fields across different schemas."""
        normalized = dict(item)
        normalized["_source"] = source
        # Optionally add a timestamp of fusion if not present
        return normalized
        
    def _is_duplicate(self, existing: List[Dict[str, Any]], new_item: Dict[str, Any], unique_keys: List[str]) -> bool:
        """Simple deduplication logic based on unique identifier keys."""
        for existing_item in existing:
            # Check if all unique_keys match and none are None in the new item
            if all(existing_item.get(k) == new_item.get(k) and new_item.get(k) is not None for k in unique_keys):
                return True
        return False

    def fuse(self, retrieved_data: Dict[str, Dict[str, Any]]) -> UnifiedContext:
        """
        Fuses data from multiple retrievers.
        Args:
            retrieved_data: dictionary mapping retriever_name -> retriever_output_dict
        """
        unified = UnifiedContext()
        
        for source_name, data in retrieved_data.items():
            if not data:
                continue
            
            added_any = False
            
            # Handle medication_retriever output
            if source_name == "medication_retriever":
                for cat in ["pending_medicines", "taken_medicines", "missed_medicines"]:
                    for item in data.get(cat, []):
                        norm = self._normalize_item(item, source_name)
                        norm["_medication_status"] = cat.split("_")[0]
                        # id and medicine_name make it unique
                        if not self._is_duplicate(unified.medications, norm, ["id", "medicine_name"]):
                            unified.medications.append(norm)
                            added_any = True

            # Handle planner_retriever output
            elif source_name == "planner_retriever":
                # If we process daily_planner we don't need to process the specific sub-lists 
                # because daily_planner contains all of them in our implementation.
                for item in data.get("daily_planner", []):
                    norm = self._normalize_item(item, source_name)
                    if not self._is_duplicate(unified.planner, norm, ["id", "title"]):
                        unified.planner.append(norm)
                        added_any = True
                
                # In case a retriever only provides sub-lists
                if not data.get("daily_planner"):
                    for cat in ["appointments", "exercise_plans", "vaccinations", "blood_tests"]:
                        for item in data.get(cat, []):
                            norm = self._normalize_item(item, source_name)
                            if not self._is_duplicate(unified.planner, norm, ["id", "title"]):
                                unified.planner.append(norm)
                                added_any = True

            # Handle health_record_retriever output
            elif source_name == "health_record_retriever":
                for cat in ["blood_pressure", "blood_sugar", "weight", "reports", "doctor_visits"]:
                    for item in data.get(cat, []):
                        norm = self._normalize_item(item, source_name)
                        if not self._is_duplicate(unified.health_records, norm, ["id", "type", "date"]):
                            unified.health_records.append(norm)
                            added_any = True
            
            # Handle memory_retriever output
            elif source_name == "memory_retriever":
                for cat in ["stored_ai_memories", "important_events", "user_preferences"]:
                    for item in data.get(cat, []):
                        norm = self._normalize_item(item, source_name)
                        if not self._is_duplicate(unified.memories, norm, ["id", "content"]):
                            unified.memories.append(norm)
                            added_any = True
                            
            # Handle conversation_retriever output
            elif source_name == "conversation_retriever":
                for item in data.get("previous_conversations", []):
                    norm = self._normalize_item(item, source_name)
                    if not self._is_duplicate(unified.conversations, norm, ["role", "content"]):
                        unified.conversations.append(norm)
                        added_any = True

            if added_any and source_name not in unified.retrieval_sources:
                unified.retrieval_sources.append(source_name)
                        
        return unified
