"""
Semantic Cache with Similarity Search

Intelligent caching system that uses embedding similarity to find cached responses
for semantically similar queries, even if the exact wording is different.
"""

import time
import hashlib
import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cached query response with metadata"""

    query: str
    query_embedding: List[float]
    response: Dict[str, Any]
    confidence: float
    timestamp: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600
    popularity_score: float = 0.0

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl_seconds

    def update_access(self):
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        # Update popularity score (combines frequency and recency)
        recency_factor = 1.0 / (
            1.0 + (datetime.now() - self.timestamp).total_seconds() / 3600
        )
        self.popularity_score = self.access_count * recency_factor


@dataclass
class CacheStats:
    """Cache performance statistics"""

    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    exact_hits: int = 0
    semantic_hits: int = 0
    evictions: int = 0
    total_similarity_searches: int = 0
    avg_similarity_score: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_queries == 0:
            return 0.0
        return self.cache_hits / self.total_queries

    @property
    def semantic_hit_rate(self) -> float:
        """Calculate semantic hit rate"""
        if self.cache_hits == 0:
            return 0.0
        return self.semantic_hits / self.cache_hits


class SemanticCache:
    """
    Semantic cache with similarity-based retrieval.

    Features:
    - Exact match lookup (O(1))
    - Semantic similarity search using embeddings
    - Popularity-based eviction (LRU + frequency)
    - Configurable similarity thresholds
    - Cache warming support
    - Detailed analytics
    """

    def __init__(
        self,
        embedding_service,
        max_size: int = 1000,
        default_ttl: int = 3600,
        similarity_threshold_high: float = 0.95,
        similarity_threshold_medium: float = 0.85,
        enable_semantic_search: bool = True,
    ):
        """
        Initialize semantic cache.

        Args:
            embedding_service: Service for generating query embeddings
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
            similarity_threshold_high: Threshold for high confidence match (>= 0.95)
            similarity_threshold_medium: Threshold for medium confidence match (>= 0.85)
            enable_semantic_search: Enable semantic similarity search
        """
        self.embedding_service = embedding_service
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.similarity_threshold_high = similarity_threshold_high
        self.similarity_threshold_medium = similarity_threshold_medium
        self.enable_semantic_search = enable_semantic_search

        # Storage
        self._exact_cache: Dict[str, CacheEntry] = {}  # query_hash -> entry
        self._semantic_cache: List[CacheEntry] = []  # All entries for similarity search

        # Statistics
        self.stats = CacheStats()

        # Popularity tracking
        self._query_frequency: Dict[str, int] = defaultdict(int)

        logger.info(
            f"Initialized SemanticCache: max_size={max_size}, "
            f"ttl={default_ttl}s, semantic_search={enable_semantic_search}"
        )

    def _hash_query(self, query: str) -> str:
        """Generate hash for exact match lookup"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    async def get(
        self, query: str, return_similarity: bool = False
    ) -> Optional[Tuple[Dict[str, Any], float, str]]:
        """
        Get cached response for query.

        Tries exact match first, then semantic similarity if enabled.

        Args:
            query: User query
            return_similarity: If True, return (response, similarity, match_type)

        Returns:
            Cached response dict, or None if not found
            If return_similarity=True: (response, similarity_score, match_type)
            match_type: 'exact' | 'semantic_high' | 'semantic_medium'
        """
        self.stats.total_queries += 1
        query_hash = self._hash_query(query)

        # Try exact match first
        if query_hash in self._exact_cache:
            entry = self._exact_cache[query_hash]

            # Check if expired
            if entry.is_expired():
                self._evict_entry(query_hash)
                self.stats.cache_misses += 1
                return None

            # Validate cached response before returning
            if not self._is_valid_response(entry.response):
                logger.warning(
                    f"Invalid response found in cache for query '{query[:50]}...', "
                    f"removing from cache"
                )
                self._evict_entry(query_hash)
                self.stats.cache_misses += 1
                return None

            # Update access stats
            entry.update_access()
            self.stats.cache_hits += 1
            self.stats.exact_hits += 1

            logger.debug(f"Cache HIT (exact): '{query[:50]}...'")

            if return_similarity:
                return entry.response, 1.0, "exact"
            return entry.response

        # Try semantic similarity search
        if self.enable_semantic_search:
            result = await self._semantic_search(query)
            if result:
                response, similarity, entry = result

                # Update access stats
                entry.update_access()
                self.stats.cache_hits += 1
                self.stats.semantic_hits += 1

                match_type = (
                    "semantic_high"
                    if similarity >= self.similarity_threshold_high
                    else "semantic_medium"
                )

                logger.debug(
                    f"Cache HIT (semantic): '{query[:50]}...' "
                    f"(similarity={similarity:.3f}, type={match_type})"
                )

                if return_similarity:
                    return response, similarity, match_type
                return response

        # Cache miss
        self.stats.cache_misses += 1
        logger.debug(f"Cache MISS: '{query[:50]}...'")
        return None

    async def _semantic_search(
        self, query: str
    ) -> Optional[Tuple[Dict[str, Any], float, CacheEntry]]:
        """
        Search for semantically similar cached queries.

        Returns:
            (response, similarity_score, entry) or None
        """
        if not self._semantic_cache:
            return None

        self.stats.total_similarity_searches += 1
        start_time = time.time()

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)

        # Calculate similarities
        best_similarity = 0.0
        best_entry = None
        similarities = []

        for entry in self._semantic_cache:
            if entry.is_expired():
                continue

            # Validate cached response
            if not self._is_valid_response(entry.response):
                continue

            # Cosine similarity
            similarity = self._cosine_similarity(query_embedding, entry.query_embedding)
            similarities.append(similarity)

            if similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry

        # Update average similarity
        if similarities:
            avg_sim = np.mean(similarities)
            # Running average
            alpha = 0.1
            self.stats.avg_similarity_score = (
                alpha * avg_sim + (1 - alpha) * self.stats.avg_similarity_score
            )

        search_time = (time.time() - start_time) * 1000
        logger.debug(f"Semantic search completed in {search_time:.1f}ms")

        # Check if similarity meets threshold
        if best_entry and best_similarity >= self.similarity_threshold_medium:
            return best_entry.response, best_similarity, best_entry

        return None

    def _is_valid_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate if a response is suitable for caching/returning.

        Args:
            response: Response to validate

        Returns:
            True if response is valid, False otherwise
        """
        # Extract response text
        response_text = (
            response.get("response", "")
            if isinstance(response, dict)
            else str(response)
        )

        # Check for empty response
        if not response_text or response_text.strip() == "":
            return False

        # Check for error indicators
        error_indicators = [
            "No response generated",
            "Unable to generate",
            "Processing your query",
            "Please wait for detailed results",
            "An error occurred",
            "Unable to process",
            "No relevant documents found",
            "Performing deeper search",
            "try again",
            "contact support",
        ]

        response_lower = response_text.lower()
        if any(indicator.lower() in response_lower for indicator in error_indicators):
            return False

        # Check confidence score if available
        confidence = (
            response.get("confidence_score", 1.0) if isinstance(response, dict) else 1.0
        )
        if confidence < 0.3:
            return False

        # Check for sources
        sources = response.get("sources", []) if isinstance(response, dict) else []
        if not sources or len(sources) == 0:
            return False

        return True

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def set(
        self,
        query: str,
        response: Dict[str, Any],
        confidence: float = 1.0,
        ttl: Optional[int] = None,
    ):
        """
        Cache a query response.

        Only caches valid responses (not empty or error responses).

        Args:
            query: User query
            response: Response to cache
            confidence: Confidence score of response
            ttl: Time-to-live in seconds (None = use default)
        """
        # Don't cache invalid responses
        response_text = (
            response.get("response", "")
            if isinstance(response, dict)
            else str(response)
        )

        if not response_text or response_text.strip() == "":
            logger.debug(f"Skipping cache for empty response")
            return

        # Don't cache error responses or fallback messages
        error_indicators = [
            "No response generated",
            "Unable to generate",
            "Processing your query",
            "Please wait for detailed results",
            "An error occurred",
            "Unable to process",
            "No relevant documents found",
            "Performing deeper search",
            "try again",
            "contact support",
        ]

        response_lower = response_text.lower()
        if any(indicator.lower() in response_lower for indicator in error_indicators):
            logger.debug(f"Skipping cache for error/fallback response")
            return

        # Don't cache low confidence responses
        if confidence < 0.3:
            logger.debug(
                f"Skipping cache for low confidence response ({confidence:.2f})"
            )
            return

        # Don't cache responses with no sources (likely invalid)
        sources = response.get("sources", []) if isinstance(response, dict) else []
        if not sources or len(sources) == 0:
            logger.debug(f"Skipping cache for response with no sources")
            return

        query_hash = self._hash_query(query)

        # Check if cache is full
        if len(self._exact_cache) >= self.max_size:
            self._evict_least_popular()

        # Generate embedding for semantic search
        query_embedding = await self.embedding_service.embed_query(query)

        # Create cache entry
        entry = CacheEntry(
            query=query,
            query_embedding=query_embedding,
            response=response,
            confidence=confidence,
            timestamp=datetime.now(),
            ttl_seconds=ttl or self.default_ttl,
        )

        # Store in both caches
        self._exact_cache[query_hash] = entry
        self._semantic_cache.append(entry)

        # Update frequency tracking
        self._query_frequency[query_hash] += 1

        logger.debug(
            f"Cached response for: '{query[:50]}...' (confidence: {confidence:.2f})"
        )

    def _evict_entry(self, query_hash: str):
        """Evict a specific cache entry"""
        if query_hash in self._exact_cache:
            entry = self._exact_cache[query_hash]
            del self._exact_cache[query_hash]

            # Remove from semantic cache
            self._semantic_cache = [e for e in self._semantic_cache if e != entry]

            self.stats.evictions += 1
            logger.debug(f"Evicted cache entry: {query_hash}")

    def _evict_least_popular(self):
        """Evict least popular entry based on LRU + frequency"""
        if not self._exact_cache:
            return

        # Calculate eviction scores (lower = more likely to evict)
        # Score = popularity_score * recency_factor
        scores = {}
        for query_hash, entry in self._exact_cache.items():
            recency = (datetime.now() - entry.last_accessed).total_seconds()
            recency_factor = 1.0 / (1.0 + recency / 3600)  # Decay over hours
            scores[query_hash] = entry.popularity_score * recency_factor

        # Find entry with lowest score
        least_popular_hash = min(scores, key=scores.get)
        self._evict_entry(least_popular_hash)

        logger.debug(
            f"Evicted least popular entry (score={scores[least_popular_hash]:.3f})"
        )

    def invalidate(self, query: str):
        """Invalidate cached entry for specific query"""
        query_hash = self._hash_query(query)
        self._evict_entry(query_hash)

    def clear(self):
        """Clear all cache entries"""
        self._exact_cache.clear()
        self._semantic_cache.clear()
        self._query_frequency.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self):
        """Remove all expired entries"""
        expired_hashes = [
            query_hash
            for query_hash, entry in self._exact_cache.items()
            if entry.is_expired()
        ]

        for query_hash in expired_hashes:
            self._evict_entry(query_hash)

        if expired_hashes:
            logger.info(f"Cleaned up {len(expired_hashes)} expired entries")

    async def warm_cache(self, common_queries: List[Tuple[str, Dict[str, Any]]]):
        """
        Pre-populate cache with common queries.

        Args:
            common_queries: List of (query, response) tuples
        """
        logger.info(f"Warming cache with {len(common_queries)} queries...")

        for query, response in common_queries:
            await self.set(query, response, confidence=1.0)

        logger.info(f"Cache warming complete. Cache size: {len(self._exact_cache)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_queries": self.stats.total_queries,
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
            "hit_rate": round(self.stats.hit_rate, 3),
            "exact_hits": self.stats.exact_hits,
            "semantic_hits": self.stats.semantic_hits,
            "semantic_hit_rate": round(self.stats.semantic_hit_rate, 3),
            "evictions": self.stats.evictions,
            "cache_size": len(self._exact_cache),
            "max_size": self.max_size,
            "utilization": round(len(self._exact_cache) / self.max_size, 3),
            "avg_similarity_score": round(self.stats.avg_similarity_score, 3),
            "total_similarity_searches": self.stats.total_similarity_searches,
        }

    def get_popular_queries(self, top_n: int = 10) -> List[Tuple[str, int, float]]:
        """
        Get most popular cached queries.

        Returns:
            List of (query, access_count, popularity_score) tuples
        """
        entries_with_scores = [
            (entry.query, entry.access_count, entry.popularity_score)
            for entry in self._semantic_cache
        ]

        # Sort by popularity score
        entries_with_scores.sort(key=lambda x: x[2], reverse=True)

        return entries_with_scores[:top_n]


# Singleton instance
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """Get singleton semantic cache instance"""
    global _semantic_cache
    if _semantic_cache is None:
        raise RuntimeError(
            "Semantic cache not initialized. Call initialize_semantic_cache() first."
        )
    return _semantic_cache


def initialize_semantic_cache(
    embedding_service,
    max_size: int = 1000,
    default_ttl: int = 3600,
    similarity_threshold_high: float = 0.95,
    similarity_threshold_medium: float = 0.85,
    enable_semantic_search: bool = True,
) -> SemanticCache:
    """Initialize singleton semantic cache"""
    global _semantic_cache
    _semantic_cache = SemanticCache(
        embedding_service=embedding_service,
        max_size=max_size,
        default_ttl=default_ttl,
        similarity_threshold_high=similarity_threshold_high,
        similarity_threshold_medium=similarity_threshold_medium,
        enable_semantic_search=enable_semantic_search,
    )
    return _semantic_cache
