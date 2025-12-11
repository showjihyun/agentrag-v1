"""
Integration tests for hybrid search system.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from backend.services.hybrid_search import HybridSearchService as HybridSearchManager
from backend.services.search_cache import SearchCacheManager
from backend.services.query_expansion import QueryExpansionService
from backend.services.reranker import RerankerService


@pytest.fixture
def mock_milvus():
    """Mock Milvus manager."""
    milvus_mock = Mock()
    milvus_mock.search = AsyncMock(return_value=[])
    milvus_mock.dimension = 768
    return milvus_mock


@pytest.fixture
def mock_embedding():
    """Mock embedding service."""
    embedding_mock = Mock()
    embedding_mock.embed_text = Mock(return_value=[0.1] * 768)
    embedding_mock.embed_batch = Mock(return_value=[[0.1] * 768])
    embedding_mock.dimension = 768
    return embedding_mock


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock()
    redis_mock.setex = Mock()
    redis_mock.incr = Mock(return_value=1)
    redis_mock.zincrby = Mock(return_value=1)
    return redis_mock


@pytest.fixture
def mock_llm():
    """Mock LLM manager."""
    llm_mock = Mock()
    llm_mock.generate = AsyncMock(return_value="Test response")
    return llm_mock


class TestHybridIntegration:
    """Test integration of hybrid search components."""

    @pytest.mark.asyncio
    async def test_hybrid_search_with_cache(
        self, mock_milvus, mock_embedding, mock_redis
    ):
        """Test hybrid search with caching."""
        # Setup
        hybrid_search = HybridSearchManager(
            milvus_manager=mock_milvus, embedding_service=mock_embedding
        )

        cache_manager = SearchCacheManager(redis_client=mock_redis, l1_ttl=3600)

        # Build BM25 index
        documents = [
            {
                "id": "1",
                "text": "인공지능은 컴퓨터가 인간의 지능을 모방하는 기술입니다.",
                "document_id": "doc1",
                "document_name": "AI.txt",
                "chunk_index": 0,
            }
        ]
        hybrid_search.build_bm25_index(documents)

        # Perform search
        results = await hybrid_search.hybrid_search(query="인공지능이란?", top_k=5)

        # Cache results
        await cache_manager.cache_results(
            query="인공지능이란?",
            top_k=5,
            filters=None,
            search_mode="hybrid",
            results=results,
        )

        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_query_expansion_with_reranking(self, mock_llm, mock_embedding):
        """Test query expansion with reranking."""
        # Setup
        query_expansion = QueryExpansionService(
            llm_manager=mock_llm, embedding_service=mock_embedding
        )

        reranker = RerankerService(use_cross_encoder=False)

        # Expand query
        expanded_queries = await query_expansion.hyde_expansion("AI란?")

        assert len(expanded_queries) >= 1

        # Rerank results
        sample_results = [
            {"id": "1", "text": "AI is great", "score": 0.8},
            {"id": "2", "text": "ML is cool", "score": 0.9},
        ]

        reranked = reranker.rerank(
            query="AI란?", results=sample_results, top_k=2, method="mmr"
        )

        assert len(reranked) == 2

    @pytest.mark.asyncio
    async def test_full_pipeline(
        self, mock_milvus, mock_embedding, mock_redis, mock_llm
    ):
        """Test full search pipeline."""
        # Setup all components
        hybrid_search = HybridSearchManager(
            milvus_manager=mock_milvus, embedding_service=mock_embedding
        )

        cache_manager = SearchCacheManager(redis_client=mock_redis)

        query_expansion = QueryExpansionService(
            llm_manager=mock_llm, embedding_service=mock_embedding
        )

        reranker = RerankerService(use_cross_encoder=False)

        # Build index
        documents = [
            {
                "id": "1",
                "text": "인공지능 기술",
                "document_id": "doc1",
                "document_name": "AI.txt",
                "chunk_index": 0,
            }
        ]
        hybrid_search.build_bm25_index(documents)

        # 1. Check cache (miss)
        cached = await cache_manager.get_cached_results(query="AI", top_k=5)
        assert cached is None

        # 2. Expand query
        queries = await query_expansion.hyde_expansion("AI")
        assert len(queries) >= 1

        # 3. Search
        results = await hybrid_search.hybrid_search(query=queries[0], top_k=5)

        # 4. Rerank
        if results:
            reranked = reranker.rerank(query="AI", results=results, top_k=5)
            results = reranked

        # 5. Cache results
        await cache_manager.cache_results(
            query="AI", top_k=5, filters=None, search_mode="hybrid", results=results
        )

        assert True  # Pipeline completed successfully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
