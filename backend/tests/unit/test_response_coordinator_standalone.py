"""
Standalone unit tests for ResponseCoordinator.

Tests cover:
- Source deduplication with various overlap scenarios
- Response merging logic with different confidence levels
- Change detection accuracy between versions
- Streaming coordination
- Version management
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

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
    print("✓ Deduplication with no duplicates works correctly")


def test_deduplicate_sources_with_duplicates(coordinator, duplicate_sources):
    """Test deduplication with exact and near duplicates."""
    result = coordinator._deduplicate_sources(duplicate_sources)

    # Should keep highest scoring version of duplicates
    assert len(result) == 2  # chunk_1 (0.95) and chunk_3 (0.88)
    assert result[0].chunk_id == "chunk_1"
    assert result[0].score == 0.95
    assert result[1].chunk_id == "chunk_3"
    print("✓ Deduplication with duplicates works correctly")


def test_deduplicate_sources_empty_list(coordinator):
    """Test deduplication with empty list."""
    result = coordinator._deduplicate_sources([])
    assert result == []
    print("✓ Deduplication with empty list works correctly")


# Test Source Merging


def test_merge_sources_no_overlap(coordinator, sample_sources):
    """Test merging sources with no overlap."""
    spec_sources = sample_sources[:2]
    agentic_sources = sample_sources[2:]

    result = coordinator._merge_sources(spec_sources, agentic_sources)

    assert len(result) == 3
    assert all(s.chunk_id in ["chunk_1", "chunk_2", "chunk_3"] for s in result)
    print("✓ Merging sources with no overlap works correctly")


def test_merge_sources_with_overlap(coordinator, sample_sources):
    """Test merging sources with overlapping chunks."""
    spec_sources = sample_sources[:2]
    agentic_sources = [sample_sources[1], sample_sources[2]]  # chunk_2 overlaps

    result = coordinator._merge_sources(spec_sources, agentic_sources)

    # Should deduplicate chunk_2
    assert len(result) == 3
    chunk_ids = [s.chunk_id for s in result]
    assert chunk_ids.count("chunk_2") == 1
    print("✓ Merging sources with overlap works correctly")


# Test Response Merging


def test_merge_responses_both_present(coordinator):
    """Test merging when both responses present."""
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
    print("✓ Response merging with both paths works correctly")


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
    print("✓ Response merging with speculative only works correctly")


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
    print("✓ Response merging with agentic only works correctly")


# Test Version Management


def test_store_and_retrieve_versions(coordinator, sample_sources):
    """Test storing and retrieving versions."""
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
    print("✓ Version storage and retrieval works correctly")


# Test Change Detection


def test_detect_changes(coordinator, sample_sources):
    """Test change detection between versions."""
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
        content="Machine learning is a comprehensive subset of artificial intelligence.",
        path_source=PathSource.AGENTIC,
        confidence_score=0.90,
        sources=sample_sources,
    )

    changes = coordinator.detect_changes(query_id, v1, v2)

    assert changes["content_changed"] is True
    assert changes["confidence_improved"] is True
    assert changes["sources_added"] == 2
    print("✓ Change detection works correctly")


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
    print("✓ Streaming coordination with speculative only works correctly")


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
    assert chunks[1].type == ResponseType.REFINEMENT
    assert chunks[2].type == ResponseType.FINAL
    assert chunks[2].path_source == PathSource.HYBRID
    print("✓ Streaming coordination with both paths works correctly")


# Test Hybrid Response Creation


def test_create_hybrid_response(coordinator, speculative_response, sample_sources):
    """Test creating hybrid response."""
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
    print("✓ Hybrid response creation works correctly")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RESPONSE COORDINATOR UNIT TESTS")
    print("=" * 70 + "\n")

    # Run tests manually
    coord = ResponseCoordinator(similarity_threshold=0.85)

    # Create sample data
    sources = [
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

    dup_sources = [
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
            text="Machine learning is a subset of artificial intelligence.",
            score=0.93,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_2",
            document_id="doc_1",
            document_name="Document 1",
            text="Machine learning is a part of artificial intelligence.",
            score=0.92,
            metadata={},
        ),
        SearchResult(
            chunk_id="chunk_3",
            document_id="doc_2",
            document_name="Document 2",
            text="Deep learning is different from machine learning.",
            score=0.88,
            metadata={},
        ),
    ]

    spec_resp = SpeculativeResponse(
        response="Machine learning is a subset of AI that enables computers to learn from data.",
        confidence_score=0.75,
        sources=sources[:2],
        cache_hit=False,
        processing_time=1.5,
        metadata={"vector_search_time_ms": 120, "llm_time_ms": 1380},
    )

    # Run tests
    test_deduplicate_sources_no_duplicates(coord, sources)
    test_deduplicate_sources_with_duplicates(coord, dup_sources)
    test_deduplicate_sources_empty_list(coord)
    test_merge_sources_no_overlap(coord, sources)
    test_merge_sources_with_overlap(coord, sources)
    test_merge_responses_both_present(coord)
    test_merge_responses_only_speculative(coord)
    test_merge_responses_only_agentic(coord)
    test_store_and_retrieve_versions(coord, sources)
    test_detect_changes(coord, sources)

    # Async tests
    async def run_async_tests():
        await test_coordinate_streaming_speculative_only(coord, spec_resp)
        await test_coordinate_streaming_both_paths(coord, spec_resp, sources)

    asyncio.run(run_async_tests())

    test_create_hybrid_response(coord, spec_resp, sources)

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70 + "\n")
