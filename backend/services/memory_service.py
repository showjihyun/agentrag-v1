"""
Memory Service

Provides memory storage and retrieval for agents with support for
different memory types (STM, LTM, Entity, Contextual).
"""

import logging
from typing import Any, Optional, Dict, List
import json
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for agent memory management using Redis."""
    
    def __init__(self, redis_url: str = "redis://localhost:6380"):
        """
        Initialize Memory service.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Connected to Redis for memory service")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Disconnected from Redis")
    
    async def store(
        self,
        namespace: str,
        key: str,
        value: Any,
        memory_type: str = "short_term",
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store data in memory.
        
        Args:
            namespace: Memory namespace (e.g., user_id, session_id)
            key: Memory key
            value: Value to store (will be JSON serialized)
            memory_type: Type of memory (short_term, long_term, entity, contextual)
            ttl: Time to live in seconds (None for permanent)
            metadata: Optional metadata to store with the value
            
        Returns:
            Result dict with success status
        """
        await self.connect()
        
        try:
            full_key = self._build_key(namespace, memory_type, key)
            
            # Prepare data to store
            data = {
                "value": value,
                "memory_type": memory_type,
                "namespace": namespace,
                "key": key,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
            
            serialized = json.dumps(data)
            
            # Store with TTL if specified
            if ttl:
                await self.redis_client.setex(full_key, ttl, serialized)
            else:
                await self.redis_client.set(full_key, serialized)
            
            logger.info(f"Stored memory: {full_key} (TTL: {ttl})")
            
            return {
                "success": True,
                "namespace": namespace,
                "key": key,
                "memory_type": memory_type,
                "ttl": ttl,
            }
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve(
        self,
        namespace: str,
        key: str,
        memory_type: str = "short_term",
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from memory.
        
        Args:
            namespace: Memory namespace
            key: Memory key
            memory_type: Type of memory
            
        Returns:
            Stored data or None if not found
        """
        await self.connect()
        
        try:
            full_key = self._build_key(namespace, memory_type, key)
            
            value = await self.redis_client.get(full_key)
            
            if value:
                data = json.loads(value)
                logger.info(f"Retrieved memory: {full_key}")
                return data
            
            logger.info(f"Memory not found: {full_key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            raise
    
    async def update(
        self,
        namespace: str,
        key: str,
        value: Any,
        memory_type: str = "short_term",
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update existing memory.
        
        Args:
            namespace: Memory namespace
            key: Memory key
            value: New value
            memory_type: Type of memory
            ttl: Optional new TTL
            
        Returns:
            Result dict with success status
        """
        await self.connect()
        
        try:
            # Get existing data to preserve metadata
            existing = await self.retrieve(namespace, key, memory_type)
            
            metadata = existing.get("metadata", {}) if existing else {}
            metadata["updated_at"] = datetime.utcnow().isoformat()
            
            # Store updated value
            return await self.store(
                namespace=namespace,
                key=key,
                value=value,
                memory_type=memory_type,
                ttl=ttl,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            raise
    
    async def delete(
        self,
        namespace: str,
        key: str,
        memory_type: str = "short_term",
    ) -> Dict[str, Any]:
        """
        Delete memory.
        
        Args:
            namespace: Memory namespace
            key: Memory key
            memory_type: Type of memory
            
        Returns:
            Result dict with success status
        """
        await self.connect()
        
        try:
            full_key = self._build_key(namespace, memory_type, key)
            
            deleted = await self.redis_client.delete(full_key)
            
            logger.info(f"Deleted memory: {full_key} (existed: {deleted > 0})")
            
            return {
                "success": True,
                "deleted": deleted > 0,
                "namespace": namespace,
                "key": key,
                "memory_type": memory_type,
            }
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            raise
    
    async def clear_namespace(
        self,
        namespace: str,
        memory_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clear all memories in a namespace.
        
        Args:
            namespace: Memory namespace to clear
            memory_type: Optional specific memory type to clear
            
        Returns:
            Result dict with count of deleted keys
        """
        await self.connect()
        
        try:
            if memory_type:
                pattern = self._build_key(namespace, memory_type, "*")
            else:
                pattern = f"memory:{namespace}:*"
            
            # Find all matching keys
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete all keys
            if keys:
                deleted = await self.redis_client.delete(*keys)
            else:
                deleted = 0
            
            logger.info(f"Cleared {deleted} memories from namespace: {namespace}")
            
            return {
                "success": True,
                "deleted_count": deleted,
                "namespace": namespace,
                "memory_type": memory_type,
            }
            
        except Exception as e:
            logger.error(f"Failed to clear namespace: {e}")
            raise
    
    async def list_keys(
        self,
        namespace: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[str]:
        """
        List all keys in a namespace.
        
        Args:
            namespace: Memory namespace
            memory_type: Optional specific memory type
            limit: Maximum number of keys to return
            
        Returns:
            List of keys
        """
        await self.connect()
        
        try:
            if memory_type:
                pattern = self._build_key(namespace, memory_type, "*")
            else:
                pattern = f"memory:{namespace}:*"
            
            keys = []
            count = 0
            async for key in self.redis_client.scan_iter(match=pattern):
                # Extract just the key part
                parts = key.split(":")
                if len(parts) >= 4:
                    keys.append(parts[3])
                count += 1
                if count >= limit:
                    break
            
            logger.info(f"Listed {len(keys)} keys from namespace: {namespace}")
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            raise
    
    async def get_ttl(
        self,
        namespace: str,
        key: str,
        memory_type: str = "short_term",
    ) -> Optional[int]:
        """
        Get remaining TTL for a key.
        
        Args:
            namespace: Memory namespace
            key: Memory key
            memory_type: Type of memory
            
        Returns:
            Remaining TTL in seconds, or None if no TTL
        """
        await self.connect()
        
        try:
            full_key = self._build_key(namespace, memory_type, key)
            ttl = await self.redis_client.ttl(full_key)
            
            # -1 means no expiry, -2 means key doesn't exist
            if ttl == -1:
                return None
            elif ttl == -2:
                return None
            else:
                return ttl
                
        except Exception as e:
            logger.error(f"Failed to get TTL: {e}")
            raise
    
    def _build_key(self, namespace: str, memory_type: str, key: str) -> str:
        """
        Build full Redis key.
        
        Args:
            namespace: Memory namespace
            memory_type: Type of memory
            key: Memory key
            
        Returns:
            Full Redis key
        """
        return f"memory:{namespace}:{memory_type}:{key}"
    
    async def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if healthy
        """
        try:
            await self.connect()
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Memory service health check failed: {e}")
            return False


# Singleton instance
_memory_service: Optional[MemoryService] = None


def get_memory_service(redis_url: str = "redis://localhost:6380") -> MemoryService:
    """
    Get or create memory service singleton.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        MemoryService instance
    """
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(redis_url)
    return _memory_service
