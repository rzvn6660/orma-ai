import time
import logging
from typing import Callable, Any
from functools import wraps
from .exceptions import ProviderUnavailableError, RateLimitError, AuthenticationError, PromptTooLargeError

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: int = 3, initial_backoff: float = 1.0, backoff_factor: float = 2.0):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            backoff = initial_backoff
            
            while True:
                try:
                    return func(*args, **kwargs)
                except (ProviderUnavailableError, RateLimitError) as e:
                    if retries >= max_retries:
                        logger.error(f"Max retries ({max_retries}) reached. Failing.")
                        raise e
                    
                    logger.warning(f"Transient error: {str(e)}. Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    retries += 1
                    backoff *= backoff_factor
                except (AuthenticationError, PromptTooLargeError) as e:
                    # Do not retry on these
                    raise e
                except Exception as e:
                    # General exception
                    logger.error(f"Unexpected error in LLM provider: {str(e)}")
                    raise e
                    
        return wrapper
    return decorator
