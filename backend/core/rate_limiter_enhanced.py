"""
Enhanced Rate Limiting with Redis Backend

Features:
- Sliding window rate limiting
- Per-user and per-IP limits
- Endpoint-specific limits
- Burst handling
- Rate limit headers
"""

import time
import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitTier(str, Enum):
    """Rate limit tiers for different user types."""
    ANONYMOUS = "anonymous"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int
    requests_per_hour: int
    burst_size: int  # Max requests in a short burst
    burst_window_seconds: int = 10


# Default rate limits by tier
DEFAULT_LIMITS: Dict[RateLimitTier, RateLimitConfig] = {
    RateLimitTier.ANONYMOUS: RateLimitConfig(
        requests_per_minute=20,
        requests_per_hour=200,
        burst_size=10,
    ),
    RateLimitTier.FREE: RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_size=20,
    ),
    RateLimitTier.PRO: RateLimitConfig(
        requests_per_minute=200,
        requests_per_hour=5000,
        burst_size=50,
    ),
    RateLimitTier.ENTERPRISE: RateLimitConfig(
        requests_per_minute=1000,
        requests_per_hour=50000,
        burst_size=200,
    ),
    RateLimitTier.UNLIMITED: RateLimitConfig(
        requests_per_minute=999999,
        requests_per_hour=999999,
        burst_size=999999,
    ),
}

# Endpoint-specific limits (overrides default)
ENDPOINT_LIMITS: Dict[str, RateLimitConfig] = {
    "/api/query": RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=500,
        burst_size=10,
    ),
    "/api/documents/upload": RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        burst_size=5,
    ),
    "/api/agent-builder/workflows/execute": RateLimitConfig(
        requests_per_minute=20,
        requests_per_hour=200,
        burst_size=5,
    ),
}


class EnhancedRateLimiter:
    """
    Enhanced rate limiter with Redis backend and sliding window algorithm.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._local_cache: Dict[str, list] = {}  # Fallback for no Redis
    
    def _get_key(self, identifier: str, window: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"ratelimit:{identifier}:{window}"
    
    def _get_identifier(self, request: Request, user_id: Optional[str] = None) -> str:
        """Get unique identifier for rate limiting."""
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _sliding_window_check(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window algorithm.
        
        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        now = time.time()
        window_start = now - window_seconds
        
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                
                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                
                # Count current entries
                pipe.zcard(key)
                
                # Add current request
                pipe.zadd(key, {str(now): now})
                
                # Set expiry
                pipe.expire(key, window_seconds)
                
                results = pipe.execute()
                current_count = results[1]
                
                remaining = max(0, limit - current_count - 1)
                reset_time = int(now + window_seconds)
                
                if current_count >= limit:
                    # Remove the request we just added
                    self.redis.zrem(key, str(now))
                    return False, 0, reset_time
                
                return True, remaining, reset_time
                
            except Exception as e:
                logger.warning(f"Redis rate limit error: {e}, falling back to local")
        
        # Local fallback
        if key not in self._local_cache:
            self._local_cache[key] = []
        
        # Clean old entries
        self._local_cache[key] = [
            t for t in self._local_cache[key] if t > window_start
        ]
        
        current_count = len(self._local_cache[key])
        remaining = max(0, limit - current_count - 1)
        reset_time = int(now + window_seconds)
        
        if current_count >= limit:
            return False, 0, reset_time
        
        self._local_cache[key].append(now)
        return True, remaining, reset_time
    
    def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        tier: RateLimitTier = RateLimitTier.ANONYMOUS,
        endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (allowed, headers_dict)
        """
        identifier = self._get_identifier(request, user_id)
        
        # Get config (endpoint-specific or tier default)
        if endpoint and endpoint in ENDPOINT_LIMITS:
            config = ENDPOINT_LIMITS[endpoint]
        else:
            config = DEFAULT_LIMITS.get(tier, DEFAULT_LIMITS[RateLimitTier.ANONYMOUS])
        
        # Check minute limit
        minute_key = self._get_key(identifier, "minute")
        minute_allowed, minute_remaining, minute_reset = self._sliding_window_check(
            minute_key, config.requests_per_minute, 60
        )
        
        # Check hour limit
        hour_key = self._get_key(identifier, "hour")
        hour_allowed, hour_remaining, hour_reset = self._sliding_window_check(
            hour_key, config.requests_per_hour, 3600
        )
        
        # Check burst limit
        burst_key = self._get_key(identifier, "burst")
        burst_allowed, burst_remaining, burst_reset = self._sliding_window_check(
            burst_key, config.burst_size, config.burst_window_seconds
        )
        
        allowed = minute_allowed and hour_allowed and burst_allowed
        
        # Build headers
        headers = {
            "X-RateLimit-Limit-Minute": str(config.requests_per_minute),
            "X-RateLimit-Remaining-Minute": str(minute_remaining),
            "X-RateLimit-Reset-Minute": str(minute_reset),
            "X-RateLimit-Limit-Hour": str(config.requests_per_hour),
            "X-RateLimit-Remaining-Hour": str(hour_remaining),
            "X-RateLimit-Reset-Hour": str(hour_reset),
        }
        
        if not allowed:
            if not minute_allowed:
                headers["Retry-After"] = str(minute_reset - int(time.time()))
            elif not hour_allowed:
                headers["Retry-After"] = str(hour_reset - int(time.time()))
            else:
                headers["Retry-After"] = str(burst_reset - int(time.time()))
        
        return allowed, headers
    
    def get_usage_stats(
        self,
        request: Request,
        user_id: Optional[str] = None
    ) -> Dict[str, any]:
        """Get current rate limit usage statistics."""
        identifier = self._get_identifier(request, user_id)
        now = time.time()
        
        stats = {
            "identifier": identifier,
            "timestamp": now,
        }
        
        for window, seconds in [("minute", 60), ("hour", 3600)]:
            key = self._get_key(identifier, window)
            
            if self.redis:
                try:
                    count = self.redis.zcount(key, now - seconds, now)
                    stats[f"{window}_usage"] = count
                except Exception:
                    stats[f"{window}_usage"] = "unavailable"
            else:
                if key in self._local_cache:
                    count = len([t for t in self._local_cache[key] if t > now - seconds])
                    stats[f"{window}_usage"] = count
                else:
                    stats[f"{window}_usage"] = 0
        
        return stats


# Global instance
_rate_limiter: Optional[EnhancedRateLimiter] = None


def get_rate_limiter() -> EnhancedRateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        try:
            from backend.core.dependencies import get_container
            redis = get_container().get_redis_client()
            _rate_limiter = EnhancedRateLimiter(redis)
        except Exception:
            _rate_limiter = EnhancedRateLimiter(None)
    return _rate_limiter


def rate_limit(
    tier: RateLimitTier = RateLimitTier.FREE,
    endpoint_key: Optional[str] = None
):
    """
    Decorator for rate limiting endpoints.
    
    Usage:
        @router.get("/items")
        @rate_limit(tier=RateLimitTier.FREE)
        async def get_items():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                limiter = get_rate_limiter()
                
                # Get user ID if authenticated
                user_id = None
                if hasattr(request.state, "user") and request.state.user:
                    user_id = str(request.state.user.id)
                
                allowed, headers = limiter.check_rate_limit(
                    request,
                    user_id=user_id,
                    tier=tier,
                    endpoint=endpoint_key or request.url.path
                )
                
                if not allowed:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "success": False,
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": "Too many requests. Please try again later.",
                            }
                        },
                        headers=headers
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
