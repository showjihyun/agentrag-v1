"""
Speculative Processor for fast initial responses in hybrid RAG system.

This processor provides quick initial responses using fast vector search and
simple LLM generation, with caching for sub-500ms responses on cache hits.
"""

import logging
import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import redis.asyncio as redis

from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager, SearchResult
from backend.services.llm_manager import LLMManager
from backend.services.semantic_cache import SemanticCache
from backend.models.hybrid import SpeculativeResponse, PathSource
from backend.models.query import SearchResult as QuerySearchResult
from backend.memory.stm import ShortTermMemory

logger = logging.getLogger(__name__)


class SpeculativeProcessor:
    """
    Fast speculative processor for initial responses.

    Features:
    - Quick vector search with top_k=5 and 1-second timeout
    - Cache check before vector search for sub-500ms responses
    - Fast LLM generation with low temperature and short max_tokens
    - Confidence scoring based on vector similarity and document count
    - TTL-based cache with LRU eviction

    Requirements: 2.1, 2.2, 2.3, 2.6, 5.1, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        milvus_manager: MilvusManager,
        llm_manager: LLMManager,
        redis_client: redis.Redis,
        stm: Optional[ShortTermMemory] = None,
        semantic_cache: Optional[SemanticCache] = None,
        cache_ttl: int = 3600,  # 1 hour
        cache_prefix: str = "speculative:",
        max_cache_size: int = 1000,
    ):
        """
        Initialize SpeculativeProcessor with Smart Hybrid Search.

        Args:
            embedding_service: Service for generating embeddings
            milvus_manager: Manager for vector database operations
            llm_manager: Manager for LLM interactions
            redis_client: Redis client for caching
            stm: Optional ShortTermMemory instance for conversation context
            semantic_cache: Optional SemanticCache for similarity-based caching
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            cache_prefix: Prefix for cache keys
            max_cache_size: Maximum number of cached entries (LRU eviction)
        """
        self.embedding_service = embedding_service
        self.milvus_manager = milvus_manager
        self.llm_manager = llm_manager
        self.redis_client = redis_client
        self.stm = stm
        self.semantic_cache = semantic_cache
        self.cache_ttl = cache_ttl
        self.cache_prefix = cache_prefix
        self.max_cache_size = max_cache_size

        # Smart Hybrid Search components
        try:
            from backend.services.bm25_search import get_bm25_service
            from backend.services.hybrid_search import get_hybrid_search_service
            from backend.services.query_type_analyzer import get_query_type_analyzer

            self.bm25_service = get_bm25_service()
            self.hybrid_service = get_hybrid_search_service(
                vector_weight=0.7, bm25_weight=0.3
            )
            self.query_analyzer = get_query_type_analyzer()
            self.smart_hybrid_enabled = True

            logger.info("Smart Hybrid Search enabled in SpeculativeProcessor")
        except Exception as e:
            logger.warning(f"Smart Hybrid Search not available: {e}")
            self.bm25_service = None
            self.hybrid_service = None
            self.query_analyzer = None
            self.smart_hybrid_enabled = False

        logger.info(
            f"SpeculativeProcessor initialized with cache_ttl={cache_ttl}s, "
            f"max_cache_size={max_cache_size}, stm_enabled={stm is not None}, "
            f"semantic_cache_enabled={semantic_cache is not None}, "
            f"smart_hybrid_enabled={self.smart_hybrid_enabled}"
        )

    def _generate_cache_key(self, query: str, top_k: int) -> str:
        """
        Generate cache key from query and parameters.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            Cache key string
        """
        # Create a hash of the query and parameters
        key_data = f"{query}:{top_k}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{self.cache_prefix}{key_hash}"

    async def _check_cache(self, cache_key: str) -> Optional[SpeculativeResponse]:
        """
        Check cache for existing response.

        Args:
            cache_key: Cache key to check

        Returns:
            Cached SpeculativeResponse if found and valid, None otherwise

        Requirements: 7.1, 7.2, 7.3
        """
        try:
            start_time = time.time()

            # Get from Redis
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                # Parse cached response
                response_dict = json.loads(cached_data)
                response = SpeculativeResponse(**response_dict)

                # Validate cached response before returning
                if not self._is_valid_response(response):
                    logger.warning(
                        f"Invalid response found in cache for key {cache_key}, "
                        f"removing from cache"
                    )
                    # Remove invalid cached response
                    await self.redis_client.delete(cache_key)
                    return None

                # Update cache hit flag
                response.cache_hit = True

                cache_time = (time.time() - start_time) * 1000
                logger.info(
                    f"Cache hit for key {cache_key} (retrieved in {cache_time:.1f}ms)"
                )

                return response

            logger.debug(f"Cache miss for key {cache_key}")
            return None

        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None

    def _is_valid_response(self, response: SpeculativeResponse) -> bool:
        """
        Validate if a response is suitable for caching/returning.

        Args:
            response: Response to validate

        Returns:
            True if response is valid, False otherwise
        """
        # Check for empty response
        if not response.response or response.response.strip() == "":
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

        response_lower = response.response.lower()
        if any(indicator.lower() in response_lower for indicator in error_indicators):
            return False

        # Check confidence score
        if response.confidence_score < 0.3:
            return False

        # Check for sources
        if not response.sources or len(response.sources) == 0:
            return False

        return True

    async def _store_in_cache(
        self, cache_key: str, response: SpeculativeResponse
    ) -> None:
        """
        Store response in cache with TTL and LRU eviction.

        Only caches valid responses (not empty or error responses).

        Args:
            cache_key: Cache key
            response: Response to cache

        Requirements: 7.1, 7.4, 7.5, 7.6
        """
        try:
            # Don't cache invalid responses
            if not response.response or response.response.strip() == "":
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

            response_lower = response.response.lower()
            if any(
                indicator.lower() in response_lower for indicator in error_indicators
            ):
                logger.debug(f"Skipping cache for error/fallback response")
                return

            # Don't cache low confidence responses
            if response.confidence_score < 0.3:
                logger.debug(
                    f"Skipping cache for low confidence response ({response.confidence_score:.2f})"
                )
                return

            # Don't cache responses with no sources (likely invalid)
            if not response.sources or len(response.sources) == 0:
                logger.debug(f"Skipping cache for response with no sources")
                return

            # Check cache size and evict if necessary
            await self._enforce_cache_size()

            # Serialize response
            response_dict = response.model_dump()
            response_json = json.dumps(response_dict, default=str)

            # Store with TTL
            await self.redis_client.setex(cache_key, self.cache_ttl, response_json)

            # Track cache key for LRU
            await self.redis_client.zadd(
                f"{self.cache_prefix}lru", {cache_key: time.time()}
            )

            logger.debug(
                f"Stored response in cache: {cache_key} (confidence: {response.confidence_score:.2f})"
            )

        except Exception as e:
            logger.warning(f"Failed to store in cache: {e}")

    async def _enforce_cache_size(self) -> None:
        """
        Enforce maximum cache size using LRU eviction.

        Requirements: 7.6
        """
        try:
            lru_key = f"{self.cache_prefix}lru"

            # Get current cache size
            cache_size = await self.redis_client.zcard(lru_key)

            if cache_size >= self.max_cache_size:
                # Calculate how many to evict (10% of max size)
                evict_count = max(1, self.max_cache_size // 10)

                # Get oldest entries
                oldest_keys = await self.redis_client.zrange(
                    lru_key, 0, evict_count - 1
                )

                if oldest_keys:
                    # Delete old entries
                    await self.redis_client.delete(*oldest_keys)
                    await self.redis_client.zrem(lru_key, *oldest_keys)

                    logger.info(f"Evicted {len(oldest_keys)} old cache entries (LRU)")

        except Exception as e:
            logger.warning(f"Cache size enforcement failed: {e}")

    async def _fast_vector_search(
        self, query: str, top_k: int = 5, timeout: float = 1.0
    ) -> Tuple[List[SearchResult], float]:
        """
        Perform fast vector search with timeout.

        Args:
            query: Query text
            top_k: Number of results (default: 5 for speed)
            timeout: Search timeout in seconds

        Returns:
            Tuple of (search results, search time in seconds)

        Requirements: 2.1, 2.2
        """
        start_time = time.time()

        try:
            # Generate query embedding (now async)
            query_embedding = await self.embedding_service.embed_text(query)

            # Perform search with timeout
            search_task = self.milvus_manager.search(
                query_embedding=query_embedding, top_k=top_k
            )

            results = await asyncio.wait_for(search_task, timeout=timeout)

            search_time = time.time() - start_time

            logger.info(
                f"Fast vector search completed in {search_time:.3f}s, "
                f"found {len(results)} results"
            )

            return results, search_time

        except asyncio.TimeoutError:
            search_time = time.time() - start_time
            logger.warning(f"Vector search timed out after {search_time:.3f}s")
            return [], search_time

        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"Vector search failed: {e}")
            return [], search_time

    async def _fast_hybrid_search(
        self, query: str, top_k: int = 5, timeout: float = 1.2
    ) -> Tuple[List[SearchResult], float]:
        """
        Perform fast hybrid search (Vector + BM25) with parallel execution.

        Args:
            query: Query text
            top_k: Number of results (default: 5 for speed)
            timeout: Search timeout in seconds

        Returns:
            Tuple of (search results, search time in seconds)
        """
        start_time = time.time()

        try:
            # Parallel execution of vector and BM25 search
            async def vector_search():
                query_embedding = await self.embedding_service.embed_text(query)
                return await self.milvus_manager.search(
                    query_embedding=query_embedding,
                    top_k=top_k * 2,  # Get more for fusion
                )

            async def bm25_search():
                results = await self.bm25_service.search(query, top_k * 2)
                # Convert (doc_id, score) tuples to SearchResult format if needed
                return results

            # Execute both searches in parallel with timeout
            vector_task = asyncio.wait_for(vector_search(), timeout=timeout / 2)
            bm25_task = asyncio.wait_for(bm25_search(), timeout=timeout / 2)

            vector_results, bm25_results = await asyncio.gather(
                vector_task, bm25_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(vector_results, Exception):
                logger.warning(f"Vector search failed in hybrid: {vector_results}")
                vector_results = []

            if isinstance(bm25_results, Exception):
                logger.warning(f"BM25 search failed in hybrid: {bm25_results}")
                bm25_results = []

            # If both failed, return empty
            if not vector_results and not bm25_results:
                search_time = time.time() - start_time
                logger.warning("Both vector and BM25 searches failed")
                return [], search_time

            # If only one succeeded, use that
            if not vector_results:
                search_time = time.time() - start_time
                logger.info(f"Using BM25 only: {len(bm25_results)} results")
                return bm25_results[:top_k], search_time

            if not bm25_results:
                search_time = time.time() - start_time
                logger.info(f"Using vector only: {len(vector_results)} results")
                return vector_results[:top_k], search_time

            # Merge results using RRF
            merged = self.hybrid_service.reciprocal_rank_fusion(
                vector_results, bm25_results, top_k=top_k
            )

            search_time = time.time() - start_time

            logger.info(
                f"Fast hybrid search completed in {search_time:.3f}s, "
                f"found {len(merged)} results "
                f"(vector={len(vector_results)}, bm25={len(bm25_results)})"
            )

            return merged, search_time

        except asyncio.TimeoutError:
            search_time = time.time() - start_time
            logger.warning(f"Hybrid search timed out after {search_time:.3f}s")
            # Fallback to vector only
            return await self._fast_vector_search(query, top_k, timeout=1.0)

        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"Hybrid search failed: {e}, falling back to vector")
            # Fallback to vector only
            return await self._fast_vector_search(query, top_k, timeout=1.0)

    def _calculate_confidence_score(
        self, search_results: List[SearchResult], cache_hit: bool
    ) -> float:
        """
        Calculate confidence score for speculative response.

        Factors:
        - Vector similarity scores (average of top results)
        - Number of relevant documents found
        - Cache hit/miss (cache hits get slight boost)

        Args:
            search_results: Search results from vector database
            cache_hit: Whether response came from cache

        Returns:
            Confidence score between 0.0 and 1.0

        Requirements: 2.6, 5.1, 5.5
        """
        if not search_results:
            return 0.1  # Very low confidence with no results

        # Calculate average similarity score
        avg_similarity = sum(r.score for r in search_results) / len(search_results)

        # Factor in number of documents (more is better, up to 5)
        doc_count_factor = min(len(search_results) / 5.0, 1.0)

        # Base confidence from similarity and document count
        base_confidence = (avg_similarity * 0.7) + (doc_count_factor * 0.3)

        # Small boost for cache hits (they've been validated before)
        if cache_hit:
            base_confidence = min(base_confidence * 1.05, 1.0)

        # Ensure score is in valid range
        confidence = max(0.0, min(base_confidence, 1.0))

        logger.debug(
            f"Confidence score: {confidence:.3f} "
            f"(avg_sim={avg_similarity:.3f}, docs={len(search_results)}, "
            f"cache_hit={cache_hit})"
        )

        return confidence

    async def _load_conversation_context(
        self, session_id: str, max_messages: int = 5
    ) -> str:
        """
        Load recent conversation context from STM.

        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages to load

        Returns:
            Formatted conversation context string

        Requirements: 9.1, 9.2
        """
        if not self.stm or not session_id:
            return ""

        try:
            # Get recent conversation history
            history = self.stm.get_conversation_history(
                session_id=session_id, limit=max_messages
            )

            if not history:
                return ""

            # Format conversation context
            context_parts = []
            for msg in history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                # Truncate long messages for speed
                if len(content) > 150:
                    content = content[:150] + "..."

                context_parts.append(f"{role.capitalize()}: {content}")

            context = "\n".join(context_parts)
            logger.debug(
                f"Loaded {len(history)} messages from STM for session {session_id}"
            )

            return context

        except Exception as e:
            logger.warning(f"Failed to load conversation context: {e}")
            return ""

    async def _fast_llm_generation(
        self,
        query: str,
        search_results: List[SearchResult],
        session_id: Optional[str] = None,
        timeout: float = 1.5,
    ) -> Tuple[str, float]:
        """
        Generate fast response using LLM with low temperature and short tokens.

        Args:
            query: User query
            search_results: Retrieved documents
            session_id: Optional session ID for conversation context
            timeout: Generation timeout in seconds

        Returns:
            Tuple of (generated response, generation time in seconds)

        Requirements: 2.1, 2.3, 9.1, 9.2
        """
        start_time = time.time()

        try:
            # Load conversation context if available
            conversation_context = ""
            if session_id:
                conversation_context = await self._load_conversation_context(
                    session_id=session_id, max_messages=5
                )

            # Build context from search results with optimization
            from backend.core.context_optimizer import get_context_optimizer

            optimizer = get_context_optimizer(
                min_relevance_score=0.6,  # Higher threshold for fast path
                max_docs=3,  # Top 3 for speed
                max_chars_per_doc=300,  # Slightly more than 200 for better context
            )

            # Filter and optimize
            filtered_results = optimizer.filter_by_relevance(
                search_results, min_score=0.6, max_docs=3
            )

            context_parts = []
            for result in filtered_results:
                # Truncate without metadata overhead
                text, _ = optimizer.truncate_text(result.text, max_length=300)
                context_parts.append(text)

            context = (
                "\n\n".join(context_parts)
                if context_parts
                else "No relevant documents found."
            )

            logger.debug(
                f"Fast path context: {len(filtered_results)} docs, "
                f"~{len(context)/4:.0f} tokens"
            )

            # Optimize prompt for minimal token usage
            from backend.core.prompt_optimizer import get_prompt_optimizer

            prompt_optimizer = get_prompt_optimizer(enable_context_compression=True)

            # Get optimized prompt
            optimized_prompt = prompt_optimizer.optimize_prompt(
                query=query,
                context=context,
                mode="fast",
                complexity="simple",  # Fast path assumes simple queries
                conversation_history=None,  # Conversation context handled separately
            )

            # Add conversation context if available (already compressed)
            user_prompt = optimized_prompt.user_prompt
            if conversation_context:
                # Prepend compressed context
                user_prompt = f"{conversation_context}\n\n{user_prompt}"

            logger.debug(
                f"Optimized prompt: ~{optimized_prompt.estimated_input_tokens} input tokens, "
                f"max {optimized_prompt.max_tokens} output tokens"
            )

            # Generate with optimized settings
            generation_task = self.llm_manager.generate(
                messages=[
                    {"role": "system", "content": optimized_prompt.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=optimized_prompt.temperature,
                max_tokens=optimized_prompt.max_tokens,
                stream=False,
            )

            response = await asyncio.wait_for(generation_task, timeout=timeout)

            generation_time = time.time() - start_time

            logger.info(
                f"Fast LLM generation completed in {generation_time:.3f}s, "
                f"response length: {len(response)} chars"
            )

            return response, generation_time

        except asyncio.TimeoutError:
            generation_time = time.time() - start_time
            logger.warning(f"LLM generation timed out after {generation_time:.3f}s")
            # Return raw documents as fallback (Requirement 8.5)
            if search_results:
                fallback_response = self._format_raw_documents_fallback(
                    query, search_results
                )
                return fallback_response, generation_time
            return "Searching for more information...", generation_time

        except Exception as e:
            generation_time = time.time() - start_time
            # Log error without exposing internal details (Requirement 8.6)
            logger.error(
                f"LLM generation failed with {type(e).__name__}: {str(e)[:100]}",
                exc_info=True,
            )
            # Return raw documents as fallback (Requirement 8.5)
            if search_results:
                fallback_response = self._format_raw_documents_fallback(
                    query, search_results
                )
                return fallback_response, generation_time
            # Provide clear error message (Requirement 8.6)
            return (
                "Unable to generate a response at this time. "
                "Please try again or contact support if the issue persists."
            ), generation_time

    def _format_raw_documents_fallback(
        self, query: str, search_results: List[SearchResult]
    ) -> str:
        """
        Format raw retrieved documents as fallback when LLM is unavailable.

        Provides a clear, user-friendly presentation of the retrieved documents
        without LLM synthesis.

        Args:
            query: User query
            search_results: Retrieved documents

        Returns:
            Formatted string with raw document excerpts

        Requirements: 8.5, 8.6
        """
        if not search_results:
            return (
                "I found no relevant documents for your query. "
                "Please try rephrasing your question."
            )

        # Build response with document excerpts
        response_parts = [
            f"I found {len(search_results)} relevant document(s) for your query. "
            f"Here are the key excerpts:\n"
        ]

        for i, result in enumerate(search_results[:3], 1):
            # Truncate text for readability
            text = result.text[:300]
            if len(result.text) > 300:
                text += "..."

            response_parts.append(
                f"\n{i}. From '{result.document_name}' "
                f"(relevance: {result.score:.2f}):\n{text}"
            )

        response_parts.append(
            "\n\nNote: This is a direct excerpt from the documents. "
            "For a synthesized answer, please try again in a moment."
        )

        return "\n".join(response_parts)

    def _convert_search_results(
        self, milvus_results: List[SearchResult]
    ) -> List[QuerySearchResult]:
        """
        Convert Milvus SearchResult to QuerySearchResult format.

        Args:
            milvus_results: Results from Milvus search

        Returns:
            List of QuerySearchResult objects
        """
        converted = []
        for result in milvus_results:
            converted.append(
                QuerySearchResult(
                    chunk_id=result.id,
                    document_id=result.document_id,
                    document_name=result.document_name,
                    text=result.text,
                    score=result.score,
                    metadata=result.metadata,
                )
            )
        return converted

    async def _save_to_stm(
        self, session_id: str, query: str, response: str, metadata: Dict[str, Any]
    ) -> None:
        """
        Save speculative results to STM with path marker.

        Args:
            session_id: Session identifier
            query: User query
            response: Generated response
            metadata: Response metadata

        Requirements: 9.2, 9.6
        """
        if not self.stm or not session_id:
            return

        try:
            # Add user query to STM
            self.stm.add_message(
                session_id=session_id,
                role="user",
                content=query,
                metadata={"path": "speculative"},
            )

            # Add speculative response to STM with path marker
            response_metadata = {
                "path": "speculative",
                "confidence_score": metadata.get("confidence_score", 0.0),
                "processing_time": metadata.get("processing_time", 0.0),
                "cache_hit": metadata.get("cache_hit", False),
            }

            self.stm.add_message(
                session_id=session_id,
                role="assistant",
                content=response,
                metadata=response_metadata,
            )

            logger.debug(f"Saved speculative results to STM for session {session_id}")

        except Exception as e:
            logger.warning(f"Failed to save to STM: {e}")

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        enable_cache: bool = True,
    ) -> SpeculativeResponse:
        """
        Process query through speculative path for fast initial response.

        Workflow:
        1. Load conversation context from STM (if available)
        2. Check cache for existing response (if enabled)
        3. If cache miss, perform fast vector search (1s timeout)
        4. Generate quick LLM response with conversation context (1.5s timeout)
        5. Calculate confidence score
        6. Cache the response
        7. Save results to STM with path marker

        Args:
            query: User query text
            session_id: Optional session ID for conversation context
            top_k: Number of documents to retrieve (default: 5)
            enable_cache: Whether to use caching

        Returns:
            SpeculativeResponse with answer, confidence, and metadata

        Requirements: 2.1, 2.2, 2.3, 2.6, 5.1, 7.1, 7.2, 7.3, 9.1, 9.2, 9.6
        """
        overall_start = time.time()
        cache_hit = False
        search_results = []
        response_text = ""
        metadata = {}

        try:
            # Generate cache key
            cache_key = self._generate_cache_key(query, top_k)

            # Check cache first (try semantic cache, then fallback to Redis)
            cache_match_type = None
            cache_similarity = None

            if enable_cache:
                # Try semantic cache first if available
                if self.semantic_cache:
                    cache_result = await self.semantic_cache.get(
                        query=query, return_similarity=True
                    )

                    if cache_result:
                        cached_data, cache_similarity, cache_match_type = cache_result

                        # Convert cached data to SpeculativeResponse
                        cached_response = SpeculativeResponse(**cached_data)
                        cached_response.cache_hit = True

                        # Add cache metadata
                        cached_response.metadata.update(
                            {
                                "cache_match_type": cache_match_type,
                                "cache_similarity": cache_similarity,
                            }
                        )

                        logger.info(
                            f"Returning cached response from semantic cache "
                            f"(type={cache_match_type}, similarity={cache_similarity:.3f})"
                        )

                        # Still save to STM even for cached responses
                        if session_id:
                            await self._save_to_stm(
                                session_id=session_id,
                                query=query,
                                response=cached_response.response,
                                metadata={
                                    "confidence_score": cached_response.confidence_score,
                                    "processing_time": cached_response.processing_time,
                                    "cache_hit": True,
                                    "cache_match_type": cache_match_type,
                                    "cache_similarity": cache_similarity,
                                },
                            )
                        return cached_response

                # Fallback to Redis cache
                cached_response = await self._check_cache(cache_key)
                if cached_response:
                    cache_match_type = "exact"
                    cache_similarity = 1.0

                    # Add cache metadata
                    cached_response.metadata.update(
                        {
                            "cache_match_type": cache_match_type,
                            "cache_similarity": cache_similarity,
                        }
                    )

                    logger.info("Returning cached response from Redis (exact match)")

                    # Still save to STM even for cached responses
                    if session_id:
                        await self._save_to_stm(
                            session_id=session_id,
                            query=query,
                            response=cached_response.response,
                            metadata={
                                "confidence_score": cached_response.confidence_score,
                                "processing_time": cached_response.processing_time,
                                "cache_hit": True,
                                "cache_match_type": cache_match_type,
                                "cache_similarity": cache_similarity,
                            },
                        )
                    return cached_response

            # Cache miss - perform smart search (hybrid or vector based on query type)
            search_method = "vector"  # default

            if self.smart_hybrid_enabled and self.query_analyzer:
                # Analyze query type
                query_analysis = self.query_analyzer.analyze(query)

                if query_analysis.use_hybrid:
                    # Use hybrid search for keyword/technical/comparison queries
                    search_results, search_time = await self._fast_hybrid_search(
                        query=query, top_k=top_k, timeout=1.2
                    )
                    search_method = "hybrid"
                    metadata["query_type"] = query_analysis.query_type
                    metadata["query_analysis_confidence"] = query_analysis.confidence
                    logger.info(
                        f"Using hybrid search for {query_analysis.query_type} query "
                        f"(confidence: {query_analysis.confidence:.2f})"
                    )
                else:
                    # Use vector search for semantic queries
                    search_results, search_time = await self._fast_vector_search(
                        query=query, top_k=top_k, timeout=1.0
                    )
                    metadata["query_type"] = query_analysis.query_type
                    metadata["query_analysis_confidence"] = query_analysis.confidence
                    logger.info(
                        f"Using vector search for {query_analysis.query_type} query "
                        f"(confidence: {query_analysis.confidence:.2f})"
                    )
            else:
                # Fallback to vector search if smart hybrid not available
                search_results, search_time = await self._fast_vector_search(
                    query=query, top_k=top_k, timeout=1.0
                )

            metadata["search_method"] = search_method
            metadata["search_time_ms"] = int(search_time * 1000)

            # Generate fast LLM response with conversation context
            if search_results:
                response_text, gen_time = await self._fast_llm_generation(
                    query=query,
                    search_results=search_results,
                    session_id=session_id,
                    timeout=1.5,
                )
                metadata["llm_time_ms"] = int(gen_time * 1000)
            else:
                response_text = (
                    "No relevant documents found. "
                    "Performing deeper search for more comprehensive results..."
                )
                metadata["llm_time_ms"] = 0

            # Calculate confidence score
            confidence = self._calculate_confidence_score(
                search_results=search_results, cache_hit=cache_hit
            )

            # Calculate total processing time
            processing_time = time.time() - overall_start

            # Create response object
            response = SpeculativeResponse(
                response=response_text,
                confidence_score=confidence,
                sources=self._convert_search_results(search_results),
                cache_hit=cache_hit,
                processing_time=processing_time,
                metadata=metadata,
            )

            # Cache the response (both Redis and semantic cache)
            if enable_cache:
                # Store in Redis cache
                await self._store_in_cache(cache_key, response)

                # Store in semantic cache if available
                if self.semantic_cache:
                    await self.semantic_cache.set(
                        query=query,
                        response=response.model_dump(),
                        confidence=confidence,
                    )

            # Save to STM with path marker
            if session_id:
                await self._save_to_stm(
                    session_id=session_id,
                    query=query,
                    response=response_text,
                    metadata={
                        "confidence_score": confidence,
                        "processing_time": processing_time,
                        "cache_hit": cache_hit,
                    },
                )

            logger.info(
                f"Speculative processing completed in {processing_time:.3f}s, "
                f"confidence={confidence:.3f}"
            )

            return response

        except Exception as e:
            logger.error(f"Speculative processing failed: {e}")

            # Return fallback response
            processing_time = time.time() - overall_start
            return SpeculativeResponse(
                response="Processing your query. Please wait for detailed results...",
                confidence_score=0.1,
                sources=[],
                cache_hit=False,
                processing_time=processing_time,
                metadata={"error": str(e)},
            )
