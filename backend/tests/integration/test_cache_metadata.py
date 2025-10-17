"""
Integration tests for cache metadata in query responses.

Tests that cache information is properly included in streaming responses.
"""

import pytest
import asyncio
import json
from datetime import datetime

from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.semantic_cache import SemanticCache, initialize_semantic_cache
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.llm_manager import LLMManager
from backend.models.hybrid import SpeculativeResponse


@pytest.fixture
async def embedding_service():
    """Create embedding service."""
    return EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")


@pytest.fixture
async def semantic_cache(embedding_service):
    """Create semantic cache."""
    return initialize_semantic_cache(
        embedding_service=embedding_service,
        max_size=100,
        default_ttl=3600,
        similarity_threshold_high=0.95,
        similarity_threshold_medium=0.85,
        enable_semantic_search=True,
    )


@pytest.fixture
async def speculative_processor(
    embedding_service,
    semantic_cache,
    mock_milvus_manager,
    mock_llm_manager,
    mock_redis_client,
):
    """Create speculative processor with semantic cache."""
    return SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=mock_milvus_manager,
        llm_manager=mock_llm_manager,
        redis_client=mock_redis_client,
        semantic_cache=semantic_cache,
    )


class TestCacheMetadataExactMatch:
    """Test cache metadata for exact matches."""

    @pytest.mark.asyncio
    async def test_exact_cache_hit_metadata(self, speculative_processor):
        """Test that exact cache hits include proper metadata."""
        query = "What is machine learning?"

        # First request - cache miss
        response1 = await speculative_processor.process(
            query=query, top_k=5, enable_cache=True
        )

        assert response1.cache_hit is False
        assert "cache_match_type" not in response1.metadata

        # Second request - exact cache hit
        response2 = await speculative_processor.process(
            query=query, top_k=5, enable_cache=True
        )

        assert response2.cache_hit is True
        assert response2.metadata.get("cache_match_type") == "exact"
        assert response2.metadata.get("cache_similarity") == 1.0

        # Response should be identical
        assert response2.response == response1.response
        assert response2.confidence_score == response1.confidence_score

    @pytest.mark.asyncio
    async def test_cache_hit_faster_than_miss(self, speculative_processor):
        """Test that cache hits are significantly faster."""
        query = "Explain neural networks"

        # First request - cache miss
        response1 = await speculative_processor.process(
            query=query, top_k=5, enable_cache=True
        )
        time1 = response1.processing_time

        # Second request - cache hit
        response2 = await speculative_processor.process(
            query=query, top_k=5, enable_cache=True
        )
        time2 = response2.processing_time

        # Cache hit should be much faster (at least 2x)
        assert time2 < time1 / 2
        assert response2.cache_hit is True


class TestCacheMetadataSemanticMatch:
    """Test cache metadata for semantic similarity matches."""

    @pytest.mark.asyncio
    async def test_semantic_high_similarity_match(self, speculative_processor):
        """Test semantic cache with high similarity match."""
        # First query
        query1 = "What is machine learning?"
        response1 = await speculative_processor.process(
            query=query1, top_k=5, enable_cache=True
        )

        # Very similar query (should match with high similarity)
        query2 = "What is machine learning"  # Minor punctuation difference
        response2 = await speculative_processor.process(
            query=query2, top_k=5, enable_cache=True
        )

        # Should be semantic cache hit
        assert response2.cache_hit is True
        assert response2.metadata.get("cache_match_type") in ["exact", "semantic_high"]

        similarity = response2.metadata.get("cache_similarity")
        assert similarity is not None
        assert similarity >= 0.95  # High similarity threshold

    @pytest.mark.asyncio
    async def test_semantic_medium_similarity_match(self, speculative_processor):
        """Test semantic cache with medium similarity match."""
        # First query
        query1 = "What is deep learning?"
        response1 = await speculative_processor.process(
            query=query1, top_k=5, enable_cache=True
        )

        # Semantically similar query
        query2 = "Explain deep learning concepts"
        response2 = await speculative_processor.process(
            query=query2, top_k=5, enable_cache=True
        )

        # May or may not be a cache hit depending on similarity
        if response2.cache_hit:
            match_type = response2.metadata.get("cache_match_type")
            assert match_type in ["semantic_high", "semantic_medium"]

            similarity = response2.metadata.get("cache_similarity")
            assert similarity >= 0.85  # Medium similarity threshold

    @pytest.mark.asyncio
    async def test_no_semantic_match_below_threshold(self, speculative_processor):
        """Test that dissimilar queries don't match."""
        # First query
        query1 = "What is machine learning?"
        response1 = await speculative_processor.process(
            query=query1, top_k=5, enable_cache=True
        )

        # Completely different query
        query2 = "How to cook pasta?"
        response2 = await speculative_processor.process(
            query=query2, top_k=5, enable_cache=True
        )

        # Should not be a cache hit
        assert response2.cache_hit is False
        assert "cache_match_type" not in response2.metadata


class TestCacheMetadataInStreamingResponse:
    """Test that cache metadata appears in streaming responses."""

    @pytest.mark.asyncio
    async def test_cache_metadata_in_response_chunk(self, speculative_processor):
        """Test that ResponseChunk includes cache metadata."""
        from services.hybrid_query_router import HybridQueryRouter
        from services.response_coordinator import ResponseCoordinator
        from agents.aggregator import AggregatorAgent
        from models.hybrid import QueryMode

        # Create mock components
        mock_agentic = None  # Not needed for this test
        mock_coordinator = None

        router = HybridQueryRouter(
            speculative_processor=speculative_processor,
            agentic_processor=mock_agentic,
            response_coordinator=mock_coordinator,
        )

        query = "What is AI?"

        # First request - cache miss
        chunks1 = []
        async for chunk in router.process_query(
            query=query, mode=QueryMode.FAST, enable_cache=True
        ):
            chunks1.append(chunk)

        # Check first response has no cache metadata
        final_chunk1 = chunks1[-1]
        assert final_chunk1.metadata.get("cache_hit") is False

        # Second request - cache hit
        chunks2 = []
        async for chunk in router.process_query(
            query=query, mode=QueryMode.FAST, enable_cache=True
        ):
            chunks2.append(chunk)

        # Check second response has cache metadata
        final_chunk2 = chunks2[-1]
        assert final_chunk2.metadata.get("cache_hit") is True
        assert "cache_match_type" in final_chunk2.metadata
        assert "cache_similarity" in final_chunk2.metadata


class TestCacheMetadataStatistics:
    """Test cache statistics and analytics."""

    @pytest.mark.asyncio
    async def test_semantic_cache_stats(self, semantic_cache):
        """Test semantic cache statistics."""
        # Perform some cache operations
        query1 = "What is machine learning?"
        response1 = {"response": "ML is...", "confidence": 0.9}

        await semantic_cache.set(query1, response1, confidence=0.9)

        # Cache hit
        result = await semantic_cache.get(query1)
        assert result is not None

        # Cache miss
        result = await semantic_cache.get("Completely different query")
        assert result is None

        # Get statistics
        stats = semantic_cache.get_stats()

        assert stats["total_queries"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["cache_size"] == 1

    @pytest.mark.asyncio
    async def test_popular_queries_tracking(self, semantic_cache):
        """Test tracking of popular queries."""
        # Add and access queries multiple times
        queries = [
            ("What is AI?", {"response": "AI is...", "confidence": 0.9}),
            ("What is ML?", {"response": "ML is...", "confidence": 0.85}),
            ("What is DL?", {"response": "DL is...", "confidence": 0.88}),
        ]

        for query, response in queries:
            await semantic_cache.set(query, response, confidence=response["confidence"])

        # Access first query multiple times
        for _ in range(5):
            await semantic_cache.get("What is AI?")

        # Access second query twice
        for _ in range(2):
            await semantic_cache.get("What is ML?")

        # Get popular queries
        popular = semantic_cache.get_popular_queries(top_n=3)

        assert len(popular) == 3
        # Most popular should be first
        assert popular[0][0] == "What is AI?"
        assert popular[0][1] == 5  # Access count


class TestCacheDisabled:
    """Test behavior when caching is disabled."""

    @pytest.mark.asyncio
    async def test_no_cache_metadata_when_disabled(self, speculative_processor):
        """Test that cache metadata is not included when caching is disabled."""
        query = "What is machine learning?"

        # First request with cache disabled
        response1 = await speculative_processor.process(
            query=query, top_k=5, enable_cache=False
        )

        assert response1.cache_hit is False

        # Second request with cache disabled
        response2 = await speculative_processor.process(
            query=query, top_k=5, enable_cache=False
        )

        # Should not be cached
        assert response2.cache_hit is False
        assert "cache_match_type" not in response2.metadata

        # Processing times should be similar (both doing full processing)
        assert abs(response1.processing_time - response2.processing_time) < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
