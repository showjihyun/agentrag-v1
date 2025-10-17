"""
Rate limiting utilities using Redis for distributed rate limiting.

This module provides flexible rate limiting with multiple time windows
and per-endpoint configuration.
"""

import logging
from typing import Tuple, Optional, Dict
from datetime import datetime
from redis.asyncio import Redis
from fastapi import Request, HTTPException, status, Depends

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based distributed rate limiter.

    Features:
    - Multiple time windows (minute, hour, day)
    - Per-user and per-IP rate limiting
    - Per-endpoint rate limits
    - Graceful degradation if Redis is unavailable
    """

    def __init__(
        self,
        redis_client: Redis,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        enabled: bool = True,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis client instance
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
            requests_per_day: Maximum requests per day
            enabled: Whether rate limiting is enabled
        """
        self.redis = redis_client
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.rpd = requests_per_day
        self.enabled = enabled

    async def check_rate_limit(
        self, identifier: str, endpoint: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Dict[str, int]]:
        """
        Check if request is within rate limits.

        Args:
            identifier: User identifier (user_id or IP address)
            endpoint: Optional endpoint path for per-endpoint limits

        Returns:
            Tuple of (is_allowed, error_message, remaining_counts)
            - is_allowed: True if request is allowed
            - error_message: None if allowed, error description if blocked
            - remaining_counts: Dict with remaining requests for each window
        """
        if not self.enabled:
            return True, None, {}

        try:
            now = datetime.now()

            # Generate keys for different time windows
            minute_key = f"rate_limit:{identifier}:minute:{now.strftime('%Y%m%d%H%M')}"
            hour_key = f"rate_limit:{identifier}:hour:{now.strftime('%Y%m%d%H')}"
            day_key = f"rate_limit:{identifier}:day:{now.strftime('%Y%m%d')}"

            if endpoint:
                minute_key += f":{endpoint}"
                hour_key += f":{endpoint}"
                day_key += f":{endpoint}"

            # Check and increment counters
            minute_count = await self._increment_counter(minute_key, 60)
            hour_count = await self._increment_counter(hour_key, 3600)
            day_count = await self._increment_counter(day_key, 86400)

            # Calculate remaining requests
            remaining = {
                "minute": max(0, self.rpm - minute_count),
                "hour": max(0, self.rph - hour_count),
                "day": max(0, self.rpd - day_count),
            }

            # Check limits
            if minute_count > self.rpm:
                return (
                    False,
                    f"Rate limit exceeded: {self.rpm} requests per minute",
                    remaining,
                )

            if hour_count > self.rph:
                return (
                    False,
                    f"Rate limit exceeded: {self.rph} requests per hour",
                    remaining,
                )

            if day_count > self.rpd:
                return (
                    False,
                    f"Rate limit exceeded: {self.rpd} requests per day",
                    remaining,
                )

            logger.debug(
                f"Rate limit check passed for {identifier}",
                extra={
                    "identifier": identifier,
                    "endpoint": endpoint,
                    "counts": {
                        "minute": minute_count,
                        "hour": hour_count,
                        "day": day_count,
                    },
                    "remaining": remaining,
                },
            )

            return True, None, remaining

        except Exception as e:
            # Graceful degradation: allow request if Redis fails
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            return True, None, {}

    async def _increment_counter(self, key: str, ttl: int) -> int:
        """
        Increment counter and set TTL if new.

        Args:
            key: Redis key
            ttl: Time to live in seconds

        Returns:
            Current count
        """
        count = await self.redis.incr(key)

        # Set TTL only for new keys
        if count == 1:
            await self.redis.expire(key, ttl)

        return count

    async def reset_limit(self, identifier: str, endpoint: Optional[str] = None):
        """
        Reset rate limit for an identifier.

        Args:
            identifier: User identifier
            endpoint: Optional endpoint path
        """
        try:
            now = datetime.now()

            keys_to_delete = [
                f"rate_limit:{identifier}:minute:{now.strftime('%Y%m%d%H%M')}",
                f"rate_limit:{identifier}:hour:{now.strftime('%Y%m%d%H')}",
                f"rate_limit:{identifier}:day:{now.strftime('%Y%m%d')}",
            ]

            if endpoint:
                keys_to_delete = [f"{key}:{endpoint}" for key in keys_to_delete]

            await self.redis.delete(*keys_to_delete)

            logger.info(f"Rate limit reset for {identifier}")

        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}", exc_info=True)


# FastAPI dependency for rate limiting
async def rate_limit_dependency(
    request: Request, rpm: int = 60, rph: int = 1000, rpd: int = 10000
):
    """
    FastAPI dependency for rate limiting.

    Args:
        request: FastAPI request
        rpm: Requests per minute
        rph: Requests per hour
        rpd: Requests per day

    Raises:
        HTTPException: If rate limit is exceeded
    """
    from backend.core.dependencies import get_redis_client
    from backend.core.auth_dependencies import get_optional_user

    # Get Redis client
    redis_client = await get_redis_client()

    # Get user if authenticated
    try:
        current_user = await get_optional_user(request)
        identifier = str(current_user.id) if current_user else request.client.host
    except:
        identifier = request.client.host if request.client else "unknown"

    # Create rate limiter
    rate_limiter = RateLimiter(
        redis_client=redis_client,
        requests_per_minute=rpm,
        requests_per_hour=rph,
        requests_per_day=rpd,
    )

    # Check rate limit
    is_allowed, error_msg, remaining = await rate_limiter.check_rate_limit(
        identifier=identifier, endpoint=request.url.path
    )

    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded for {identifier}",
            extra={
                "identifier": identifier,
                "endpoint": request.url.path,
                "remaining": remaining,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg,
            headers={
                "X-RateLimit-Remaining-Minute": str(remaining.get("minute", 0)),
                "X-RateLimit-Remaining-Hour": str(remaining.get("hour", 0)),
                "X-RateLimit-Remaining-Day": str(remaining.get("day", 0)),
                "Retry-After": "60",  # Retry after 1 minute
            },
        )

    # Add rate limit info to response headers
    request.state.rate_limit_remaining = remaining


# Convenience functions for different rate limit tiers
def rate_limit_strict():
    """Strict rate limit: 30/min, 500/hour, 5000/day"""
    return Depends(
        lambda request: rate_limit_dependency(request, rpm=30, rph=500, rpd=5000)
    )


def rate_limit_normal():
    """Normal rate limit: 60/min, 1000/hour, 10000/day"""
    return Depends(
        lambda request: rate_limit_dependency(request, rpm=60, rph=1000, rpd=10000)
    )


def rate_limit_relaxed():
    """Relaxed rate limit: 120/min, 2000/hour, 20000/day"""
    return Depends(
        lambda request: rate_limit_dependency(request, rpm=120, rph=2000, rpd=20000)
    )
