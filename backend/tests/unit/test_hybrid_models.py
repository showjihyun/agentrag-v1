"""Unit tests for hybrid system models."""

import pytest
from datetime import datetime
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


class TestQueryMode:
    """Test QueryMode enum."""

    def test_query_mode_values(self):
        """Test that QueryMode has correct values."""
        assert QueryMode.FAST.value == "fast"
        assert QueryMode.BALANCED.value == "balanced"
        assert QueryMode.DEEP.value == "deep"

    def test_query_mode_from_string(self):
        """Test creating QueryMode from string."""
        assert QueryMode("fast") == QueryMode.FAST
        assert QueryMode("balanced") == QueryMode.BALANCED
        assert QueryMode("deep") == QueryMode.DEEP


class TestResponseType:
    """Test ResponseType enum."""

    def test_response_type_values(self):
        """Test that ResponseType has correct values."""
        assert ResponseType.PRELIMINARY.value == "preliminary"
        assert ResponseType.REFINEMENT.value == "refinement"
        assert ResponseType.FINAL.value == "final"


class TestPathSource:
    """Test PathSource enum."""

    def test_path_source_values(self):
        """Test that PathSource has correct values."""
        assert PathSource.SPECULATIVE.value == "speculative"
        assert PathSource.AGENTIC.value == "agentic"
        assert PathSource.HYBRID.value == "hybrid"


class TestResponseChunk:
    """Test ResponseChunk model."""

    def test_create_response_chunk(self):
        """Test creating a ResponseChunk."""
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
        assert isinstance(chunk.timestamp, datetime)
        assert chunk.metadata == {}

    def test_response_chunk_with_sources(self):
        """Test ResponseChunk with sources."""
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

    def test_confidence_score_validation(self):
        """Test that confidence score is validated."""
        # Valid scores
        chunk = ResponseChunk(
            chunk_id="chunk_003",
            type=ResponseType.FINAL,
            content="Final response",
            path_source=PathSource.HYBRID,
            confidence_score=0.0,
        )
        assert chunk.confidence_score == 0.0

        chunk = ResponseChunk(
            chunk_id="chunk_004",
            type=ResponseType.FINAL,
            content="Final response",
            path_source=PathSource.HYBRID,
            confidence_score=1.0,
        )
        assert chunk.confidence_score == 1.0

        # Invalid scores should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            ResponseChunk(
                chunk_id="chunk_005",
                type=ResponseType.FINAL,
                content="Final response",
                path_source=PathSource.HYBRID,
                confidence_score=1.5,
            )


class TestHybridQueryRequest:
    """Test HybridQueryRequest model."""

    def test_create_hybrid_query_request(self):
        """Test creating a HybridQueryRequest."""
        request = HybridQueryRequest(
            query="What is machine learning?",
            session_id="session_123",
            mode=QueryMode.BALANCED,
        )

        assert request.query == "What is machine learning?"
        assert request.session_id == "session_123"
        assert request.mode == QueryMode.BALANCED
        assert request.top_k == 10  # default
        assert request.enable_cache is True  # default
        assert request.speculative_timeout == 2.0  # default
        assert request.agentic_timeout == 15.0  # default
        assert request.stream is True  # default

    def test_hybrid_query_request_defaults(self):
        """Test that HybridQueryRequest has correct defaults."""
        request = HybridQueryRequest(query="Test query")

        assert request.mode == QueryMode.BALANCED
        assert request.enable_cache is True
        assert request.speculative_timeout == 2.0
        assert request.agentic_timeout == 15.0

    def test_hybrid_query_request_custom_values(self):
        """Test HybridQueryRequest with custom values."""
        request = HybridQueryRequest(
            query="Test query",
            mode=QueryMode.FAST,
            enable_cache=False,
            speculative_timeout=1.5,
            agentic_timeout=20.0,
            top_k=5,
        )

        assert request.mode == QueryMode.FAST
        assert request.enable_cache is False
        assert request.speculative_timeout == 1.5
        assert request.agentic_timeout == 20.0
        assert request.top_k == 5

    def test_timeout_validation(self):
        """Test that timeouts are validated."""
        # Valid timeouts
        request = HybridQueryRequest(
            query="Test", speculative_timeout=0.5, agentic_timeout=5.0
        )
        assert request.speculative_timeout == 0.5
        assert request.agentic_timeout == 5.0

        # Invalid timeouts should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            HybridQueryRequest(query="Test", speculative_timeout=0.1)  # Too low

        with pytest.raises(Exception):  # Pydantic ValidationError
            HybridQueryRequest(query="Test", agentic_timeout=100.0)  # Too high


class TestHybridQueryResponse:
    """Test HybridQueryResponse model."""

    def test_create_hybrid_query_response(self):
        """Test creating a HybridQueryResponse."""
        response = HybridQueryResponse(
            query_id="query_123",
            query="What is ML?",
            mode=QueryMode.BALANCED,
            response="Machine learning is...",
            confidence_score=0.88,
            path_used=PathSource.HYBRID,
            total_time=5.5,
        )

        assert response.query_id == "query_123"
        assert response.query == "What is ML?"
        assert response.mode == QueryMode.BALANCED
        assert response.response == "Machine learning is..."
        assert response.confidence_score == 0.88
        assert response.path_used == PathSource.HYBRID
        assert response.total_time == 5.5
        assert response.sources == []
        assert response.reasoning_steps == []
        assert response.cache_hit is False

    def test_hybrid_query_response_with_timing(self):
        """Test HybridQueryResponse with path timing."""
        response = HybridQueryResponse(
            query_id="query_124",
            query="Test",
            mode=QueryMode.BALANCED,
            response="Response",
            confidence_score=0.9,
            path_used=PathSource.HYBRID,
            speculative_time=1.8,
            agentic_time=8.5,
            total_time=8.5,
        )

        assert response.speculative_time == 1.8
        assert response.agentic_time == 8.5
        assert response.total_time == 8.5


class TestSpeculativeResponse:
    """Test SpeculativeResponse model."""

    def test_create_speculative_response(self):
        """Test creating a SpeculativeResponse."""
        response = SpeculativeResponse(
            response="Quick answer", confidence_score=0.75, processing_time=1.5
        )

        assert response.response == "Quick answer"
        assert response.confidence_score == 0.75
        assert response.processing_time == 1.5
        assert response.sources == []
        assert response.cache_hit is False
        assert response.metadata == {}

    def test_speculative_response_with_cache_hit(self):
        """Test SpeculativeResponse with cache hit."""
        response = SpeculativeResponse(
            response="Cached answer",
            confidence_score=0.85,
            cache_hit=True,
            processing_time=0.3,
            metadata={"cache_key": "query_hash_123"},
        )

        assert response.cache_hit is True
        assert response.processing_time == 0.3
        assert response.metadata["cache_key"] == "query_hash_123"
