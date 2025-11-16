"""
Enhanced Rate Limiter for API endpoints.

Provides flexible rate limiting with Redis backend.
"""

import logging
import time
from typing import Optional
from fastapi import HTTPException, Request
from functools import wraps

logger = logging.getLogger(__name__)


class EnhancedRateLimiter:
    """
    Enhanced rate limiter with multiple strategies.
    
    Features:
    - Per-user rate limiting
    - Per-IP rate limiting
    - Sliding window algorithm
    - Configurable limits
    """
    
    def __init__(self, redis_client):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client for storing rate limit data
        """
        self.redis_client = redis_client
        logger.info("EnhancedRateLimiter initialized")
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique key for rate limiting (e.g., user_id, ip)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if within limit, False otherwise
        """
        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Redis key
            redis_key = f"rate_limit:{key}"
            
            # Remove old entries
            await self.redis_client.zremrangebyscore(
                redis_key,
                0,
                window_start
            )
            
            # Count requests in window
            request_count = await self.redis_client.zcard(redis_key)
            
            if request_count >= max_requests:
                logger.warning(
                    f"Rate limit exceeded: key={key}, "
                    f"count={request_count}, limit={max_requests}"
                )
                return False
            
            # Add current request
            await self.redis_client.zadd(
                redis_key,
                {str(current_time): current_time}
            )
            
            # Set expiry
            await self.redis_client.expire(redis_key, window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiter fails
            return True
    
    async def get_remaining_requests(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """
        Get remaining requests in current window.
        
        Args:
            key: Unique key for rate limiting
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Number of remaining requests
        """
        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            redis_key = f"rate_limit:{key}"
            
            # Remove old entries
            await self.redis_client.zremrangebyscore(
                redis_key,
                0,
                window_start
            )
            
            # Count requests
            request_count = await self.redis_client.zcard(redis_key)
            
            return max(0, max_requests - request_count)
            
        except Exception as e:
            logger.error(f"Failed to get remaining requests: {e}")
            return max_requests


def rate_limit(
    max_requests: int = 60,
    window_seconds: int = 60,
    key_func=None
):
    """
    Rate limit decorator for FastAPI endpoints.
    
    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: user_id)
        
    Example:
        @rate_limit(max_requests=10, window_seconds=60)
        async def my_endpoint(request: Request, current_user: User):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request and user from kwargs
            request = kwargs.get('request')
            current_user = kwargs.get('current_user')
            
            if not request:
                # No request object, skip rate limiting
                return await func(*args, **kwargs)
            
            # Generate rate limit key
            if key_func:
                key = key_func(request, current_user)
            elif current_user:
                key = f"user:{current_user.id}"
            else:
                # Fallback to IP
                key = f"ip:{request.client.host}"
            
            # Get rate limiter from app state
            rate_limiter = getattr(request.app.state, 'rate_limiter', None)
            
            if rate_limiter:
                # Check rate limit
                allowed = await rate_limiter.check_rate_limit(
                    key,
                    max_requests,
                    window_seconds
                )
                
                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds."
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global rate limiter instance
_rate_limiter: Optional[EnhancedRateLimiter] = None


def get_rate_limiter(redis_client) -> EnhancedRateLimiter:
    """
    Get or create global rate limiter.
    
    Args:
        redis_client: Redis client
        
    Returns:
        EnhancedRateLimiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = EnhancedRateLimiter(redis_client)
    
    return _rate_limiter
