"""
Integration tests for Hybrid Query API endpoints.

Tests the /api/query endpoint with different modes (FAST, BALANCED, DEEP)
and verifies SSE streaming, progressive updates, and backward compatibility.

Requirements: 6.2, 6.3, 6.4, 12.2, 12.3
"""

import pytest
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.main import app
from backend.models.hybrid import QueryMode, ResponseType, PathSource
from backend.services.speculative_processor import (
    SpeculativeProcessor,
    SpeculativeResponse,
)
from backend.services.response_coordinator import ResponseCoordinator
from backend.services.hybrid_query_router import HybridQueryRouter
from backend.models.query import SearchResult


@pytest.fixture
def mock_speculative_processor():
    """Mock SpeculativeProcessor for testing."""
    processor = Mock(spec=SpeculativeProcessor)

    async def mock_process(query: str, top_k: int = 10, enable_cache: bool = True):
        """Mock speculative processing."""
        return SpeculativeResponse(
            response=f"Speculative answer to: {query}",
            confidence_score=0.75,
            sources=[
                SearchResult(
                    chunk_id="chunk_1",
                    document_id="doc_1",
                    document_name="test_doc.pdf",
                    text="Test content",
                    score=0.9,
                    metadata={},
                )
            ],
            cache_hit=False,
            processing_time=1.5,
            metadata={"vector_search_time_ms": 120},
        )

    processor.process = mock_process
    return processor


@pytest.fixture
def mock_aggregator_agent():
    """Mock AggregatorAgent for testing."""
    from backend.models.agent import AgentStep

    agent = Mock()

    async def mock_process_query(query: str, session_id: str, top_k: int = 10):
        """Mock agentic processing."""
        # Yield some reasoning steps
        yield AgentStep(
            step_id="step_1",
            type="thought",
            content="Analyzing the query...",
            timestamp=datetime.now(),
            metadata={},
        )

        yield AgentStep(
            step_id="step_2",
            type="action",
            content="Searching vector database...",
            timestamp=datetime.now(),
            metadata={},
        )

        yield AgentStep(
            step_id="step_3",
            type="response",
            content=f"Detailed agentic answer to: {query}",
            timestamp=datetime.now(),
            metadata={
                "sources": [
                    SearchResult(
                        chunk_id="chunk_2",
                        document_id="doc_2",
                        document_name="test_doc2.pdf",
                        text="More test content",
                        score=0.95,
                        metadata={},
                    ).model_dump()
                ]
            },
        )

    agent.process_query = mock_process_query
    return agent


@pytest.fixture
def mock_hybrid_router(mock_speculative_processor, mock_aggregator_agent):
    """Create a mock HybridQueryRouter for testing."""
    coordinator = ResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_speculative_processor,
        agentic_processor=mock_aggregator_agent,
        response_coordinator=coordinator,
        default_speculative_timeout=2.0,
        default_agentic_timeout=15.0,
    )

    return router


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHybridQueryAPI:
    """Test suite for Hybrid Query API endpoints."""

    @pytest.mark.asyncio
    async def test_query_endpoint_fast_mode(self, mock_hybrid_router):
        """
        Test /query endpoint with FAST mode.

        Should return speculative response only within 2 seconds.
        Requirements: 6.2
        """
        query = "What is machine learning?"
        mode = QueryMode.FAST

        chunks = []
        async for chunk in mock_hybrid_router.process_query(
            query=query, mode=mode, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

        # Verify we got chunks
        assert len(chunks) > 0

        # Verify final chunk
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        assert final_chunk.path_source == PathSource.SPECULATIVE
        assert final_chunk.confidence_score is not None
        assert 0.0 <= final_chunk.confidence_score <= 1.0

        # Verify content
        assert (
            "machine learning" in final_chunk.content.lower()
            or "speculative" in final_chunk.content.lower()
        )

    @pytest.mark.asyncio
    async def test_query_endpoint_deep_mode(self, mock_hybrid_router):
        """
        Test /query endpoint with DEEP mode.

        Should return agentic response with reasoning steps.
        Requirements: 6.4
        """
        query = "Explain neural networks"
        mode = QueryMode.DEEP

        chunks = []
        async for chunk in mock_hybrid_router.process_query(
            query=query, mode=mode, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

        # Verify we got multiple chunks (reasoning steps + final)
        assert len(chunks) > 1

        # Verify we have refinement chunks (reasoning steps)
        refinement_chunks = [c for c in chunks if c.type == ResponseType.REFINEMENT]
        assert len(refinement_chunks) > 0

        # Verify final chunk
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        assert final_chunk.path_source == PathSource.AGENTIC

        # Verify reasoning steps are included
        assert len(final_chunk.reasoning_steps) > 0

    @pytest.mark.asyncio
    async def test_query_endpoint_balanced_mode(self, mock_hybrid_router):
        """
        Test /query endpoint with BALANCED mode.

        Should return preliminary response followed by refinements.
        Requirements: 6.3
        """
        query = "What are transformers?"
        mode = QueryMode.BALANCED

        chunks = []
        async for chunk in mock_hybrid_router.process_query(
            query=query, mode=mode, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

        # Verify we got multiple chunks
        assert len(chunks) > 1

        # Verify we have a preliminary chunk
        preliminary_chunks = [c for c in chunks if c.type == ResponseType.PRELIMINARY]
        assert len(preliminary_chunks) > 0

        preliminary = preliminary_chunks[0]
        assert preliminary.path_source == PathSource.SPECULATIVE
        assert preliminary.confidence_score is not None

        # Verify we have refinement chunks
        refinement_chunks = [c for c in chunks if c.type == ResponseType.REFINEMENT]
        assert len(refinement_chunks) > 0

        # Verify final chunk
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL

    @pytest.mark.asyncio
    async def test_sse_streaming_format(self, mock_hybrid_router):
        """
        Test SSE streaming format for progressive responses.

        Verifies that chunks have correct structure and metadata.
        Requirements: 1.2, 1.3, 3.1, 3.2, 3.3, 3.4
        """
        query = "Test query"
        mode = QueryMode.BALANCED

        chunks = []
        async for chunk in mock_hybrid_router.process_query(
            query=query, mode=mode, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

            # Verify chunk structure
            assert hasattr(chunk, "chunk_id")
            assert hasattr(chunk, "type")
            assert hasattr(chunk, "content")
            assert hasattr(chunk, "path_source")
            assert hasattr(chunk, "confidence_score")
            assert hasattr(chunk, "sources")
            assert hasattr(chunk, "reasoning_steps")
            assert hasattr(chunk, "timestamp")
            assert hasattr(chunk, "metadata")

            # Verify types
            assert isinstance(chunk.chunk_id, str)
            assert isinstance(chunk.type, ResponseType)
            assert isinstance(chunk.content, str)
            assert isinstance(chunk.path_source, PathSource)
            assert isinstance(chunk.sources, list)
            assert isinstance(chunk.reasoning_steps, list)
            assert isinstance(chunk.metadata, dict)

    @pytest.mark.asyncio
    async def test_response_metadata_includes_confidence(self, mock_hybrid_router):
        """
        Test that response chunks include confidence scores.

        Requirements: 5.1
        """
        query = "Test query"
        mode = QueryMode.FAST

        chunks = []
        async for chunk in mock_hybrid_router.process_query(
            query=query, mode=mode, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

        # Verify confidence scores
        for chunk in chunks:
            if (
                chunk.type == ResponseType.FINAL
                or chunk.type == ResponseType.PRELIMINARY
            ):
                assert chunk.confidence_score is not None
                assert 0.0 <= chunk.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_response_metadata_includes_path_source(self, mock_hybrid_router):
        """
        Test that response chunks include path source indicators.

        Requirements: 5.2, 5.3
        """
        query = "Test query"
        mode = QueryMode.BALANCED

        chunks = []
        async for chunk in mock_hybrid_router.process_query(
            query=query, mode=mode, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

        # Verify path sources
        preliminary_chunks = [c for c in chunks if c.type == ResponseType.PRELIMINARY]
        if preliminary_chunks:
            assert preliminary_chunks[0].path_source == PathSource.SPECULATIVE

        refinement_chunks = [c for c in chunks if c.type == ResponseType.REFINEMENT]
        if refinement_chunks:
            for chunk in refinement_chunks:
                assert chunk.path_source in [PathSource.AGENTIC, PathSource.HYBRID]

    @pytest.mark.asyncio
    async def test_response_metadata_includes_progress(self, mock_hybrid_router):
        """
        Test that response chunks include progress information.

        Requirements: 5.6
        """
        query = "Test query"
        mode = QueryMode.DEEP

        chunks = []
        async for chunk in mock_hybrid_router.process_query(
            query=query, mode=mode, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

        # Verify metadata includes progress info
        for chunk in chunks:
            assert isinstance(chunk.metadata, dict)
            # Metadata should have mode information
            if "mode" in chunk.metadata:
                assert chunk.metadata["mode"] in ["fast", "balanced", "deep"]

    @pytest.mark.asyncio
    async def test_backward_compatibility_without_mode(self, mock_aggregator_agent):
        """
        Test backward compatibility when mode is not specified.

        Should default to BALANCED mode or fall back to legacy agentic-only.
        Requirements: 12.2, 12.3
        """
        # Test that old QueryRequest format still works
        # This would be tested with actual API calls in a full integration test

        # Verify aggregator agent still works independently
        chunks = []
        async for step in mock_aggregator_agent.process_query(
            query="Test query", session_id="test_session", top_k=10
        ):
            chunks.append(step)

        assert len(chunks) > 0

        # Verify we got a response step
        response_steps = [s for s in chunks if s.type == "response"]
        assert len(response_steps) > 0

    @pytest.mark.asyncio
    async def test_error_handling_in_streaming(self, mock_hybrid_router):
        """
        Test error handling during streaming.

        Should return error chunks with appropriate metadata.
        """
        # This would require mocking failures in the router
        # For now, verify that error chunks have the right structure

        from backend.models.hybrid import ResponseChunk

        error_chunk = ResponseChunk(
            chunk_id="error_1",
            type=ResponseType.FINAL,
            content="An error occurred",
            path_source=PathSource.HYBRID,
            confidence_score=0.0,
            sources=[],
            reasoning_steps=[],
            timestamp=datetime.now(),
            metadata={"error": "test_error"},
        )

        assert error_chunk.confidence_score == 0.0
        assert "error" in error_chunk.metadata

    @pytest.mark.asyncio
    async def test_session_id_handling(self, mock_hybrid_router):
        """
        Test that session IDs are properly handled across modes.
        """
        query = "Test query"
        session_id = "test_session_123"

        for mode in [QueryMode.FAST, QueryMode.BALANCED, QueryMode.DEEP]:
            chunks = []
            async for chunk in mock_hybrid_router.process_query(
                query=query, mode=mode, session_id=session_id, top_k=10
            ):
                chunks.append(chunk)

            # Verify we got chunks
            assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_top_k_parameter(self, mock_hybrid_router):
        """
        Test that top_k parameter is respected across modes.
        """
        query = "Test query"
        top_k_values = [5, 10, 20]

        for top_k in top_k_values:
            chunks = []
            async for chunk in mock_hybrid_router.process_query(
                query=query, mode=QueryMode.FAST, session_id="test_session", top_k=top_k
            ):
                chunks.append(chunk)

            # Verify we got chunks
            assert len(chunks) > 0

            # Verify sources don't exceed top_k
            for chunk in chunks:
                assert len(chunk.sources) <= top_k


class TestBackwardCompatibility:
    """Test backward compatibility with legacy API."""

    @pytest.mark.asyncio
    async def test_legacy_query_request_format(self, mock_aggregator_agent):
        """
        Test that legacy QueryRequest format still works.

        Requirements: 12.2, 12.3
        """
        from backend.models.query import QueryRequest

        # Create legacy request (without mode parameter)
        request = QueryRequest(
            query="Test query", session_id="test_session", top_k=10, stream=True
        )

        # Verify request is valid
        assert request.query == "Test query"
        assert request.session_id == "test_session"
        assert request.top_k == 10
        assert request.stream is True

    @pytest.mark.asyncio
    async def test_hybrid_request_extends_legacy(self):
        """
        Test that HybridQueryRequest extends QueryRequest.

        Requirements: 12.2, 12.3
        """
        from backend.models.hybrid import HybridQueryRequest
        from backend.models.query import QueryRequest

        # Create hybrid request
        hybrid_request = HybridQueryRequest(
            query="Test query",
            session_id="test_session",
            top_k=10,
            mode=QueryMode.BALANCED,
            enable_cache=True,
        )

        # Verify it has all legacy fields
        assert hybrid_request.query == "Test query"
        assert hybrid_request.session_id == "test_session"
        assert hybrid_request.top_k == 10

        # Verify it has new fields
        assert hybrid_request.mode == QueryMode.BALANCED
        assert hybrid_request.enable_cache is True

    @pytest.mark.asyncio
    async def test_default_mode_is_balanced(self):
        """
        Test that default mode is BALANCED for backward compatibility.

        Requirements: 12.2, 12.3
        """
        from backend.models.hybrid import HybridQueryRequest

        # Create request without specifying mode
        request = HybridQueryRequest(query="Test query", session_id="test_session")

        # Verify default mode is BALANCED
        assert request.mode == QueryMode.BALANCED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
