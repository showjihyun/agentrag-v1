"""
Agent Performance Optimizer

Provides performance optimizations for agent execution:
- Response caching
- Parallel tool execution
- Prompt optimization
- Token usage optimization
"""

import logging
import hashlib
import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Caching strategies."""
    NONE = "none"
    EXACT = "exact"           # Exact input match
    SEMANTIC = "semantic"     # Semantic similarity
    HYBRID = "hybrid"         # Exact + semantic fallback


@dataclass
class CacheEntry:
    """Cached response entry."""
    key: str
    input_hash: str
    input_text: str
    output_text: str
    agent_id: str
    model: str
    token_usage: int
    created_at: str
    expires_at: str
    hit_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "input_hash": self.input_hash,
            "input_text": self.input_text[:200],
            "output_text": self.output_text[:500],
            "agent_id": self.agent_id,
            "model": self.model,
            "token_usage": self.token_usage,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "hit_count": self.hit_count,
        }


class AgentResponseCache:
    """
    Response caching for agent executions.
    
    Features:
    - Exact match caching
    - TTL-based expiration
    - Hit count tracking
    - Cache statistics
    """
    
    def __init__(
        self,
        redis: Redis,
        default_ttl: int = 3600,  # 1 hour
        max_cache_size: int = 10000,
    ):
        self.redis = redis
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        
        # Redis keys
        self.cache_prefix = "agent:cache:"
        self.stats_key = "agent:cache:stats"
    
    def _generate_cache_key(
        self,
        agent_id: str,
        input_text: str,
        context: Optional[Dict] = None,
    ) -> str:
        """Generate cache key from input."""
        content = {
            "agent_id": agent_id,
            "input": input_text.strip().lower(),
            "context": context or {},
        }
        content_str = json.dumps(content, sort_keys=True)
        hash_value = hashlib.sha256(content_str.encode()).hexdigest()[:32]
        return f"{self.cache_prefix}{agent_id}:{hash_value}"
    
    async def get(
        self,
        agent_id: str,
        input_text: str,
        context: Optional[Dict] = None,
    ) -> Optional[CacheEntry]:
        """Get cached response."""
        key = self._generate_cache_key(agent_id, input_text, context)
        
        data = await self.redis.get(key)
        if not data:
            await self._record_miss()
            return None
        
        try:
            entry_data = json.loads(data)
            entry = CacheEntry(**entry_data)
            
            # Check expiration
            if datetime.fromisoformat(entry.expires_at) < datetime.utcnow():
                await self.redis.delete(key)
                await self._record_miss()
                return None
            
            # Update hit count
            entry.hit_count += 1
            await self.redis.setex(
                key,
                self.default_ttl,
                json.dumps(entry.__dict__)
            )
            
            await self._record_hit()
            logger.debug(f"Cache hit for agent {agent_id}")
            return entry
            
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            await self._record_miss()
            return None
    
    async def set(
        self,
        agent_id: str,
        input_text: str,
        output_text: str,
        model: str,
        token_usage: int,
        context: Optional[Dict] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """Cache a response."""
        key = self._generate_cache_key(agent_id, input_text, context)
        effective_ttl = ttl or self.default_ttl
        
        entry = CacheEntry(
            key=key,
            input_hash=hashlib.sha256(input_text.encode()).hexdigest()[:16],
            input_text=input_text,
            output_text=output_text,
            agent_id=agent_id,
            model=model,
            token_usage=token_usage,
            created_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() + timedelta(seconds=effective_ttl)).isoformat(),
        )
        
        await self.redis.setex(key, effective_ttl, json.dumps(entry.__dict__))
        await self._record_set()
        
        logger.debug(f"Cached response for agent {agent_id}")
        return key
    
    async def invalidate(self, agent_id: str) -> int:
        """Invalidate all cache entries for an agent."""
        pattern = f"{self.cache_prefix}{agent_id}:*"
        keys = []
        
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self.redis.delete(*keys)
        
        logger.info(f"Invalidated {len(keys)} cache entries for agent {agent_id}")
        return len(keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = await self.redis.hgetall(self.stats_key)
        
        hits = int(stats.get(b"hits", 0))
        misses = int(stats.get(b"misses", 0))
        sets = int(stats.get(b"sets", 0))
        total = hits + misses
        
        return {
            "hits": hits,
            "misses": misses,
            "sets": sets,
            "hit_rate": round(hits / total * 100, 2) if total > 0 else 0,
            "total_requests": total,
        }
    
    async def _record_hit(self):
        await self.redis.hincrby(self.stats_key, "hits", 1)
    
    async def _record_miss(self):
        await self.redis.hincrby(self.stats_key, "misses", 1)
    
    async def _record_set(self):
        await self.redis.hincrby(self.stats_key, "sets", 1)


class ParallelToolExecutor:
    """
    Parallel execution of agent tools.
    
    Features:
    - Concurrent tool execution
    - Dependency resolution
    - Timeout handling
    - Error isolation
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        default_timeout: float = 30.0,
    ):
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_tools(
        self,
        tools: List[Dict[str, Any]],
        tool_executor: Callable,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in parallel.
        
        Args:
            tools: List of tool configurations
            tool_executor: Async function to execute a single tool
            context: Shared execution context
            
        Returns:
            List of tool results
        """
        # Group tools by dependencies
        independent_tools = []
        dependent_tools = []
        
        for tool in tools:
            if tool.get("depends_on"):
                dependent_tools.append(tool)
            else:
                independent_tools.append(tool)
        
        results = {}
        
        # Execute independent tools in parallel
        if independent_tools:
            independent_results = await self._execute_parallel(
                independent_tools, tool_executor, context
            )
            for tool, result in zip(independent_tools, independent_results):
                results[tool["id"]] = result
        
        # Execute dependent tools (respecting dependencies)
        for tool in dependent_tools:
            # Wait for dependencies
            dep_results = {
                dep: results.get(dep)
                for dep in tool.get("depends_on", [])
            }
            
            # Add dependency results to context
            tool_context = {**context, "dependencies": dep_results}
            
            result = await self._execute_single(tool, tool_executor, tool_context)
            results[tool["id"]] = result
        
        return [results.get(t["id"]) for t in tools]
    
    async def _execute_parallel(
        self,
        tools: List[Dict[str, Any]],
        tool_executor: Callable,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Execute tools in parallel with semaphore."""
        tasks = [
            self._execute_with_semaphore(tool, tool_executor, context)
            for tool in tools
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append({
                    "success": False,
                    "error": str(result),
                    "tool_id": tools[i]["id"],
                })
            else:
                processed.append(result)
        
        return processed
    
    async def _execute_with_semaphore(
        self,
        tool: Dict[str, Any],
        tool_executor: Callable,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute single tool with semaphore control."""
        async with self.semaphore:
            return await self._execute_single(tool, tool_executor, context)
    
    async def _execute_single(
        self,
        tool: Dict[str, Any],
        tool_executor: Callable,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single tool with timeout."""
        timeout = tool.get("timeout", self.default_timeout)
        
        try:
            result = await asyncio.wait_for(
                tool_executor(tool, context),
                timeout=timeout
            )
            return {
                "success": True,
                "tool_id": tool["id"],
                "result": result,
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "tool_id": tool["id"],
                "error": f"Tool execution timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "success": False,
                "tool_id": tool["id"],
                "error": str(e),
            }


class PromptOptimizer:
    """
    Optimize prompts for better performance.
    
    Features:
    - Token reduction
    - Context compression
    - Prompt templating
    """
    
    def __init__(self, max_context_tokens: int = 4000):
        self.max_context_tokens = max_context_tokens
    
    def optimize_prompt(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Optimize prompt for token efficiency.
        
        Returns optimized system prompt, user message, and context.
        """
        max_tokens = max_tokens or self.max_context_tokens
        
        # Estimate tokens (rough: 4 chars per token)
        def estimate_tokens(text: str) -> int:
            return len(text) // 4
        
        # Optimize system prompt
        optimized_system = self._compress_text(system_prompt, max_tokens // 3)
        
        # Optimize context if provided
        optimized_context = ""
        if context:
            context_budget = max_tokens // 3
            optimized_context = self._compress_text(context, context_budget)
        
        # User message gets remaining budget
        user_budget = max_tokens - estimate_tokens(optimized_system) - estimate_tokens(optimized_context)
        optimized_user = self._compress_text(user_message, max(user_budget, 500))
        
        return {
            "system_prompt": optimized_system,
            "user_message": optimized_user,
            "context": optimized_context,
            "estimated_tokens": estimate_tokens(optimized_system + optimized_user + optimized_context),
        }
    
    def _compress_text(self, text: str, max_tokens: int) -> str:
        """Compress text to fit within token budget."""
        if not text:
            return ""
        
        estimated = len(text) // 4
        if estimated <= max_tokens:
            return text
        
        # Simple truncation with ellipsis
        max_chars = max_tokens * 4
        if len(text) > max_chars:
            return text[:max_chars - 3] + "..."
        
        return text
    
    def deduplicate_context(self, contexts: List[str]) -> str:
        """Remove duplicate information from multiple contexts."""
        seen_sentences = set()
        unique_parts = []
        
        for context in contexts:
            sentences = context.split(". ")
            for sentence in sentences:
                normalized = sentence.strip().lower()
                if normalized and normalized not in seen_sentences:
                    seen_sentences.add(normalized)
                    unique_parts.append(sentence.strip())
        
        return ". ".join(unique_parts)


class AgentOptimizer:
    """
    Main optimizer combining all optimization strategies.
    """
    
    def __init__(
        self,
        redis: Redis,
        cache_ttl: int = 3600,
        max_parallel_tools: int = 5,
    ):
        self.cache = AgentResponseCache(redis, default_ttl=cache_ttl)
        self.parallel_executor = ParallelToolExecutor(max_concurrent=max_parallel_tools)
        self.prompt_optimizer = PromptOptimizer()
    
    async def get_cached_response(
        self,
        agent_id: str,
        input_text: str,
        context: Optional[Dict] = None,
    ) -> Optional[str]:
        """Get cached response if available."""
        entry = await self.cache.get(agent_id, input_text, context)
        if entry:
            return entry.output_text
        return None
    
    async def cache_response(
        self,
        agent_id: str,
        input_text: str,
        output_text: str,
        model: str,
        token_usage: int,
        context: Optional[Dict] = None,
    ):
        """Cache a response."""
        await self.cache.set(
            agent_id=agent_id,
            input_text=input_text,
            output_text=output_text,
            model=model,
            token_usage=token_usage,
            context=context,
        )
    
    async def execute_tools_parallel(
        self,
        tools: List[Dict[str, Any]],
        tool_executor: Callable,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Execute tools in parallel."""
        return await self.parallel_executor.execute_tools(
            tools, tool_executor, context
        )
    
    def optimize_prompt(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
    ) -> Dict[str, str]:
        """Optimize prompt for token efficiency."""
        return self.prompt_optimizer.optimize_prompt(
            system_prompt, user_message, context
        )
    
    async def invalidate_agent_cache(self, agent_id: str) -> int:
        """Invalidate cache for an agent."""
        return await self.cache.invalidate(agent_id)
    
    async def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        cache_stats = await self.cache.get_stats()
        
        return {
            "cache": cache_stats,
            "parallel_executor": {
                "max_concurrent": self.parallel_executor.max_concurrent,
                "default_timeout": self.parallel_executor.default_timeout,
            },
        }
