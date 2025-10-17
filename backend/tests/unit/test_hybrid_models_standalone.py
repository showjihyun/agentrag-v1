"""Standalone unit tests for hybrid system models (no conftest dependencies)."""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.models.hybrid import (
    QueryMode,
    ResponseType,
    PathSource,
    ResponseChunk,
    HybridQueryRequest,
    HybridQueryResponse,
    SpeculativeResponse,
)
from backend.models.query import SearchResult


def test_query_mode_enum():
    """Test QueryMode enum values."""
    assert QueryMode.FAST.value == "fast"
    assert QueryMode.BALANCED.value == "balanced"
    assert QueryMode.DEEP.value == "deep"
    print("✓ QueryMode enum test passed")


def test_response_type_enum():
    """Test ResponseType enum values."""
    assert ResponseType.PRELIMINARY.value == "preliminary"
    assert ResponseType.REFINEMENT.value == "refinement"
    assert ResponseType.FINAL.value == "final"
    print("✓ ResponseType enum test passed")


def test_path_source_enum():
    """Test PathSource enum values."""
    assert PathSource.SPECULATIVE.value == "speculative"
    assert PathSource.AGENTIC.value == "agentic"
    assert PathSource.HYBRID.value == "hybrid"
    print("✓ PathSource enum test passed")


def test_response_chunk_creation():
    """Test creating ResponseChunk instances."""
    chunk = ResponseChunk(
        chunk_id="chunk_001",
        type=ResponseType.PRELIMINARY,
        content="Initial response",
        path_source=PathSource.SPECULATIVE,
        confidence_score=0.75,
    )

    assert chunk.chunk_id == "chunk_001"
    assert chunk.type == ResponseType.PRELIMINARY
    assert chunk.content == "Initial response"
    assert chunk.path_source == PathSource.SPECULATIVE
    assert chunk.confidence_score == 0.75
    assert chunk.sources == []
    assert chunk.reasoning_steps == []
    assert chunk.metadata == {}
    print("✓ ResponseChunk creation test passed")


def test_hybrid_query_request_defaults():
    """Test HybridQueryRequest with default values."""
    request = HybridQueryRequest(query="What is machine learning?")

    assert request.query == "What is machine learning?"
    assert request.mode == QueryMode.BALANCED
    assert request.enable_cache is True
    assert request.speculative_timeout == 2.0
    assert request.agentic_timeout == 15.0
    assert request.stream is True
    assert request.top_k == 10
    print("✓ HybridQueryRequest defaults test passed")


def test_hybrid_query_request_custom():
    """Test HybridQueryRequest with custom values."""
    request = HybridQueryRequest(
        query="Test query",
        session_id="session_123",
        mode=QueryMode.FAST,
        enable_cache=False,
        speculative_timeout=1.5,
        agentic_timeout=20.0,
        top_k=5,
    )

    assert request.query == "Test query"
    assert request.session_id == "session_123"
    assert request.mode == QueryMode.FAST
    assert request.enable_cache is False
    assert request.speculative_timeout == 1.5
    assert request.agentic_timeout == 20.0
    assert request.top_k == 5
    print("✓ HybridQueryRequest custom values test passed")


def test_hybrid_query_response():
    """Test HybridQueryResponse creation."""
    response = HybridQueryResponse(
        query_id="query_123",
        query="What is ML?",
        mode=QueryMode.BALANCED,
        response="Machine learning is...",
        confidence_score=0.88,
        path_used=PathSource.HYBRID,
        speculative_time=1.8,
        agentic_time=8.5,
        total_time=8.5,
    )

    assert response.query_id == "query_123"
    assert response.query == "What is ML?"
    assert response.mode == QueryMode.BALANCED
    assert response.response == "Machine learning is..."
    assert response.confidence_score == 0.88
    assert response.path_used == PathSource.HYBRID
    assert response.speculative_time == 1.8
    assert response.agentic_time == 8.5
    assert response.total_time == 8.5
    assert response.cache_hit is False
    print("✓ HybridQueryResponse test passed")


def test_speculative_response():
    """Test SpeculativeResponse creation."""
    response = SpeculativeResponse(
        response="Quick answer",
        confidence_score=0.75,
        processing_time=1.5,
        cache_hit=True,
        metadata={"cache_key": "query_hash_123"},
    )

    assert response.response == "Quick answer"
    assert response.confidence_score == 0.75
    assert response.processing_time == 1.5
    assert response.cache_hit is True
    assert response.metadata["cache_key"] == "query_hash_123"
    assert response.sources == []
    print("✓ SpeculativeResponse test passed")


def test_confidence_score_bounds():
    """Test confidence score validation (0-1 range)."""
    # Valid scores
    chunk1 = ResponseChunk(
        chunk_id="chunk_1",
        type=ResponseType.FINAL,
        content="Test",
        path_source=PathSource.HYBRID,
        confidence_score=0.0,
    )
    assert chunk1.confidence_score == 0.0

    chunk2 = ResponseChunk(
        chunk_id="chunk_2",
        type=ResponseType.FINAL,
        content="Test",
        path_source=PathSource.HYBRID,
        confidence_score=1.0,
    )
    assert chunk2.confidence_score == 1.0

    chunk3 = ResponseChunk(
        chunk_id="chunk_3",
        type=ResponseType.FINAL,
        content="Test",
        path_source=PathSource.HYBRID,
        confidence_score=0.5,
    )
    assert chunk3.confidence_score == 0.5

    print("✓ Confidence score bounds test passed")


def test_response_chunk_with_sources():
    """Test ResponseChunk with SearchResult sources."""
    source = SearchResult(
        chunk_id="chunk_1",
        document_id="doc_1",
        document_name="test.pdf",
        text="Test content",
        score=0.9,
    )

    chunk = ResponseChunk(
        chunk_id="chunk_002",
        type=ResponseType.REFINEMENT,
        content="Refined response",
        path_source=PathSource.AGENTIC,
        confidence_score=0.92,
        sources=[source],
    )

    assert len(chunk.sources) == 1
    assert chunk.sources[0].document_name == "test.pdf"
    assert chunk.sources[0].score == 0.9
    print("✓ ResponseChunk with sources test passed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Hybrid Models Tests")
    print("=" * 60 + "\n")

    try:
        test_query_mode_enum()
        test_response_type_enum()
        test_path_source_enum()
        test_response_chunk_creation()
        test_hybrid_query_request_defaults()
        test_hybrid_query_request_custom()
        test_hybrid_query_response()
        test_speculative_response()
        test_confidence_score_bounds()
        test_response_chunk_with_sources()

        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        sys.exit(1)
