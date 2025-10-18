"""Retry utilities with exponential backoff."""

import asyncio
import functools
from typing import Callable, Optional, Tuple, Type
from .logger import logger


def retry_with_exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """Decorator for retrying async functions with exponential backoff.
    
    Implements retry logic with exponential backoff as specified in FR-031a:
    - Retry sequence: 1s, 2s, 4s, 8s, 16s (up to max_retries)
    - Configurable max retries (default: 5)
    - Configurable base delay (default: 1.0 second)
    
    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry
        
    Returns:
        Decorated async function with retry logic
        
    Examples:
        >>> @retry_with_exponential_backoff(max_retries=3)
        ... async def fetch_data():
        ...     # Your async function here
        ...     pass
        
        >>> @retry_with_exponential_backoff(
        ...     max_retries=5,
        ...     exceptions=(httpx.HTTPError, ConnectionError)
        ... )
        ... async def api_call():
        ...     # API call that might fail
        ...     pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    # If this was the last attempt, raise the exception
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries",
                            extra={
                                "event_type": "retry_exhausted",
                                "metadata": {
                                    "function": func.__name__,
                                    "attempts": max_retries + 1,
                                    "error": str(e)
                                }
                            }
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    logger.warning(
                        f"Function {func.__name__} failed, retrying in {delay}s (attempt {attempt + 1}/{max_retries})",
                        extra={
                            "event_type": "retry_attempt",
                            "metadata": {
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "delay": delay,
                                "error": str(e)
                            }
                        }
                    )
                    
                    # Call optional retry callback
                    if on_retry:
                        try:
                            await on_retry(attempt, delay, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Retry callback failed: {callback_error}",
                                extra={"event_type": "retry_callback_error"}
                            )
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        timeout: Optional[float] = None
    ):
        """Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay between retries
            timeout: Optional timeout for the entire operation
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.timeout = timeout


async def retry_async(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
):
    """Retry an async function with the given configuration.
    
    Args:
        func: Async function to retry
        config: RetryConfig instance
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of the function call
        
    Raises:
        Last exception if all retries fail
        asyncio.TimeoutError: If timeout is exceeded
    """
    async def _execute():
        for attempt in range(config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == config.max_retries:
                    raise
                
                delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                logger.warning(
                    f"Retry attempt {attempt + 1}/{config.max_retries} after {delay}s",
                    extra={
                        "event_type": "retry",
                        "metadata": {"attempt": attempt + 1, "delay": delay}
                    }
                )
                await asyncio.sleep(delay)
    
    if config.timeout:
        return await asyncio.wait_for(_execute(), timeout=config.timeout)
    else:
        return await _execute()


# Predefined retry configurations for different services
GEMINI_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=1.0,
    max_delay=16.0,
    timeout=30.0  # FR-031b: 30 seconds for Gemini API
)

EVOLUTION_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=1.0,
    max_delay=16.0,
    timeout=10.0  # FR-031b: 10 seconds for Evolution API
)

SUPABASE_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=1.0,
    max_delay=16.0,
    timeout=5.0  # FR-031b: 5 seconds for Supabase queries
)

# Alias for convenience
with_retry = retry_with_exponential_backoff
