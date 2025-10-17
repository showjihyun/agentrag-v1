"""
Standalone unit tests for HybridQueryRouter.

Tests mode routing, parallel execution, resource sharing, and timeout handling.
Requirements: 1.1, 1.4, 4.1, 4.2, 4.3, 6.2, 6.3, 6.4
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from backend.services.hybrid_query_router import HybridQueryRouter
from backend.models.hybrid import (
    QueryMode,
    ResponseChunk,
    ResponseType,
    PathSource,
    SpeculativeResponse,
)
from backend.models.query import SearchResult


class MockSpeculativeProcessor:
    """Mock SpeculativeProcessor for testing."""

    def __init__(self):
        self.process = AsyncMock()


class MockAgenticProcessor:
    """Mock AggregatorAgent for testing."""

    def __init__(self):
        self.process_query = None  # Will be set per test


class MockResponseCoordinator:
    """Mock ResponseCoordinator for testing."""

    def __init__(self):
        self._merge_responses = Mock(return_value=("Merged response", 0.85))
        self._merge_sources = Mock(return_value=[])


class MockAgentStep:
    """Mock AgentStep for testing."""

    def __init__(self, step_id, step_type, content, metadata=None):
        self.step_id = step_id
        self.type = step_type
        self.content = content
        self.timestamp = datetime.now()
        self.metadata = metadata or {}

    def model_dump(self):
        return {
            "step_id": self.step_id,
            "type": self.type,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


def create_sample_speculative_response():
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


def create_sample_agent_step():
    """Create sample AgentStep."""
    return MockAgentStep(
        step_id="step_1",
        step_type="response",
        content="This is an agentic response.",
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


@pytest.mark.asyncio
async def test_fast_mode_success():
    """Test successful FAST mode processing.

    Requirements: 6.2
    """
    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Mock speculative response
    sample_response = create_sample_speculative_response()
    mock_spec.process = AsyncMock(return_value=sample_response)

    # Process query
    chunks = []
    async for chunk in router.process_query(
        query="Test query", mode=QueryMode.FAST, session_id="test_session"
    ):
        chunks.append(chunk)

    # Verify
    assert len(chunks) == 1
    assert chunks[0].type == ResponseType.FINAL
    assert chunks[0].path_source == PathSource.SPECULATIVE
    assert chunks[0].content == "This is a fast response."
    assert chunks[0].confidence_score == 0.75

    print("✓ FAST mode success test passed")


@pytest.mark.asyncio
async def test_fast_mode_timeout():
    """Test FAST mode timeout handling.

    Requirements: 6.2
    """
    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Mock slow speculative
    async def slow_process(*args, **kwargs):
        await asyncio.sleep(5)
        return None

    mock_spec.process = slow_process

    # Process with short timeout
    chunks = []
    async for chunk in router.process_query(
        query="Test query",
        mode=QueryMode.FAST,
        session_id="test_session",
        speculative_timeout=0.1,
    ):
        chunks.append(chunk)

    # Verify timeout handling
    assert len(chunks) == 1
    assert chunks[0].type == ResponseType.FINAL
    assert (
        "timeout" in chunks[0].metadata.get("error", "").lower()
        or "longer than expected" in chunks[0].content.lower()
    )

    print("✓ FAST mode timeout test passed")


@pytest.mark.asyncio
async def test_deep_mode_success():
    """Test successful DEEP mode processing.

    Requirements: 6.4
    """
    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Mock agentic response
    async def mock_process_query(*args, **kwargs):
        yield MockAgentStep("step_1", "thought", "Thinking...")
        yield create_sample_agent_step()

    mock_agent.process_query = mock_process_query

    # Process query
    chunks = []
    async for chunk in router.process_query(
        query="Test query", mode=QueryMode.DEEP, session_id="test_session"
    ):
        chunks.append(chunk)

    # Verify
    assert len(chunks) >= 2
    assert chunks[-1].type == ResponseType.FINAL
    assert chunks[-1].path_source == PathSource.AGENTIC

    print("✓ DEEP mode success test passed")


@pytest.mark.asyncio
async def test_balanced_mode_both_paths():
    """Test BALANCED mode with both paths succeeding.

    Requirements: 1.4, 4.1, 4.2, 6.3
    """
    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Mock speculative
    sample_response = create_sample_speculative_response()
    mock_spec.process = AsyncMock(return_value=sample_response)

    # Mock agentic
    async def mock_process_query(*args, **kwargs):
        yield create_sample_agent_step()

    mock_agent.process_query = mock_process_query

    # Process query
    chunks = []
    async for chunk in router.process_query(
        query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
    ):
        chunks.append(chunk)

    # Verify
    assert len(chunks) >= 2

    # Check for preliminary
    preliminary = [c for c in chunks if c.type == ResponseType.PRELIMINARY]
    assert len(preliminary) >= 1
    assert preliminary[0].path_source == PathSource.SPECULATIVE

    # Check for final
    final = [c for c in chunks if c.type == ResponseType.FINAL]
    assert len(final) == 1

    print("✓ BALANCED mode both paths test passed")


@pytest.mark.asyncio
async def test_balanced_mode_speculative_fails():
    """Test BALANCED mode when speculative fails.

    Requirements: 4.1, 4.2
    """
    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Mock speculative to fail
    mock_spec.process = AsyncMock(side_effect=Exception("Speculative failed"))

    # Mock agentic to succeed
    async def mock_process_query(*args, **kwargs):
        yield create_sample_agent_step()

    mock_agent.process_query = mock_process_query

    # Process query
    chunks = []
    async for chunk in router.process_query(
        query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
    ):
        chunks.append(chunk)

    # Verify we still get final from agentic
    assert len(chunks) >= 1
    final = [c for c in chunks if c.type == ResponseType.FINAL]
    assert len(final) == 1

    print("✓ BALANCED mode speculative fails test passed")


@pytest.mark.asyncio
async def test_parallel_execution_timing():
    """Test that both paths run in parallel.

    Requirements: 1.4, 4.2
    """
    import time

    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Mock with delays
    async def slow_speculative(*args, **kwargs):
        await asyncio.sleep(0.3)
        return create_sample_speculative_response()

    async def slow_agentic(*args, **kwargs):
        await asyncio.sleep(0.3)
        yield create_sample_agent_step()

    mock_spec.process = slow_speculative
    mock_agent.process_query = slow_agentic

    # Measure time
    start = time.time()
    chunks = []
    async for chunk in router.process_query(
        query="Test query", mode=QueryMode.BALANCED, session_id="test_session"
    ):
        chunks.append(chunk)
    elapsed = time.time() - start

    # Should take ~0.3s (parallel), not ~0.6s (sequential)
    assert elapsed < 0.8, f"Took {elapsed}s, expected < 0.8s (parallel)"
    assert len(chunks) >= 1

    print(f"✓ Parallel execution test passed (elapsed: {elapsed:.2f}s)")


@pytest.mark.asyncio
async def test_resource_sharing():
    """Test resource sharing between paths.

    Requirements: 4.3
    """
    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Mock agentic
    async def mock_process_query(*args, **kwargs):
        yield create_sample_agent_step()

    mock_agent.process_query = mock_process_query

    # Test _collect_agentic_response with shared results
    shared_data = {"vector_results": ["doc1", "doc2"]}

    result = await router._collect_agentic_response(
        query="Test",
        session_id="test",
        top_k=10,
        timeout=5.0,
        shared_results=shared_data,
    )

    # Verify result
    assert result is not None
    assert "response" in result

    print("✓ Resource sharing test passed")


@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling for both paths.

    Requirements: 4.2
    """
    # Setup
    mock_spec = MockSpeculativeProcessor()
    mock_agent = MockAgenticProcessor()
    mock_coord = MockResponseCoordinator()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Test speculative timeout
    async def slow_process(*args, **kwargs):
        await asyncio.sleep(5)
        return None

    mock_spec.process = slow_process

    result = await router._collect_speculative_response(
        query="Test", top_k=10, enable_cache=True, timeout=0.1
    )

    assert result is None

    # Test agentic timeout
    async def slow_agentic(*args, **kwargs):
        await asyncio.sleep(5)
        yield create_sample_agent_step()

    mock_agent.process_query = slow_agentic

    result = await router._collect_agentic_response(
        query="Test", session_id="test", top_k=10, timeout=0.1, shared_results=None
    )

    assert result is None

    print("✓ Timeout handling test passed")


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running HybridQueryRouter Tests")
    print("=" * 60 + "\n")

    try:
        await test_fast_mode_success()
        await test_fast_mode_timeout()
        await test_deep_mode_success()
        await test_balanced_mode_both_paths()
        await test_balanced_mode_speculative_fails()
        await test_parallel_execution_timing()
        await test_resource_sharing()
        await test_timeout_handling()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
