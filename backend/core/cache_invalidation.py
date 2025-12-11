"""
Smart Cache Invalidation with Dependency Tracking

Automatically invalidates dependent cache entries.
"""

from typing import List, Set, Optional
from redis import Redis

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class CacheDependencyGraph:
    """
    Track cache dependencies for smart invalidation
    
    Example:
        workflow:123 depends on user:456
        When user:456 changes, workflow:123 is automatically invalidated
    """
    
    def __init__(self, redis: Redis, prefix: str = "cache_deps"):
        self.redis = redis
        self.prefix = prefix
        self.logger = get_logger(__name__)
    
    def _dep_key(self, key: str) -> str:
        """Get dependency key"""
        return f"{self.prefix}:{key}"
    
    async def add_dependency(self, key: str, depends_on: List[str]):
        """
        Add cache key dependencies
        
        Args:
            key: Cache key
            depends_on: List of keys this key depends on
        """
        for dep in depends_on:
            dep_key = self._dep_key(dep)
            await self.redis.sadd(dep_key, key)
        
        self.logger.debug(
            "cache_dependency_added",
            key=key,
            depends_on=depends_on
        )
    
    async def get_dependents(self, key: str) -> Set[str]:
        """
        Get all keys that depend on this key
        
        Args:
            key: Cache key
            
        Returns:
            Set of dependent keys
        """
        dep_key = self._dep_key(key)
        dependents = await self.redis.smembers(dep_key)
        return {d.decode() if isinstance(d, bytes) else d for d in dependents}
    
    async def invalidate(self, key: str, cascade: bool = True):
        """
        Invalidate key and optionally all dependent keys
        
        Args:
            key: Cache key to invalidate
            cascade: If True, also invalidate dependent keys
        """
        keys_to_delete = [key]
        
        if cascade:
            # Get all dependent keys recursively
            visited = set()
            to_visit = [key]
            
            while to_visit:
                current = to_visit.pop()
                if current in visited:
                    continue
                
                visited.add(current)
                dependents = await self.get_dependents(current)
                
                for dep in dependents:
                    if dep not in visited:
                        to_visit.append(dep)
                        keys_to_delete.append(dep)
        
        # Delete all keys
        if keys_to_delete:
            await self.redis.delete(*keys_to_delete)
            
            self.logger.info(
                "cache_invalidated",
                key=key,
                cascade=cascade,
                keys_deleted=len(keys_to_delete)
            )
    
    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "workflow:*")
        """
        cursor = 0
        deleted_count = 0
        
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            
            if keys:
                await self.redis.delete(*keys)
                deleted_count += len(keys)
            
            if cursor == 0:
                break
        
        self.logger.info(
            "cache_pattern_invalidated",
            pattern=pattern,
            keys_deleted=deleted_count
        )
    
    async def clear_dependencies(self, key: str):
        """
        Clear dependency tracking for a key
        
        Args:
            key: Cache key
        """
        dep_key = self._dep_key(key)
        await self.redis.delete(dep_key)


# Example usage patterns

async def cache_workflow_with_deps(
    redis: Redis,
    workflow_id: int,
    user_id: int,
    data: dict
):
    """
    Cache workflow with dependency tracking
    
    Example:
        workflow:123 depends on user:456 and workflow_list:456
    """
    cache_deps = CacheDependencyGraph(redis)
    
    # Cache the workflow
    key = f"workflow:{workflow_id}"
    await redis.setex(key, 3600, str(data))
    
    # Track dependencies
    await cache_deps.add_dependency(
        key=key,
        depends_on=[
            f"user:{user_id}",
            f"workflow_list:{user_id}"
        ]
    )


async def invalidate_user_cache(redis: Redis, user_id: int):
    """
    Invalidate all user-related caches
    
    This will automatically invalidate:
    - user:123
    - workflow_list:123 (depends on user:123)
    - workflow:456 (depends on workflow_list:123)
    - etc.
    """
    cache_deps = CacheDependencyGraph(redis)
    
    await cache_deps.invalidate(
        key=f"user:{user_id}",
        cascade=True  # Invalidate all dependents
    )
