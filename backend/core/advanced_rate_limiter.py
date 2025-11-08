"""
Advanced Rate Limiting with Token Bucket Algorithm

Provides sophisticated rate limiting with multiple strategies.
"""

import time
import logging
from typing import Tuple, Optional, Dict
from enum import Enum

import redis.asyncio as redis


logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategy."""
    
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter.
    
    Allows burst traffic while maintaining average rate.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        capacity: int = 100,
        refill_rate: float = 10.0,  # tokens per second
        key_prefix: str = "rate_limit:token_bucket"
    ):
        """
        Initialize Token Bucket Rate Limiter.
        
        Args:
            redis_client: Redis client
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
            key_prefix: Redis key prefix
        """
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.key_prefix = key_prefix
        
        # Lua script for atomic token bucket operation
        self.lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local cost = tonumber(ARGV[4])
        
        -- Get current bucket state
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now
        
        -- Calculate tokens to add
        local elapsed = now - last_refill
        local tokens_to_add = elapsed * refill_rate
        tokens = math.min(capacity, tokens + tokens_to_add)
        
        -- Try to consume tokens
        if tokens >= cost then
            tokens = tokens - cost
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            return {1, math.floor(tokens)}
        else
            -- Calculate wait time
            local tokens_needed = cost - tokens
            local wait_time = math.ceil(tokens_needed / refill_rate)
            return {0, 0, wait_time}
        end
        """
    
    async def allow_request(
        self,
        identifier: str,
        cost: int = 1
    ) -> Tuple[bool, int, Optional[int]]:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier (user_id, IP, etc.)
            cost: Token cost for this request
            
        Returns:
            Tuple of (allowed, remaining_tokens, wait_time_seconds)
        """
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        
        try:
            result = await self.redis.eval(
                self.lua_script,
                1,
                key,
                self.capacity,
                self.refill_rate,
                now,
                cost
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            wait_time = int(result[2]) if len(result) > 2 else None
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier}",
                    extra={
                        "identifier": identifier,
                        "remaining": remaining,
                        "wait_time": wait_time
                    }
                )
            
            return allowed, remaining, wait_time
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}", exc_info=True)
            # Fail open (allow request on error)
            return True, self.capacity, None
    
    async def get_status(self, identifier: str) -> Dict[str, any]:
        """
        Get current rate limit status.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Status dictionary
        """
        key = f"{self.key_prefix}:{identifier}"
        
        try:
            bucket = await self.redis.hmget(key, "tokens", "last_refill")
            
            if bucket[0] is None:
                return {
                    "tokens": self.capacity,
                    "capacity": self.capacity,
                    "refill_rate": self.refill_rate,
                    "last_refill": None
                }
            
            tokens = float(bucket[0])
            last_refill = float(bucket[1])
            
            # Calculate current tokens
            now = time.time()
            elapsed = now - last_refill
            tokens_to_add = elapsed * self.refill_rate
            current_tokens = min(self.capacity, tokens + tokens_to_add)
            
            return {
                "tokens": current_tokens,
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "last_refill": last_refill
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {
                "tokens": self.capacity,
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
                "last_refill": None
            }
    
    async def reset(self, identifier: str):
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: Unique identifier
        """
        key = f"{self.key_prefix}:{identifier}"
        await self.redis.delete(key)
        
        logger.info(f"Rate limit reset for {identifier}")


class SlidingWindowRateLimiter:
    """
    Sliding Window Rate Limiter.
    
    More accurate than fixed window, prevents burst at window boundaries.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit:sliding_window"
    ):
        """
        Initialize Sliding Window Rate Limiter.
        
        Args:
            redis_client: Redis client
            max_requests: Maximum requests per window
            window_seconds: Window size in seconds
            key_prefix: Redis key prefix
        """
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        
        # Lua script for atomic sliding window operation
        self.lua_script = """
        local key = KEYS[1]
        local max_requests = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        -- Remove old entries
        local min_time = now - window
        redis.call('ZREMRANGEBYSCORE', key, '-inf', min_time)
        
        -- Count current requests
        local count = redis.call('ZCARD', key)
        
        if count < max_requests then
            -- Add new request
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, window)
            return {1, max_requests - count - 1}
        else
            -- Get oldest request time
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local reset_time = 0
            if #oldest > 0 then
                reset_time = math.ceil(tonumber(oldest[2]) + window - now)
            end
            return {0, 0, reset_time}
        end
        """
    
    async def allow_request(
        self,
        identifier: str
    ) -> Tuple[bool, int, Optional[int]]:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Tuple of (allowed, remaining_requests, reset_time_seconds)
        """
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        
        try:
            result = await self.redis.eval(
                self.lua_script,
                1,
                key,
                self.max_requests,
                self.window_seconds,
                now
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            reset_time = int(result[2]) if len(result) > 2 else None
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier}",
                    extra={
                        "identifier": identifier,
                        "remaining": remaining,
                        "reset_time": reset_time
                    }
                )
            
            return allowed, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}", exc_info=True)
            return True, self.max_requests, None
    
    async def get_status(self, identifier: str) -> Dict[str, any]:
        """
        Get current rate limit status.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Status dictionary
        """
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        min_time = now - self.window_seconds
        
        try:
            # Remove old entries
            await self.redis.zremrangebyscore(key, '-inf', min_time)
            
            # Count current requests
            count = await self.redis.zcard(key)
            
            return {
                "requests": count,
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "remaining": self.max_requests - count
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {
                "requests": 0,
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "remaining": self.max_requests
            }
    
    async def reset(self, identifier: str):
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: Unique identifier
        """
        key = f"{self.key_prefix}:{identifier}"
        await self.redis.delete(key)
        
        logger.info(f"Rate limit reset for {identifier}")


class AdaptiveRateLimiter:
    """
    Adaptive Rate Limiter.
    
    Adjusts rate limits based on system load and user behavior.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        base_capacity: int = 100,
        base_refill_rate: float = 10.0,
        key_prefix: str = "rate_limit:adaptive"
    ):
        """
        Initialize Adaptive Rate Limiter.
        
        Args:
            redis_client: Redis client
            base_capacity: Base token capacity
            base_refill_rate: Base refill rate
            key_prefix: Redis key prefix
        """
        self.redis = redis_client
        self.base_capacity = base_capacity
        self.base_refill_rate = base_refill_rate
        self.key_prefix = key_prefix
        
        # Token bucket for each user
        self.token_bucket = TokenBucketRateLimiter(
            redis_client=redis_client,
            capacity=base_capacity,
            refill_rate=base_refill_rate,
            key_prefix=key_prefix
        )
    
    async def allow_request(
        self,
        identifier: str,
        user_tier: str = "free",
        system_load: float = 0.5
    ) -> Tuple[bool, int, Optional[int]]:
        """
        Check if request is allowed with adaptive limits.
        
        Args:
            identifier: Unique identifier
            user_tier: User tier (free, pro, enterprise)
            system_load: System load (0.0 to 1.0)
            
        Returns:
            Tuple of (allowed, remaining_tokens, wait_time_seconds)
        """
        # Adjust capacity based on user tier
        tier_multipliers = {
            "free": 1.0,
            "pro": 2.0,
            "enterprise": 5.0
        }
        tier_multiplier = tier_multipliers.get(user_tier, 1.0)
        
        # Adjust based on system load
        load_multiplier = 1.0 - (system_load * 0.5)  # Reduce by up to 50% under high load
        
        # Calculate adjusted limits
        adjusted_capacity = int(self.base_capacity * tier_multiplier * load_multiplier)
        adjusted_refill_rate = self.base_refill_rate * tier_multiplier * load_multiplier
        
        # Update token bucket limits
        self.token_bucket.capacity = adjusted_capacity
        self.token_bucket.refill_rate = adjusted_refill_rate
        
        return await self.token_bucket.allow_request(identifier)
