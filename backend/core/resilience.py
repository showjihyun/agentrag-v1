"""
Resilience Patterns: Circuit Breaker, Retry Logic, Fallback

Implements patterns for building resilient systems that can handle
failures gracefully and recover automatically.
"""

import logging
import asyncio
import time
import random
from typing import Optional, Callable, Any, TypeVar, Dict
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.

    Protects external service calls by:
    - Tracking failures
    - Opening circuit after threshold
    - Allowing periodic test requests
    - Closing circuit when service recovers
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
            half_open_max_calls: Max calls in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0

        logger.info(
            f"Circuit breaker '{name}' initialized "
            f"(threshold={failure_threshold}, timeout={recovery_timeout}s)"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self._state == CircuitState.HALF_OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return False

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self._state = CircuitState.OPEN
        self._last_failure_time = datetime.now()

        logger.warning(
            f"Circuit breaker '{self.name}' OPENED " f"(failures={self._failure_count})"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._success_count = 0

        logger.info(f"Circuit breaker '{self.name}' HALF-OPEN (testing recovery)")

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

        logger.info(f"Circuit breaker '{self.name}' CLOSED (recovered)")

    def _record_success(self) -> None:
        """Record successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1

            # If enough successes in half-open, close circuit
            if self._success_count >= self.half_open_max_calls:
                self._transition_to_closed()

        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def _record_failure(self) -> None:
        """Record failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens circuit
            self._transition_to_open()

        elif self._state == CircuitState.CLOSED:
            # Open circuit if threshold reached
            if self._failure_count >= self.failure_threshold:
                self._transition_to_open()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function fails
        """
        # Check if should attempt reset
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            self._transition_to_half_open()

        # Reject if circuit is open
        if self._state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable. Retry after {self.recovery_timeout}s."
            )

        # Limit calls in half-open state
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls > self.half_open_max_calls:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is HALF-OPEN. "
                    f"Too many test calls."
                )

        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            self._record_success()
            return result

        except self.expected_exception as e:
            self._record_failure()
            logger.error(f"Circuit breaker '{self.name}' recorded failure: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure": (
                self._last_failure_time.isoformat() if self._last_failure_time else None
            ),
        }


class RetryStrategy:
    """
    Retry strategy with exponential backoff and jitter.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry strategy.

        Args:
            max_attempts: Maximum retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delay
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )

        # Add jitter (random ±25%)
        if self.jitter:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


async def retry_async(
    func: Callable[..., T],
    *args,
    strategy: Optional[RetryStrategy] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    **kwargs,
) -> T:
    """
    Retry async function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Function arguments
        strategy: Retry strategy (default: 3 attempts)
        exceptions: Exceptions to catch and retry
        on_retry: Callback on retry (exception, attempt)
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Raises:
        Exception: If all retries fail
    """
    if strategy is None:
        strategy = RetryStrategy()

    last_exception = None

    for attempt in range(strategy.max_attempts):
        try:
            return await func(*args, **kwargs)

        except exceptions as e:
            last_exception = e

            if attempt < strategy.max_attempts - 1:
                delay = strategy.get_delay(attempt)

                logger.warning(
                    f"Retry attempt {attempt + 1}/{strategy.max_attempts} "
                    f"after {delay:.2f}s: {e}"
                )

                if on_retry:
                    on_retry(e, attempt)

                await asyncio.sleep(delay)
            else:
                logger.error(f"All {strategy.max_attempts} retry attempts failed: {e}")

    raise last_exception


def retry_sync(
    func: Callable[..., T],
    *args,
    strategy: Optional[RetryStrategy] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    **kwargs,
) -> T:
    """
    Retry sync function with exponential backoff.

    Args:
        func: Sync function to retry
        *args: Function arguments
        strategy: Retry strategy (default: 3 attempts)
        exceptions: Exceptions to catch and retry
        on_retry: Callback on retry (exception, attempt)
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Raises:
        Exception: If all retries fail
    """
    if strategy is None:
        strategy = RetryStrategy()

    last_exception = None

    for attempt in range(strategy.max_attempts):
        try:
            return func(*args, **kwargs)

        except exceptions as e:
            last_exception = e

            if attempt < strategy.max_attempts - 1:
                delay = strategy.get_delay(attempt)

                logger.warning(
                    f"Retry attempt {attempt + 1}/{strategy.max_attempts} "
                    f"after {delay:.2f}s: {e}"
                )

                if on_retry:
                    on_retry(e, attempt)

                time.sleep(delay)
            else:
                logger.error(f"All {strategy.max_attempts} retry attempts failed: {e}")

    raise last_exception


def with_circuit_breaker(
    circuit_breaker: CircuitBreaker, fallback: Optional[Callable] = None
):
    """
    Decorator to protect function with circuit breaker.

    Usage:
        breaker = CircuitBreaker("external_api")

        @with_circuit_breaker(breaker)
        async def call_external_api():
            # API call
            pass
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await circuit_breaker.call(func, *args, **kwargs)
            except CircuitBreakerError as e:
                if fallback:
                    logger.info(f"Using fallback for {func.__name__}")
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    else:
                        return fallback(*args, **kwargs)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return asyncio.run(circuit_breaker.call(func, *args, **kwargs))
            except CircuitBreakerError as e:
                if fallback:
                    logger.info(f"Using fallback for {func.__name__}")
                    return fallback(*args, **kwargs)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator to retry function with exponential backoff.

    Usage:
        @with_retry(max_attempts=3, initial_delay=1.0)
        async def unstable_function():
            # Function that might fail
            pass
    """
    strategy = RetryStrategy(
        max_attempts=max_attempts, initial_delay=initial_delay, max_delay=max_delay
    )

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_async(
                func, *args, strategy=strategy, exceptions=exceptions, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return retry_sync(
                func, *args, strategy=strategy, exceptions=exceptions, **kwargs
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Global circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str, failure_threshold: int = 5, recovery_timeout: int = 60
) -> CircuitBreaker:
    """
    Get or create a circuit breaker.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds before attempting recovery

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    return _circuit_breakers[name]


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return _circuit_breakers.copy()


def reset_circuit_breaker(name: str) -> bool:
    """
    Manually reset a circuit breaker.

    Args:
        name: Circuit breaker name

    Returns:
        True if reset, False if not found
    """
    if name in _circuit_breakers:
        _circuit_breakers[name]._transition_to_closed()
        return True
    return False
