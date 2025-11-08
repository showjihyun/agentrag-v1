"""
Unit tests for Circuit Breaker
"""

import pytest
import asyncio
from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    get_circuit_breaker_registry
)


class TestException(Exception):
    """Test exception"""
    pass


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """Test circuit breaker in CLOSED state"""
    breaker = CircuitBreaker(failure_threshold=3, timeout=1)
    
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures"""
    breaker = CircuitBreaker(
        failure_threshold=3,
        timeout=1,
        expected_exception=TestException
    )
    
    async def failing_func():
        raise TestException("Service unavailable")
    
    # Fail 3 times
    for i in range(3):
        with pytest.raises(TestException):
            await breaker.call(failing_func)
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 3


@pytest.mark.asyncio
async def test_circuit_breaker_fails_fast_when_open():
    """Test circuit breaker fails fast when open"""
    breaker = CircuitBreaker(
        failure_threshold=2,
        timeout=10,
        expected_exception=TestException
    )
    
    async def failing_func():
        raise TestException("Service unavailable")
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(TestException):
            await breaker.call(failing_func)
    
    # Should fail fast without calling function
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(failing_func)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker recovery through HALF_OPEN state"""
    breaker = CircuitBreaker(
        failure_threshold=2,
        success_threshold=2,
        timeout=1,
        expected_exception=TestException
    )
    
    call_count = 0
    
    async def sometimes_failing_func():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise TestException("Failing")
        return "success"
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(TestException):
            await breaker.call(sometimes_failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for timeout
    await asyncio.sleep(1.1)
    
    # Should transition to HALF_OPEN and succeed
    result = await breaker.call(sometimes_failing_func)
    assert breaker.state == CircuitState.HALF_OPEN
    
    # One more success should close circuit
    result = await breaker.call(sometimes_failing_func)
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_fallback():
    """Test circuit breaker fallback function"""
    
    async def fallback_func(*args, **kwargs):
        return "fallback_result"
    
    breaker = CircuitBreaker(
        failure_threshold=2,
        timeout=10,
        expected_exception=TestException,
        fallback=fallback_func
    )
    
    async def failing_func():
        raise TestException("Service unavailable")
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(TestException):
            await breaker.call(failing_func)
    
    # Should use fallback
    result = await breaker.call(failing_func)
    assert result == "fallback_result"


@pytest.mark.asyncio
async def test_circuit_breaker_registry():
    """Test circuit breaker registry"""
    registry = get_circuit_breaker_registry()
    
    # Register breaker
    breaker = registry.register(
        name="test_service",
        failure_threshold=3,
        timeout=60
    )
    
    assert breaker is not None
    assert registry.get("test_service") == breaker
    
    # Get all states
    states = registry.get_all_states()
    assert "test_service" in states
    
    # Reset all
    await registry.reset_all()
