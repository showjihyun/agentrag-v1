"""
Multi-Level Cache System - Phase 3.1 + Mode-Aware Caching

3-tier caching for maximum performance:
- L1: In-memory LRU (fastest, 100% hit = 0ms)
- L2: Redis (fast, 100% hit = 10ms)
- L3: Semantic (Milvus-based, similar queries)

Mode-aware caching strategy:
- FAST: L1 only (fastest access, TTL=3600s)
- BALANCED: L1 + L2 (fast + distributed, TTL=1800s/3600s)
- DEEP: L1 + L2 + L3 (all levels, TTL=7200s)

Expected impact:
- Cache hit rate: 60-80%
- Cached query latency: 50ms (vs 300ms)
- Additional 40% LLM cost reduction
"""

import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from functools import lru_cache
from enum import Enum
import json

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache strategy for different query modes."""

    FAST = "fast"  # L1 only
    BALANCED = "balanced"  # L1 + L2
    DEEP = "deep"  # L1 + L2 + L3


class CachedResult:
    """Cached query result."""

    def __init__(
        self,
        query: str,
        response: str,
        metadata: Dict[str, Any],
        timestamp: datetime,
        ttl: int = 3600,
    ):
        self.query = query
        self.response = response
        self.metadata = metadata
        self.timestamp = timestamp
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "response": self.response,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedResult":
        """Create from dictionary."""
        return cls(
            query=data["query"],
            response=data["response"],
            metadata=data["metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl=data["ttl"],
        )


class L1Cache:
    """
    L1: In-memory LRU cache.

    Fastest cache tier (0ms overhead).
    Stores most recent queries.
    """

    def __init__(self, maxsize: int = 100):
        """
        Initialize L1 cache.

        Args:
            maxsize: Maximum number of entries
        """
        self.maxsize = maxsize
        self._cache: Dict[str, CachedResult] = {}
        self._access_order = []
        self._mode_hits = {"fast": 0, "balanced": 0, "deep": 0}

        logger.info(f"L1Cache initialized: maxsize={maxsize}")

    def _make_key(self, query: str) -> str:
        """Create cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str, mode: Optional[str] = None) -> Optional[CachedResult]:
        """Get from L1 cache."""
        key = self._make_key(query)

        if key in self._cache:
            result = self._cache[key]

            # Check expiration
            if result.is_expired():
                del self._cache[key]
                self._access_order.remove(key)
                return None

            # Update access order (LRU)
            self._access_order.remove(key)
            self._access_order.append(key)

            # Track mode-specific hits
            if mode:
                self._mode_hits[mode] = self._mode_hits.get(mode, 0) + 1

            logger.debug(f"L1 cache hit: {query[:50]} (mode={mode})")
            return result

        return None

    def set(self, query: str, result: CachedResult, ttl: Optional[int] = None):
        """Set in L1 cache with optional TTL override."""
        key = self._make_key(query)

        # Override TTL if provided
        if ttl is not None:
            result.ttl = ttl

        # Evict if full
        if len(self._cache) >= self.maxsize and key not in self._cache:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        self._cache[key] = result

        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"L1 cache set: {query[:50]} (ttl={result.ttl}s)")

    def clear(self):
        """Clear L1 cache."""
        self._cache.clear()
        self._access_order.clear()
        logger.info("L1 cache cleared")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "utilization": len(self._cache) / self.maxsize if self.maxsize > 0 else 0,
            "mode_hits": self._mode_hits,
        }


class L2Cache:
    """
    L2: Redis cache.

    Fast distributed cache (~10ms overhead).
    Shared across instances.
    """

    def __init__(self, redis_client, ttl: int = 3600):
        """
        Initialize L2 cache.

        Args:
            redis_client: Redis client
            ttl: Time to live (seconds)
        """
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = "rag:cache:"
        self._mode_hits = {"fast": 0, "balanced": 0, "deep": 0}

        logger.info(f"L2Cache initialized: ttl={ttl}s")

    def _make_key(self, query: str) -> str:
        """Create cache key."""
        hash_key = hashlib.md5(query.encode()).hexdigest()
        return f"{self.prefix}{hash_key}"

    async def get(
        self, query: str, mode: Optional[str] = None
    ) -> Optional[CachedResult]:
        """Get from L2 cache."""
        key = self._make_key(query)

        try:
            data = await self.redis.get(key)

            if data:
                result_dict = json.loads(data)
                result = CachedResult.from_dict(result_dict)

                # Check expiration
                if result.is_expired():
                    await self.redis.delete(key)
                    return None

                # Track mode-specific hits
                if mode:
                    self._mode_hits[mode] = self._mode_hits.get(mode, 0) + 1

                logger.debug(f"L2 cache hit: {query[:50]} (mode={mode})")
                return result

        except Exception as e:
            logger.error(f"L2 cache get error: {e}")

        return None

    async def set(self, query: str, result: CachedResult, ttl: Optional[int] = None):
        """Set in L2 cache with optional TTL override."""
        key = self._make_key(query)

        try:
            # Use provided TTL or default
            cache_ttl = ttl if ttl is not None else self.ttl

            data = json.dumps(result.to_dict())
            await self.redis.setex(key, cache_ttl, data)

            logger.debug(f"L2 cache set: {query[:50]} (ttl={cache_ttl}s)")

        except Exception as e:
            logger.error(f"L2 cache set error: {e}")

    async def clear(self):
        """Clear L2 cache."""
        try:
            pattern = f"{self.prefix}*"
            keys = await self.redis.keys(pattern)

            if keys:
                await self.redis.delete(*keys)

            logger.info(f"L2 cache cleared: {len(keys)} keys")

        except Exception as e:
            logger.error(f"L2 cache clear error: {e}")

    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            pattern = f"{self.prefix}*"
            keys = await self.redis.keys(pattern)

            return {"size": len(keys), "ttl": self.ttl, "mode_hits": self._mode_hits}

        except Exception as e:
            logger.error(f"L2 cache stats error: {e}")
            return {"size": 0, "ttl": self.ttl, "mode_hits": self._mode_hits}


class L3Cache:
    """
    L3: Semantic cache (Milvus-based).

    Finds similar queries using embeddings.
    Useful for paraphrased or similar questions.
    """

    def __init__(
        self, milvus_manager, embedding_service, similarity_threshold: float = 0.95
    ):
        """
        Initialize L3 cache.

        Args:
            milvus_manager: Milvus manager
            embedding_service: Embedding service
            similarity_threshold: Minimum similarity for cache hit
        """
        self.milvus = milvus_manager
        self.embedding = embedding_service
        self.threshold = similarity_threshold
        self.collection_name = "query_cache"
        self._mode_hits = {"fast": 0, "balanced": 0, "deep": 0}

        logger.info(f"L3Cache initialized: " f"threshold={similarity_threshold}")

    async def find_similar(
        self, query: str, threshold: Optional[float] = None, mode: Optional[str] = None
    ) -> Optional[CachedResult]:
        """Find similar cached query."""
        threshold = threshold or self.threshold

        try:
            # Generate query embedding
            query_embedding = await self.embedding.embed_text(query)

            # Search for similar queries
            results = await self.milvus.search(
                collection_name=self.collection_name,
                query_vectors=[query_embedding],
                limit=1,
                output_fields=["query", "response", "metadata", "timestamp"],
            )

            if results and results[0]:
                result = results[0][0]
                similarity = result.score

                if similarity >= threshold:
                    cached_result = CachedResult(
                        query=result.entity.get("query"),
                        response=result.entity.get("response"),
                        metadata=result.entity.get("metadata", {}),
                        timestamp=datetime.fromisoformat(
                            result.entity.get("timestamp")
                        ),
                    )

                    # Check expiration
                    if not cached_result.is_expired():
                        # Track mode-specific hits
                        if mode:
                            self._mode_hits[mode] = self._mode_hits.get(mode, 0) + 1

                        logger.debug(
                            f"L3 cache hit: {query[:50]} "
                            f"(similarity={similarity:.3f}, mode={mode})"
                        )
                        return cached_result

        except Exception as e:
            logger.error(f"L3 cache find error: {e}")

        return None

    async def add(self, query: str, result: CachedResult):
        """Add to L3 cache."""
        try:
            # Generate embedding
            query_embedding = await self.embedding.embed_text(query)

            # Insert into Milvus
            await self.milvus.insert(
                collection_name=self.collection_name,
                data=[
                    {
                        "query": query,
                        "response": result.response,
                        "metadata": result.metadata,
                        "timestamp": result.timestamp.isoformat(),
                        "embedding": query_embedding,
                    }
                ],
            )

            logger.debug(f"L3 cache add: {query[:50]}")

        except Exception as e:
            logger.error(f"L3 cache add error: {e}")


class MultiLevelCache:
    """
    Multi-level cache system.

    Combines L1 (memory), L2 (Redis), L3 (semantic) for optimal performance.

    Cache hierarchy:
    1. L1: Check in-memory (0ms)
    2. L2: Check Redis (10ms)
    3. L3: Check semantic similarity (50ms)
    4. Miss: Execute query (300ms+)

    On hit, populate upper levels for faster future access.
    """

    def __init__(
        self,
        redis_client=None,
        milvus_manager=None,
        embedding_service=None,
        l1_maxsize: int = 100,
        l2_ttl: int = 3600,
        l3_threshold: float = 0.95,
        enabled: bool = True,
    ):
        """
        Initialize multi-level cache.

        Args:
            redis_client: Redis client (optional)
            milvus_manager: Milvus manager (optional)
            embedding_service: Embedding service (optional)
            l1_maxsize: L1 cache size
            l2_ttl: L2 TTL (seconds)
            l3_threshold: L3 similarity threshold
            enabled: Enable caching
        """
        self.enabled = enabled

        if not enabled:
            logger.info("MultiLevelCache disabled")
            return

        # Initialize cache levels
        self.l1 = L1Cache(maxsize=l1_maxsize)

        self.l2 = L2Cache(redis_client, ttl=l2_ttl) if redis_client else None

        self.l3 = (
            L3Cache(
                milvus_manager, embedding_service, similarity_threshold=l3_threshold
            )
            if (milvus_manager and embedding_service)
            else None
        )

        # Statistics
        self.stats_hits = {"l1": 0, "l2": 0, "l3": 0}
        self.stats_misses = 0
        self.stats_mode_hits = {"fast": 0, "balanced": 0, "deep": 0}
        self.stats_mode_misses = {"fast": 0, "balanced": 0, "deep": 0}

        # Mode-specific TTLs (can be overridden via config)
        self.mode_ttls = {
            "fast": 3600,  # 1 hour for FAST mode
            "balanced": 1800,  # 30 minutes for BALANCED mode (L1), 3600 for L2
            "deep": 7200,  # 2 hours for DEEP mode
        }

        logger.info(
            f"MultiLevelCache initialized: "
            f"L1={l1_maxsize}, "
            f"L2={'enabled' if self.l2 else 'disabled'}, "
            f"L3={'enabled' if self.l3 else 'disabled'}"
        )

    async def get_with_mode(
        self, query: str, mode: str = "balanced"
    ) -> Optional[CachedResult]:
        """
        Get from cache with mode-specific strategy.

        Mode strategies:
        - FAST: L1 only (fastest, in-memory)
        - BALANCED: L1 + L2 (fast + distributed)
        - DEEP: L1 + L2 + L3 (all levels including semantic)

        Args:
            query: Query string
            mode: Query mode (fast, balanced, deep)

        Returns:
            Cached result or None
        """
        if not self.enabled:
            return None

        mode = mode.lower()

        # L1: Always check in-memory cache first
        if result := self.l1.get(query, mode=mode):
            self.stats_hits["l1"] += 1
            self.stats_mode_hits[mode] = self.stats_mode_hits.get(mode, 0) + 1
            logger.debug(f"Cache hit (L1) for mode={mode}")
            return result

        # FAST mode: L1 only
        if mode == "fast":
            self.stats_misses += 1
            self.stats_mode_misses[mode] = self.stats_mode_misses.get(mode, 0) + 1
            return None

        # L2: Check Redis for BALANCED and DEEP modes
        if self.l2 and mode in ["balanced", "deep"]:
            if result := await self.l2.get(query, mode=mode):
                self.stats_hits["l2"] += 1
                self.stats_mode_hits[mode] = self.stats_mode_hits.get(mode, 0) + 1

                # Populate L1 for faster future access
                self.l1.set(query, result, ttl=self.mode_ttls.get(mode, 3600))

                logger.debug(f"Cache hit (L2) for mode={mode}")
                return result

        # BALANCED mode: L1 + L2 only
        if mode == "balanced":
            self.stats_misses += 1
            self.stats_mode_misses[mode] = self.stats_mode_misses.get(mode, 0) + 1
            return None

        # L3: Check semantic cache for DEEP mode only
        if self.l3 and mode == "deep":
            if result := await self.l3.find_similar(query, mode=mode):
                self.stats_hits["l3"] += 1
                self.stats_mode_hits[mode] = self.stats_mode_hits.get(mode, 0) + 1

                # Populate L2 and L1 for faster future access
                if self.l2:
                    await self.l2.set(query, result, ttl=self.mode_ttls.get(mode, 7200))
                self.l1.set(query, result, ttl=self.mode_ttls.get(mode, 7200))

                logger.debug(f"Cache hit (L3) for mode={mode}")
                return result

        # Cache miss
        self.stats_misses += 1
        self.stats_mode_misses[mode] = self.stats_mode_misses.get(mode, 0) + 1
        return None

    async def set_with_mode(
        self,
        query: str,
        response: str,
        metadata: Dict[str, Any],
        mode: str = "balanced",
    ):
        """
        Set in cache with mode-specific strategy and TTLs.

        Mode strategies:
        - FAST: L1 only with TTL=3600s (aggressive caching)
        - BALANCED: L1 (TTL=1800s) + L2 (TTL=3600s)
        - DEEP: L2 (TTL=7200s) + L3 (persistent)

        Args:
            query: Query string
            response: Response string
            metadata: Additional metadata
            mode: Query mode (fast, balanced, deep)
        """
        if not self.enabled:
            return

        mode = mode.lower()
        ttl = self.mode_ttls.get(mode, 3600)

        result = CachedResult(
            query=query,
            response=response,
            metadata=metadata,
            timestamp=datetime.now(),
            ttl=ttl,
        )

        # FAST mode: L1 only with aggressive caching
        if mode == "fast":
            self.l1.set(query, result, ttl=ttl)
            logger.debug(f"Cache set (L1) for mode={mode}, ttl={ttl}s")
            return

        # BALANCED mode: L1 + L2
        if mode == "balanced":
            # L1 with shorter TTL (30 min)
            self.l1.set(query, result, ttl=1800)

            # L2 with longer TTL (1 hour)
            if self.l2:
                await self.l2.set(query, result, ttl=3600)

            logger.debug(f"Cache set (L1+L2) for mode={mode}")
            return

        # DEEP mode: L2 + L3 (skip L1 to save memory for frequent queries)
        if mode == "deep":
            # L2 with long TTL (2 hours)
            if self.l2:
                await self.l2.set(query, result, ttl=ttl)

            # L3 for semantic matching (persistent)
            if self.l3:
                await self.l3.add(query, result)

            logger.debug(f"Cache set (L2+L3) for mode={mode}, ttl={ttl}s")
            return

    async def get(self, query: str) -> Optional[CachedResult]:
        """
        Get from cache (checks all levels).

        Args:
            query: Query string

        Returns:
            Cached result or None
        """
        if not self.enabled:
            return None

        # L1: In-memory
        if result := self.l1.get(query):
            self.stats_hits["l1"] += 1
            return result

        # L2: Redis
        if self.l2:
            if result := await self.l2.get(query):
                self.stats_hits["l2"] += 1

                # Populate L1
                self.l1.set(query, result)

                return result

        # L3: Semantic
        if self.l3:
            if result := await self.l3.find_similar(query):
                self.stats_hits["l3"] += 1

                # Populate L2 and L1
                if self.l2:
                    await self.l2.set(query, result)
                self.l1.set(query, result)

                return result

        # Cache miss
        self.stats_misses += 1
        return None

    async def set(self, query: str, response: str, metadata: Dict[str, Any]):
        """
        Set in cache (all levels).

        Args:
            query: Query string
            response: Response string
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        result = CachedResult(
            query=query, response=response, metadata=metadata, timestamp=datetime.now()
        )

        # Set in all levels
        self.l1.set(query, result)

        if self.l2:
            await self.l2.set(query, result)

        if self.l3:
            await self.l3.add(query, result)

    async def clear(self):
        """Clear all cache levels."""
        if not self.enabled:
            return

        self.l1.clear()

        if self.l2:
            await self.l2.clear()

        # L3 is persistent, don't clear

        # Reset stats
        self.stats_hits = {"l1": 0, "l2": 0, "l3": 0}
        self.stats_misses = 0

        logger.info("All cache levels cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics including mode-specific metrics."""
        total_requests = sum(self.stats_hits.values()) + self.stats_misses

        if total_requests == 0:
            hit_rate = 0.0
        else:
            hit_rate = sum(self.stats_hits.values()) / total_requests

        # Calculate mode-specific hit rates
        mode_hit_rates = {}
        for mode in ["fast", "balanced", "deep"]:
            mode_total = self.stats_mode_hits.get(mode, 0) + self.stats_mode_misses.get(
                mode, 0
            )
            if mode_total > 0:
                mode_hit_rates[mode] = self.stats_mode_hits.get(mode, 0) / mode_total
            else:
                mode_hit_rates[mode] = 0.0

        return {
            "enabled": self.enabled,
            "hits": self.stats_hits,
            "misses": self.stats_misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "mode_hits": self.stats_mode_hits,
            "mode_misses": self.stats_mode_misses,
            "mode_hit_rates": mode_hit_rates,
            "mode_ttls": self.mode_ttls,
            "l1_stats": self.l1.stats() if self.enabled else {},
            "l2_stats": {} if not self.l2 else {},  # Async, skip for now
            "l3_enabled": self.l3 is not None,
        }

    def get_hit_rate(self) -> float:
        """Get overall cache hit rate."""
        stats = self.get_stats()
        return stats["hit_rate"]
