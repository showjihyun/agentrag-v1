"""
Unit tests for SpeculativeProcessor.

Tests cover:
- Fast vector search with various query types
- Confidence score calculation accuracy
- Cache hit/miss scenarios
- Timeout and error handling

Requirements: 2.1, 2.2, 2.3, 2.6, 5.1
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.milvus import SearchResult
from backend.models.hybrid import SpeculativeResponse
from backend.models.query import SearchResult as QuerySearchResult


@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService."""
    service = Mock()
    service.embed_text = Mock(return_value=[0.1] * 384)
    return service


@pytest.fixture
def mock_milvus_manager():
    """Mock MilvusManager."""
    manager = Mock()
    manager.search = AsyncMock()
    return manager


@pytest.fixture
def mock_llm_manager():
    """Mock LLMManager."""
    manager = Mock()
    manager.generate = AsyncMock()
    return manager


@pytest.fixture
async def mock_redis_client():
    """Mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock()
    client.zadd = AsyncMock()
    client.zcard = AsyncMock(return_value=0)
    client.zrange = AsyncMock(return_value=[])
    client.delete = AsyncMock()
    client.zrem = AsyncMock()
    return client


@pytest.fixture
async def processor(
    mock_embedding_service, mock_milvus_manager, mock_llm_manager, mock_redis_client
):
    """Create SpeculativeProcessor instance with mocks."""
    return SpeculativeProcessor(
        embedding_service=mock_embedding_service,
        milvus_manager=mock_milvus_manager,
        llm_manager=mock_llm_manager,
        redis_client=mock_redis_client,
        cache_ttl=3600,
        max_cache_size=100,
    )


class TestCacheOperations:
    """Test caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_miss(self, processor, mock_redis_client):
        """Test cache miss scenario."""
        # Setup
        mock_redis_client.get.return_value = None

        # Execute
        result = await processor._check_cache("test_key")

        # Verify
        assert result is None
        mock_redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_hit(self, processor, mock_redis_client):
        """Test cache hit scenario."""
        # Setup - create a cached response
        cached_response = SpeculativeResponse(
            response="Cached answer",
            confidence_score=0.85,
            sources=[],
            cache_hit=False,
            processing_time=1.5,
            metadata={},
        )

        cached_json = json.dumps(cached_response.model_dump(), default=str)
        mock_redis_client.get.return_value = cached_json

        # Execute
        result = await processor._check_cache("test_key")

        # Verify
        assert result is not None
        assert result.response == "Cached answer"
        assert result.cache_hit is True  # Should be updated to True
        assert result.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_store_in_cache(self, processor, mock_redis_client):
        """Test storing response in cache."""
        # Setup
        response = SpeculativeResponse(
            response="Test answer",
            confidence_score=0.75,
            sources=[],
            cache_hit=False,
            processing_time=1.2,
            metadata={},
        )

        # Execute
        await processor._store_in_cache("test_key", response)

        # Verify
        mock_redis_client.setex.assert_called_once()
        args = mock_redis_client.setex.call_args[0]
        assert args[0] == "test_key"
        assert args[1] == 3600  # TTL

        # Verify LRU tracking
        mock_redis_client.zadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self, processor, mock_redis_client):
        """Test LRU eviction when cache is full."""
        # Setup - cache is at max size
        mock_redis_client.zcard.return_value = 100
        mock_redis_client.zrange.return_value = ["old_key_1", "old_key_2", "old_key_3"]

        # Execute
        await processor._enforce_cache_size()

        # Verify eviction occurred
        mock_redis_client.delete.assert_called_once()
        mock_redis_client.zrem.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, processor):
        """Test cache key generation is consistent."""
        # Execute
        key1 = processor._generate_cache_key("test query", 5)
        key2 = processor._generate_cache_key("test query", 5)
        key3 = processor._generate_cache_key("different query", 5)

        # Verify
        assert key1 == key2  # Same query produces same key
        assert key1 != key3  # Different query produces different key
        assert key1.startswith("speculative:")


class TestVectorSearch:
    """Test fast vector search functionality."""

    @pytest.mark.asyncio
    async def test_fast_vector_search_success(
        self, processor, mock_milvus_manager, mock_embedding_service
    ):
        """Test successful fast vector search."""
        # Setup
        mock_results = [
            SearchResult(
                id="chunk_1",
                document_id="doc_1",
                text="Machine learning is a subset of AI.",
                score=0.92,
                document_name="ml_basics.pdf",
                chunk_index=0,
                metadata={},
            ),
            SearchResult(
                id="chunk_2",
                document_id="doc_1",
                text="Deep learning uses neural networks.",
                score=0.88,
                document_name="ml_basics.pdf",
                chunk_index=1,
                metadata={},
            ),
        ]
        mock_milvus_manager.search.return_value = mock_results

        # Execute
        results, search_time = await processor._fast_vector_search(
            query="What is machine learning?", top_k=5, timeout=1.0
        )

        # Verify
        assert len(results) == 2
        assert results[0].score == 0.92
        assert search_time < 1.0
        mock_embedding_service.embed_text.assert_called_once()
        mock_milvus_manager.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_fast_vector_search_timeout(self, processor, mock_milvus_manager):
        """Test vector search timeout handling."""

        # Setup - simulate slow search
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(2.0)
            return []

        mock_milvus_manager.search = slow_search

        # Execute
        results, search_time = await processor._fast_vector_search(
            query="test query", top_k=5, timeout=0.5
        )

        # Verify
        assert len(results) == 0  # Timeout returns empty results
        assert search_time >= 0.5

    @pytest.mark.asyncio
    async def test_fast_vector_search_error(self, processor, mock_milvus_manager):
        """Test vector search error handling."""
        # Setup
        mock_milvus_manager.search.side_effect = Exception("Search failed")

        # Execute
        results, search_time = await processor._fast_vector_search(
            query="test query", top_k=5, timeout=1.0
        )

        # Verify
        assert len(results) == 0  # Error returns empty results
        assert search_time >= 0


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def test_confidence_with_high_similarity(self, processor):
        """Test confidence score with high similarity results."""
        # Setup
        results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.95,
                document_name="doc",
                chunk_index=0,
                metadata={},
            ),
            SearchResult(
                id="2",
                document_id="d1",
                text="text",
                score=0.92,
                document_name="doc",
                chunk_index=1,
                metadata={},
            ),
            SearchResult(
                id="3",
                document_id="d1",
                text="text",
                score=0.90,
                document_name="doc",
                chunk_index=2,
                metadata={},
            ),
        ]

        # Execute
        confidence = processor._calculate_confidence_score(results, cache_hit=False)

        # Verify
        assert 0.8 <= confidence <= 1.0  # High similarity should give high confidence

    def test_confidence_with_low_similarity(self, processor):
        """Test confidence score with low similarity results."""
        # Setup
        results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.45,
                document_name="doc",
                chunk_index=0,
                metadata={},
            ),
            SearchResult(
                id="2",
                document_id="d1",
                text="text",
                score=0.40,
                document_name="doc",
                chunk_index=1,
                metadata={},
            ),
        ]

        # Execute
        confidence = processor._calculate_confidence_score(results, cache_hit=False)

        # Verify
        assert 0.2 <= confidence <= 0.6  # Low similarity should give lower confidence

    def test_confidence_with_no_results(self, processor):
        """Test confidence score with no results."""
        # Execute
        confidence = processor._calculate_confidence_score([], cache_hit=False)

        # Verify
        assert confidence == 0.1  # Minimum confidence

    def test_confidence_cache_hit_boost(self, processor):
        """Test that cache hits get a confidence boost."""
        # Setup
        results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.80,
                document_name="doc",
                chunk_index=0,
                metadata={},
            )
        ]

        # Execute
        confidence_no_cache = processor._calculate_confidence_score(
            results, cache_hit=False
        )
        confidence_with_cache = processor._calculate_confidence_score(
            results, cache_hit=True
        )

        # Verify
        assert confidence_with_cache > confidence_no_cache

    def test_confidence_document_count_factor(self, processor):
        """Test that more documents increase confidence."""
        # Setup - same similarity, different counts
        single_result = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.80,
                document_name="doc",
                chunk_index=0,
                metadata={},
            )
        ]

        multiple_results = [
            SearchResult(
                id=str(i),
                document_id="d1",
                text="text",
                score=0.80,
                document_name="doc",
                chunk_index=i,
                metadata={},
            )
            for i in range(5)
        ]

        # Execute
        confidence_single = processor._calculate_confidence_score(
            single_result, cache_hit=False
        )
        confidence_multiple = processor._calculate_confidence_score(
            multiple_results, cache_hit=False
        )

        # Verify
        assert confidence_multiple > confidence_single


class TestLLMGeneration:
    """Test fast LLM generation."""

    @pytest.mark.asyncio
    async def test_fast_llm_generation_success(self, processor, mock_llm_manager):
        """Test successful LLM generation."""
        # Setup
        mock_llm_manager.generate.return_value = "Machine learning is a field of AI."

        results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="Machine learning is a subset of artificial intelligence.",
                score=0.90,
                document_name="ml.pdf",
                chunk_index=0,
                metadata={},
            )
        ]

        # Execute
        response, gen_time = await processor._fast_llm_generation(
            query="What is machine learning?", search_results=results, timeout=1.5
        )

        # Verify
        assert len(response) > 0
        assert "Machine learning" in response
        assert gen_time < 1.5
        mock_llm_manager.generate.assert_called_once()

        # Verify generation parameters
        call_kwargs = mock_llm_manager.generate.call_args[1]
        assert call_kwargs["temperature"] == 0.3  # Low temperature
        assert call_kwargs["max_tokens"] == 150  # Short response

    @pytest.mark.asyncio
    async def test_fast_llm_generation_timeout(self, processor, mock_llm_manager):
        """Test LLM generation timeout handling."""

        # Setup - simulate slow generation
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(3.0)
            return "Response"

        mock_llm_manager.generate = slow_generate

        results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.90,
                document_name="doc",
                chunk_index=0,
                metadata={},
            )
        ]

        # Execute
        response, gen_time = await processor._fast_llm_generation(
            query="test", search_results=results, timeout=0.5
        )

        # Verify
        assert "Searching for more information" in response
        assert gen_time >= 0.5

    @pytest.mark.asyncio
    async def test_fast_llm_generation_error(self, processor, mock_llm_manager):
        """Test LLM generation error handling."""
        # Setup
        mock_llm_manager.generate.side_effect = Exception("LLM error")

        results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.90,
                document_name="doc",
                chunk_index=0,
                metadata={},
            )
        ]

        # Execute
        response, gen_time = await processor._fast_llm_generation(
            query="test", search_results=results, timeout=1.5
        )

        # Verify
        assert "Unable to generate response" in response


class TestEndToEndProcessing:
    """Test complete speculative processing workflow."""

    @pytest.mark.asyncio
    async def test_process_with_cache_hit(self, processor, mock_redis_client):
        """Test processing with cache hit."""
        # Setup - cached response
        cached_response = SpeculativeResponse(
            response="Cached answer about ML",
            confidence_score=0.85,
            sources=[],
            cache_hit=False,
            processing_time=1.5,
            metadata={},
        )

        cached_json = json.dumps(cached_response.model_dump(), default=str)
        mock_redis_client.get.return_value = cached_json

        # Execute
        result = await processor.process(
            query="What is machine learning?", top_k=5, enable_cache=True
        )

        # Verify
        assert result.cache_hit is True
        assert result.response == "Cached answer about ML"
        assert result.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_process_with_cache_miss(
        self, processor, mock_milvus_manager, mock_llm_manager, mock_redis_client
    ):
        """Test processing with cache miss."""
        # Setup
        mock_redis_client.get.return_value = None

        mock_results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="Machine learning is AI.",
                score=0.90,
                document_name="ml.pdf",
                chunk_index=0,
                metadata={},
            )
        ]
        mock_milvus_manager.search.return_value = mock_results
        mock_llm_manager.generate.return_value = "ML is a field of AI."

        # Execute
        result = await processor.process(
            query="What is machine learning?", top_k=5, enable_cache=True
        )

        # Verify
        assert result.cache_hit is False
        assert len(result.response) > 0
        assert result.confidence_score > 0
        assert len(result.sources) == 1
        assert result.processing_time > 0

        # Verify caching occurred
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_without_cache(
        self, processor, mock_milvus_manager, mock_llm_manager, mock_redis_client
    ):
        """Test processing with caching disabled."""
        # Setup
        mock_results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.90,
                document_name="doc",
                chunk_index=0,
                metadata={},
            )
        ]
        mock_milvus_manager.search.return_value = mock_results
        mock_llm_manager.generate.return_value = "Response"

        # Execute
        result = await processor.process(
            query="test query", top_k=5, enable_cache=False
        )

        # Verify
        assert result.cache_hit is False
        mock_redis_client.get.assert_not_called()
        mock_redis_client.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_with_no_results(
        self, processor, mock_milvus_manager, mock_redis_client
    ):
        """Test processing when no documents are found."""
        # Setup
        mock_redis_client.get.return_value = None
        mock_milvus_manager.search.return_value = []

        # Execute
        result = await processor.process(
            query="obscure query", top_k=5, enable_cache=True
        )

        # Verify
        assert "No relevant documents found" in result.response
        assert result.confidence_score == 0.1
        assert len(result.sources) == 0

    @pytest.mark.asyncio
    async def test_process_with_error(
        self, processor, mock_milvus_manager, mock_redis_client
    ):
        """Test processing with error fallback."""
        # Setup
        mock_redis_client.get.return_value = None
        mock_milvus_manager.search.side_effect = Exception("Database error")

        # Execute
        result = await processor.process(query="test query", top_k=5, enable_cache=True)

        # Verify - should return fallback response
        assert "Processing your query" in result.response
        assert result.confidence_score == 0.1
        assert "error" in result.metadata

    @pytest.mark.asyncio
    async def test_process_timing_constraint(
        self, processor, mock_milvus_manager, mock_llm_manager, mock_redis_client
    ):
        """Test that processing completes within time constraints."""
        # Setup
        mock_redis_client.get.return_value = None

        mock_results = [
            SearchResult(
                id="1",
                document_id="d1",
                text="text",
                score=0.90,
                document_name="doc",
                chunk_index=0,
                metadata={},
            )
        ]
        mock_milvus_manager.search.return_value = mock_results
        mock_llm_manager.generate.return_value = "Response"

        # Execute
        import time

        start = time.time()
        result = await processor.process(query="test query", top_k=5, enable_cache=True)
        elapsed = time.time() - start

        # Verify - should complete quickly (under 3 seconds for mocked operations)
        assert elapsed < 3.0
        assert result.processing_time < 3.0


class TestSearchResultConversion:
    """Test conversion between search result types."""

    def test_convert_search_results(self, processor):
        """Test converting Milvus SearchResult to QuerySearchResult."""
        # Setup
        milvus_results = [
            SearchResult(
                id="chunk_1",
                document_id="doc_1",
                text="Test text",
                score=0.92,
                document_name="test.pdf",
                chunk_index=0,
                metadata={"page": 1},
            )
        ]

        # Execute
        converted = processor._convert_search_results(milvus_results)

        # Verify
        assert len(converted) == 1
        assert isinstance(converted[0], QuerySearchResult)
        assert converted[0].chunk_id == "chunk_1"
        assert converted[0].document_id == "doc_1"
        assert converted[0].score == 0.92
        assert converted[0].metadata["page"] == 1
