import uuid
from typing import Dict, Any
from .timeline_models import TimelineEvent

class EventNormalizer:
    """Normalizes various structured dictionary events into TimelineEvents."""
    
    def _normalize_timestamp(self, item: Dict[str, Any]) -> str:
        # Tries to find the most appropriate timestamp field
        ts = item.get("timestamp") or item.get("date") or item.get("taken_at") or item.get("reminder_time") or item.get("time")
        
        # In a real app we would parse strings to ISO 8601 strings.
        # For this foundational sprint, we just return the raw string if it exists.
        return str(ts) if ts else "1970-01-01T00:00:00Z"
        
    def _determine_category_and_severity(self, item: Dict[str, Any], source: str) -> tuple[str, str]:
        # Basic heuristic mapping
        category = "general"
        severity = "low"
        
        source = source.lower()
        title = str(item.get("title", item.get("medicine_name", item.get("content", item.get("type", ""))))).lower()
        
        if "medication" in source:
            category = "medication"
            if item.get("_medication_status") == "missed":
                severity = "medium"
        elif "planner" in source:
            if "doctor" in title or "visit" in title or "appointment" in title:
                category = "doctor_visit"
            elif "exercise" in title:
                category = "exercise"
            else:
                category = "reminder"
        elif "health_record" in source:
            category = "lab_result"
            severity = "medium"
        elif "emergency" in source:
            category = "emergency"
            severity = "high"
        elif "memory" in source:
            category = "memory"
            
        return category, severity

    def normalize(self, item: Dict[str, Any], source: str) -> TimelineEvent:
        event_id = str(item.get("id", uuid.uuid4()))
        timestamp = self._normalize_timestamp(item)
        category, severity = self._determine_category_and_severity(item, source)
        
        title = item.get("title") or item.get("medicine_name") or item.get("type") or item.get("content", "Unknown Event")
        title = str(title)[:100]  # Truncate just in case
        
        return TimelineEvent(
            id=event_id,
            timestamp=timestamp,
            title=title.title() if isinstance(title, str) else str(title),
            category=category,
            severity=severity,
            source=source,
            metadata={k: v for k, v in item.items() if k not in ["id", "title", "medicine_name", "type", "content"]}
        )
