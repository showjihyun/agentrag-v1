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
    
    def get_unhealthy(self) -> list[str]:
        """Get list of unhealthy (open) circuit breakers"""
        return [
            name for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.OPEN
        ]
    
    def get_summary(self) -> dict:
        """Get summary of all circuit breakers"""
        states = self.get_all_states()
        return {
            "total": len(states),
            "closed": sum(1 for s in states.values() if s["state"] == "closed"),
            "open": sum(1 for s in states.values() if s["state"] == "open"),
            "half_open": sum(1 for s in states.values() if s["state"] == "half_open"),
            "breakers": states,
        }


# ============================================================================
# Resilient Service Wrapper
# ============================================================================

class ResilientService:
    """
    Wrapper for external services with circuit breaker and retry support.
    
    Combines circuit breaker pattern with retry logic for robust
    external service calls.
    
    Usage:
        llm_service = ResilientService(
            name="llm",
            circuit_breaker=registry.get("llm_service"),
            max_retries=3,
            base_delay=1.0,
        )
        
        result = await llm_service.call(
            llm_client.generate,
            prompt="Hello"
        )
    """
    
    def __init__(
        self,
        name: str,
        circuit_breaker: Optional[CircuitBreaker] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        timeout: float = 30.0,
    ):
        self.name = name
        self.circuit_breaker = circuit_breaker
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.timeout = timeout
        
        # Metrics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.total_retries = 0
    
    async def call(
        self,
        func: Callable[..., T],
        *args,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> T:
        """
        Execute function with circuit breaker and retry protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            timeout: Override default timeout
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If all retries exhausted
        """
        import random
        
        self.total_calls += 1
        effective_timeout = timeout or self.timeout
        
        # Check circuit breaker first
        if self.circuit_breaker:
            if self.circuit_breaker.state == CircuitState.OPEN:
                if not self.circuit_breaker._should_attempt_reset():
                    self.failed_calls += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker for {self.name} is OPEN"
                    )
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Execute with timeout
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=effective_timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, lambda: func(*args, **kwargs)
                        ),
                        timeout=effective_timeout
                    )
                
                # Success
                self.successful_calls += 1
                
                if self.circuit_breaker:
                    await self.circuit_breaker._on_success()
                
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(
                    f"{self.name}: Timeout after {effective_timeout}s "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"{self.name}: {type(e).__name__}: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
            
            # Record failure in circuit breaker
            if self.circuit_breaker and last_exception:
                await self.circuit_breaker._on_failure(last_exception)
            
            # Retry with backoff
            if attempt < self.max_retries:
                self.total_retries += 1
                delay = min(
                    self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self.max_delay
                )
                logger.info(f"{self.name}: Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        self.failed_calls += 1
        raise last_exception or Exception(f"{self.name}: All retries exhausted")
    
    def get_stats(self) -> dict:
        """Get service call statistics."""
        success_rate = (
            self.successful_calls / self.total_calls * 100
            if self.total_calls > 0 else 0
        )
        
        return {
            "name": self.name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "total_retries": self.total_retries,
            "success_rate": round(success_rate, 2),
            "circuit_breaker_state": (
                self.circuit_breaker.state.value
                if self.circuit_breaker else "none"
            ),
        }


# Global registry
_registry = CircuitBreakerRegistry()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry"""
    return _registry
