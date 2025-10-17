"""
Unit tests for error handling and fallback mechanisms in hybrid query router.

Tests cover:
- Speculative path failure scenarios
- Agentic path failure scenarios
- Timeout handling
- LLM unavailability fallback
- Graceful degradation

Requirements: 8.1, 8.2, 8.3, 8.4, 8.6
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.services.hybrid_query_router import HybridQueryRouter
from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.response_coordinator import ResponseCoordinator
from backend.agents.aggregator import AggregatorAgent
from backend.models.hybrid import (
    QueryMode,
    ResponseChunk,
    ResponseType,
    PathSource,
    SpeculativeResponse,
)
from backend.models.agent import AgentStep
from backend.models.query import SearchResult


@pytest.fixture
def mock_speculative_processor():
    """Create mock speculative processor."""
    processor = Mock(spec=SpeculativeProcessor)
    processor.process = AsyncMock()
    return processor


@pytest.fixture
def mock_agentic_processor():
    """Create mock agentic processor."""
    processor = Mock(spec=AggregatorAgent)
    processor.process_query = AsyncMock()
    return processor


@pytest.fixture
def mock_response_coordinator():
    """Create mock response coordinator."""
    coordinator = Mock(spec=ResponseCoordinator)
    coordinator._merge_responses = Mock(return_value=("Merged response", 0.8))
    coordinator._merge_sources = Mock(return_value=[])
    return coordinator


@pytest.fixture
def hybrid_router(
    mock_speculative_processor, mock_agentic_processor, mock_response_coordinator
):
    """Create HybridQueryRouter with mocked dependencies."""
    return HybridQueryRouter(
        speculative_processor=mock_speculative_processor,
        agentic_processor=mock_agentic_processor,
        response_coordinator=mock_response_coordinator,
        default_speculative_timeout=2.0,
        default_agentic_timeout=15.0,
    )


class TestSpeculativePathFailures:
    """Test speculative path failure scenarios (Requirement 8.1)."""

    @pytest.mark.asyncio
    async def test_speculative_timeout_in_fast_mode(
        self, hybrid_router, mock_speculative_processor
    ):
        """Test that FAST mode handles speculative timeout gracefully."""
        # Simulate timeout
        mock_speculative_processor.process.side_effect = asyncio.TimeoutError()

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.FAST, session_id="test_session"
        ):
            chunks.append(chunk)

        # Should yield error chunk
        assert len(chunks) == 1
        assert chunks[0].type == ResponseType.FINAL
        assert chunks[0].confidence_score == 0.0
        assert "longer than expected" in chunks[0].content.lower()
        assert chunks[0].metadata.get("error") == "timeout"

    @pytest.mark.asyncio
    async def test_speculative_exception_in_fast_mode(
        self, hybrid_router, mock_speculative_processor
    ):
        """Test that FAST mode handles speculative exceptions gracefully."""
        # Simulate exception
        mock_speculative_processor.process.side_effect = Exception(
            "Vector DB connection failed"
        )

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.FAST, session_id="test_session"
        ):
            chunks.append(chunk)

        # Should yield error chunk
        assert len(chunks) == 1
        assert chunks[0].type == ResponseType.FINAL
        assert chunks[0].confidence_score == 0.0
        assert "error occurred" in chunks[0].content.lower()

    @pytest.mark.asyncio
    async def test_speculative_failure_in_balanced_mode(
        self, hybrid_router, mock_speculative_processor, mock_agentic_processor
    ):
        """Test that BALANCED mode falls back to agentic-only when speculative fails."""
        # Speculative fails
        mock_speculative_processor.process.side_effect = Exception("Speculative failed")

        # Agentic succeeds
        async def mock_agentic_generator():
            yield AgentStep(
                step_id="step1",
                type="response",
                content="Agentic response",
                metadata={"sources": []},
            )

        mock_agentic_processor.process_query.return_value = mock_agentic_generator()

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)

        # Should get agentic results only (no preliminary chunk)
        assert len(chunks) >= 1
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        # Should use agentic path since speculative failed
        assert final_chunk.path_source in [PathSource.AGENTIC, PathSource.HYBRID]


class TestAgenticPathFailures:
    """Test agentic path failure scenarios (Requirement 8.2)."""

    @pytest.mark.asyncio
    async def test_agentic_timeout_in_deep_mode(
        self, hybrid_router, mock_agentic_processor
    ):
        """Test that DEEP mode handles agentic timeout with partial results."""

        # Simulate timeout with partial results
        async def mock_agentic_generator():
            yield AgentStep(
                step_id="step1",
                type="thought",
                content="Analyzing query...",
                metadata={},
            )
            # Then timeout occurs
            await asyncio.sleep(20)  # Will be interrupted by timeout

        mock_agentic_processor.process_query.return_value = mock_agentic_generator()

        # Process query with short timeout
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query",
            mode=QueryMode.DEEP,
            session_id="test_session",
            agentic_timeout=0.1,  # Very short timeout
        ):
            chunks.append(chunk)

        # Should yield partial results
        assert len(chunks) >= 1
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        # Should indicate partial results
        assert "partial" in final_chunk.content.lower() or final_chunk.metadata.get(
            "timeout"
        )

    @pytest.mark.asyncio
    async def test_agentic_exception_in_deep_mode(
        self, hybrid_router, mock_agentic_processor
    ):
        """Test that DEEP mode handles agentic exceptions gracefully."""

        # Simulate exception
        async def mock_agentic_generator():
            raise Exception("Agent execution failed")
            yield  # Never reached

        mock_agentic_processor.process_query.return_value = mock_agentic_generator()

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.DEEP, session_id="test_session"
        ):
            chunks.append(chunk)

        # Should yield error chunk
        assert len(chunks) >= 1
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        assert final_chunk.confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_agentic_failure_in_balanced_mode(
        self, hybrid_router, mock_speculative_processor, mock_agentic_processor
    ):
        """Test that BALANCED mode falls back to speculative-only when agentic fails."""
        # Speculative succeeds
        mock_speculative_processor.process.return_value = SpeculativeResponse(
            response="Speculative response",
            confidence_score=0.7,
            sources=[],
            cache_hit=False,
            processing_time=0.5,
            metadata={},
        )

        # Agentic fails
        async def mock_agentic_generator():
            raise Exception("Agentic failed")
            yield  # Never reached

        mock_agentic_processor.process_query.return_value = mock_agentic_generator()

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)

        # Should get speculative results
        assert len(chunks) >= 1
        # Should have preliminary chunk
        preliminary_chunks = [c for c in chunks if c.type == ResponseType.PRELIMINARY]
        assert len(preliminary_chunks) > 0
        # Final chunk should use speculative path
        final_chunk = chunks[-1]
        assert final_chunk.path_source in [PathSource.SPECULATIVE, PathSource.HYBRID]


class TestBothPathsFailure:
    """Test scenarios where both paths fail (Requirement 8.3)."""

    @pytest.mark.asyncio
    async def test_both_paths_fail_in_balanced_mode(
        self, hybrid_router, mock_speculative_processor, mock_agentic_processor
    ):
        """Test that BALANCED mode provides clear error when both paths fail."""
        # Both paths fail
        mock_speculative_processor.process.side_effect = Exception("Speculative failed")

        async def mock_agentic_generator():
            raise Exception("Agentic failed")
            yield  # Never reached

        mock_agentic_processor.process_query.return_value = mock_agentic_generator()

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)

        # Should yield error chunk
        assert len(chunks) >= 1
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        assert final_chunk.confidence_score == 0.0
        assert (
            "unable" in final_chunk.content.lower()
            or "error" in final_chunk.content.lower()
        )
        # Should indicate both paths failed
        assert final_chunk.metadata.get("error") or final_chunk.metadata.get(
            "both_paths_failed"
        )


class TestTimeoutHandling:
    """Test timeout handling and partial results (Requirement 8.4)."""

    @pytest.mark.asyncio
    async def test_speculative_timeout_logged(
        self, hybrid_router, mock_speculative_processor, caplog
    ):
        """Test that speculative timeouts are logged for monitoring."""
        import logging

        caplog.set_level(logging.WARNING)

        # Simulate timeout
        mock_speculative_processor.process.side_effect = asyncio.TimeoutError()

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.FAST, session_id="test_session"
        ):
            chunks.append(chunk)

        # Check that timeout was logged
        assert any("timed out" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_agentic_timeout_returns_partial_results(
        self, hybrid_router, mock_agentic_processor
    ):
        """Test that agentic timeout returns partial results if available."""

        # Simulate partial execution before timeout
        async def mock_agentic_generator():
            yield AgentStep(
                step_id="step1",
                type="thought",
                content="Starting analysis...",
                metadata={},
            )
            yield AgentStep(
                step_id="step2",
                type="response",
                content="Partial response",
                metadata={"sources": []},
            )
            # Then timeout would occur
            await asyncio.sleep(20)

        mock_agentic_processor.process_query.return_value = mock_agentic_generator()

        # Process with short timeout
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query",
            mode=QueryMode.DEEP,
            session_id="test_session",
            agentic_timeout=0.1,
        ):
            chunks.append(chunk)

        # Should have some results
        assert len(chunks) >= 1
        # Final chunk should indicate partial results
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL


class TestLLMUnavailabilityFallback:
    """Test LLM unavailability fallback (Requirement 8.5, 8.6)."""

    @pytest.mark.asyncio
    async def test_llm_failure_returns_raw_documents(self):
        """Test that LLM failure returns raw retrieved documents."""
        from services.milvus import SearchResult

        # Create speculative processor with mocked dependencies
        mock_embedding = Mock()
        mock_embedding.embed_text = Mock(return_value=[0.1] * 768)

        mock_milvus = Mock()
        mock_milvus.search = AsyncMock(
            return_value=[
                SearchResult(
                    id="doc1",
                    document_id="doc1",
                    document_name="Test Doc",
                    text="This is test content from the document.",
                    score=0.9,
                    metadata={},
                )
            ]
        )

        mock_llm = Mock()
        mock_llm.generate = AsyncMock(side_effect=Exception("LLM unavailable"))

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        processor = SpeculativeProcessor(
            embedding_service=mock_embedding,
            milvus_manager=mock_milvus,
            llm_manager=mock_llm,
            redis_client=mock_redis,
        )

        # Process query
        response = await processor.process(
            query="test query", top_k=5, enable_cache=False
        )

        # Should return response with raw documents
        assert response is not None
        assert response.response is not None
        # Response should contain document content or fallback message
        assert len(response.response) > 0
        # Should have low confidence due to LLM failure
        assert response.confidence_score < 0.9

    @pytest.mark.asyncio
    async def test_llm_timeout_returns_raw_documents(self):
        """Test that LLM timeout returns raw retrieved documents."""
        from services.milvus import SearchResult

        # Create speculative processor with mocked dependencies
        mock_embedding = Mock()
        mock_embedding.embed_text = Mock(return_value=[0.1] * 768)

        mock_milvus = Mock()
        mock_milvus.search = AsyncMock(
            return_value=[
                SearchResult(
                    id="doc1",
                    document_id="doc1",
                    document_name="Test Doc",
                    text="This is test content from the document.",
                    score=0.9,
                    metadata={},
                )
            ]
        )

        mock_llm = Mock()

        # Simulate timeout
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(10)
            return "Never reached"

        mock_llm.generate = slow_generate

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        processor = SpeculativeProcessor(
            embedding_service=mock_embedding,
            milvus_manager=mock_milvus,
            llm_manager=mock_llm,
            redis_client=mock_redis,
        )

        # Process query
        response = await processor.process(
            query="test query", top_k=5, enable_cache=False
        )

        # Should return response with fallback content
        assert response is not None
        assert response.response is not None
        assert len(response.response) > 0

    def test_format_raw_documents_fallback(self):
        """Test formatting of raw documents as fallback."""
        from services.milvus import SearchResult

        mock_embedding = Mock()
        mock_milvus = Mock()
        mock_llm = Mock()
        mock_redis = Mock()

        processor = SpeculativeProcessor(
            embedding_service=mock_embedding,
            milvus_manager=mock_milvus,
            llm_manager=mock_llm,
            redis_client=mock_redis,
        )

        # Test with documents
        search_results = [
            SearchResult(
                id="doc1",
                document_id="doc1",
                document_name="Test Doc 1",
                text="This is content from document 1.",
                score=0.9,
                metadata={},
            ),
            SearchResult(
                id="doc2",
                document_id="doc2",
                document_name="Test Doc 2",
                text="This is content from document 2.",
                score=0.8,
                metadata={},
            ),
        ]

        result = processor._format_raw_documents_fallback(
            query="test query", search_results=search_results
        )

        # Should contain document information
        assert "Test Doc 1" in result
        assert "Test Doc 2" in result
        assert "relevant document" in result.lower()
        # Should indicate it's raw excerpts
        assert "excerpt" in result.lower() or "note" in result.lower()

    def test_format_raw_documents_fallback_no_results(self):
        """Test formatting when no documents are found."""
        mock_embedding = Mock()
        mock_milvus = Mock()
        mock_llm = Mock()
        mock_redis = Mock()

        processor = SpeculativeProcessor(
            embedding_service=mock_embedding,
            milvus_manager=mock_milvus,
            llm_manager=mock_llm,
            redis_client=mock_redis,
        )

        result = processor._format_raw_documents_fallback(
            query="test query", search_results=[]
        )

        # Should provide helpful message
        assert "no relevant" in result.lower() or "found no" in result.lower()
        assert len(result) > 0


class TestErrorLogging:
    """Test that errors are logged without exposing internal details (Requirement 8.6)."""

    @pytest.mark.asyncio
    async def test_errors_logged_without_internal_details(
        self, hybrid_router, mock_speculative_processor, caplog
    ):
        """Test that errors are logged but not exposed to users."""
        import logging

        caplog.set_level(logging.ERROR)

        # Simulate internal error with sensitive details
        mock_speculative_processor.process.side_effect = Exception(
            "Database connection failed: host=internal-db.company.com port=5432"
        )

        # Process query
        chunks = []
        async for chunk in hybrid_router.process_query(
            query="test query", mode=QueryMode.FAST, session_id="test_session"
        ):
            chunks.append(chunk)

        # Error should be logged
        assert any("error" in record.message.lower() for record in caplog.records)

        # But user-facing message should be generic
        assert len(chunks) >= 1
        final_chunk = chunks[-1]
        # Should not contain internal details
        assert "internal-db" not in final_chunk.content
        assert "5432" not in final_chunk.content
        # Should be user-friendly
        assert (
            "error occurred" in final_chunk.content.lower()
            or "unable" in final_chunk.content.lower()
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
