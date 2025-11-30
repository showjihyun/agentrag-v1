"""
Retry Pattern Implementation with Exponential Backoff

Provides robust retry mechanisms for handling transient failures:
- Exponential backoff with jitter
- Configurable retry conditions
- Integration with Circuit Breaker
- Async support
"""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Sequence, Type, TypeVar, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(str, Enum):
    """Retry backoff strategies."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"
    LINEAR = "linear"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
    jitter_factor: float = 0.5  # 0-1, amount of randomness
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()
    retry_on_result: Optional[Callable[[Any], bool]] = None
    on_retry: Optional[Callable[[int, Exception, float], None]] = None


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """
    Calculate delay before next retry attempt.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    if config.strategy == RetryStrategy.FIXED:
        delay = config.base_delay
        
    elif config.strategy == RetryStrategy.LINEAR:
        delay = config.base_delay * (attempt + 1)
        
    elif config.strategy == RetryStrategy.EXPONENTIAL:
        delay = config.base_delay * (2 ** attempt)
        
    elif config.strategy == RetryStrategy.EXPONENTIAL_JITTER:
        # Exponential backoff with full jitter
        base = config.base_delay * (2 ** attempt)
        jitter = random.uniform(0, config.jitter_factor * base)
        delay = base + jitter
    
    else:
        delay = config.base_delay
    
    # Cap at max delay
    return min(delay, config.max_delay)


def should_retry(
    exception: Exception,
    result: Any,
    config: RetryConfig,
) -> bool:
    """
    Determine if operation should be retried.
    
    Args:
        exception: Exception that occurred (or None)
        result: Result of operation (if no exception)
        config: Retry configuration
        
    Returns:
        True if should retry
    """
    # Check non-retryable exceptions first
    if exception and isinstance(exception, config.non_retryable_exceptions):
        return False
    
    # Check retryable exceptions
    if exception and isinstance(exception, config.retryable_exceptions):
        return True
    
    # Check result-based retry condition
    if config.retry_on_result and not exception:
        return config.retry_on_result(result)
    
    return False


async def retry_async(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """
    Execute async function with retry logic.
    
    Args:
        func: Async function to execute
        *args: Positional arguments
        config: Retry configuration
        **kwargs: Keyword arguments
        
    Returns:
        Function result
        
    Raises:
        RetryExhaustedError: If all retries exhausted
    """
    if config is None:
        config = RetryConfig()
    
    last_exception: Optional[Exception] = None
    
    for attempt in range(config.max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            
            # Check if result should trigger retry
            if config.retry_on_result and config.retry_on_result(result):
                if attempt < config.max_retries:
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"due to result condition, waiting {delay:.2f}s"
                    )
                    if config.on_retry:
                        config.on_retry(attempt + 1, None, delay)
                    await asyncio.sleep(delay)
                    continue
            
            return result
            
        except config.non_retryable_exceptions as e:
            # Don't retry these
            logger.error(f"Non-retryable exception in {func.__name__}: {e}")
            raise
            
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_retries:
                delay = calculate_delay(attempt, config)
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                    f"after {type(e).__name__}: {e}, waiting {delay:.2f}s"
                )
                if config.on_retry:
                    config.on_retry(attempt + 1, e, delay)
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_retries} retries exhausted for {func.__name__}: {e}"
                )
    
    raise RetryExhaustedError(
        f"All {config.max_retries} retries exhausted for {func.__name__}",
        last_exception=last_exception,
    )


def retry_sync(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """
    Execute sync function with retry logic.
    
    Args:
        func: Sync function to execute
        *args: Positional arguments
        config: Retry configuration
        **kwargs: Keyword arguments
        
    Returns:
        Function result
        
    Raises:
        RetryExhaustedError: If all retries exhausted
    """
    if config is None:
        config = RetryConfig()
    
    last_exception: Optional[Exception] = None
    
    for attempt in range(config.max_retries + 1):
        try:
            result = func(*args, **kwargs)
            
            if config.retry_on_result and config.retry_on_result(result):
                if attempt < config.max_retries:
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"due to result condition, waiting {delay:.2f}s"
                    )
                    if config.on_retry:
                        config.on_retry(attempt + 1, None, delay)
                    time.sleep(delay)
                    continue
            
            return result
            
        except config.non_retryable_exceptions as e:
            logger.error(f"Non-retryable exception in {func.__name__}: {e}")
            raise
            
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_retries:
                delay = calculate_delay(attempt, config)
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                    f"after {type(e).__name__}: {e}, waiting {delay:.2f}s"
                )
                if config.on_retry:
                    config.on_retry(attempt + 1, e, delay)
                time.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_retries} retries exhausted for {func.__name__}: {e}"
                )
    
    raise RetryExhaustedError(
        f"All {config.max_retries} retries exhausted for {func.__name__}",
        last_exception=last_exception,
    )


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = (),
):
    """
    Decorator for adding retry logic to functions.
    
    Usage:
        @with_retry(max_retries=3, base_delay=1.0)
        async def call_external_api():
            return await api.get_data()
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=strategy,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await retry_async(func, *args, config=config, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return retry_sync(func, *args, config=config, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ============================================================================
# Retry with Circuit Breaker Integration
# ============================================================================

async def retry_with_circuit_breaker(
    func: Callable[..., T],
    *args,
    circuit_breaker: "CircuitBreaker",
    retry_config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """
    Execute function with both retry and circuit breaker protection.
    
    The circuit breaker wraps the retry logic, so:
    1. If circuit is open, fail fast
    2. If circuit is closed/half-open, attempt with retries
    3. Failures count toward circuit breaker threshold
    
    Args:
        func: Function to execute
        circuit_breaker: Circuit breaker instance
        retry_config: Retry configuration
        *args, **kwargs: Function arguments
        
    Returns:
        Function result
    """
    from backend.core.circuit_breaker import CircuitBreakerOpenError
    
    async def wrapped_func(*a, **kw):
        return await retry_async(func, *a, config=retry_config, **kw)
    
    return await circuit_breaker.call(wrapped_func, *args, **kwargs)


# ============================================================================
# Common Retry Configurations
# ============================================================================

# For external HTTP APIs
HTTP_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL_JITTER,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        OSError,
    ),
)

# For database operations
DB_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.5,
    max_delay=10.0,
    strategy=RetryStrategy.EXPONENTIAL,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
    ),
)

# For LLM API calls
LLM_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    base_delay=2.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL_JITTER,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
    ),
)

# For Redis operations
REDIS_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.1,
    max_delay=5.0,
    strategy=RetryStrategy.EXPONENTIAL,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
    ),
)
