import asyncio
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class RetryManager:
    """
    Retries recoverable failures with exponential backoff.
    """
    
    async def execute_with_retry(self, func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
        retries = 0
        backoff = 1 # seconds
        
        while retries < max_retries:
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                retries += 1
                logger.warning(f"[RetryManager] Step failed: {str(e)}. Retry {retries}/{max_retries} in {backoff}s...")
                if retries >= max_retries:
                    logger.error(f"[RetryManager] Max retries reached.")
                    raise e
                await asyncio.sleep(backoff)
                backoff *= 2 # Exponential backoff

retry_manager = RetryManager()
