"""
Unit tests for resilience patterns.
"""

import pytest
import asyncio
from backend.core.resilience import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    with_retry,
    with_timeout,
    RateLimiter,
)


class TestCircuitBreaker:
    """Tests for Circuit Breaker pattern."""

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker(failure_threshold=3)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_function():
            raise Exception("Test failure")

        # Fail 3 times
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(failing_function)

        # Circuit should be open
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects calls when open."""
        cb = CircuitBreaker(failure_threshold=2)

        def failing_function():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            cb.call(failing_function)

    def test_circuit_breaker_success_resets_count(self):
        """Test successful call resets failure count."""
        cb = CircuitBreaker(failure_threshold=3)

        def sometimes_failing(should_fail):
            if should_fail:
                raise Exception("Test failure")
            return "success"

        # Fail once
        with pytest.raises(Exception):
            cb.call(sometimes_failing, True)

        assert cb.failure_count == 1

        # Succeed
        result = cb.call(sometimes_failing, False)
        assert result == "success"
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_async(self):
        """Test circuit breaker with async functions."""
        cb = CircuitBreaker(failure_threshold=2)

        async def async_failing():
            raise Exception("Async failure")

        # Fail twice
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call_async(async_failing)

        # Circuit should be open
        assert cb.state == CircuitState.OPEN

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await cb.call_async(async_failing)

    def test_circuit_breaker_manual_reset(self):
        """Test manual circuit breaker reset."""
        cb = CircuitBreaker(failure_threshold=2)

        def failing_function():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)

        assert cb.state == CircuitState.OPEN

        # Manual reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestRetryDecorator:
    """Tests for retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test retry succeeds on first attempt."""
        call_count = 0

        @with_retry(max_attempts=3)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry succeeds after some failures."""
        call_count = 0

        @with_retry(max_attempts=3, delay=0.1)
        async def sometimes_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = await sometimes_failing()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Test retry exhausts all attempts."""
        call_count = 0

        @with_retry(max_attempts=3, delay=0.1)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")

        with pytest.raises(Exception, match="Always fails"):
            await always_failing()

        assert call_count == 3


class TestTimeoutDecorator:
    """Tests for timeout decorator."""

    @pytest.mark.asyncio
    async def test_timeout_success(self):
        """Test function completes within timeout."""

        @with_timeout(1.0)
        async def fast_function():
            await asyncio.sleep(0.1)
            return "success"

        result = await fast_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        """Test function times out."""

        @with_timeout(0.5)
        async def slow_function():
            await asyncio.sleep(2.0)
            return "should not reach here"

        with pytest.raises(TimeoutError):
            await slow_function()


class TestRateLimiter:
    """Tests for rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_within_limit(self):
        """Test rate limiter allows requests within limit."""
        limiter = RateLimiter(rate=10.0, capacity=10)

        # Should allow 10 tokens
        for _ in range(10):
            allowed = await limiter.acquire(1)
            assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_over_limit(self):
        """Test rate limiter blocks requests over limit."""
        limiter = RateLimiter(rate=10.0, capacity=5)

        # Acquire all tokens
        for _ in range(5):
            await limiter.acquire(1)

        # Next request should be blocked
        allowed = await limiter.acquire(1)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_rate_limiter_refills_tokens(self):
        """Test rate limiter refills tokens over time."""
        limiter = RateLimiter(rate=10.0, capacity=5)

        # Acquire all tokens
        for _ in range(5):
            await limiter.acquire(1)

        # Wait for refill
        await asyncio.sleep(0.5)

        # Should have some tokens now
        allowed = await limiter.acquire(1)
        assert allowed is True
