"""
Advanced caching strategies for performance optimization.
"""
import json
import hashlib
from functools import wraps
from typing import Callable, Any, Optional, List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheStrategy:
    """Advanced caching strategies."""
    
    # Cache TTL configurations (in seconds)
    TTL_SHORT = 300  # 5 minutes - frequently changing data
    TTL_MEDIUM = 1800  # 30 minutes - moderately stable data
    TTL_LONG = 3600  # 1 hour - stable data
    TTL_VERY_LONG = 7200  # 2 hours - rarely changing data
    
    # Cache key prefixes
    PREFIX_AGENT_STATS = "agent_stats"
    PREFIX_USER_STATS = "user_stats"
    PREFIX_TOOL_EXECUTION = "tool_exec"
    PREFIX_WORKFLOW_STATS = "workflow_stats"
    PREFIX_AGENT_LIST = "agent_list"
    PREFIX_TOOL_LIST = "tool_list"
    
    @staticmethod
    def generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate consistent cache key from arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create hash of arguments
        args_str = json.dumps({
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
        }, sort_keys=True)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]
        
        return f"cache:{prefix}:{args_hash}"
    
    @staticmethod
    async def get_or_compute(
        redis_client,
        cache_key: str,
        compute_func: Callable,
        ttl: int,
        *args,
        **kwargs
    ) -> Any:
        """
        Get from cache or compute and cache result.
        
        Args:
            redis_client: Redis client instance
            cache_key: Cache key
            compute_func: Function to compute value if not cached
            ttl: Time to live in seconds
            *args: Arguments for compute_func
            **kwargs: Keyword arguments for compute_func
            
        Returns:
            Cached or computed value
        """
        try:
            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
            
            # Compute value
            logger.debug(f"Cache miss: {cache_key}, computing...")
            result = await compute_func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                await redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                logger.debug(f"Cached: {cache_key} (TTL: {ttl}s)")
            
            return result
            
        except Exception as e:
            logger.warning(f"Cache operation failed: {e}, computing without cache")
            return await compute_func(*args, **kwargs)
    
    @staticmethod
    async def invalidate_pattern(redis_client, pattern: str) -> int:
        """
        Invalidate all cache keys matching pattern.
        
        Args:
            redis_client: Redis client instance
            pattern: Key pattern (e.g., "cache:agent_stats:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await redis_client.delete(*keys)
                    deleted_count += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated {deleted_count} keys matching '{pattern}'")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0
    
    @staticmethod
    async def warm_cache(
        redis_client,
        cache_entries: List[Dict[str, Any]]
    ) -> int:
        """
        Warm cache with pre-computed values.
        
        Args:
            redis_client: Redis client instance
            cache_entries: List of dicts with 'key', 'value', 'ttl'
            
        Returns:
            Number of entries cached
        """
        try:
            cached_count = 0
            
            for entry in cache_entries:
                key = entry['key']
                value = entry['value']
                ttl = entry.get('ttl', CacheStrategy.TTL_MEDIUM)
                
                await redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
                cached_count += 1
            
            logger.info(f"Warmed cache with {cached_count} entries")
            return cached_count
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return 0
    
    @staticmethod
    async def get_cache_stats(redis_client) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Args:
            redis_client: Redis client instance
            
        Returns:
            Cache statistics
        """
        try:
            info = await redis_client.info('stats')
            
            return {
                "total_keys": await redis_client.dbsize(),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "hit_rate": (
                    info.get('keyspace_hits', 0) / 
                    (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))
                    * 100
                ),
                "memory_used": info.get('used_memory_human', 'N/A'),
                "evicted_keys": info.get('evicted_keys', 0),
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


def cache_with_strategy(
    strategy: str = "medium",
    key_prefix: Optional[str] = None,
    skip_if_none: bool = True,
    invalidate_on: Optional[List[str]] = None
):
    """
    Advanced cache decorator with strategy support.
    
    Args:
        strategy: Cache strategy (short, medium, long, very_long)
        key_prefix: Custom key prefix
        skip_if_none: Don't cache None results
        invalidate_on: List of events that should invalidate this cache
        
    Usage:
        @cache_with_strategy(strategy="long", key_prefix="agent_stats")
        async def get_agent_stats(agent_id: str):
            return expensive_query()
    """
    # Map strategy to TTL
    ttl_map = {
        "short": CacheStrategy.TTL_SHORT,
        "medium": CacheStrategy.TTL_MEDIUM,
        "long": CacheStrategy.TTL_LONG,
        "very_long": CacheStrategy.TTL_VERY_LONG,
    }
    ttl = ttl_map.get(strategy, CacheStrategy.TTL_MEDIUM)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from backend.core.dependencies import get_redis_client
            
            try:
                redis_client = await get_redis_client()
                
                # Generate cache key
                prefix = key_prefix or func.__name__
                cache_key = CacheStrategy.generate_cache_key(prefix, *args, **kwargs)
                
                # Get or compute
                result = await CacheStrategy.get_or_compute(
                    redis_client,
                    cache_key,
                    func,
                    ttl,
                    *args,
                    **kwargs
                )
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache operation failed: {e}, executing without cache")
                return await func(*args, **kwargs)
        
        # Store metadata for cache invalidation
        wrapper._cache_metadata = {
            "key_prefix": key_prefix or func.__name__,
            "invalidate_on": invalidate_on or []
        }
        
        return wrapper
    return decorator


class CacheInvalidator:
    """Centralized cache invalidation manager."""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    async def invalidate_agent_caches(self, agent_id: str):
        """Invalidate all caches related to an agent."""
        patterns = [
            f"cache:{CacheStrategy.PREFIX_AGENT_STATS}:*{agent_id}*",
            f"cache:{CacheStrategy.PREFIX_AGENT_LIST}:*",
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await CacheStrategy.invalidate_pattern(
                self.redis_client, 
                pattern
            )
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} agent-related caches")
        return total_deleted
    
    async def invalidate_user_caches(self, user_id: str):
        """Invalidate all caches related to a user."""
        patterns = [
            f"cache:{CacheStrategy.PREFIX_USER_STATS}:*{user_id}*",
            f"cache:{CacheStrategy.PREFIX_AGENT_LIST}:*{user_id}*",
            f"cache:{CacheStrategy.PREFIX_WORKFLOW_STATS}:*{user_id}*",
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await CacheStrategy.invalidate_pattern(
                self.redis_client,
                pattern
            )
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} user-related caches")
        return total_deleted
    
    async def invalidate_tool_caches(self, tool_id: str):
        """Invalidate all caches related to a tool."""
        patterns = [
            f"cache:{CacheStrategy.PREFIX_TOOL_EXECUTION}:*{tool_id}*",
            f"cache:{CacheStrategy.PREFIX_TOOL_LIST}:*",
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await CacheStrategy.invalidate_pattern(
                self.redis_client,
                pattern
            )
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} tool-related caches")
        return total_deleted
