"""Retry handler with exponential backoff for resilient operations."""

import logging
import asyncio
from typing import TypeVar, Callable, Optional, Any
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on_exceptions: tuple = (Exception,),
        timeout: Optional[float] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delays
            retry_on_exceptions: Tuple of exceptions to retry on
            timeout: Overall timeout for all attempts (seconds)
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on_exceptions = retry_on_exceptions
        self.timeout = timeout
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay


def retry_async(config: Optional[RetryConfig] = None):
    """
    Decorator for async functions with retry logic.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    # Check timeout
                    if config.timeout:
                        elapsed = time.time() - start_time
                        if elapsed >= config.timeout:
                            raise TimeoutError(
                                f"Operation timed out after {elapsed:.2f}s"
                            )
                    
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Log success if retried
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except config.retry_on_exceptions as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {config.max_attempts} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay
                    delay = config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}, "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_sync(config: Optional[RetryConfig] = None):
    """
    Decorator for sync functions with retry logic.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    # Check timeout
                    if config.timeout:
                        elapsed = time.time() - start_time
                        if elapsed >= config.timeout:
                            raise TimeoutError(
                                f"Operation timed out after {elapsed:.2f}s"
                            )
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Log success if retried
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except config.retry_on_exceptions as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {config.max_attempts} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay
                    delay = config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}, "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery (seconds)
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker entering half-open state")
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset if in half-open state
            if self.state == "half_open":
                logger.info("Circuit breaker closing after successful call")
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = "open"
            
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call async function through circuit breaker.
        
        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker entering half-open state")
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset if in half-open state
            if self.state == "half_open":
                logger.info("Circuit breaker closing after successful call")
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = "open"
            
            raise
    
    def reset(self):
        """Reset circuit breaker to closed state."""
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")
