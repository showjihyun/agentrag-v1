"""
Cache decorator for function results.
"""
import json
import hashlib
from functools import wraps
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


def cache_result(
    ttl: int = 3600,
    key_prefix: Optional[str] = None,
    skip_if_none: bool = True
):
    """
    Decorator to cache function results in Redis.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Custom key prefix (default: function name)
        skip_if_none: Don't cache None results (default: True)
    
    Usage:
        @cache_result(ttl=1800)
        async def get_agent_stats(agent_id: str):
            # Expensive query
            return stats
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from backend.core.dependencies import get_redis_client
            
            try:
                redis_client = await get_redis_client()
                
                # Generate cache key
                prefix = key_prefix or func.__name__
                
                # Create hash of arguments
                args_str = json.dumps({
                    "args": [str(a) for a in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()}
                }, sort_keys=True)
                args_hash = hashlib.md5(args_str.encode()).hexdigest()
                
                cache_key = f"cache:{prefix}:{args_hash}"
                
                # Try to get from cache
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result if not None or skip_if_none is False
                if result is not None or not skip_if_none:
                    await redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                    logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache operation failed, executing without cache: {e}")
                # Fallback: execute without cache
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(key_pattern: str):
    """
    Invalidate cache entries matching pattern.
    
    Args:
        key_pattern: Redis key pattern (e.g., "cache:get_agent_stats:*")
    
    Usage:
        await invalidate_cache("cache:get_agent_stats:*")
    """
    async def _invalidate():
        from backend.core.dependencies import get_redis_client
        
        try:
            redis_client = await get_redis_client()
            
            # Find matching keys
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await redis_client.scan(
                    cursor=cursor,
                    match=key_pattern,
                    count=100
                )
                
                if keys:
                    await redis_client.delete(*keys)
                    deleted_count += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated {deleted_count} cache entries matching '{key_pattern}'")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0
    
    return _invalidate()
