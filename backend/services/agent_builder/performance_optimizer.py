"""
Performance Optimization for Agent Builder.

Provides caching, connection pooling, and concurrency management for optimal performance.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from functools import lru_cache, wraps
from datetime import datetime, timezone
import hashlib
import json

from redis.asyncio import Redis
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Manages performance optimizations for agent executions.
    
    Features:
    - LLM response caching
    - Compiled graph caching
    - Concurrent execution limiting
    - Database query optimization
    """
    
    def __init__(
        self,
        redis_client: Redis,
        max_concurrent_llm_calls: int = 5,
        llm_cache_ttl: int = 3600,
        graph_cache_size: int = 100
    ):
        """
        Initialize performance optimizer.
        
        Args:
            redis_client: Redis client for caching
            max_concurrent_llm_calls: Maximum concurrent LLM calls
            llm_cache_ttl: LLM cache TTL in seconds
            graph_cache_size: Maximum number of compiled graphs to cache
        """
        self.redis = redis_client
        self.llm_cache_ttl = llm_cache_ttl
        
        # Semaphore for limiting concurrent LLM calls
        self.llm_semaphore = asyncio.Semaphore(max_concurrent_llm_calls)
        
        # In-memory cache for compiled graphs
        self._graph_cache: Dict[str, StateGraph] = {}
        self._graph_cache_size = graph_cache_size
        self._graph_cache_access: Dict[str, datetime] = {}
        
        logger.info(
            f"PerformanceOptimizer initialized: "
            f"max_concurrent_llm={max_concurrent_llm_calls}, "
            f"llm_cache_ttl={llm_cache_ttl}s, "
            f"graph_cache_size={graph_cache_size}"
        )
    
    # ========================================================================
    # LLM Response Caching
    # ========================================================================
    
    def _generate_llm_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        **kwargs
    ) -> str:
        """
        Generate cache key for LLM response.
        
        Args:
            prompt: LLM prompt
            model: Model name
            temperature: Temperature parameter
            **kwargs: Additional parameters
            
        Returns:
            Cache key string
        """
        cache_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            **kwargs
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()
        
        return f"llm_cache:{cache_hash}"
    
    async def get_cached_llm_response(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        **kwargs
    ) -> Optional[str]:
        """
        Get cached LLM response if available.
        
        Args:
            prompt: LLM prompt
            model: Model name
            temperature: Temperature parameter
            **kwargs: Additional parameters
            
        Returns:
            Cached response or None
        """
        try:
            cache_key = self._generate_llm_cache_key(prompt, model, temperature, **kwargs)
            cached = await self.redis.get(cache_key)
            
            if cached:
                logger.debug(f"LLM cache hit: {cache_key[:16]}...")
                return cached.decode('utf-8')
            
            logger.debug(f"LLM cache miss: {cache_key[:16]}...")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached LLM response: {e}")
            return None
    
    async def cache_llm_response(
        self,
        prompt: str,
        model: str,
        response: str,
        temperature: float = 0.7,
        ttl: Optional[int] = None,
        **kwargs
    ):
        """
        Cache LLM response.
        
        Args:
            prompt: LLM prompt
            model: Model name
            response: LLM response to cache
            temperature: Temperature parameter
            ttl: Time to live in seconds (uses default if None)
            **kwargs: Additional parameters
        """
        try:
            cache_key = self._generate_llm_cache_key(prompt, model, temperature, **kwargs)
            ttl = ttl or self.llm_cache_ttl
            
            await self.redis.setex(
                cache_key,
                ttl,
                response.encode('utf-8')
            )
            
            logger.debug(f"Cached LLM response: {cache_key[:16]}... (ttl={ttl}s)")
            
        except Exception as e:
            logger.error(f"Failed to cache LLM response: {e}")
    
    async def with_llm_cache(
        self,
        llm_func: Callable,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Execute LLM function with caching.
        
        Args:
            llm_func: Async LLM function to execute
            prompt: LLM prompt
            model: Model name
            temperature: Temperature parameter
            **kwargs: Additional parameters
            
        Returns:
            LLM response (cached or fresh)
        """
        # Check cache first
        cached_response = await self.get_cached_llm_response(
            prompt, model, temperature, **kwargs
        )
        
        if cached_response:
            return cached_response
        
        # Execute LLM function with concurrency limit
        async with self.llm_semaphore:
            response = await llm_func(prompt, model, temperature, **kwargs)
        
        # Cache response
        await self.cache_llm_response(
            prompt, model, response, temperature, **kwargs
        )
        
        return response
    
    # ========================================================================
    # Compiled Graph Caching
    # ========================================================================
    
    def _generate_graph_cache_key(
        self,
        workflow_id: str,
        workflow_version: str
    ) -> str:
        """
        Generate cache key for compiled graph.
        
        Args:
            workflow_id: Workflow ID
            workflow_version: Workflow version/updated_at timestamp
            
        Returns:
            Cache key string
        """
        return f"{workflow_id}:{workflow_version}"
    
    def get_cached_graph(
        self,
        workflow_id: str,
        workflow_version: str
    ) -> Optional[StateGraph]:
        """
        Get cached compiled graph.
        
        Args:
            workflow_id: Workflow ID
            workflow_version: Workflow version/updated_at timestamp
            
        Returns:
            Cached StateGraph or None
        """
        cache_key = self._generate_graph_cache_key(workflow_id, workflow_version)
        
        if cache_key in self._graph_cache:
            # Update access time for LRU
            self._graph_cache_access[cache_key] = datetime.now(timezone.utc)
            logger.debug(f"Graph cache hit: {cache_key}")
            return self._graph_cache[cache_key]
        
        logger.debug(f"Graph cache miss: {cache_key}")
        return None
    
    def cache_compiled_graph(
        self,
        workflow_id: str,
        workflow_version: str,
        compiled_graph: StateGraph
    ):
        """
        Cache compiled graph.
        
        Args:
            workflow_id: Workflow ID
            workflow_version: Workflow version/updated_at timestamp
            compiled_graph: Compiled StateGraph
        """
        cache_key = self._generate_graph_cache_key(workflow_id, workflow_version)
        
        # Evict oldest entry if cache is full
        if len(self._graph_cache) >= self._graph_cache_size:
            self._evict_oldest_graph()
        
        self._graph_cache[cache_key] = compiled_graph
        self._graph_cache_access[cache_key] = datetime.now(timezone.utc)
        
        logger.debug(f"Cached compiled graph: {cache_key}")
    
    def _evict_oldest_graph(self):
        """Evict least recently used graph from cache."""
        if not self._graph_cache_access:
            return
        
        # Find oldest accessed key
        oldest_key = min(
            self._graph_cache_access.keys(),
            key=lambda k: self._graph_cache_access[k]
        )
        
        # Remove from cache
        del self._graph_cache[oldest_key]
        del self._graph_cache_access[oldest_key]
        
        logger.debug(f"Evicted graph from cache: {oldest_key}")
    
    def clear_graph_cache(self):
        """Clear all cached graphs."""
        self._graph_cache.clear()
        self._graph_cache_access.clear()
        logger.info("Cleared graph cache")
    
    # ========================================================================
    # Concurrency Management
    # ========================================================================
    
    async def with_llm_concurrency_limit(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with LLM concurrency limit.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        async with self.llm_semaphore:
            return await func(*args, **kwargs)
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Get Redis info
            redis_info = await self.redis.info("stats")
            
            return {
                "graph_cache": {
                    "size": len(self._graph_cache),
                    "max_size": self._graph_cache_size,
                    "utilization": len(self._graph_cache) / self._graph_cache_size
                },
                "redis": {
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                    "hit_rate": self._calculate_hit_rate(
                        redis_info.get("keyspace_hits", 0),
                        redis_info.get("keyspace_misses", 0)
                    )
                },
                "concurrency": {
                    "max_concurrent_llm": self.llm_semaphore._value,
                    "available_slots": self.llm_semaphore._value
                }
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate."""
        total = hits + misses
        if total == 0:
            return 0.0
        return hits / total


# Decorator for caching function results
def cached_result(ttl: int = 3600):
    """
    Decorator for caching function results in Redis.
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"func_cache:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try to get from cache
            if hasattr(self, 'redis'):
                try:
                    cached = await self.redis.get(cache_key)
                    if cached:
                        return json.loads(cached.decode('utf-8'))
                except Exception as e:
                    logger.debug(f"Cache get failed: {e}")
            
            # Execute function
            result = await func(self, *args, **kwargs)
            
            # Cache result
            if hasattr(self, 'redis'):
                try:
                    await self.redis.setex(
                        cache_key,
                        ttl,
                        json.dumps(result).encode('utf-8')
                    )
                except Exception as e:
                    logger.debug(f"Cache set failed: {e}")
            
            return result
        
        return wrapper
    return decorator


# Global optimizer instance
_optimizer_instance: Optional[PerformanceOptimizer] = None


def get_optimizer() -> PerformanceOptimizer:
    """Get global optimizer instance."""
    if _optimizer_instance is None:
        raise RuntimeError("PerformanceOptimizer not initialized")
    return _optimizer_instance


def init_optimizer(redis_client: Redis) -> PerformanceOptimizer:
    """
    Initialize global optimizer instance.
    
    Args:
        redis_client: Redis client
        
    Returns:
        PerformanceOptimizer instance
    """
    global _optimizer_instance
    _optimizer_instance = PerformanceOptimizer(redis_client)
    return _optimizer_instance
