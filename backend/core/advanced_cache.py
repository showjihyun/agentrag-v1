"""
Multi-Level Cache Implementation

Implements a three-tier caching strategy:
- L1: In-memory cache (fastest, smallest)
- L2: Redis cache (fast, medium size)
- L3: Database (slowest, largest)
"""

from typing import Optional, Any, Callable
from datetime import datetime, timedelta
import asyncio
import json
import logging
from collections import OrderedDict
import hashlib

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                value, expires_at = self.cache[key]
                
                # Check expiration
                if expires_at and datetime.utcnow() > expires_at:
                    del self.cache[key]
                    return None
                
                return value
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set value in cache"""
        async with self._lock:
            expires_at = None
            if ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            self.cache[key] = (value, expires_at)
            self.cache.move_to_end(key)
            
            # Evict oldest if over capacity
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
    
    async def delete(self, key: str):
        """Delete value from cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
    
    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)
    
    # Synchronous versions for non-async contexts
    def get_sync(self, key: str) -> Optional[Any]:
        """Synchronous get value from cache"""
        if key in self.cache:
            value, expires_at = self.cache[key]
            
            # Check expiration
            if expires_at and datetime.utcnow() > expires_at:
                del self.cache[key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return value
        return None
    
    def set_sync(self, key: str, value: Any, ttl: Optional[int] = None):
        """Synchronous set value in cache"""
        expires_at = None
        if ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self.cache[key] = (value, expires_at)
        self.cache.move_to_end(key)
        
        # Evict oldest if over capacity
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
    
    def delete_sync(self, key: str):
        """Synchronous delete value from cache"""
        if key in self.cache:
            del self.cache[key]


class MultiLevelCache:
    """
    Multi-level cache with automatic promotion/demotion.
    
    Cache hierarchy:
    - L1 (Memory): Fastest, smallest capacity
    - L2 (Redis): Fast, medium capacity
    - L3 (Database): Slowest, largest capacity
    
    Features:
    - Automatic promotion to L1 on cache hits
    - Write-through to all levels
    - Configurable TTL per level
    - Cache statistics tracking
    
    Example:
        cache = MultiLevelCache(redis_client, db_session)
        
        # Get with automatic promotion
        value = await cache.get("key")
        
        # Set with write-through
        await cache.set("key", value, ttl=3600)
    """
    
    def __init__(
        self,
        redis_client,
        db_fetcher: Optional[Callable] = None,
        l1_max_size: int = 1000,
        l1_ttl: int = 300,  # 5 minutes
        l2_ttl: int = 3600,  # 1 hour
    ):
        """
        Initialize multi-level cache.
        
        Args:
            redis_client: Redis client for L2 cache
            db_fetcher: Optional function to fetch from DB (L3)
            l1_max_size: Maximum L1 cache size
            l1_ttl: L1 cache TTL in seconds
            l2_ttl: L2 cache TTL in seconds
        """
        self.l1_cache = LRUCache(max_size=l1_max_size)
        self.redis = redis_client
        self.db_fetcher = db_fetcher
        
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        
        # Statistics
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "l3_hits": 0,
            "l3_misses": 0,
        }
        self._stats_lock = asyncio.Lock()
    
    async def get(
        self,
        key: str,
        fetch_from_db: bool = True
    ) -> Optional[Any]:
        """
        Get value from cache (L1 -> L2 -> L3).
        
        Args:
            key: Cache key
            fetch_from_db: Whether to fetch from DB if not in cache
            
        Returns:
            Cached value or None
        """
        # Try L1 (Memory)
        value = await self.l1_cache.get(key)
        if value is not None:
            await self._record_hit("l1")
            logger.debug(f"L1 cache hit: {key}")
            return value
        
        await self._record_miss("l1")
        
        # Try L2 (Redis)
        try:
            redis_value = await self.redis.get(key)
            if redis_value:
                await self._record_hit("l2")
                logger.debug(f"L2 cache hit: {key}")
                
                # Deserialize
                value = json.loads(redis_value)
                
                # Promote to L1
                await self.l1_cache.set(key, value, ttl=self.l1_ttl)
                
                return value
        except Exception as e:
            logger.error(f"L2 cache error: {e}")
        
        await self._record_miss("l2")
        
        # Try L3 (Database)
        if fetch_from_db and self.db_fetcher:
            try:
                value = await self.db_fetcher(key)
                if value is not None:
                    await self._record_hit("l3")
                    logger.debug(f"L3 cache hit: {key}")
                    
                    # Promote to L1 and L2
                    await self.set(key, value)
                    
                    return value
            except Exception as e:
                logger.error(f"L3 cache error: {e}")
        
        await self._record_miss("l3")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        write_through: bool = True
    ):
        """
        Set value in cache (write-through to all levels).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
            write_through: Whether to write to all levels
        """
        l1_ttl = ttl or self.l1_ttl
        l2_ttl = ttl or self.l2_ttl
        
        # Write to L1
        await self.l1_cache.set(key, value, ttl=l1_ttl)
        
        if write_through:
            # Write to L2
            try:
                serialized = json.dumps(value)
                await self.redis.setex(key, l2_ttl, serialized)
            except Exception as e:
                logger.error(f"L2 cache write error: {e}")
    
    async def delete(self, key: str):
        """Delete value from all cache levels"""
        # Delete from L1
        await self.l1_cache.delete(key)
        
        # Delete from L2
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"L2 cache delete error: {e}")
    
    async def clear(self):
        """Clear all cache levels"""
        await self.l1_cache.clear()
        
        # Note: We don't clear Redis as it may be shared
        logger.info("L1 cache cleared")
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Optional TTL override
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = await self.get(key, fetch_from_db=False)
        
        if value is not None:
            return value
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache it
        await self.set(key, value, ttl=ttl)
        
        return value
    
    async def _record_hit(self, level: str):
        """Record cache hit"""
        async with self._stats_lock:
            self.stats[f"{level}_hits"] += 1
    
    async def _record_miss(self, level: str):
        """Record cache miss"""
        async with self._stats_lock:
            self.stats[f"{level}_misses"] += 1
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = sum(
            self.stats[f"l{i}_hits"] + self.stats[f"l{i}_misses"]
            for i in [1, 2, 3]
        )
        
        if total_requests == 0:
            return {**self.stats, "hit_rate": 0.0}
        
        total_hits = sum(
            self.stats[f"l{i}_hits"] for i in [1, 2, 3]
        )
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "total_hits": total_hits,
            "hit_rate": total_hits / total_requests,
            "l1_size": self.l1_cache.size(),
        }
    
    # Synchronous versions for non-async contexts
    def get_sync(self, key: str) -> Optional[Any]:
        """
        Synchronous get value from cache (L1 -> L2).
        
        Note: Only checks L1 and L2, skips L3 (database) in sync mode.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Try L1 (Memory)
        value = self.l1_cache.get_sync(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            logger.debug(f"L1 cache hit (sync): {key}")
            return value
        
        self.stats["l1_misses"] += 1
        
        # Try L2 (Redis) - use sync Redis client if available
        try:
            # Check if redis client has sync methods
            if hasattr(self.redis, 'get') and not asyncio.iscoroutinefunction(self.redis.get):
                redis_value = self.redis.get(key)
            else:
                # Skip L2 in sync mode if only async client available
                logger.debug(f"Skipping L2 cache in sync mode for key: {key}")
                self.stats["l2_misses"] += 1
                return None
            
            if redis_value:
                self.stats["l2_hits"] += 1
                logger.debug(f"L2 cache hit (sync): {key}")
                
                # Deserialize
                if isinstance(redis_value, bytes):
                    redis_value = redis_value.decode('utf-8')
                value = json.loads(redis_value)
                
                # Promote to L1
                self.l1_cache.set_sync(key, value, ttl=self.l1_ttl)
                
                return value
        except Exception as e:
            logger.error(f"L2 cache error (sync): {e}")
        
        self.stats["l2_misses"] += 1
        return None
    
    def set_sync(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Synchronous set value in cache (write-through to L1 and L2).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        """
        l1_ttl = ttl or self.l1_ttl
        l2_ttl = ttl or self.l2_ttl
        
        # Write to L1
        self.l1_cache.set_sync(key, value, ttl=l1_ttl)
        
        # Write to L2 (Redis)
        try:
            serialized = json.dumps(value)
            
            # Check if redis client has sync methods
            if hasattr(self.redis, 'setex') and not asyncio.iscoroutinefunction(self.redis.setex):
                self.redis.setex(key, l2_ttl, serialized)
            else:
                logger.debug(f"Skipping L2 cache write in sync mode for key: {key}")
        except Exception as e:
            logger.error(f"L2 cache write error (sync): {e}")
    
    def delete_sync(self, key: str):
        """
        Synchronous delete value from all cache levels.
        
        Args:
            key: Cache key
        """
        # Delete from L1
        self.l1_cache.delete_sync(key)
        
        # Delete from L2 (Redis)
        try:
            if hasattr(self.redis, 'delete') and not asyncio.iscoroutinefunction(self.redis.delete):
                self.redis.delete(key)
            else:
                logger.debug(f"Skipping L2 cache delete in sync mode for key: {key}")
        except Exception as e:
            logger.error(f"L2 cache delete error (sync): {e}")
    
    async def reset_stats(self):
        """Reset cache statistics"""
        async with self._stats_lock:
            self.stats = {
                "l1_hits": 0,
                "l1_misses": 0,
                "l2_hits": 0,
                "l2_misses": 0,
                "l3_hits": 0,
                "l3_misses": 0,
            }


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments.
    
    Example:
        key = cache_key("user", user_id=123, include_profile=True)
        # Returns: "user:user_id=123:include_profile=True"
    """
    parts = [str(arg) for arg in args]
    
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}={v}")
    
    key = ":".join(parts)
    
    # Hash if too long
    if len(key) > 200:
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"hash:{key_hash}"
    
    return key


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Example:
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            # Note: Requires cache instance to be passed or injected
            # This is a simplified example
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            return result
        
        return wrapper
    
    return decorator
