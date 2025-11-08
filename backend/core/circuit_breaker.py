"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by monitoring service health and
automatically opening/closing the circuit based on failure rates.
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Optional, Any, TypeVar, Generic
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker(Generic[T]):
    """
    Circuit Breaker implementation with automatic recovery.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    Example:
        breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            expected_exception=RequestException
        )
        
        result = await breaker.call(
            external_service.get_data,
            param1="value"
        )
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        expected_exception: type = Exception,
        fallback: Optional[Callable] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes in HALF_OPEN before closing
            timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
            fallback: Optional fallback function when circuit is open
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.fallback = fallback
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback
        """
        async with self._lock:
            # Check if we should attempt reset
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    # Circuit is open, use fallback or fail fast
                    if self.fallback:
                        logger.warning(
                            f"Circuit breaker OPEN, using fallback. "
                            f"Will retry after {self.timeout}s"
                        )
                        return await self._execute_fallback(*args, **kwargs)
                    else:
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker is OPEN. "
                            f"Service unavailable. "
                            f"Will retry after {self.timeout}s"
                        )
        
        # Execute function
        try:
            result = await self._execute(func, *args, **kwargs)
            await self._on_success()
            return result
            
        except self.expected_exception as e:
            await self._on_failure(e)
            raise
    
    async def _execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute the function (sync or async)"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def _execute_fallback(self, *args, **kwargs) -> T:
        """Execute fallback function"""
        if asyncio.iscoroutinefunction(self.fallback):
            return await self.fallback(*args, **kwargs)
        else:
            return self.fallback(*args, **kwargs)
    
    async def _on_success(self):
        """Handle successful execution"""
        async with self._lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                if self.success_count >= self.success_threshold:
                    logger.info(
                        f"Circuit breaker closing after "
                        f"{self.success_count} successful requests"
                    )
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            logger.warning(
                f"Circuit breaker failure {self.failure_count}/"
                f"{self.failure_threshold}: {exception}"
            )
            
            if self.state == CircuitState.HALF_OPEN:
                # Failed during recovery, reopen circuit
                logger.warning("Circuit breaker reopening after failed recovery attempt")
                self.state = CircuitState.OPEN
                self.failure_count = 0
                
            elif self.failure_count >= self.failure_threshold:
                # Too many failures, open circuit
                logger.error(
                    f"Circuit breaker opening after "
                    f"{self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if not self.last_failure_time:
            return True
        
        elapsed = datetime.utcnow() - self.last_failure_time
        return elapsed > timedelta(seconds=self.timeout)
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": (
                self.last_failure_time.isoformat() 
                if self.last_failure_time else None
            ),
        }
    
    async def reset(self):
        """Manually reset circuit breaker"""
        async with self._lock:
            logger.info("Circuit breaker manually reset")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: type = Exception,
    fallback: Optional[Callable] = None
):
    """
    Decorator for circuit breaker pattern.
    
    Example:
        @circuit_breaker(failure_threshold=3, timeout=30)
        async def call_external_api():
            return await api.get_data()
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        expected_exception=expected_exception,
        fallback=fallback
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        # Attach breaker to function for inspection
        wrapper.circuit_breaker = breaker
        
        return wrapper
    
    return decorator


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
    
    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception,
        fallback: Optional[Callable] = None
    ) -> CircuitBreaker:
        """Register a new circuit breaker"""
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
            fallback=fallback
        )
        self._breakers[name] = breaker
        logger.info(f"Registered circuit breaker: {name}")
        return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self._breakers.get(name)
    
    def get_all_states(self) -> dict[str, dict]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in self._breakers.items()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for name, breaker in self._breakers.items():
            await breaker.reset()
            logger.info(f"Reset circuit breaker: {name}")


# Global registry
_registry = CircuitBreakerRegistry()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry"""
    return _registry
