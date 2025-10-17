"""
Standalone unit tests for error handling and fallback mechanisms.

Tests cover:
- Speculative path failure scenarios
- Agentic path failure scenarios
- Timeout handling
- LLM unavailability fallback
- Graceful degradation

Requirements: 8.1, 8.2, 8.3, 8.4, 8.6
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

# Also add parent directory for 'backend' module imports
parent_dir = os.path.abspath(os.path.join(backend_dir, ".."))
sys.path.insert(0, parent_dir)

import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime


def test_speculative_processor_llm_fallback():
    """Test that SpeculativeProcessor formats raw documents when LLM fails."""
    from services.speculative_processor import SpeculativeProcessor
    from services.milvus import SearchResult

    # Create processor with mocked dependencies
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
            text="This is content from document 1 with important information.",
            score=0.9,
            chunk_index=0,
            metadata={},
        ),
        SearchResult(
            id="doc2",
            document_id="doc2",
            document_name="Test Doc 2",
            text="This is content from document 2 with more details.",
            score=0.8,
            chunk_index=0,
            metadata={},
        ),
    ]

    result = processor._format_raw_documents_fallback(
        query="test query", search_results=search_results
    )

    # Verify fallback response
    assert result is not None
    assert len(result) > 0
    assert "Test Doc 1" in result
    assert "Test Doc 2" in result
    assert "relevant document" in result.lower()
    assert "excerpt" in result.lower() or "note" in result.lower()

    print("✓ Test passed: LLM fallback formats raw documents correctly")


def test_speculative_processor_llm_fallback_no_results():
    """Test fallback when no documents are found."""
    from services.speculative_processor import SpeculativeProcessor

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

    # Verify helpful message
    assert result is not None
    assert len(result) > 0
    assert "no relevant" in result.lower() or "found no" in result.lower()

    print("✓ Test passed: LLM fallback handles no results correctly")


async def test_hybrid_router_speculative_timeout():
    """Test that HybridQueryRouter handles speculative timeout gracefully."""
    from services.hybrid_query_router import HybridQueryRouter
    from models.hybrid import QueryMode, ResponseType

    # Create mocks
    mock_spec = Mock()
    mock_spec.process = AsyncMock(side_effect=asyncio.TimeoutError())

    mock_agent = Mock()
    mock_coord = Mock()
    mock_coord._merge_responses = Mock(return_value=("Merged", 0.8))
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
        default_speculative_timeout=2.0,
        default_agentic_timeout=15.0,
    )

    # Process query in FAST mode
    chunks = []
    async for chunk in router.process_query(
        query="test query", mode=QueryMode.FAST, session_id="test_session"
    ):
        chunks.append(chunk)

    # Verify error handling
    assert len(chunks) == 1
    assert chunks[0].type == ResponseType.FINAL
    assert chunks[0].confidence_score == 0.0
    assert "longer than expected" in chunks[0].content.lower()
    assert chunks[0].metadata.get("error") == "timeout"

    print("✓ Test passed: Speculative timeout handled correctly")


async def test_hybrid_router_speculative_exception():
    """Test that HybridQueryRouter handles speculative exceptions gracefully."""
    from services.hybrid_query_router import HybridQueryRouter
    from models.hybrid import QueryMode, ResponseType

    # Create mocks
    mock_spec = Mock()
    mock_spec.process = AsyncMock(side_effect=Exception("Vector DB failed"))

    mock_agent = Mock()
    mock_coord = Mock()
    mock_coord._merge_responses = Mock(return_value=("Merged", 0.8))
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Process query in FAST mode
    chunks = []
    async for chunk in router.process_query(
        query="test query", mode=QueryMode.FAST, session_id="test_session"
    ):
        chunks.append(chunk)

    # Verify error handling
    assert len(chunks) == 1
    assert chunks[0].type == ResponseType.FINAL
    assert chunks[0].confidence_score == 0.0
    assert "error occurred" in chunks[0].content.lower()

    print("✓ Test passed: Speculative exception handled correctly")


async def test_hybrid_router_agentic_timeout():
    """Test that HybridQueryRouter handles agentic timeout with partial results."""
    from services.hybrid_query_router import HybridQueryRouter
    from models.hybrid import QueryMode, ResponseType
    from models.agent import AgentStep

    # Create mocks
    mock_spec = Mock()

    async def mock_agentic_generator():
        yield AgentStep(
            step_id="step1", type="thought", content="Analyzing...", metadata={}
        )
        # Simulate long-running operation
        await asyncio.sleep(20)

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Process query in DEEP mode with short timeout
    chunks = []
    async for chunk in router.process_query(
        query="test query",
        mode=QueryMode.DEEP,
        session_id="test_session",
        agentic_timeout=0.1,
    ):
        chunks.append(chunk)

    # Verify partial results handling
    assert len(chunks) >= 1
    final_chunk = chunks[-1]
    assert final_chunk.type == ResponseType.FINAL
    # Should indicate partial results or timeout
    has_timeout_indicator = (
        "partial" in final_chunk.content.lower()
        or final_chunk.metadata.get("timeout")
        or final_chunk.metadata.get("partial_results")
    )
    assert has_timeout_indicator

    print("✓ Test passed: Agentic timeout returns partial results")


async def test_hybrid_router_both_paths_fail():
    """Test that HybridQueryRouter provides clear error when both paths fail."""
    from services.hybrid_query_router import HybridQueryRouter
    from models.hybrid import QueryMode, ResponseType

    # Create mocks - both fail
    mock_spec = Mock()
    mock_spec.process = AsyncMock(side_effect=Exception("Speculative failed"))

    async def mock_agentic_generator():
        raise Exception("Agentic failed")
        yield  # Never reached

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()
    mock_coord._merge_responses = Mock(return_value=("Merged", 0.8))
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Process query in BALANCED mode
    chunks = []
    async for chunk in router.process_query(
        query="test query", mode=QueryMode.BALANCED, session_id="test_session"
    ):
        chunks.append(chunk)

    # Verify error handling
    assert len(chunks) >= 1
    final_chunk = chunks[-1]
    assert final_chunk.type == ResponseType.FINAL
    assert final_chunk.confidence_score == 0.0
    # Should have clear error message
    assert (
        "unable" in final_chunk.content.lower()
        or "error" in final_chunk.content.lower()
    )

    print("✓ Test passed: Both paths failure handled correctly")


async def test_hybrid_router_graceful_degradation_spec_fails():
    """Test graceful degradation when speculative fails but agentic succeeds."""
    from services.hybrid_query_router import HybridQueryRouter
    from models.hybrid import QueryMode, ResponseType, PathSource
    from models.agent import AgentStep

    # Speculative fails
    mock_spec = Mock()
    mock_spec.process = AsyncMock(side_effect=Exception("Speculative failed"))

    # Agentic succeeds
    async def mock_agentic_generator():
        yield AgentStep(
            step_id="step1",
            type="response",
            content="Agentic response",
            metadata={"sources": []},
        )

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()
    mock_coord._merge_responses = Mock(return_value=("Agentic response", 0.85))
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Process query in BALANCED mode
    chunks = []
    async for chunk in router.process_query(
        query="test query", mode=QueryMode.BALANCED, session_id="test_session"
    ):
        chunks.append(chunk)

    # Should get agentic results (graceful degradation)
    assert len(chunks) >= 1
    final_chunk = chunks[-1]
    assert final_chunk.type == ResponseType.FINAL
    # Should use agentic path since speculative failed
    assert final_chunk.path_source in [PathSource.AGENTIC, PathSource.HYBRID]

    print("✓ Test passed: Graceful degradation to agentic-only works")


async def test_hybrid_router_graceful_degradation_agentic_fails():
    """Test graceful degradation when agentic fails but speculative succeeds."""
    from services.hybrid_query_router import HybridQueryRouter
    from models.hybrid import QueryMode, ResponseType, PathSource, SpeculativeResponse

    # Speculative succeeds
    mock_spec = Mock()
    mock_spec.process = AsyncMock(
        return_value=SpeculativeResponse(
            response="Speculative response",
            confidence_score=0.7,
            sources=[],
            cache_hit=False,
            processing_time=0.5,
            metadata={},
        )
    )

    # Agentic fails
    async def mock_agentic_generator():
        raise Exception("Agentic failed")
        yield  # Never reached

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()
    mock_coord._merge_responses = Mock(return_value=("Speculative response", 0.7))
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    # Process query in BALANCED mode
    chunks = []
    async for chunk in router.process_query(
        query="test query", mode=QueryMode.BALANCED, session_id="test_session"
    ):
        chunks.append(chunk)

    # Should get speculative results (graceful degradation)
    assert len(chunks) >= 1
    # Should have preliminary chunk
    preliminary_chunks = [c for c in chunks if c.type == ResponseType.PRELIMINARY]
    assert len(preliminary_chunks) > 0
    # Final chunk should use speculative path
    final_chunk = chunks[-1]
    assert final_chunk.path_source in [PathSource.SPECULATIVE, PathSource.HYBRID]

    print("✓ Test passed: Graceful degradation to speculative-only works")


def run_async_test(test_func):
    """Helper to run async tests."""
    asyncio.run(test_func())


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Running Error Handling Tests")
    print("=" * 70 + "\n")

    # Synchronous tests
    print("Testing LLM Fallback...")
    test_speculative_processor_llm_fallback()
    test_speculative_processor_llm_fallback_no_results()

    # Asynchronous tests
    print("\nTesting Timeout Handling...")
    run_async_test(test_hybrid_router_speculative_timeout)
    run_async_test(test_hybrid_router_agentic_timeout)

    print("\nTesting Exception Handling...")
    run_async_test(test_hybrid_router_speculative_exception)
    run_async_test(test_hybrid_router_both_paths_fail)

    print("\nTesting Graceful Degradation...")
    run_async_test(test_hybrid_router_graceful_degradation_spec_fails)
    run_async_test(test_hybrid_router_graceful_degradation_agentic_fails)

    print("\n" + "=" * 70)
    print("All Error Handling Tests Passed! ✓")
    print("=" * 70 + "\n")
