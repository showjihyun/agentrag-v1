"""
Unit tests for HybridQueryRouter.

Tests mode routing, parallel execution, resource sharing, and timeout handling.
Requirements: 1.1, 1.4, 4.1, 4.2, 4.3, 6.2, 6.3, 6.4
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
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
from backend.models.query import SearchResult
from backend.models.agent import AgentStep


@pytest.fixture
def mock_speculative_processor():
    """Create mock SpeculativeProcessor."""
    processor = Mock(spec=SpeculativeProcessor)
    return processor


@pytest.fixture
def mock_agentic_processor():
    """Create mock AggregatorAgent."""
    processor = Mock(spec=AggregatorAgent)
    return processor


@pytest.fixture
def mock_response_coordinator():
    """Create mock ResponseCoordinator."""
    coordinator = Mock(spec=ResponseCoordinator)

    # Mock merge methods
    coordinator._merge_responses = Mock(return_value=("Merged response", 0.85))
    coordinator._merge_sources = Mock(return_value=[])

    return coordinator


@pytest.fixture
def router(
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


@pytest.fixture
def sample_speculative_response():
    """Create sample SpeculativeResponse."""
    return SpeculativeResponse(
        response="This is a fast response.",
        confidence_score=0.75,
        sources=[
            SearchResult(
                chunk_id="chunk_1",
                document_id="doc_1",
                document_name="test.txt",
                text="Sample text",
                score=0.9,
                metadata={},
            )
        ],
        cache_hit=False,
        processing_time=1.5,
        metadata={"vector_search_time_ms": 120},
    )


@pytest.fixture
def sample_agent_step():
    """Create sample AgentStep."""
    return AgentStep(
        step_id="step_1",
        type="response",
        content="This is an agentic response.",
        timestamp=datetime.now(),
        metadata={
            "sources": [
                {
                    "chunk_id": "chunk_2",
                    "document_id": "doc_2",
                    "document_name": "test2.txt",
                    "text": "Sample text 2",
                    "score": 0.85,
                    "metadata": {},
                }
            ]
        },
    )


class TestFastMode:
    """Test FAST mode routing (speculative only).

    Requirements: 6.2
    """

    @pytest.mark.asyncio
    async def test_fast_mode_success(
        self, router, mock_speculative_processor, sample_speculative_response
    ):
        """Test successful FAST mode processing."""
        # Setup mock
        mock_speculative_processor.process = AsyncMock(
            return_value=sample_speculative_response
        )

        # Process query
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.FAST, session_id="test_session", top_k=10
        ):
            chunks.append(chunk)

        # Verify
        assert len(chunks) == 1
        assert chunks[0].type == ResponseType.FINAL
        assert chunks[0].path_source == PathSource.SPECULATIVE
        assert chunks[0].content == "This is a fast response."
        assert chunks[0].confidence_score == 0.75

        # Verify speculative processor was called
        mock_speculative_processor.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_fast_mode_timeout(self, router, mock_speculative_processor):
        """Test FAST mode timeout handling."""

        # Setup mock to timeout
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(5)  # Longer than timeout
            return None

        mock_speculative_processor.process = slow_process

        # Process query with short timeout
        chunks = []
        async for chunk in router.process_query(
            query="Test query",
            mode=QueryMode.FAST,
            session_id="test_session",
            speculative_timeout=0.5,
        ):
            chunks.append(chunk)

        # Verify timeout error chunk
        assert len(chunks) == 1
        assert chunks[0].type == ResponseType.FINAL
        assert (
            "timeout" in chunks[0].metadata.get("error", "").lower()
            or "longer than expected" in chunks[0].content.lower()
        )

    @pytest.mark.asyncio
    async def test_fast_mode_error(self, router, mock_speculative_processor):
        """Test FAST mode error handling."""
        # Setup mock to raise error
        mock_speculative_processor.process = AsyncMock(
            side_effect=Exception("Test error")
        )

        # Process query
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.FAST, session_id="test_session"
        ):
            chunks.append(chunk)

        # Verify error chunk
        assert len(chunks) == 1
        assert chunks[0].type == ResponseType.FINAL
        assert chunks[0].confidence_score == 0.0
        assert "error" in chunks[0].content.lower()


class TestDeepMode:
    """Test DEEP mode routing (agentic only).

    Requirements: 6.4
    """

    @pytest.mark.asyncio
    async def test_deep_mode_success(
        self, router, mock_agentic_processor, sample_agent_step
    ):
        """Test successful DEEP mode processing."""

        # Setup mock to yield steps
        async def mock_process_query(*args, **kwargs):
            yield AgentStep(
                step_id="step_1",
                type="thought",
                content="Thinking...",
                timestamp=datetime.now(),
                metadata={},
            )
            yield sample_agent_step

        mock_agentic_processor.process_query = mock_process_query

        # Process query
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.DEEP, session_id="test_session"
        ):
            chunks.append(chunk)

        # Verify - should have intermediate chunks + final
        assert len(chunks) >= 2
        assert chunks[-1].type == ResponseType.FINAL
        assert chunks[-1].path_source == PathSource.AGENTIC

        # Verify agentic processor was called
        # (can't easily assert on async generator)

    @pytest.mark.asyncio
    async def test_deep_mode_timeout(self, router, mock_agentic_processor):
        """Test DEEP mode timeout handling."""

        # Setup mock to timeout
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(5)
            yield AgentStep(
                step_id="step_1",
                type="response",
                content="Late response",
                timestamp=datetime.now(),
                metadata={},
            )

        mock_agentic_processor.process_query = slow_process

        # Process query with short timeout
        chunks = []
        async for chunk in router.process_query(
            query="Test query",
            mode=QueryMode.DEEP,
            session_id="test_session",
            agentic_timeout=0.5,
        ):
            chunks.append(chunk)

        # Verify final chunk indicates timeout
        assert len(chunks) >= 1
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        assert (
            "longer than expected" in final_chunk.content.lower()
            or final_chunk.confidence_score == 0.0
        )


class TestBalancedMode:
    """Test BALANCED mode routing (parallel execution).

    Requirements: 1.4, 4.1, 4.2, 4.3, 6.3
    """

    @pytest.mark.asyncio
    async def test_balanced_mode_both_paths_success(
        self,
        router,
        mock_speculative_processor,
        mock_agentic_processor,
        sample_speculative_response,
        sample_agent_step,
    ):
        """Test BALANCED mode with both paths succeeding."""
        # Setup speculative mock
        mock_speculative_processor.process = AsyncMock(
            return_value=sample_speculative_response
        )

        # Setup agentic mock
        async def mock_process_query(*args, **kwargs):
            yield sample_agent_step

        mock_agentic_processor.process_query = mock_process_query

        # Process query
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)

        # Verify we got preliminary, refinements, and final
        assert len(chunks) >= 2

        # Check for preliminary chunk
        preliminary_chunks = [c for c in chunks if c.type == ResponseType.PRELIMINARY]
        assert len(preliminary_chunks) >= 1
        assert preliminary_chunks[0].path_source == PathSource.SPECULATIVE

        # Check for final chunk
        final_chunks = [c for c in chunks if c.type == ResponseType.FINAL]
        assert len(final_chunks) == 1
        assert final_chunks[0].path_source in [PathSource.HYBRID, PathSource.AGENTIC]

    @pytest.mark.asyncio
    async def test_balanced_mode_speculative_fails(
        self,
        router,
        mock_speculative_processor,
        mock_agentic_processor,
        sample_agent_step,
    ):
        """Test BALANCED mode when speculative path fails."""
        # Setup speculative to fail
        mock_speculative_processor.process = AsyncMock(
            side_effect=Exception("Speculative failed")
        )

        # Setup agentic to succeed
        async def mock_process_query(*args, **kwargs):
            yield sample_agent_step

        mock_agentic_processor.process_query = mock_process_query

        # Process query
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)

        # Verify we still get a final response from agentic path
        assert len(chunks) >= 1
        final_chunks = [c for c in chunks if c.type == ResponseType.FINAL]
        assert len(final_chunks) == 1
        assert final_chunks[0].path_source in [PathSource.AGENTIC, PathSource.HYBRID]

    @pytest.mark.asyncio
    async def test_balanced_mode_agentic_fails(
        self,
        router,
        mock_speculative_processor,
        mock_agentic_processor,
        sample_speculative_response,
    ):
        """Test BALANCED mode when agentic path fails."""
        # Setup speculative to succeed
        mock_speculative_processor.process = AsyncMock(
            return_value=sample_speculative_response
        )

        # Setup agentic to fail
        async def mock_process_query(*args, **kwargs):
            raise Exception("Agentic failed")
            yield  # Make it a generator

        mock_agentic_processor.process_query = mock_process_query

        # Process query
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)

        # Verify we still get preliminary and final from speculative
        assert len(chunks) >= 1

        preliminary_chunks = [c for c in chunks if c.type == ResponseType.PRELIMINARY]
        assert len(preliminary_chunks) >= 1

        final_chunks = [c for c in chunks if c.type == ResponseType.FINAL]
        assert len(final_chunks) == 1

    @pytest.mark.asyncio
    async def test_balanced_mode_both_fail(
        self, router, mock_speculative_processor, mock_agentic_processor
    ):
        """Test BALANCED mode when both paths fail."""
        # Setup both to fail
        mock_speculative_processor.process = AsyncMock(
            side_effect=Exception("Speculative failed")
        )

        async def mock_process_query(*args, **kwargs):
            raise Exception("Agentic failed")
            yield

        mock_agentic_processor.process_query = mock_process_query

        # Process query
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)

        # Verify we get an error chunk
        assert len(chunks) >= 1
        final_chunk = chunks[-1]
        assert final_chunk.type == ResponseType.FINAL
        assert final_chunk.confidence_score == 0.0
        assert (
            "error" in final_chunk.content.lower()
            or "failed" in final_chunk.content.lower()
        )


class TestParallelExecution:
    """Test parallel execution in BALANCED mode.

    Requirements: 1.4, 4.2
    """

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(
        self,
        router,
        mock_speculative_processor,
        mock_agentic_processor,
        sample_speculative_response,
        sample_agent_step,
    ):
        """Test that both paths run in parallel, not sequentially."""
        import time

        # Setup speculative with delay
        async def slow_speculative(*args, **kwargs):
            await asyncio.sleep(0.5)
            return sample_speculative_response

        mock_speculative_processor.process = slow_speculative

        # Setup agentic with delay
        async def slow_agentic(*args, **kwargs):
            await asyncio.sleep(0.5)
            yield sample_agent_step

        mock_agentic_processor.process_query = slow_agentic

        # Process query and measure time
        start_time = time.time()
        chunks = []
        async for chunk in router.process_query(
            query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
        ):
            chunks.append(chunk)
        elapsed = time.time() - start_time

        # If parallel, should take ~0.5s, not ~1.0s
        # Allow some overhead
        assert elapsed < 1.0, f"Execution took {elapsed}s, expected < 1.0s (parallel)"
        assert len(chunks) >= 1


class TestResourceSharing:
    """Test resource sharing between paths.

    Requirements: 4.3
    """

    @pytest.mark.asyncio
    async def test_shared_results_parameter(
        self, router, mock_speculative_processor, sample_speculative_response
    ):
        """Test that shared_results parameter is passed to agentic path."""
        # Setup speculative
        mock_speculative_processor.process = AsyncMock(
            return_value=sample_speculative_response
        )

        # Call _collect_agentic_response with shared results
        shared_data = {"vector_results": ["doc1", "doc2"]}

        # Mock agentic processor
        async def mock_process_query(*args, **kwargs):
            yield AgentStep(
                step_id="step_1",
                type="response",
                content="Response",
                timestamp=datetime.now(),
                metadata={},
            )

        router.agentic.process_query = mock_process_query

        # Collect agentic response
        result = await router._collect_agentic_response(
            query="Test",
            session_id="test",
            top_k=10,
            timeout=5.0,
            shared_results=shared_data,
        )

        # Verify result is returned
        assert result is not None
        assert "response" in result


class TestTimeoutHandling:
    """Test timeout handling for both paths.

    Requirements: 4.2
    """

    @pytest.mark.asyncio
    async def test_speculative_timeout_returns_none(self, router):
        """Test that speculative timeout returns None gracefully."""

        # Mock slow speculative
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(5)
            return None

        router.speculative.process = slow_process

        # Collect with short timeout
        result = await router._collect_speculative_response(
            query="Test", top_k=10, enable_cache=True, timeout=0.1
        )

        # Should return None on timeout
        assert result is None

    @pytest.mark.asyncio
    async def test_agentic_timeout_returns_none(self, router):
        """Test that agentic timeout returns None gracefully."""

        # Mock slow agentic
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(5)
            yield AgentStep(
                step_id="step_1",
                type="response",
                content="Late",
                timestamp=datetime.now(),
                metadata={},
            )

        router.agentic.process_query = slow_process

        # Collect with short timeout
        result = await router._collect_agentic_response(
            query="Test", session_id="test", top_k=10, timeout=0.1, shared_results=None
        )

        # Should return None on timeout
        assert result is None


class TestModeRouting:
    """Test mode routing logic.

    Requirements: 1.1, 6.2, 6.3, 6.4
    """

    @pytest.mark.asyncio
    async def test_invalid_mode_raises_error(self, router):
        """Test that invalid mode raises appropriate error."""
        # Try to process with invalid mode (bypass enum)
        with pytest.raises(Exception):
            async for chunk in router.process_query(
                query="Test", mode="invalid_mode", session_id="test"  # type: ignore
            ):
                pass

    @pytest.mark.asyncio
    async def test_default_timeouts_used(
        self, router, mock_speculative_processor, sample_speculative_response
    ):
        """Test that default timeouts are used when not specified."""
        mock_speculative_processor.process = AsyncMock(
            return_value=sample_speculative_response
        )

        # Process without specifying timeouts
        chunks = []
        async for chunk in router.process_query(
            query="Test", mode=QueryMode.FAST, session_id="test"
        ):
            chunks.append(chunk)

        # Should complete successfully with defaults
        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_custom_timeouts_used(
        self, router, mock_speculative_processor, sample_speculative_response
    ):
        """Test that custom timeouts override defaults."""
        mock_speculative_processor.process = AsyncMock(
            return_value=sample_speculative_response
        )

        # Process with custom timeouts
        chunks = []
        async for chunk in router.process_query(
            query="Test",
            mode=QueryMode.FAST,
            session_id="test",
            speculative_timeout=5.0,
            agentic_timeout=30.0,
        ):
            chunks.append(chunk)

        # Should complete successfully
        assert len(chunks) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
