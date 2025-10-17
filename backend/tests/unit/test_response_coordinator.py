"""
Unit tests for ResponseCoordinator.

Tests cover:
- Source deduplication with various overlap scenarios
- Response merging logic with different confidence levels
- Change detection accuracy between versions
- Streaming coordination
- Version management
"""

import pytest
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

from backend.services.response_coordinator import ResponseCoordinator, ResponseVersion
from backend.models.hybrid import (
    ResponseChunk,
    ResponseType,
    PathSource,
    SpeculativeResponse,
    QueryMode,
)
from backend.models.query import SearchResult


# Test Fixtures


@pytest.fixture
def coordinator():
    """Create a ResponseCoordinator instance."""
    return ResponseCoordinator(similarity_threshold=0.85)


@pytest.fixture
def sample_sources():
    """Create sample search results."""
    return [
        SearchResult(
            chunk_id="chunk_1",
            document_id="doc_1",
            document_name="Document 1",
            text="Machine learning is a subset of artificial intelligence.",
            score=0.95,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_2",
            document_id="doc_1",
            document_name="Document 1",
            text="Deep learning uses neural networks with multiple layers.",
            score=0.90,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_3",
            document_id="doc_2",
            document_name="Document 2",
            text="Natural language processing enables computers to understand text.",
            score=0.85,
            metadata={},
        ),
    ]


@pytest.fixture
def duplicate_sources():
    """Create sources with duplicates."""
    return [
        SearchResult(
            chunk_id="chunk_1",
            document_id="doc_1",
            document_name="Document 1",
            text="Machine learning is a subset of artificial intelligence.",
            score=0.95,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_1_dup",
            document_id="doc_1",
            document_name="Document 1",
            text="Machine learning is a subset of artificial intelligence.",  # Exact duplicate
            score=0.93,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_2",
            document_id="doc_1",
            document_name="Document 1",
            text="Machine learning is a part of artificial intelligence.",  # Near duplicate
            score=0.92,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_3",
            document_id="doc_2",
            document_name="Document 2",
            text="Deep learning is different from machine learning.",  # Unique
            score=0.88,
            metadata={},
        ),
    ]


@pytest.fixture
def speculative_response(sample_sources):
    """Create a sample speculative response."""
    return SpeculativeResponse(
        response="Machine learning is a subset of AI that enables computers to learn from data.",
        confidence_score=0.75,
        sources=sample_sources[:2],
        cache_hit=False,
        processing_time=1.5,
        metadata={"vector_search_time_ms": 120, "llm_time_ms": 1380},
    )


# Test Source Deduplication


def test_deduplicate_sources_no_duplicates(coordinator, sample_sources):
    """Test deduplication with no duplicates."""
    result = coordinator._deduplicate_sources(sample_sources)

    assert len(result) == 3
    assert all(s.chunk_id in ["chunk_1", "chunk_2", "chunk_3"] for s in result)


def test_deduplicate_sources_with_duplicates(coordinator, duplicate_sources):
    """Test deduplication with exact and near duplicates."""
    result = coordinator._deduplicate_sources(duplicate_sources)

    # Should keep highest scoring version of duplicates
    assert len(result) == 2  # chunk_1 (0.95) and chunk_3 (0.88)
    assert result[0].chunk_id == "chunk_1"
    assert result[0].score == 0.95
    assert result[1].chunk_id == "chunk_3"


def test_deduplicate_sources_empty_list(coordinator):
    """Test deduplication with empty list."""
    result = coordinator._deduplicate_sources([])
    assert result == []


def test_deduplicate_sources_preserves_highest_score(coordinator):
    """Test that deduplication keeps highest scoring duplicates."""
    sources = [
        SearchResult(
            chunk_id="chunk_1",
            document_id="doc_1",
            document_name="Doc 1",
            text="Same text content here.",
            score=0.80,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_2",
            document_id="doc_1",
            document_name="Doc 1",
            text="Same text content here.",
            score=0.95,  # Higher score
            metadata={},
        ),
    ]

    result = coordinator._deduplicate_sources(sources)

    assert len(result) == 1
    assert result[0].chunk_id == "chunk_2"
    assert result[0].score == 0.95


# Test Source Merging


def test_merge_sources_no_overlap(coordinator, sample_sources):
    """Test merging sources with no overlap."""
    spec_sources = sample_sources[:2]
    agentic_sources = sample_sources[2:]

    result = coordinator._merge_sources(spec_sources, agentic_sources)

    assert len(result) == 3
    assert all(s.chunk_id in ["chunk_1", "chunk_2", "chunk_3"] for s in result)


def test_merge_sources_with_overlap(coordinator, sample_sources):
    """Test merging sources with overlapping chunks."""
    spec_sources = sample_sources[:2]
    agentic_sources = [sample_sources[1], sample_sources[2]]  # chunk_2 overlaps

    result = coordinator._merge_sources(spec_sources, agentic_sources)

    # Should deduplicate chunk_2
    assert len(result) == 3
    chunk_ids = [s.chunk_id for s in result]
    assert chunk_ids.count("chunk_2") == 1


def test_merge_sources_empty_lists(coordinator):
    """Test merging with empty source lists."""
    result = coordinator._merge_sources([], [])
    assert result == []


# Test Response Merging


def test_merge_responses_both_present_similar_confidence(coordinator):
    """Test merging when both responses present with similar confidence."""
    spec_response = "Machine learning is a subset of AI."
    agentic_response = "Machine learning is a branch of artificial intelligence."

    result, confidence = coordinator._merge_responses(
        speculative_response=spec_response,
        agentic_response=agentic_response,
        speculative_confidence=0.75,
        agentic_confidence=0.80,
    )

    # Should prefer agentic (more thorough)
    assert result == agentic_response
    assert confidence == 0.80


def test_merge_responses_agentic_much_higher_confidence(coordinator):
    """Test merging when agentic has significantly higher confidence."""
    spec_response = "Machine learning is AI."
    agentic_response = "Machine learning is a comprehensive subset of AI."

    result, confidence = coordinator._merge_responses(
        speculative_response=spec_response,
        agentic_response=agentic_response,
        speculative_confidence=0.60,
        agentic_confidence=0.90,
    )

    assert result == agentic_response
    assert confidence == 0.90


def test_merge_responses_only_speculative(coordinator):
    """Test merging when only speculative response exists."""
    spec_response = "Machine learning is a subset of AI."

    result, confidence = coordinator._merge_responses(
        speculative_response=spec_response,
        agentic_response=None,
        speculative_confidence=0.75,
        agentic_confidence=0.0,
    )

    assert result == spec_response
    assert confidence == 0.75


def test_merge_responses_only_agentic(coordinator):
    """Test merging when only agentic response exists."""
    agentic_response = "Machine learning is a comprehensive field."

    result, confidence = coordinator._merge_responses(
        speculative_response=None,
        agentic_response=agentic_response,
        speculative_confidence=0.0,
        agentic_confidence=0.85,
    )

    assert result == agentic_response
    assert confidence == 0.85


def test_merge_responses_neither_present(coordinator):
    """Test merging when neither response exists."""
    result, confidence = coordinator._merge_responses(
        speculative_response=None,
        agentic_response=None,
        speculative_confidence=0.0,
        agentic_confidence=0.0,
    )

    assert result == "No response generated."
    assert confidence == 0.0


def test_merge_responses_very_similar_content(coordinator):
    """Test merging when responses are very similar."""
    spec_response = "Machine learning enables computers to learn from data."
    agentic_response = (
        "Machine learning enables computers to learn from data and improve."
    )

    result, confidence = coordinator._merge_responses(
        speculative_response=spec_response,
        agentic_response=agentic_response,
        speculative_confidence=0.75,
        agentic_confidence=0.80,
    )

    # Should use agentic when similar
    assert result == agentic_response
    assert confidence == 0.80


# Test Version Management


def test_store_version(coordinator, sample_sources):
    """Test storing a response version."""
    query_id = "query_123"

    version_id = coordinator.store_version(
        query_id=query_id,
        content="Test response",
        path_source=PathSource.SPECULATIVE,
        confidence_score=0.75,
        sources=sample_sources,
    )

    assert version_id.startswith("v_")
    assert query_id in coordinator.response_versions
    assert len(coordinator.response_versions[query_id]) == 1


def test_store_multiple_versions(coordinator, sample_sources):
    """Test storing multiple versions for same query."""
    query_id = "query_123"

    v1 = coordinator.store_version(
        query_id=query_id,
        content="First response",
        path_source=PathSource.SPECULATIVE,
        confidence_score=0.70,
        sources=sample_sources[:1],
    )

    v2 = coordinator.store_version(
        query_id=query_id,
        content="Second response",
        path_source=PathSource.AGENTIC,
        confidence_score=0.85,
        sources=sample_sources,
    )

    versions = coordinator.get_versions(query_id)
    assert len(versions) == 2
    assert versions[0].version_id == v1
    assert versions[1].version_id == v2


def test_get_versions_nonexistent_query(coordinator):
    """Test getting versions for non-existent query."""
    versions = coordinator.get_versions("nonexistent")
    assert versions == []


# Test Change Detection


def test_detect_changes_significant_difference(coordinator, sample_sources):
    """Test change detection with significant differences."""
    query_id = "query_123"

    v1 = coordinator.store_version(
        query_id=query_id,
        content="Machine learning is AI.",
        path_source=PathSource.SPECULATIVE,
        confidence_score=0.70,
        sources=sample_sources[:1],
    )

    v2 = coordinator.store_version(
        query_id=query_id,
        content="Machine learning is a comprehensive subset of artificial intelligence with many applications.",
        path_source=PathSource.AGENTIC,
        confidence_score=0.90,
        sources=sample_sources,
    )

    changes = coordinator.detect_changes(query_id, v1, v2)

    assert changes["content_changed"] is True
    assert changes["confidence_improved"] is True
    assert changes["confidence_delta"] == pytest.approx(0.20, abs=0.01)
    assert changes["sources_added"] == 2


def test_detect_changes_minimal_difference(coordinator, sample_sources):
    """Test change detection with minimal differences."""
    query_id = "query_123"

    v1 = coordinator.store_version(
        query_id=query_id,
        content="Machine learning is a subset of AI.",
        path_source=PathSource.SPECULATIVE,
        confidence_score=0.80,
        sources=sample_sources,
    )

    v2 = coordinator.store_version(
        query_id=query_id,
        content="Machine learning is a subset of AI.",  # Same content
        path_source=PathSource.AGENTIC,
        confidence_score=0.82,
        sources=sample_sources,
    )

    changes = coordinator.detect_changes(query_id, v1, v2)

    assert changes["content_changed"] is False
    assert changes["similarity"] > 0.95
    assert changes["sources_added"] == 0
    assert changes["sources_removed"] == 0


def test_detect_changes_version_not_found(coordinator):
    """Test change detection with non-existent version."""
    query_id = "query_123"

    changes = coordinator.detect_changes(query_id, "v_fake1", "v_fake2")

    assert "error" in changes
    assert changes["error"] == "Version not found"


# Test Streaming Coordination


@pytest.mark.asyncio
async def test_coordinate_streaming_speculative_only(coordinator, speculative_response):
    """Test streaming coordination with only speculative response."""
    query_id = "query_123"

    chunks = []
    async for chunk in coordinator.coordinate_streaming(
        query_id=query_id,
        speculative_response=speculative_response,
        agentic_generator=None,
    ):
        chunks.append(chunk)

    # Should have preliminary and final chunks
    assert len(chunks) == 2
    assert chunks[0].type == ResponseType.PRELIMINARY
    assert chunks[0].path_source == PathSource.SPECULATIVE
    assert chunks[1].type == ResponseType.FINAL
    assert chunks[1].path_source == PathSource.SPECULATIVE


@pytest.mark.asyncio
async def test_coordinate_streaming_agentic_only(coordinator, sample_sources):
    """Test streaming coordination with only agentic response."""
    query_id = "query_123"

    async def mock_agentic_generator():
        yield {
            "response": "Agentic response here",
            "confidence": 0.85,
            "sources": sample_sources,
            "reasoning_steps": [{"step": "search", "result": "found docs"}],
            "is_final": True,
        }

    chunks = []
    async for chunk in coordinator.coordinate_streaming(
        query_id=query_id,
        speculative_response=None,
        agentic_generator=mock_agentic_generator(),
    ):
        chunks.append(chunk)

    # Should have refinement and final chunks
    assert len(chunks) == 2
    assert chunks[0].type == ResponseType.REFINEMENT
    assert chunks[0].path_source == PathSource.AGENTIC
    assert chunks[1].type == ResponseType.FINAL
    assert chunks[1].path_source == PathSource.AGENTIC


@pytest.mark.asyncio
async def test_coordinate_streaming_both_paths(
    coordinator, speculative_response, sample_sources
):
    """Test streaming coordination with both paths."""
    query_id = "query_123"

    async def mock_agentic_generator():
        yield {
            "response": "Refined agentic response",
            "confidence": 0.90,
            "sources": sample_sources,
            "reasoning_steps": [{"step": "analyze", "result": "completed"}],
            "is_final": True,
        }

    chunks = []
    async for chunk in coordinator.coordinate_streaming(
        query_id=query_id,
        speculative_response=speculative_response,
        agentic_generator=mock_agentic_generator(),
    ):
        chunks.append(chunk)

    # Should have preliminary, refinement, and final chunks
    assert len(chunks) == 3
    assert chunks[0].type == ResponseType.PRELIMINARY
    assert chunks[0].path_source == PathSource.SPECULATIVE
    assert chunks[1].type == ResponseType.REFINEMENT
    assert chunks[1].path_source == PathSource.AGENTIC
    assert chunks[2].type == ResponseType.FINAL
    assert chunks[2].path_source == PathSource.HYBRID

    # Final chunk should have change detection
    assert "changes" in chunks[2].metadata
    assert chunks[2].metadata["changes"] is not None


@pytest.mark.asyncio
async def test_coordinate_streaming_multiple_refinements(
    coordinator, speculative_response, sample_sources
):
    """Test streaming with multiple agentic refinements."""
    query_id = "query_123"

    async def mock_agentic_generator():
        yield {
            "response": "First refinement",
            "confidence": 0.80,
            "sources": sample_sources[:1],
            "reasoning_steps": [{"step": "search"}],
            "is_final": False,
            "step": "searching",
            "progress": 0.3,
        }
        yield {
            "response": "Second refinement",
            "confidence": 0.85,
            "sources": sample_sources[:2],
            "reasoning_steps": [{"step": "analyze"}],
            "is_final": False,
            "step": "analyzing",
            "progress": 0.6,
        }
        yield {
            "response": "Final refinement",
            "confidence": 0.92,
            "sources": sample_sources,
            "reasoning_steps": [{"step": "synthesize"}],
            "is_final": True,
            "step": "complete",
            "progress": 1.0,
        }

    chunks = []
    async for chunk in coordinator.coordinate_streaming(
        query_id=query_id,
        speculative_response=speculative_response,
        agentic_generator=mock_agentic_generator(),
    ):
        chunks.append(chunk)

    # Should have preliminary, 3 refinements, and final
    assert len(chunks) == 5
    assert chunks[0].type == ResponseType.PRELIMINARY
    assert chunks[1].type == ResponseType.REFINEMENT
    assert chunks[2].type == ResponseType.REFINEMENT
    assert chunks[3].type == ResponseType.REFINEMENT
    assert chunks[4].type == ResponseType.FINAL


# Test Text Similarity Calculation


def test_calculate_text_similarity_identical(coordinator):
    """Test similarity calculation with identical text."""
    text1 = "Machine learning is a subset of AI."
    text2 = "Machine learning is a subset of AI."

    similarity = coordinator._calculate_text_similarity(text1, text2)
    assert similarity == 1.0


def test_calculate_text_similarity_very_different(coordinator):
    """Test similarity calculation with very different text."""
    text1 = "Machine learning is a subset of AI."
    text2 = "The weather is nice today."

    similarity = coordinator._calculate_text_similarity(text1, text2)
    assert similarity < 0.3


def test_calculate_text_similarity_similar(coordinator):
    """Test similarity calculation with similar text."""
    text1 = "Machine learning is a subset of artificial intelligence."
    text2 = "Machine learning is a part of artificial intelligence."

    similarity = coordinator._calculate_text_similarity(text1, text2)
    assert 0.7 < similarity < 1.0


# Test Hybrid Response Creation


def test_create_hybrid_response_both_paths(
    coordinator, speculative_response, sample_sources
):
    """Test creating hybrid response with both paths."""
    query_id = "query_123"
    agentic_response = {
        "response": "Comprehensive agentic response",
        "confidence": 0.90,
        "sources": sample_sources,
        "processing_time": 8.5,
        "reasoning_steps": [{"step": "search"}, {"step": "analyze"}],
    }

    result = coordinator.create_hybrid_response(
        query_id=query_id,
        query="What is machine learning?",
        mode=QueryMode.BALANCED,
        speculative_response=speculative_response,
        agentic_response=agentic_response,
        session_id="session_123",
    )

    assert result.query_id == query_id
    assert result.mode == QueryMode.BALANCED
    assert result.path_used == PathSource.HYBRID
    assert result.speculative_time == 1.5
    assert result.agentic_time == 8.5
    assert result.total_time == 8.5  # Max of both
    assert len(result.sources) > 0
    assert len(result.reasoning_steps) == 2


def test_create_hybrid_response_speculative_only(coordinator, speculative_response):
    """Test creating hybrid response with only speculative path."""
    query_id = "query_123"

    result = coordinator.create_hybrid_response(
        query_id=query_id,
        query="What is machine learning?",
        mode=QueryMode.FAST,
        speculative_response=speculative_response,
        agentic_response=None,
        session_id="session_123",
    )

    assert result.path_used == PathSource.SPECULATIVE
    assert result.speculative_time == 1.5
    assert result.agentic_time is None
    assert result.cache_hit is False


def test_create_hybrid_response_agentic_only(coordinator, sample_sources):
    """Test creating hybrid response with only agentic path."""
    query_id = "query_123"
    agentic_response = {
        "response": "Deep agentic response",
        "confidence": 0.92,
        "sources": sample_sources,
        "processing_time": 12.0,
        "reasoning_steps": [{"step": "plan"}, {"step": "execute"}],
    }

    result = coordinator.create_hybrid_response(
        query_id=query_id,
        query="What is machine learning?",
        mode=QueryMode.DEEP,
        speculative_response=None,
        agentic_response=agentic_response,
        session_id="session_123",
    )

    assert result.path_used == PathSource.AGENTIC
    assert result.speculative_time is None
    assert result.agentic_time == 12.0
    assert result.total_time == 12.0
