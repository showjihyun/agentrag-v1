"""
Shared Memory Pool for Multi-Agent Systems.

Provides shared memory and context management for agents to collaborate.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from collections import defaultdict
import asyncio

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SharedMemoryPool:
    """
    Shared memory pool for agent collaboration.
    
    Features:
    - Conversation history sharing
    - Intermediate result caching
    - Context propagation
    - Memory scoping (global, session, agent)
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        ttl: int = 3600
    ):
        """
        Initialize shared memory pool.
        
        Args:
            redis_client: Redis client for distributed memory
            ttl: Time-to-live for memory entries in seconds
        """
        self.redis_client = redis_client
        self.ttl = ttl
        self.local_memory: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        logger.info("SharedMemoryPool initialized")
    
    async def set(
        self,
        scope: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in shared memory.
        
        Args:
            scope: Memory scope (e.g., "session:123", "agent:456")
            key: Memory key
            value: Value to store
            ttl: Optional TTL override
            
        Returns:
            Success status
        """
        try:
            memory_key = f"{scope}:{key}"
            serialized_value = json.dumps(value)
            
            if self.redis_client:
                await self.redis_client.setex(
                    memory_key,
                    ttl or self.ttl,
                    serialized_value
                )
            else:
                self.local_memory[scope][key] = {
                    "value": value,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            logger.debug(f"Set memory: {memory_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set memory: {e}")
            return False
    
    async def get(
        self,
        scope: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get value from shared memory.
        
        Args:
            scope: Memory scope
            key: Memory key
            default: Default value if not found
            
        Returns:
            Stored value or default
        """
        try:
            memory_key = f"{scope}:{key}"
            
            if self.redis_client:
                value = await self.redis_client.get(memory_key)
                if value:
                    return json.loads(value)
            else:
                entry = self.local_memory.get(scope, {}).get(key)
                if entry:
                    return entry["value"]
            
            return default
            
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            return default
    
    async def append(
        self,
        scope: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Append value to a list in shared memory.
        
        Args:
            scope: Memory scope
            key: Memory key
            value: Value to append
            
        Returns:
            Success status
        """
        try:
            current = await self.get(scope, key, [])
            if not isinstance(current, list):
                current = [current]
            
            current.append(value)
            return await self.set(scope, key, current)
            
        except Exception as e:
            logger.error(f"Failed to append to memory: {e}")
            return False
    
    async def get_all(self, scope: str) -> Dict[str, Any]:
        """
        Get all values in a scope.
        
        Args:
            scope: Memory scope
            
        Returns:
            Dictionary of all key-value pairs in scope
        """
        try:
            if self.redis_client:
                pattern = f"{scope}:*"
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key.decode() if isinstance(key, bytes) else key)
                
                result = {}
                for key in keys:
                    value = await self.redis_client.get(key)
                    if value:
                        clean_key = key.split(":", 1)[1]
                        result[clean_key] = json.loads(value)
                
                return result
            else:
                return {
                    k: v["value"]
                    for k, v in self.local_memory.get(scope, {}).items()
                }
                
        except Exception as e:
            logger.error(f"Failed to get all memory: {e}")
            return {}
    
    async def delete(self, scope: str, key: str) -> bool:
        """Delete value from shared memory."""
        try:
            memory_key = f"{scope}:{key}"
            
            if self.redis_client:
                await self.redis_client.delete(memory_key)
            else:
                if scope in self.local_memory:
                    self.local_memory[scope].pop(key, None)
            
            logger.debug(f"Deleted memory: {memory_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    async def clear_scope(self, scope: str) -> bool:
        """Clear all memory in a scope."""
        try:
            if self.redis_client:
                pattern = f"{scope}:*"
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    await self.redis_client.delete(*keys)
            else:
                self.local_memory.pop(scope, None)
            
            logger.info(f"Cleared memory scope: {scope}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear scope: {e}")
            return False


class AgentContext:
    """
    Context manager for agent execution with shared memory.
    
    Provides convenient access to shared memory during agent execution.
    """
    
    def __init__(
        self,
        memory_pool: SharedMemoryPool,
        session_id: str,
        agent_id: str
    ):
        """
        Initialize agent context.
        
        Args:
            memory_pool: Shared memory pool
            session_id: Session ID
            agent_id: Agent ID
        """
        self.memory_pool = memory_pool
        self.session_id = session_id
        self.agent_id = agent_id
        self.session_scope = f"session:{session_id}"
        self.agent_scope = f"agent:{agent_id}"
    
    async def set_session_memory(self, key: str, value: Any) -> bool:
        """Set value in session memory."""
        return await self.memory_pool.set(self.session_scope, key, value)
    
    async def get_session_memory(self, key: str, default: Any = None) -> Any:
        """Get value from session memory."""
        return await self.memory_pool.get(self.session_scope, key, default)
    
    async def set_agent_memory(self, key: str, value: Any) -> bool:
        """Set value in agent-specific memory."""
        return await self.memory_pool.set(self.agent_scope, key, value)
    
    async def get_agent_memory(self, key: str, default: Any = None) -> Any:
        """Get value from agent-specific memory."""
        return await self.memory_pool.get(self.agent_scope, key, default)
    
    async def append_conversation(self, message: Dict[str, Any]) -> bool:
        """Append message to conversation history."""
        return await self.memory_pool.append(
            self.session_scope,
            "conversation_history",
            message
        )
    
    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return await self.memory_pool.get(
            self.session_scope,
            "conversation_history",
            []
        )
    
    async def share_result(self, result_key: str, result: Any) -> bool:
        """Share intermediate result with other agents."""
        return await self.memory_pool.set(
            self.session_scope,
            f"shared_result:{result_key}",
            result
        )
    
    async def get_shared_result(self, result_key: str) -> Any:
        """Get shared result from another agent."""
        return await self.memory_pool.get(
            self.session_scope,
            f"shared_result:{result_key}"
        )
    
    async def get_all_shared_results(self) -> Dict[str, Any]:
        """Get all shared results in session."""
        all_memory = await self.memory_pool.get_all(self.session_scope)
        return {
            k.replace("shared_result:", ""): v
            for k, v in all_memory.items()
            if k.startswith("shared_result:")
        }
