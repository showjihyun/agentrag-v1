"""
Static RAG Service

Implements a pure Static RAG pipeline without agent overhead for fast query processing.
This service provides sub-2-second responses for simple queries by using:
- Query embedding generation
- Vector similarity search
- Result ranking and filtering
- Single LLM generation call
- Response caching

Performance target: < 2 seconds (p95), < 1 second (p50)
"""

import logging
import hashlib
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager, SearchResult
from backend.services.llm_manager import LLMManager
from backend.core.cache_manager import MultiLevelCache
from backend.models.hybrid import StaticRAGResponse
from backend.exceptions import StaticRAGException

logger = logging.getLogger(__name__)


class StaticRAGService:
    """
    Static RAG Service for fast query processing.

    This service implements a streamlined RAG pipeline that:
    1. Checks cache for existing responses
    2. Generates query embedding
    3. Performs vector similarity search
    4. Ranks and filters results
    5. Generates response with single LLM call
    6. Caches the response

    Features:
    - Sub-2-second response time (p95)
    - Intelligent caching with TTL
    - Result diversity filtering
    - Preliminary confidence scoring
    - Comprehensive error handling
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        milvus_manager: MilvusManager,
        llm_manager: LLMManager,
        cache_manager: MultiLevelCache,
    ):
        """
        Initialize StaticRAGService with required dependencies.

        Args:
            embedding_service: Service for generating query embeddings
            milvus_manager: Manager for vector database operations
            llm_manager: Manager for LLM generation
            cache_manager: Multi-level cache manager
        """
        self.embedding = embedding_service
        self.milvus = milvus_manager
        self.llm = llm_manager
        self.cache = cache_manager

        # Configuration
        self.cache_namespace = "static_rag"
        self.cache_ttl = 3600  # 1 hour
        self.min_similarity_score = 0.5  # Minimum score for including results
        self.diversity_threshold = 0.85  # Similarity threshold for diversity filtering

        logger.info("StaticRAGService initialized")

    def _generate_cache_key(self, query: str, session_id: str, top_k: int) -> str:
        """
        Generate cache key for Static RAG responses.

        Args:
            query: User query text
            session_id: Session identifier
            top_k: Number of results requested

        Returns:
            Cache key string
        """
        # Create a deterministic hash from query parameters
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        session_hash = hashlib.sha256(session_id.encode()).hexdigest()[:8]

        cache_key = f"{query_hash}:{session_hash}:{top_k}"

        logger.debug(f"Generated cache key: {cache_key}")
        return cache_key

    async def _check_cache(self, cache_key: str) -> Optional[StaticRAGResponse]:
        """
        Check cache for existing response.

        Args:
            cache_key: Cache key to check

        Returns:
            Cached StaticRAGResponse or None if not found
        """
        try:
            cached_data = await self.cache.get(
                key=cache_key, namespace=self.cache_namespace
            )

            if cached_data:
                logger.info(f"Cache hit for key: {cache_key}")
                # Reconstruct StaticRAGResponse from cached data
                return StaticRAGResponse(**cached_data)

            logger.debug(f"Cache miss for key: {cache_key}")
            return None

        except Exception as e:
            logger.warning(f"Cache check error: {e}")
            return None

    async def _cache_response(
        self, cache_key: str, response: StaticRAGResponse
    ) -> None:
        """
        Cache the response for future use.

        Only caches valid responses (not empty or error responses).

        Args:
            cache_key: Cache key
            response: Response to cache
        """
        try:
            # Don't cache invalid responses
            if not response.response or response.response.strip() == "":
                logger.debug(f"Skipping cache for empty response")
                return

            # Don't cache error responses
            if "No response generated" in response.response:
                logger.debug(f"Skipping cache for error response")
                return

            # Don't cache low confidence responses
            if response.confidence_score < 0.3:
                logger.debug(
                    f"Skipping cache for low confidence response ({response.confidence_score:.2f})"
                )
                return

            # Convert response to dict for caching
            cache_data = response.model_dump()

            await self.cache.set(
                key=cache_key,
                value=cache_data,
                namespace=self.cache_namespace,
                ttl=self.cache_ttl,
            )

            logger.debug(
                f"Cached response for key: {cache_key} (confidence: {response.confidence_score:.2f})"
            )

        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def _rank_and_filter_results(
        self, results: List[SearchResult], top_k: int
    ) -> List[SearchResult]:
        """
        Rank results by similarity score and apply diversity filtering.

        Args:
            results: Search results from Milvus
            top_k: Number of results to return

        Returns:
            Filtered and ranked list of SearchResult objects
        """
        if not results:
            return []

        # Filter by minimum similarity score
        filtered = [r for r in results if r.score >= self.min_similarity_score]

        if not filtered:
            logger.warning("No results met minimum similarity threshold")
            return []

        # Sort by score (descending)
        sorted_results = sorted(filtered, key=lambda x: x.score, reverse=True)

        # Apply diversity filtering to avoid redundant results
        diverse_results = []
        for result in sorted_results:
            if len(diverse_results) >= top_k:
                break

            # Check if this result is sufficiently different from already selected ones
            is_diverse = True
            for selected in diverse_results:
                # Simple diversity check based on text similarity
                # In production, you might want to use embedding similarity
                if (
                    self._text_similarity(result.text, selected.text)
                    > self.diversity_threshold
                ):
                    is_diverse = False
                    break

            if is_diverse:
                diverse_results.append(result)

        logger.info(
            f"Ranked and filtered: {len(results)} -> {len(filtered)} -> {len(diverse_results)} results"
        )

        return diverse_results

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity (Jaccard similarity on words).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_preliminary_confidence(self, sources: List[SearchResult]) -> float:
        """
        Calculate preliminary confidence score based on search results.

        Args:
            sources: List of search results

        Returns:
            Confidence score (0-1)
        """
        if not sources:
            return 0.0

        # Factors for confidence calculation:
        # 1. Number of sources (more is better, up to a point)
        # 2. Average similarity score
        # 3. Top result score

        num_sources = len(sources)
        avg_score = sum(s.score for s in sources) / num_sources
        top_score = sources[0].score if sources else 0.0

        # Weighted combination
        num_sources_factor = min(num_sources / 5.0, 1.0)  # Normalize to 5 sources
        avg_score_factor = avg_score
        top_score_factor = top_score

        confidence = (
            0.3 * num_sources_factor + 0.4 * avg_score_factor + 0.3 * top_score_factor
        )

        logger.debug(
            f"Confidence calculation: num_sources={num_sources}, "
            f"avg_score={avg_score:.3f}, top_score={top_score:.3f}, "
            f"confidence={confidence:.3f}"
        )

        return min(confidence, 1.0)

    def _build_context_prompt(self, query: str, sources: List[SearchResult]) -> str:
        """
        Build context prompt for LLM generation.

        Args:
            query: User query
            sources: Retrieved source documents

        Returns:
            Formatted prompt string
        """
        if not sources:
            return f"""You are a helpful AI assistant. Answer the following question based on your knowledge:

Question: {query}

Please provide a clear and concise answer."""

        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[Source {i}] {source.document_name}\n{source.text}\n"
            )

        context = "\n".join(context_parts)

        prompt = f"""You are a helpful AI assistant. Answer the following question based on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, accurate answer based on the context
- Cite sources using [Source N] notation
- If the context doesn't contain enough information, acknowledge this
- Be concise but comprehensive

Answer:"""

        return prompt

    async def process_query(
        self, query: str, session_id: str, top_k: int = 5, enable_cache: bool = True
    ) -> StaticRAGResponse:
        """
        Process query using Static RAG pipeline.

        This is the main entry point for Static RAG processing. It orchestrates
        the entire pipeline from cache check to response generation.

        Args:
            query: User query text
            session_id: Session identifier for context
            top_k: Number of results to retrieve
            enable_cache: Whether to use caching

        Returns:
            StaticRAGResponse with generated answer and metadata

        Raises:
            StaticRAGException: If processing fails
        """
        start_time = time.time()
        metadata: Dict[str, Any] = {}

        try:
            logger.info(f"Processing Static RAG query: '{query[:100]}...'")

            # Step 1: Check cache
            cache_key = self._generate_cache_key(query, session_id, top_k)

            if enable_cache:
                cached_response = await self._check_cache(cache_key)
                if cached_response:
                    # Update processing time and return cached response
                    cached_response.processing_time = time.time() - start_time
                    cached_response.cache_hit = True
                    logger.info(
                        f"Returning cached response (time: {cached_response.processing_time:.3f}s)"
                    )
                    return cached_response

            # Step 2: Generate query embedding
            embedding_start = time.time()
            try:
                query_embedding = await self.embedding.embed_text(query)
                embedding_time = (time.time() - embedding_start) * 1000
                metadata["embedding_time_ms"] = round(embedding_time, 2)
                logger.debug(f"Generated embedding in {embedding_time:.2f}ms")
            except Exception as e:
                raise StaticRAGException(f"Embedding generation failed: {str(e)}")

            # Step 3: Vector search
            search_start = time.time()
            try:
                search_results = await self.milvus.search(
                    query_embedding=query_embedding,
                    top_k=top_k * 2,  # Get more results for diversity filtering
                    filters=None,
                    output_fields=None,
                )
                search_time = (time.time() - search_start) * 1000
                metadata["search_time_ms"] = round(search_time, 2)
                metadata["raw_results_count"] = len(search_results)
                logger.debug(
                    f"Vector search completed in {search_time:.2f}ms, found {len(search_results)} results"
                )
            except Exception as e:
                raise StaticRAGException(f"Vector search failed: {str(e)}")

            # Step 4: Rank and filter results
            sources = self._rank_and_filter_results(search_results, top_k)
            metadata["filtered_results_count"] = len(sources)

            # Step 5: Calculate preliminary confidence
            confidence_score = self._calculate_preliminary_confidence(sources)
            metadata["confidence_score"] = round(confidence_score, 3)

            # Step 6: Generate response with LLM
            llm_start = time.time()
            try:
                prompt = self._build_context_prompt(query, sources)

                # Single LLM call (non-streaming for Static RAG)
                response_text = await self.llm.generate(
                    messages=[{"role": "user", "content": prompt}],
                    stream=False,
                    temperature=0.7,
                    max_tokens=500,
                )

                llm_time = (time.time() - llm_start) * 1000
                metadata["llm_time_ms"] = round(llm_time, 2)
                logger.debug(f"LLM generation completed in {llm_time:.2f}ms")
            except Exception as e:
                raise StaticRAGException(f"LLM generation failed: {str(e)}")

            # Step 7: Build response
            processing_time = time.time() - start_time
            metadata["total_time_ms"] = round(processing_time * 1000, 2)
            metadata["num_sources"] = len(sources)

            response = StaticRAGResponse(
                response=response_text,
                sources=sources,
                confidence_score=confidence_score,
                processing_time=processing_time,
                cache_hit=False,
                metadata=metadata,
            )

            # Step 8: Cache the response
            if enable_cache:
                await self._cache_response(cache_key, response)

            logger.info(
                f"Static RAG completed in {processing_time:.3f}s "
                f"(confidence: {confidence_score:.3f}, sources: {len(sources)})"
            )

            return response

        except StaticRAGException:
            # Re-raise StaticRAGException as-is
            raise

        except Exception as e:
            # Wrap unexpected errors
            error_msg = f"Static RAG processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StaticRAGException(error_msg) from e

    async def invalidate_cache(
        self, query: Optional[str] = None, session_id: Optional[str] = None
    ) -> None:
        """
        Invalidate cached responses.

        Args:
            query: Specific query to invalidate (None = all)
            session_id: Specific session to invalidate (None = all)
        """
        try:
            if query and session_id:
                # Invalidate specific query
                cache_key = self._generate_cache_key(query, session_id, 5)
                await self.cache.delete(cache_key, self.cache_namespace)
                logger.info(f"Invalidated cache for specific query")
            else:
                # Clear entire namespace
                await self.cache.clear_namespace(self.cache_namespace)
                logger.info(f"Cleared all Static RAG cache")

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service stats
        """
        try:
            cache_stats = await self.cache.get_stats()

            return {
                "service": "StaticRAGService",
                "cache_namespace": self.cache_namespace,
                "cache_ttl": self.cache_ttl,
                "min_similarity_score": self.min_similarity_score,
                "diversity_threshold": self.diversity_threshold,
                "cache_stats": cache_stats,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
