"""
LLM Response Caching for improved performance.

Caches LLM responses to avoid redundant API calls for identical queries.
Uses Redis for distributed caching with TTL management.
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class LLMResponseCache:
    """
    Cache for LLM responses.

    Features:
    - Message-based cache key generation
    - TTL management
    - Hit/miss tracking
    - Cache statistics
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        default_ttl: int = 3600,
        key_prefix: str = "llm_cache",
    ):
        """
        Initialize LLM response cache.

        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds (1 hour)
            key_prefix: Prefix for cache keys
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix

        # Statistics
        self.hits = 0
        self.misses = 0

        logger.info(f"LLMResponseCache initialized (ttl={default_ttl}s)")

    def _generate_cache_key(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        model: str,
    ) -> str:
        """
        Generate cache key from messages and parameters.

        Args:
            messages: List of message dictionaries
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            model: Model name

        Returns:
            str: Cache key
        """
        # Create deterministic string representation
        cache_data = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": model,
        }

        # Sort keys for consistency
        cache_str = json.dumps(cache_data, sort_keys=True)

        # Generate hash
        cache_hash = hashlib.sha256(cache_str.encode()).hexdigest()

        return f"{self.key_prefix}:{cache_hash}"

    async def get(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: str = "default",
    ) -> Optional[str]:
        """
        Get cached response if available.

        Args:
            messages: List of message dictionaries
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            model: Model name

        Returns:
            Cached response or None if not found
        """
        try:
            cache_key = self._generate_cache_key(
                messages, temperature, max_tokens, model
            )

            # Get from Redis
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                self.hits += 1

                # Parse cached data
                data = json.loads(cached_data)
                response = data.get("response")

                logger.debug(f"Cache hit: {cache_key[:16]}...")

                return response
            else:
                self.misses += 1
                logger.debug(f"Cache miss: {cache_key[:16]}...")

                return None

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            self.misses += 1
            return None

    async def set(
        self,
        messages: List[Dict[str, str]],
        response: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: str = "default",
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache LLM response.

        Args:
            messages: List of message dictionaries
            response: LLM response to cache
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            model: Model name
            ttl: Optional custom TTL (uses default if None)

        Returns:
            bool: True if cached successfully
        """
        try:
            cache_key = self._generate_cache_key(
                messages, temperature, max_tokens, model
            )

            # Prepare cache data
            cache_data = {
                "response": response,
                "cached_at": datetime.now().isoformat(),
                "model": model,
            }

            # Set in Redis with TTL
            ttl = ttl or self.default_ttl
            await self.redis.setex(cache_key, ttl, json.dumps(cache_data))

            logger.debug(f"Cached response: {cache_key[:16]}... (ttl={ttl}s)")

            return True

        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def invalidate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: str = "default",
    ) -> bool:
        """
        Invalidate cached response.

        Args:
            messages: List of message dictionaries
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            model: Model name

        Returns:
            bool: True if invalidated
        """
        try:
            cache_key = self._generate_cache_key(
                messages, temperature, max_tokens, model
            )

            deleted = await self.redis.delete(cache_key)

            if deleted:
                logger.debug(f"Invalidated cache: {cache_key[:16]}...")

            return bool(deleted)

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False

    async def clear_all(self) -> int:
        """
        Clear all cached responses.

        Returns:
            int: Number of keys deleted
        """
        try:
            # Find all cache keys
            pattern = f"{self.key_prefix}:*"
            keys = []

            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cached responses")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics dictionary
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "default_ttl": self.default_ttl,
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.hits = 0
        self.misses = 0
        logger.info("Cache statistics reset")


async def get_or_generate(
    cache: LLMResponseCache,
    llm_manager,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    use_cache: bool = True,
    **kwargs,
) -> str:
    """
    Get cached response or generate new one.

    Args:
        cache: LLMResponseCache instance
        llm_manager: LLMManager instance
        messages: List of message dictionaries
        temperature: Temperature parameter
        max_tokens: Max tokens parameter
        use_cache: Whether to use cache
        **kwargs: Additional LLM parameters

    Returns:
        str: LLM response
    """
    model = llm_manager.model

    # Try cache first if enabled
    if use_cache:
        cached_response = await cache.get(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

        if cached_response:
            return cached_response

    # Generate new response
    response = await llm_manager.generate(
        messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
    )

    # Cache the response if enabled
    if use_cache and response:
        await cache.set(
            messages=messages,
            response=response,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

    return response
