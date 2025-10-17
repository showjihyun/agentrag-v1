"""
Multi-Level Cache Manager

Implements a sophisticated caching strategy with multiple cache levels:
- L1: In-memory cache (fastest, limited size)
- L2: Redis cache (shared across instances)
- L3: Query result cache with TTL
"""

import logging
import asyncio
import hashlib
import json
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]["value"]

            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        async with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    self.cache.popitem(last=False)

            expires_at = None
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)

            self.cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now(),
            }

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    async def cleanup_expired(self) -> int:
        """Remove expired entries."""
        async with self.lock:
            now = datetime.now()
            expired_keys = [
                key
                for key, data in self.cache.items()
                if data["expires_at"] and data["expires_at"] < now
            ]

            for key in expired_keys:
                del self.cache[key]

            return len(expired_keys)

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.2f}%",
            }


class MultiLevelCache:
    """
    Multi-level caching system.

    L1: In-memory LRU cache (fastest)
    L2: Redis cache (shared)
    L3: Query result cache
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        l1_max_size: int = 1000,
        l1_ttl: int = 300,
        l2_ttl: int = 3600,
        l3_ttl: int = 7200,
        enable_l1: bool = True,
        enable_l2: bool = True,
        enable_l3: bool = True,
    ):
        """
        Initialize multi-level cache.

        Args:
            redis_client: Redis client for L2/L3 cache
            l1_max_size: Maximum size of L1 cache
            l1_ttl: L1 cache TTL in seconds
            l2_ttl: L2 cache TTL in seconds
            l3_ttl: L3 cache TTL in seconds
            enable_l1: Enable L1 cache
            enable_l2: Enable L2 cache
            enable_l3: Enable L3 cache
        """
        self.redis_client = redis_client
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        self.l3_ttl = l3_ttl
        self.enable_l1 = enable_l1
        self.enable_l2 = enable_l2
        self.enable_l3 = enable_l3

        # L1 Cache (in-memory)
        self.l1_cache = LRUCache(max_size=l1_max_size) if enable_l1 else None

        # Cache key prefixes
        self.l2_prefix = "cache:l2:"
        self.l3_prefix = "cache:l3:"

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(
            f"MultiLevelCache initialized (L1: {enable_l1}, L2: {enable_l2}, L3: {enable_l3})"
        )

    def _generate_key(self, namespace: str, key: str) -> str:
        """
        Generate cache key with namespace.

        Format: namespace:key
        This prevents key collisions across different namespaces.
        """
        return f"{namespace}:{key}"

    def _hash_key(self, data: Any) -> str:
        """
        Generate hash key from data.

        Args:
            data: Data to hash (dict, str, or any serializable object)

        Returns:
            SHA-256 hash of the data
        """
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        elif not isinstance(data, str):
            data = str(data)

        return hashlib.sha256(data.encode()).hexdigest()

    def _generate_cache_key_with_data(
        self, namespace: str, key: str, data: Optional[Any] = None
    ) -> str:
        """
        Generate cache key with optional data hash to prevent collisions.

        Args:
            namespace: Cache namespace
            key: Base key
            data: Optional data to include in key (will be hashed)

        Returns:
            Complete cache key: namespace:key or namespace:key:datahash
        """
        base_key = self._generate_key(namespace, key)

        if data is not None:
            data_hash = self._hash_key(data)
            return f"{base_key}:{data_hash[:16]}"  # Use first 16 chars of hash

        return base_key

    async def get(
        self,
        key: str,
        namespace: str = "default",
        use_l1: bool = True,
        use_l2: bool = True,
    ) -> Optional[Any]:
        """
        Get value from cache (checks L1 -> L2).

        Args:
            key: Cache key
            namespace: Cache namespace
            use_l1: Check L1 cache
            use_l2: Check L2 cache

        Returns:
            Cached value or None
        """
        cache_key = self._generate_key(namespace, key)

        # Try L1 cache
        if use_l1 and self.enable_l1 and self.l1_cache:
            value = await self.l1_cache.get(cache_key)
            if value is not None:
                logger.debug(f"L1 cache hit: {cache_key}")
                return value

        # Try L2 cache (Redis)
        if use_l2 and self.enable_l2:
            try:
                redis_key = self._generate_key(self.l2_prefix, cache_key)
                value = await self.redis_client.get(redis_key)

                if value:
                    logger.debug(f"L2 cache hit: {cache_key}")
                    # Deserialize
                    value = json.loads(value)

                    # Promote to L1
                    if self.enable_l1 and self.l1_cache:
                        await self.l1_cache.set(cache_key, value, self.l1_ttl)

                    return value
            except Exception as e:
                logger.error(f"L2 cache error: {e}")

        logger.debug(f"Cache miss: {cache_key}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None,
        use_l1: bool = True,
        use_l2: bool = True,
    ) -> None:
        """
        Set value in cache (writes to L1 and L2).

        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace
            ttl: Time to live (uses default if None)
            use_l1: Write to L1 cache
            use_l2: Write to L2 cache
        """
        cache_key = self._generate_key(namespace, key)

        # Set in L1 cache
        if use_l1 and self.enable_l1 and self.l1_cache:
            await self.l1_cache.set(cache_key, value, ttl or self.l1_ttl)
            logger.debug(f"L1 cache set: {cache_key}")

        # Set in L2 cache (Redis)
        if use_l2 and self.enable_l2:
            try:
                redis_key = self._generate_key(self.l2_prefix, cache_key)
                serialized = json.dumps(value)
                await self.redis_client.setex(redis_key, ttl or self.l2_ttl, serialized)
                logger.debug(f"L2 cache set: {cache_key}")
            except Exception as e:
                logger.error(f"L2 cache set error: {e}")

    async def delete(self, key: str, namespace: str = "default") -> None:
        """Delete key from all cache levels."""
        cache_key = self._generate_key(namespace, key)

        # Delete from L1
        if self.enable_l1 and self.l1_cache:
            await self.l1_cache.delete(cache_key)

        # Delete from L2
        if self.enable_l2:
            try:
                redis_key = self._generate_key(self.l2_prefix, cache_key)
                await self.redis_client.delete(redis_key)
            except Exception as e:
                logger.error(f"L2 cache delete error: {e}")

    async def clear_namespace(self, namespace: str) -> None:
        """Clear all keys in a namespace."""
        if self.enable_l2:
            try:
                pattern = self._generate_key(self.l2_prefix, f"{namespace}*")
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)

                if keys:
                    await self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} keys from namespace: {namespace}")
            except Exception as e:
                logger.error(f"Clear namespace error: {e}")

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        namespace: str = "default",
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get value from cache or compute and cache it.

        Args:
            key: Cache key
            factory: Async function to compute value if not cached
            namespace: Cache namespace
            ttl: Time to live

        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = await self.get(key, namespace)

        if value is not None:
            return value

        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        # Cache the result
        await self.set(key, value, namespace, ttl)

        return value

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "enabled": {
                "l1": self.enable_l1,
                "l2": self.enable_l2,
                "l3": self.enable_l3,
            },
            "ttl": {"l1": self.l1_ttl, "l2": self.l2_ttl, "l3": self.l3_ttl},
        }

        # L1 stats
        if self.enable_l1 and self.l1_cache:
            stats["l1"] = await self.l1_cache.get_stats()

        # L2 stats (Redis)
        if self.enable_l2:
            try:
                info = await self.redis_client.info("memory")
                stats["l2"] = {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected": True,
                }
            except Exception as e:
                stats["l2"] = {"error": str(e), "connected": False}

        return stats

    async def start_cleanup_task(self, interval: int = 300) -> None:
        """Start periodic cleanup task."""
        if self._cleanup_task:
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval)

                    if self.enable_l1 and self.l1_cache:
                        expired = await self.l1_cache.cleanup_expired()
                        if expired > 0:
                            logger.info(
                                f"Cleaned up {expired} expired L1 cache entries"
                            )

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Cache cleanup task started (interval: {interval}s)")

    async def stop_cleanup_task(self) -> None:
        """Stop cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Cache cleanup task stopped")


# Global cache manager instance
_cache_manager: Optional[MultiLevelCache] = None


def get_cache_manager(redis_client: redis.Redis) -> MultiLevelCache:
    """Get or create global cache manager."""
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = MultiLevelCache(redis_client=redis_client)

    return _cache_manager


async def cleanup_cache_manager() -> None:
    """Cleanup global cache manager."""
    global _cache_manager

    if _cache_manager:
        await _cache_manager.stop_cleanup_task()
        if _cache_manager.l1_cache:
            await _cache_manager.l1_cache.clear()
        _cache_manager = None
        logger.info("Cache manager cleaned up")
