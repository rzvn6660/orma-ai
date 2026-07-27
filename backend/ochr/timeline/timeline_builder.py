from typing import List
from ochr.context.context_models import UnifiedContext
from .timeline_models import TimelineEvent
from .event_normalizer import EventNormalizer

class TimelineBuilder:
    def __init__(self):
        self.normalizer = EventNormalizer()

    def _deduplicate(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        seen = set()
        unique = []
        for e in events:
            # Simple dedup strategy based on id, timestamp, and title
            key = f"{e.id}-{e.timestamp}-{e.title}"
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def build_events(self, context: UnifiedContext) -> List[TimelineEvent]:
        raw_events = []
        
        for item in context.medications:
            raw_events.append(self.normalizer.normalize(item, item.get("_source", "medication_retriever")))
            
        for item in context.health_records:
            raw_events.append(self.normalizer.normalize(item, item.get("_source", "health_record_retriever")))
            
        for item in context.planner:
            raw_events.append(self.normalizer.normalize(item, item.get("_source", "planner_retriever")))
            
        for item in context.memories:
            raw_events.append(self.normalizer.normalize(item, item.get("_source", "memory_retriever")))
            
        # Deduplicate
        unique_events = self._deduplicate(raw_events)
        
        # Sort chronologically
        unique_events.sort(key=lambda x: x.timestamp)
        
        return unique_events
