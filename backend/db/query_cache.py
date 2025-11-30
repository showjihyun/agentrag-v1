"""
Query Result Caching

Multi-layer caching for database queries:
- L1: In-memory cache (fast, limited size)
- L2: Redis cache (distributed, larger capacity)
"""

import logging
import json
import hashlib
import fnmatch
from typing import Any, Callable, Dict, List, Optional, TypeVar
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LRUCache:
    """Simple LRU cache for L1 caching."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._expiry: Dict[str, datetime] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        # Check expiry
        if key in self._expiry and datetime.utcnow() > self._expiry[key]:
            self.delete(key)
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                # Remove oldest
                oldest_key = next(iter(self._cache))
                self.delete(oldest_key)
        
        self._cache[key] = value
        self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def delete(self, key: str):
        """Delete from cache."""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._expiry.clear()
    
    def clear_pattern(self, pattern: str):
        """Clear keys matching pattern."""
        keys_to_delete = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            self.delete(key)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "utilization_pct": len(self._cache) / self.max_size * 100,
        }


class QueryCache:
    """
    Multi-layer query result cache.
    
    Features:
    - L1 in-memory cache for hot data
    - L2 Redis cache for distributed caching
    - Automatic cache invalidation
    - Cache key generation
    """
    
    # Default TTLs by query type (seconds)
    DEFAULT_TTLS = {
        "workflow_list": 60,
        "workflow_detail": 120,
        "execution_stats": 300,
        "user_summary": 180,
        "node_stats": 300,
        "block_list": 60,
    }
    
    def __init__(
        self,
        redis_client=None,
        l1_max_size: int = 1000,
        default_ttl: int = 300,
    ):
        self.redis = redis_client
        self.l1_cache = LRUCache(max_size=l1_max_size)
        self.default_ttl = default_ttl
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._l1_hits = 0
        self._l2_hits = 0
    
    def _generate_key(self, prefix: str, **params) -> str:
        """Generate cache key from prefix and parameters."""
        # Sort params for consistent key generation
        sorted_params = sorted(params.items())
        param_str = ":".join(f"{k}={v}" for k, v in sorted_params if v is not None)
        
        if param_str:
            return f"qcache:{prefix}:{param_str}"
        return f"qcache:{prefix}"
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for SQL query."""
        return hashlib.md5(query.encode()).hexdigest()[:12]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2)."""
        # Try L1
        value = self.l1_cache.get(key)
        if value is not None:
            self._hits += 1
            self._l1_hits += 1
            return value
        
        # Try L2 (Redis)
        if self.redis:
            try:
                data = await self.redis.get(key)
                if data:
                    value = json.loads(data)
                    # Promote to L1
                    self.l1_cache.set(key, value)
                    self._hits += 1
                    self._l2_hits += 1
                    return value
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
        
        self._misses += 1
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ):
        """Set value in cache (L1 + L2)."""
        ttl = ttl or self.default_ttl
        
        # Set in L1
        self.l1_cache.set(key, value, ttl)
        
        # Set in L2 (Redis)
        if self.redis:
            try:
                await self.redis.set(
                    key,
                    json.dumps(value, default=str),
                    ex=ttl,
                )
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
    
    async def delete(self, key: str):
        """Delete from cache."""
        self.l1_cache.delete(key)
        
        if self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache delete failed: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        # Clear L1
        self.l1_cache.clear_pattern(pattern)
        
        # Clear L2
        if self.redis:
            try:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis pattern invalidation failed: {e}")
    
    async def get_or_execute(
        self,
        key: str,
        query_func: Callable[[], T],
        ttl: Optional[int] = None,
    ) -> T:
        """
        Get from cache or execute query.
        
        Args:
            key: Cache key
            query_func: Function to execute if cache miss
            ttl: Cache TTL in seconds
            
        Returns:
            Query result
        """
        # Try cache
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Execute query
        if asyncio.iscoroutinefunction(query_func):
            result = await query_func()
        else:
            result = query_func()
        
        # Cache result
        await self.set(key, result, ttl)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "total_requests": total,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round(hit_rate, 2),
            "l1_hits": self._l1_hits,
            "l2_hits": self._l2_hits,
            "l1_stats": self.l1_cache.stats(),
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self._hits = 0
        self._misses = 0
        self._l1_hits = 0
        self._l2_hits = 0


def cached_query(
    key_prefix: str,
    ttl: Optional[int] = None,
    key_params: Optional[List[str]] = None,
):
    """
    Decorator for caching query results.
    
    Usage:
        @cached_query("workflow_list", ttl=60, key_params=["user_id", "page"])
        async def get_workflows(user_id: str, page: int = 1):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Get cache instance
            cache = get_query_cache()
            
            # Build cache key
            if key_params:
                params = {k: kwargs.get(k) for k in key_params}
            else:
                params = kwargs
            
            key = cache._generate_key(key_prefix, **params)
            
            # Get or execute
            return await cache.get_or_execute(
                key,
                lambda: func(*args, **kwargs),
                ttl or cache.DEFAULT_TTLS.get(key_prefix, cache.default_ttl),
            )
        
        return wrapper
    return decorator


# Cache invalidation helpers
class CacheInvalidator:
    """Helper for cache invalidation on data changes."""
    
    def __init__(self, cache: QueryCache):
        self.cache = cache
    
    async def on_workflow_change(self, workflow_id: str, user_id: str):
        """Invalidate caches when workflow changes."""
        await self.cache.invalidate_pattern(f"qcache:workflow_detail:*workflow_id={workflow_id}*")
        await self.cache.invalidate_pattern(f"qcache:workflow_list:*user_id={user_id}*")
    
    async def on_execution_complete(self, workflow_id: str, user_id: str):
        """Invalidate caches when execution completes."""
        await self.cache.invalidate_pattern(f"qcache:execution_stats:*workflow_id={workflow_id}*")
        await self.cache.invalidate_pattern(f"qcache:user_summary:*user_id={user_id}*")
    
    async def on_block_change(self, workflow_id: str):
        """Invalidate caches when blocks change."""
        await self.cache.invalidate_pattern(f"qcache:block_list:*workflow_id={workflow_id}*")
        await self.cache.invalidate_pattern(f"qcache:workflow_detail:*workflow_id={workflow_id}*")


# Global cache instance
_query_cache: Optional[QueryCache] = None


def get_query_cache(redis_client=None) -> QueryCache:
    """Get or create global query cache."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache(redis_client)
    return _query_cache


def get_cache_invalidator(cache: Optional[QueryCache] = None) -> CacheInvalidator:
    """Get cache invalidator."""
    return CacheInvalidator(cache or get_query_cache())
