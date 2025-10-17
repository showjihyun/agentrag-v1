"""
Standalone unit tests for SpeculativeProcessor (no conftest dependency).

Tests cover:
- Fast vector search with various query types
- Confidence score calculation accuracy
- Cache hit/miss scenarios
- Timeout and error handling

Requirements: 2.1, 2.2, 2.3, 2.6, 5.1
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, MagicMock

# Direct imports
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


# Test confidence scoring (no async needed)
def test_confidence_with_high_similarity():
    """Test confidence score with high similarity results."""
    # Create processor with minimal mocks
    embedding_service = Mock()
    milvus_manager = Mock()
    llm_manager = Mock()
    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

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
    assert 0.8 <= confidence <= 1.0, f"Expected high confidence, got {confidence}"
    print(f"✓ High similarity confidence: {confidence:.3f}")


def test_confidence_with_low_similarity():
    """Test confidence score with low similarity results."""
    embedding_service = Mock()
    milvus_manager = Mock()
    llm_manager = Mock()
    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

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

    confidence = processor._calculate_confidence_score(results, cache_hit=False)

    assert 0.2 <= confidence <= 0.6, f"Expected low confidence, got {confidence}"
    print(f"✓ Low similarity confidence: {confidence:.3f}")


def test_confidence_with_no_results():
    """Test confidence score with no results."""
    embedding_service = Mock()
    milvus_manager = Mock()
    llm_manager = Mock()
    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

    confidence = processor._calculate_confidence_score([], cache_hit=False)

    assert confidence == 0.1, f"Expected 0.1 confidence, got {confidence}"
    print(f"✓ No results confidence: {confidence:.3f}")


def test_confidence_cache_hit_boost():
    """Test that cache hits get a confidence boost."""
    embedding_service = Mock()
    milvus_manager = Mock()
    llm_manager = Mock()
    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

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

    confidence_no_cache = processor._calculate_confidence_score(
        results, cache_hit=False
    )
    confidence_with_cache = processor._calculate_confidence_score(
        results, cache_hit=True
    )

    assert (
        confidence_with_cache > confidence_no_cache
    ), f"Cache hit should boost confidence: {confidence_no_cache} -> {confidence_with_cache}"
    print(f"✓ Cache boost: {confidence_no_cache:.3f} -> {confidence_with_cache:.3f}")


def test_cache_key_generation():
    """Test cache key generation is consistent."""
    embedding_service = Mock()
    milvus_manager = Mock()
    llm_manager = Mock()
    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

    key1 = processor._generate_cache_key("test query", 5)
    key2 = processor._generate_cache_key("test query", 5)
    key3 = processor._generate_cache_key("different query", 5)

    assert key1 == key2, "Same query should produce same key"
    assert key1 != key3, "Different query should produce different key"
    assert key1.startswith("speculative:"), "Key should have correct prefix"
    print(f"✓ Cache key generation: {key1}")


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss scenario."""
    embedding_service = Mock()
    milvus_manager = Mock()
    llm_manager = Mock()
    redis_client = AsyncMock()
    redis_client.get.return_value = None

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

    result = await processor._check_cache("test_key")

    assert result is None, "Should return None on cache miss"
    redis_client.get.assert_called_once_with("test_key")
    print("✓ Cache miss handled correctly")


@pytest.mark.asyncio
async def test_cache_hit():
    """Test cache hit scenario."""
    embedding_service = Mock()
    milvus_manager = Mock()
    llm_manager = Mock()
    redis_client = AsyncMock()

    # Setup cached response
    cached_response = SpeculativeResponse(
        response="Cached answer",
        confidence_score=0.85,
        sources=[],
        cache_hit=False,
        processing_time=1.5,
        metadata={},
    )

    cached_json = json.dumps(cached_response.model_dump(), default=str)
    redis_client.get.return_value = cached_json

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

    result = await processor._check_cache("test_key")

    assert result is not None, "Should return cached response"
    assert result.response == "Cached answer"
    assert result.cache_hit is True, "Cache hit flag should be updated"
    print("✓ Cache hit handled correctly")


@pytest.mark.asyncio
async def test_fast_vector_search_success():
    """Test successful fast vector search."""
    embedding_service = Mock()
    embedding_service.embed_text = Mock(return_value=[0.1] * 384)

    milvus_manager = Mock()
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
    milvus_manager.search = AsyncMock(return_value=mock_results)

    llm_manager = Mock()
    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

    results, search_time = await processor._fast_vector_search(
        query="What is machine learning?", top_k=5, timeout=1.0
    )

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert results[0].score == 0.92
    assert search_time < 1.0
    print(f"✓ Fast vector search: {len(results)} results in {search_time:.3f}s")


@pytest.mark.asyncio
async def test_fast_vector_search_timeout():
    """Test vector search timeout handling."""
    embedding_service = Mock()
    embedding_service.embed_text = Mock(return_value=[0.1] * 384)

    milvus_manager = Mock()

    # Simulate slow search
    async def slow_search(*args, **kwargs):
        await asyncio.sleep(2.0)
        return []

    milvus_manager.search = slow_search

    llm_manager = Mock()
    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

    results, search_time = await processor._fast_vector_search(
        query="test query", top_k=5, timeout=0.5
    )

    assert len(results) == 0, "Timeout should return empty results"
    assert search_time >= 0.5, f"Search time should be at least timeout: {search_time}"
    print(f"✓ Vector search timeout handled: {search_time:.3f}s")


@pytest.mark.asyncio
async def test_fast_llm_generation_success():
    """Test successful LLM generation."""
    embedding_service = Mock()
    milvus_manager = Mock()

    llm_manager = Mock()
    llm_manager.generate = AsyncMock(return_value="Machine learning is a field of AI.")

    redis_client = AsyncMock()

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

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

    response, gen_time = await processor._fast_llm_generation(
        query="What is machine learning?", search_results=results, timeout=1.5
    )

    assert len(response) > 0, "Should generate a response"
    assert "Machine learning" in response
    assert gen_time < 1.5

    # Verify generation parameters
    call_kwargs = llm_manager.generate.call_args[1]
    assert call_kwargs["temperature"] == 0.3, "Should use low temperature"
    assert call_kwargs["max_tokens"] == 150, "Should use short max_tokens"
    print(f"✓ Fast LLM generation: {len(response)} chars in {gen_time:.3f}s")


@pytest.mark.asyncio
async def test_process_with_no_results():
    """Test processing when no documents are found."""
    embedding_service = Mock()
    embedding_service.embed_text = Mock(return_value=[0.1] * 384)

    milvus_manager = Mock()
    milvus_manager.search = AsyncMock(return_value=[])

    llm_manager = Mock()
    redis_client = AsyncMock()
    redis_client.get.return_value = None

    processor = SpeculativeProcessor(
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
        llm_manager=llm_manager,
        redis_client=redis_client,
    )

    result = await processor.process(query="obscure query", top_k=5, enable_cache=True)

    assert "No relevant documents found" in result.response
    assert result.confidence_score == 0.1
    assert len(result.sources) == 0
    print(f"✓ No results handling: confidence={result.confidence_score}")


if __name__ == "__main__":
    # Run tests manually
    print("\n" + "=" * 60)
    print("Running SpeculativeProcessor Tests")
    print("=" * 60 + "\n")

    # Sync tests
    print("Confidence Scoring Tests:")
    test_confidence_with_high_similarity()
    test_confidence_with_low_similarity()
    test_confidence_with_no_results()
    test_confidence_cache_hit_boost()

    print("\nCache Key Tests:")
    test_cache_key_generation()

    # Async tests
    print("\nAsync Tests:")
    asyncio.run(test_cache_miss())
    asyncio.run(test_cache_hit())
    asyncio.run(test_fast_vector_search_success())
    asyncio.run(test_fast_vector_search_timeout())
    asyncio.run(test_fast_llm_generation_success())
    asyncio.run(test_process_with_no_results())

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
