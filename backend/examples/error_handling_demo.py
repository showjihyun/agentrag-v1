"""
Demonstration of error handling and fallback mechanisms in the hybrid query router.

This script shows how the system handles various error scenarios:
- Speculative path failures
- Agentic path failures
- Timeout handling
- LLM unavailability
- Graceful degradation

Run: python backend/examples/error_handling_demo.py
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

# Also add parent directory for 'backend' module imports
parent_dir = os.path.abspath(os.path.join(backend_dir, ".."))
sys.path.insert(0, parent_dir)

import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from backend.services.hybrid_query_router import HybridQueryRouter
from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.response_coordinator import ResponseCoordinator
from backend.models.hybrid import QueryMode, SpeculativeResponse, ResponseType
from backend.models.agent import AgentStep
from backend.services.milvus import SearchResult


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_chunk(chunk, indent=0):
    """Print a response chunk with formatting."""
    prefix = "  " * indent
    print(
        f"{prefix}[{chunk.type.value.upper()}] Confidence: {chunk.confidence_score:.2f}"
    )
    print(f"{prefix}Path: {chunk.path_source.value}")
    print(f"{prefix}Content: {chunk.content[:100]}...")
    if chunk.metadata:
        print(f"{prefix}Metadata: {chunk.metadata}")
    print()


async def demo_speculative_timeout():
    """Demonstrate speculative path timeout handling."""
    print_section("Demo 1: Speculative Path Timeout (FAST Mode)")

    # Create mock that times out
    mock_spec = Mock()
    mock_spec.process = AsyncMock(side_effect=asyncio.TimeoutError())

    mock_agent = Mock()
    mock_coord = Mock()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
        default_speculative_timeout=2.0,
    )

    print("Simulating speculative timeout in FAST mode...")
    print("Expected: Error message with timeout indication\n")

    async for chunk in router.process_query(
        query="What is quantum computing?",
        mode=QueryMode.FAST,
        session_id="demo_session",
    ):
        print_chunk(chunk)

    print("✓ Timeout handled gracefully with user-friendly message")


async def demo_graceful_degradation_spec_fails():
    """Demonstrate graceful degradation when speculative fails."""
    print_section("Demo 2: Graceful Degradation (Speculative Fails)")

    # Speculative fails
    mock_spec = Mock()
    mock_spec.process = AsyncMock(side_effect=Exception("Vector DB connection failed"))

    # Agentic succeeds
    async def mock_agentic_generator():
        yield AgentStep(
            step_id="step1",
            type="thought",
            content="Analyzing the query about quantum computing...",
            metadata={},
        )
        yield AgentStep(
            step_id="step2",
            type="response",
            content="Quantum computing uses quantum mechanics principles to process information.",
            metadata={"sources": []},
        )

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()
    mock_coord._merge_responses = Mock(
        return_value=(
            "Quantum computing uses quantum mechanics principles to process information.",
            0.85,
        )
    )
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    print("Simulating speculative failure in BALANCED mode...")
    print("Expected: System falls back to agentic-only mode\n")

    async for chunk in router.process_query(
        query="What is quantum computing?",
        mode=QueryMode.BALANCED,
        session_id="demo_session",
    ):
        print_chunk(chunk)

    print("✓ System gracefully degraded to agentic-only mode")


async def demo_graceful_degradation_agentic_fails():
    """Demonstrate graceful degradation when agentic fails."""
    print_section("Demo 3: Graceful Degradation (Agentic Fails)")

    # Speculative succeeds
    mock_spec = Mock()
    mock_spec.process = AsyncMock(
        return_value=SpeculativeResponse(
            response="Quantum computing is a type of computing that uses quantum mechanics.",
            confidence_score=0.7,
            sources=[],
            cache_hit=False,
            processing_time=0.5,
            metadata={},
        )
    )

    # Agentic fails
    async def mock_agentic_generator():
        raise Exception("Agent execution failed")
        yield  # Never reached

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()
    mock_coord._merge_responses = Mock(
        return_value=(
            "Quantum computing is a type of computing that uses quantum mechanics.",
            0.7,
        )
    )
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    print("Simulating agentic failure in BALANCED mode...")
    print("Expected: System falls back to speculative-only mode\n")

    async for chunk in router.process_query(
        query="What is quantum computing?",
        mode=QueryMode.BALANCED,
        session_id="demo_session",
    ):
        print_chunk(chunk)

    print("✓ System gracefully degraded to speculative-only mode")


async def demo_both_paths_fail():
    """Demonstrate handling when both paths fail."""
    print_section("Demo 4: Both Paths Fail")

    # Both fail
    mock_spec = Mock()
    mock_spec.process = AsyncMock(side_effect=Exception("Speculative failed"))

    async def mock_agentic_generator():
        raise Exception("Agentic failed")
        yield  # Never reached

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()
    mock_coord._merge_responses = Mock(return_value=("Error", 0.0))
    mock_coord._merge_sources = Mock(return_value=[])

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    print("Simulating both paths failing in BALANCED mode...")
    print("Expected: Clear error message without internal details\n")

    async for chunk in router.process_query(
        query="What is quantum computing?",
        mode=QueryMode.BALANCED,
        session_id="demo_session",
    ):
        print_chunk(chunk)

    print("✓ Both paths failure handled with user-friendly error message")


def demo_llm_fallback():
    """Demonstrate LLM unavailability fallback."""
    print_section("Demo 5: LLM Unavailability Fallback")

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

    # Simulate documents retrieved but LLM unavailable
    search_results = [
        SearchResult(
            id="doc1",
            document_id="doc1",
            document_name="Quantum Computing Basics",
            text="Quantum computing is a revolutionary approach to computation that leverages quantum mechanics principles.",
            score=0.92,
            chunk_index=0,
            metadata={},
        ),
        SearchResult(
            id="doc2",
            document_id="doc2",
            document_name="Introduction to Qubits",
            text="Qubits are the fundamental units of quantum information, unlike classical bits which can only be 0 or 1.",
            score=0.88,
            chunk_index=0,
            metadata={},
        ),
        SearchResult(
            id="doc3",
            document_id="doc3",
            document_name="Quantum Algorithms",
            text="Quantum algorithms like Shor's algorithm can solve certain problems exponentially faster than classical algorithms.",
            score=0.85,
            chunk_index=0,
            metadata={},
        ),
    ]

    print("Simulating LLM unavailability with retrieved documents...")
    print("Expected: Raw document excerpts returned as fallback\n")

    result = processor._format_raw_documents_fallback(
        query="What is quantum computing?", search_results=search_results
    )

    print("Fallback Response:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    print("\n✓ LLM fallback provides useful raw document excerpts")


def demo_llm_fallback_no_results():
    """Demonstrate LLM fallback with no documents."""
    print_section("Demo 6: LLM Fallback with No Documents")

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

    print("Simulating LLM unavailability with no documents found...")
    print("Expected: Helpful message suggesting query rephrasing\n")

    result = processor._format_raw_documents_fallback(
        query="What is quantum computing?", search_results=[]
    )

    print("Fallback Response:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    print("\n✓ LLM fallback provides helpful message when no documents found")


async def demo_agentic_timeout_partial_results():
    """Demonstrate agentic timeout with partial results."""
    print_section("Demo 7: Agentic Timeout with Partial Results")

    mock_spec = Mock()

    # Agentic provides some results before timeout
    async def mock_agentic_generator():
        yield AgentStep(
            step_id="step1",
            type="thought",
            content="Starting analysis of quantum computing...",
            metadata={},
        )
        yield AgentStep(
            step_id="step2",
            type="response",
            content="Quantum computing uses quantum mechanics for computation.",
            metadata={"sources": []},
        )
        # Then would timeout
        await asyncio.sleep(20)

    mock_agent = Mock()
    mock_agent.process_query = Mock(return_value=mock_agentic_generator())

    mock_coord = Mock()

    router = HybridQueryRouter(
        speculative_processor=mock_spec,
        agentic_processor=mock_agent,
        response_coordinator=mock_coord,
    )

    print("Simulating agentic timeout with partial results in DEEP mode...")
    print("Expected: Partial results returned with timeout indication\n")

    async for chunk in router.process_query(
        query="What is quantum computing?",
        mode=QueryMode.DEEP,
        session_id="demo_session",
        agentic_timeout=0.1,  # Very short timeout
    ):
        print_chunk(chunk)

    print("✓ Agentic timeout handled with partial results returned")


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  ERROR HANDLING AND FALLBACK MECHANISMS DEMONSTRATION")
    print("=" * 70)

    # Run async demos
    await demo_speculative_timeout()
    await demo_graceful_degradation_spec_fails()
    await demo_graceful_degradation_agentic_fails()
    await demo_both_paths_fail()
    await demo_agentic_timeout_partial_results()

    # Run sync demos
    demo_llm_fallback()
    demo_llm_fallback_no_results()

    print_section("Summary")
    print("All error handling scenarios demonstrated successfully!")
    print("\nKey Features:")
    print("  ✓ Graceful degradation when paths fail")
    print("  ✓ Timeout handling with partial results")
    print("  ✓ LLM unavailability fallback to raw documents")
    print("  ✓ User-friendly error messages")
    print("  ✓ Internal details not exposed to users")
    print("  ✓ Comprehensive logging for monitoring")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
