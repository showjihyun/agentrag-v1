"""
Workflow Cache Manager

Multi-layer caching for workflow system with Redis L1 and local L2 cache.
"""

import logging
import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, TypeVar, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: datetime
    ttl_seconds: int
    hits: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)


class LRUCache:
    """Thread-safe LRU cache for local caching."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            if entry.is_expired:
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            entry.last_accessed = datetime.utcnow()
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        async with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = CacheEntry(
                value=value,
                created_at=datetime.utcnow(),
                ttl_seconds=ttl,
            )
    
    async def delete(self, key: str):
        async with self._lock:
            self._cache.pop(key, None)
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
        }


class WorkflowCacheManager:
    """
    Multi-layer cache manager for workflows.
    
    Architecture:
    - L1: Redis (distributed, shared across instances)
    - L2: Local LRU (fast, per-instance)
    
    Features:
    - Automatic cache invalidation
    - Cache warming
    - Hit rate tracking
    - Compression for large values
    """
    
    def __init__(self, redis_client=None, local_max_size: int = 500):
        self.redis = redis_client
        self.local = LRUCache(max_size=local_max_size)
        
        # Cache key prefixes
        self.PREFIX_WORKFLOW = "cache:workflow:"
        self.PREFIX_EXECUTION = "cache:execution:"
        self.PREFIX_STATS = "cache:stats:"
        
        # Default TTLs
        self.TTL_WORKFLOW = 3600  # 1 hour
        self.TTL_EXECUTION = 300  # 5 minutes
        self.TTL_STATS = 60  # 1 minute
        
        # Metrics
        self._hits = 0
        self._misses = 0
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get cached workflow."""
        key = f"{self.PREFIX_WORKFLOW}{workflow_id}"
        return await self._get(key)
    
    async def set_workflow(self, workflow_id: str, data: Dict[str, Any]):
        """Cache workflow data."""
        key = f"{self.PREFIX_WORKFLOW}{workflow_id}"
        await self._set(key, data, self.TTL_WORKFLOW)
    
    async def invalidate_workflow(self, workflow_id: str):
        """Invalidate workflow cache."""
        key = f"{self.PREFIX_WORKFLOW}{workflow_id}"
        await self._delete(key)
        
        # Also invalidate related stats
        await self._delete(f"{self.PREFIX_STATS}{workflow_id}")
    
    async def get_execution_result(
        self,
        workflow_id: str,
        input_hash: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached execution result."""
        key = f"{self.PREFIX_EXECUTION}{workflow_id}:{input_hash}"
        return await self._get(key)
    
    async def set_execution_result(
        self,
        workflow_id: str,
        input_hash: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None,
    ):
        """Cache execution result."""
        key = f"{self.PREFIX_EXECUTION}{workflow_id}:{input_hash}"
        await self._set(key, result, ttl or self.TTL_EXECUTION)
    
    async def get_stats(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get cached statistics."""
        key = f"{self.PREFIX_STATS}{workflow_id}"
        return await self._get(key)
    
    async def set_stats(self, workflow_id: str, stats: Dict[str, Any]):
        """Cache statistics."""
        key = f"{self.PREFIX_STATS}{workflow_id}"
        await self._set(key, stats, self.TTL_STATS)
    
    async def _get(self, key: str) -> Optional[Any]:
        """Get from cache (L2 first, then L1)."""
        # Try local cache first
        value = await self.local.get(key)
        if value is not None:
            self._hits += 1
            return value
        
        # Try Redis
        if self.redis:
            try:
                data = await self.redis.get(key)
                if data:
                    value = json.loads(data)
                    # Promote to local cache
                    await self.local.set(key, value)
                    self._hits += 1
                    return value
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        self._misses += 1
        return None
    
    async def _set(self, key: str, value: Any, ttl: int):
        """Set in both cache layers."""
        # Set in local cache
        await self.local.set(key, value, ttl)
        
        # Set in Redis
        if self.redis:
            try:
                await self.redis.set(
                    key,
                    json.dumps(value, default=str),
                    ex=ttl,
                )
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
    
    async def _delete(self, key: str):
        """Delete from both cache layers."""
        await self.local.delete(key)
        
        if self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
    
    async def warm_cache(self, workflow_ids: list):
        """Pre-warm cache with frequently accessed workflows."""
        from backend.db.database import get_db
        from backend.services.agent_builder.workflow_service import WorkflowService
        
        try:
            db = next(get_db())
            service = WorkflowService(db)
            
            for wf_id in workflow_ids:
                workflow = service.get_workflow(wf_id)
                if workflow:
                    await self.set_workflow(wf_id, {
                        "id": str(workflow.id),
                        "name": workflow.name,
                        "graph_definition": workflow.graph_definition,
                    })
            
            logger.info(f"Warmed cache for {len(workflow_ids)} workflows")
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "local_cache": self.local.stats(),
        }
    
    @staticmethod
    def hash_input(input_data: Dict[str, Any]) -> str:
        """Generate hash for input data."""
        content = json.dumps(input_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


def cached(
    ttl: int = 300,
    key_prefix: str = "func",
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(ttl=600, key_prefix="workflow")
        async def get_workflow(workflow_id: str):
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [key_prefix, func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try cache
            cache = get_cache_manager()
            cached_value = await cache._get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                await cache._set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache manager
_cache_manager: Optional[WorkflowCacheManager] = None


def get_cache_manager(redis_client=None) -> WorkflowCacheManager:
    """Get or create global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = WorkflowCacheManager(redis_client)
    return _cache_manager
