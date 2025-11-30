"""
Workflow Rate Limiter

Advanced rate limiting for workflow executions with multiple strategies
and user/workflow-level quotas.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10  # Max burst requests
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None  # Seconds until retry
    limit: int = 0
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at.timestamp())),
        }
        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class WorkflowRateLimiter:
    """
    Rate limiter for workflow executions.
    
    Features:
    - Multiple rate limiting strategies
    - User-level and workflow-level limits
    - Burst handling
    - Redis-backed for distributed environments
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Optional Redis client
        """
        self.redis = redis_client
        self._local_counters: Dict[str, Dict[str, Any]] = {}
        
        # Default configs by tier
        self._tier_configs = {
            "free": RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=500,
                burst_limit=5,
            ),
            "basic": RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=500,
                requests_per_day=5000,
                burst_limit=10,
            ),
            "pro": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_limit=20,
            ),
            "enterprise": RateLimitConfig(
                requests_per_minute=200,
                requests_per_hour=10000,
                requests_per_day=100000,
                burst_limit=50,
            ),
        }
    
    async def check_rate_limit(
        self,
        user_id: str,
        workflow_id: Optional[str] = None,
        tier: str = "free",
    ) -> RateLimitResult:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User ID
            workflow_id: Optional workflow ID for workflow-specific limits
            tier: User tier for config lookup
            
        Returns:
            Rate limit result
        """
        config = self._tier_configs.get(tier, self._tier_configs["free"])
        
        # Check minute limit
        minute_result = await self._check_window(
            key=f"ratelimit:{user_id}:minute",
            limit=config.requests_per_minute,
            window_seconds=60,
        )
        
        if not minute_result.allowed:
            return minute_result
        
        # Check hour limit
        hour_result = await self._check_window(
            key=f"ratelimit:{user_id}:hour",
            limit=config.requests_per_hour,
            window_seconds=3600,
        )
        
        if not hour_result.allowed:
            return hour_result
        
        # Check day limit
        day_result = await self._check_window(
            key=f"ratelimit:{user_id}:day",
            limit=config.requests_per_day,
            window_seconds=86400,
        )
        
        if not day_result.allowed:
            return day_result
        
        # Check burst limit if workflow specified
        if workflow_id:
            burst_result = await self._check_burst(
                key=f"ratelimit:{user_id}:{workflow_id}:burst",
                limit=config.burst_limit,
            )
            if not burst_result.allowed:
                return burst_result
        
        # All checks passed - increment counters
        await self._increment(f"ratelimit:{user_id}:minute", 60)
        await self._increment(f"ratelimit:{user_id}:hour", 3600)
        await self._increment(f"ratelimit:{user_id}:day", 86400)
        
        return RateLimitResult(
            allowed=True,
            remaining=min(
                minute_result.remaining - 1,
                hour_result.remaining - 1,
                day_result.remaining - 1,
            ),
            reset_at=minute_result.reset_at,
            limit=config.requests_per_minute,
        )
    
    async def _check_window(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check sliding window rate limit."""
        now = time.time()
        window_start = now - window_seconds
        
        if self.redis:
            try:
                # Remove old entries
                await self.redis.zremrangebyscore(key, 0, window_start)
                
                # Count current entries
                count = await self.redis.zcard(key)
                
                if count >= limit:
                    # Get oldest entry to calculate reset time
                    oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                    reset_at = datetime.fromtimestamp(oldest[0][1] + window_seconds) if oldest else datetime.utcnow()
                    
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_at=reset_at,
                        retry_after=int(reset_at.timestamp() - now),
                        limit=limit,
                    )
                
                return RateLimitResult(
                    allowed=True,
                    remaining=limit - count,
                    reset_at=datetime.utcnow() + timedelta(seconds=window_seconds),
                    limit=limit,
                )
                
            except Exception as e:
                logger.warning(f"Redis rate limit check failed: {e}")
        
        # Fallback to local counter
        return await self._check_local_window(key, limit, window_seconds)
    
    async def _check_local_window(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check rate limit using local counter."""
        now = time.time()
        
        if key not in self._local_counters:
            self._local_counters[key] = {
                "count": 0,
                "window_start": now,
            }
        
        counter = self._local_counters[key]
        
        # Reset if window expired
        if now - counter["window_start"] >= window_seconds:
            counter["count"] = 0
            counter["window_start"] = now
        
        if counter["count"] >= limit:
            reset_at = datetime.fromtimestamp(counter["window_start"] + window_seconds)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=int(reset_at.timestamp() - now),
                limit=limit,
            )
        
        return RateLimitResult(
            allowed=True,
            remaining=limit - counter["count"],
            reset_at=datetime.fromtimestamp(counter["window_start"] + window_seconds),
            limit=limit,
        )
    
    async def _check_burst(
        self,
        key: str,
        limit: int,
    ) -> RateLimitResult:
        """Check burst limit (short window)."""
        return await self._check_window(key, limit, 10)  # 10 second burst window
    
    async def _increment(self, key: str, ttl: int) -> None:
        """Increment counter."""
        now = time.time()
        
        if self.redis:
            try:
                await self.redis.zadd(key, {str(now): now})
                await self.redis.expire(key, ttl)
                return
            except Exception as e:
                logger.warning(f"Redis increment failed: {e}")
        
        # Local fallback
        if key in self._local_counters:
            self._local_counters[key]["count"] += 1
    
    async def get_usage(
        self,
        user_id: str,
        tier: str = "free",
    ) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Args:
            user_id: User ID
            tier: User tier
            
        Returns:
            Usage statistics
        """
        config = self._tier_configs.get(tier, self._tier_configs["free"])
        
        minute_count = await self._get_count(f"ratelimit:{user_id}:minute")
        hour_count = await self._get_count(f"ratelimit:{user_id}:hour")
        day_count = await self._get_count(f"ratelimit:{user_id}:day")
        
        return {
            "user_id": user_id,
            "tier": tier,
            "usage": {
                "minute": {
                    "used": minute_count,
                    "limit": config.requests_per_minute,
                    "remaining": max(0, config.requests_per_minute - minute_count),
                },
                "hour": {
                    "used": hour_count,
                    "limit": config.requests_per_hour,
                    "remaining": max(0, config.requests_per_hour - hour_count),
                },
                "day": {
                    "used": day_count,
                    "limit": config.requests_per_day,
                    "remaining": max(0, config.requests_per_day - day_count),
                },
            },
        }
    
    async def _get_count(self, key: str) -> int:
        """Get current count for a key."""
        if self.redis:
            try:
                return await self.redis.zcard(key)
            except Exception:
                pass
        
        counter = self._local_counters.get(key, {})
        return counter.get("count", 0)
    
    def get_tier_config(self, tier: str) -> RateLimitConfig:
        """Get configuration for a tier."""
        return self._tier_configs.get(tier, self._tier_configs["free"])
    
    def set_tier_config(self, tier: str, config: RateLimitConfig) -> None:
        """Set configuration for a tier."""
        self._tier_configs[tier] = config


# Global rate limiter
_rate_limiter: Optional[WorkflowRateLimiter] = None


def get_rate_limiter(redis_client=None) -> WorkflowRateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = WorkflowRateLimiter(redis_client)
    return _rate_limiter
