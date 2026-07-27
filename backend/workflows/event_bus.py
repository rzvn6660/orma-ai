import asyncio
import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger(__name__)

class EventBus:
    """
    Internal publish/subscribe event system.
    Modules should subscribe to relevant events rather than calling each other directly.
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, callback: Callable):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
        logger.info(f"[EventBus] Subscribed to {event_name}")

    async def publish(self, event_name: str, payload: Any):
        logger.info(f"[EventBus] Publishing event: {event_name}")
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                try:
                    # Run callback asynchronously without blocking
                    asyncio.create_task(callback(payload))
                except Exception as e:
                    logger.error(f"[EventBus] Error in subscriber for {event_name}: {str(e)}")
        else:
            logger.info(f"[EventBus] No subscribers for event: {event_name}")

event_bus = EventBus()
