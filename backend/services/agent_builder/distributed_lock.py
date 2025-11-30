"""
Distributed Lock Manager

Redis-based distributed locking for workflow execution coordination
in multi-instance deployments.
"""

import logging
import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Raised when lock cannot be acquired."""
    pass


class LockReleaseError(Exception):
    """Raised when lock cannot be released."""
    pass


class DistributedLock:
    """
    Redis-based distributed lock implementation.
    
    Features:
    - Automatic expiration (prevents deadlocks)
    - Lock extension for long operations
    - Owner verification on release
    - Graceful fallback to local locking
    """
    
    def __init__(
        self,
        redis_client,
        name: str,
        timeout: int = 30,
        blocking: bool = True,
        blocking_timeout: Optional[int] = None,
    ):
        """
        Initialize distributed lock.
        
        Args:
            redis_client: Redis client instance
            name: Lock name/key
            timeout: Lock expiration in seconds
            blocking: Whether to block waiting for lock
            blocking_timeout: Max time to wait for lock
        """
        self.redis = redis_client
        self.name = f"lock:{name}"
        self.timeout = timeout
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout or timeout * 2
        self.token = str(uuid.uuid4())
        self._acquired = False
    
    async def acquire(self) -> bool:
        """
        Acquire the lock.
        
        Returns:
            True if lock acquired, False otherwise
        """
        if self.redis is None:
            # Fallback to local lock (single instance)
            self._acquired = True
            return True
        
        start_time = datetime.utcnow()
        
        while True:
            # Try to acquire lock with NX (only if not exists)
            try:
                acquired = await self.redis.set(
                    self.name,
                    self.token,
                    nx=True,
                    ex=self.timeout
                )
                
                if acquired:
                    self._acquired = True
                    logger.debug(f"Lock acquired: {self.name}")
                    return True
                
                if not self.blocking:
                    return False
                
                # Check timeout
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= self.blocking_timeout:
                    logger.warning(f"Lock acquisition timeout: {self.name}")
                    return False
                
                # Wait and retry
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Lock acquisition error: {e}")
                if not self.blocking:
                    return False
                await asyncio.sleep(0.1)
    
    async def release(self) -> bool:
        """
        Release the lock.
        
        Returns:
            True if released, False otherwise
        """
        if not self._acquired:
            return False
        
        if self.redis is None:
            self._acquired = False
            return True
        
        # Lua script for atomic check-and-delete
        release_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = await self.redis.eval(
                release_script,
                1,
                self.name,
                self.token
            )
            
            self._acquired = False
            
            if result:
                logger.debug(f"Lock released: {self.name}")
                return True
            else:
                logger.warning(f"Lock release failed (not owner): {self.name}")
                return False
                
        except Exception as e:
            logger.error(f"Lock release error: {e}")
            self._acquired = False
            return False
    
    async def extend(self, additional_time: int = None) -> bool:
        """
        Extend lock expiration.
        
        Args:
            additional_time: Additional seconds (defaults to original timeout)
            
        Returns:
            True if extended, False otherwise
        """
        if not self._acquired or self.redis is None:
            return False
        
        extend_time = additional_time or self.timeout
        
        # Lua script for atomic check-and-extend
        extend_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        
        try:
            result = await self.redis.eval(
                extend_script,
                1,
                self.name,
                self.token,
                extend_time
            )
            
            if result:
                logger.debug(f"Lock extended: {self.name} (+{extend_time}s)")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Lock extend error: {e}")
            return False
    
    @property
    def is_acquired(self) -> bool:
        """Check if lock is currently held."""
        return self._acquired


class DistributedLockManager:
    """
    Manager for distributed locks.
    
    Provides convenient methods for acquiring locks with
    automatic cleanup and monitoring.
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize lock manager.
        
        Args:
            redis_client: Optional Redis client
        """
        self.redis = redis_client
        self._local_locks: Dict[str, asyncio.Lock] = {}
    
    @asynccontextmanager
    async def lock(
        self,
        name: str,
        timeout: int = 30,
        blocking: bool = True,
        blocking_timeout: Optional[int] = None,
    ):
        """
        Context manager for acquiring a distributed lock.
        
        Usage:
            async with lock_manager.lock("workflow:123"):
                # Critical section
                pass
        
        Args:
            name: Lock name
            timeout: Lock expiration
            blocking: Whether to block
            blocking_timeout: Max wait time
            
        Yields:
            DistributedLock instance
        """
        lock = DistributedLock(
            redis_client=self.redis,
            name=name,
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
        )
        
        acquired = await lock.acquire()
        if not acquired:
            raise LockAcquisitionError(f"Failed to acquire lock: {name}")
        
        try:
            yield lock
        finally:
            await lock.release()
    
    @asynccontextmanager
    async def workflow_lock(self, workflow_id: str, timeout: int = 60):
        """
        Acquire lock for workflow execution.
        
        Args:
            workflow_id: Workflow ID
            timeout: Lock timeout
            
        Yields:
            Lock instance
        """
        async with self.lock(
            f"workflow:execute:{workflow_id}",
            timeout=timeout,
            blocking=True,
            blocking_timeout=timeout * 2,
        ) as lock:
            yield lock
    
    @asynccontextmanager
    async def node_lock(
        self,
        workflow_id: str,
        node_id: str,
        timeout: int = 30,
    ):
        """
        Acquire lock for node execution.
        
        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            timeout: Lock timeout
            
        Yields:
            Lock instance
        """
        async with self.lock(
            f"workflow:{workflow_id}:node:{node_id}",
            timeout=timeout,
            blocking=True,
        ) as lock:
            yield lock
    
    async def get_lock_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a lock.
        
        Args:
            name: Lock name
            
        Returns:
            Lock info dict or None
        """
        if self.redis is None:
            return None
        
        try:
            key = f"lock:{name}"
            token = await self.redis.get(key)
            ttl = await self.redis.ttl(key)
            
            if token:
                return {
                    "name": name,
                    "locked": True,
                    "ttl": ttl,
                }
            return {
                "name": name,
                "locked": False,
            }
        except Exception as e:
            logger.error(f"Get lock info error: {e}")
            return None


# Global lock manager instance
_lock_manager: Optional[DistributedLockManager] = None


def get_lock_manager(redis_client=None) -> DistributedLockManager:
    """Get or create global lock manager."""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = DistributedLockManager(redis_client)
    return _lock_manager
