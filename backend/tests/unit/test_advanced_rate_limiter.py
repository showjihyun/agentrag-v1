"""
Unit tests for Advanced Rate Limiter
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from backend.core.advanced_rate_limiter import (
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    AdaptiveRateLimiter
)


@pytest.fixture
async def redis_mock():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.eval = AsyncMock(return_value=[1, 99, 0])
    mock.hmget = AsyncMock(return_value=[100.0, 1234567890.0])
    mock.delete = AsyncMock()
    mock.zremrangebyscore = AsyncMock()
    mock.zcard = AsyncMock(return_value=10)
    return mock


@pytest.mark.asyncio
async def test_token_bucket_allow_request(redis_mock):
    """Test token bucket rate limiter."""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_mock,
        capacity=100,
        refill_rate=10.0
    )
    
    allowed, remaining, wait_time = await limiter.allow_request("user-123")
    
    assert allowed is True
    assert remaining == 99
    assert redis_mock.eval.called


@pytest.mark.asyncio
async def test_token_bucket_get_status(redis_mock):
    """Test getting token bucket status."""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_mock,
        capacity=100,
        refill_rate=10.0
    )
    
    status = await limiter.get_status("user-123")
    
    assert "tokens" in status
    assert "capacity" in status
    assert status["capacity"] == 100


@pytest.mark.asyncio
async def test_token_bucket_reset(redis_mock):
    """Test resetting token bucket."""
    limiter = TokenBucketRateLimiter(
        redis_client=redis_mock,
        capacity=100,
        refill_rate=10.0
    )
    
    await limiter.reset("user-123")
    
    assert redis_mock.delete.called


@pytest.mark.asyncio
async def test_sliding_window_allow_request(redis_mock):
    """Test sliding window rate limiter."""
    limiter = SlidingWindowRateLimiter(
        redis_client=redis_mock,
        max_requests=100,
        window_seconds=60
    )
    
    allowed, remaining, reset_time = await limiter.allow_request("user-123")
    
    assert allowed is True
    assert remaining == 99


@pytest.mark.asyncio
async def test_sliding_window_get_status(redis_mock):
    """Test getting sliding window status."""
    limiter = SlidingWindowRateLimiter(
        redis_client=redis_mock,
        max_requests=100,
        window_seconds=60
    )
    
    status = await limiter.get_status("user-123")
    
    assert "requests" in status
    assert "max_requests" in status
    assert status["max_requests"] == 100


@pytest.mark.asyncio
async def test_adaptive_rate_limiter(redis_mock):
    """Test adaptive rate limiter."""
    limiter = AdaptiveRateLimiter(
        redis_client=redis_mock,
        base_capacity=100,
        base_refill_rate=10.0
    )
    
    # Test with different user tiers
    allowed, remaining, wait_time = await limiter.allow_request(
        "user-123",
        user_tier="pro",
        system_load=0.5
    )
    
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_error_handling(redis_mock):
    """Test rate limiter error handling."""
    redis_mock.eval = AsyncMock(side_effect=Exception("Redis error"))
    
    limiter = TokenBucketRateLimiter(
        redis_client=redis_mock,
        capacity=100,
        refill_rate=10.0
    )
    
    # Should fail open (allow request)
    allowed, remaining, wait_time = await limiter.allow_request("user-123")
    
    assert allowed is True
