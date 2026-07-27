from ochr.context.context_models import UnifiedContext
from .timeline_models import TimelineResult
from .timeline_builder import TimelineBuilder
from collections import Counter

class TimelineEngine:
    def __init__(self):
        self.builder = TimelineBuilder()

    def _generate_statistics(self, events) -> dict:
        counter = Counter([e.category for e in events])
        return dict(counter)

    def _generate_summary(self, events, stats: dict) -> str:
        if not events:
            return "No health events found in the timeline."
        
        return f"Timeline covers {len(events)} events across {len(stats)} categories."

    def generate(self, context: UnifiedContext) -> TimelineResult:
        events = self.builder.build_events(context)
        
        stats = self._generate_statistics(events)
        summary = self._generate_summary(events, stats)
        
        date_range = {}
        if events:
            date_range["start"] = events[0].timestamp
            date_range["end"] = events[-1].timestamp
            
        return TimelineResult(
            events=events,
            date_range=date_range,
            summary=summary,
            statistics=stats
        )
