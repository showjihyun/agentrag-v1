"""
Integration test for Task 12: DEEP Mode Parallel Agent Execution

Tests the complete integration of parallel execution with the aggregator agent.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from backend.agents.aggregator_optimized import AggregatorAgentOptimized
from backend.config import settings


class MockVectorAgent:
    """Mock vector search agent."""

    async def search(self, query: str, top_k: int = 10):
        await asyncio.sleep(0.3)
        return [
            type(
                "obj",
                (object,),
                {
                    "text": f"Vector result {i}",
                    "score": 0.9 - i * 0.1,
                    "document_id": f"doc_{i}",
                    "document_name": f"document_{i}.pdf",
                },
            )()
            for i in range(min(top_k, 5))
        ]


class MockWebAgent:
    """Mock web search agent."""

    async def search(self, query: str, max_results: int = 5):
        await asyncio.sleep(0.4)
        return [f"Web result {i}" for i in range(max_results)]


class MockLocalAgent:
    """Mock local data agent."""

    async def read_file(self, path: str):
        await asyncio.sleep(0.2)
        return f"Content of {path}"


class MockLLM:
    """Mock LLM manager."""

    async def generate(self, messages, **kwargs):
        await asyncio.sleep(0.1)
        return "This is a test response."


class MockMemory:
    """Mock memory manager."""

    async def get_context_for_query(self, session_id: str, query: str):
        return type(
            "obj", (object,), {"to_dict": lambda: {"history": [], "patterns": []}}
        )()

    async def consolidate_memory(self, **kwargs):
        pass


@pytest.fixture
def aggregator_parallel():
    """Create aggregator with parallel execution enabled."""
    return AggregatorAgentOptimized(
        llm_manager=MockLLM(),
        memory_manager=MockMemory(),
        vector_agent=MockVectorAgent(),
        local_agent=MockLocalAgent(),
        search_agent=MockWebAgent(),
        max_iterations=10,
        enable_parallel=True,
        parallel_timeout=5.0,
        max_parallel_workers=3,
    )


@pytest.fixture
def aggregator_sequential():
    """Create aggregator with parallel execution disabled."""
    return AggregatorAgentOptimized(
        llm_manager=MockLLM(),
        memory_manager=MockMemory(),
        vector_agent=MockVectorAgent(),
        local_agent=MockLocalAgent(),
        search_agent=MockWebAgent(),
        max_iterations=10,
        enable_parallel=False,
    )


@pytest.mark.asyncio
async def test_parallel_execution_enabled(aggregator_parallel):
    """Test that parallel execution is properly enabled."""
    assert aggregator_parallel.enable_parallel is True
    assert aggregator_parallel.parallel_timeout == 5.0
    assert aggregator_parallel.max_parallel_workers == 3


@pytest.mark.asyncio
async def test_independent_action_detection(aggregator_parallel):
    """Test independent action detection."""
    # Test independent actions
    assert aggregator_parallel._is_independent("vector_search", ["web_search"]) is True
    assert aggregator_parallel._is_independent("vector_search", ["local_data"]) is True
    assert aggregator_parallel._is_independent("web_search", ["local_data"]) is True

    # Test dependent actions
    assert (
        aggregator_parallel._is_independent("vector_search", ["vector_search"]) is False
    )
    assert aggregator_parallel._is_independent("web_search", ["synthesis"]) is False


@pytest.mark.asyncio
async def test_parallel_execution_performance(aggregator_parallel):
    """Test that parallel execution is faster than sequential."""
    state = {"query": "test query", "retrieved_docs": [], "action_history": []}

    actions = [
        ("vector_search", {"query": "test", "top_k": 5}),
        ("web_search", {"query": "test", "max_results": 3}),
    ]

    # Measure parallel execution time
    import time

    start = time.time()
    results = await aggregator_parallel._execute_parallel_with_timeout(actions, state)
    parallel_time = time.time() - start

    # Verify results
    assert len(results) == 2
    assert all(error is None for _, _, error in results)

    # Verify it's faster than sequential (0.3 + 0.4 = 0.7s)
    assert parallel_time < 0.6  # Should be ~0.4s (max of parallel operations)


@pytest.mark.asyncio
async def test_initial_parallel_retrieval(aggregator_parallel):
    """Test initial parallel retrieval."""
    state = {"query": "test complex query", "retrieved_docs": [], "action_history": []}

    steps = []
    async for step in aggregator_parallel._initial_parallel_retrieval(
        "test query", state, top_k=5
    ):
        steps.append(step)

    # Verify steps were generated
    assert len(steps) > 0

    # Verify parallel execution metadata
    parallel_steps = [s for s in steps if s.metadata.get("parallel")]
    assert len(parallel_steps) > 0

    # Verify actions were recorded
    assert len(state["action_history"]) > 0


@pytest.mark.asyncio
async def test_result_merging(aggregator_parallel):
    """Test result merging and deduplication."""
    results1 = [
        type("obj", (object,), {"text": "Result A", "score": 0.9})(),
        type("obj", (object,), {"text": "Result B", "score": 0.8})(),
    ]

    results2 = [
        type("obj", (object,), {"text": "Result A", "score": 0.85})(),  # Duplicate
        type("obj", (object,), {"text": "Result C", "score": 0.75})(),
    ]

    merged = await aggregator_parallel._merge_parallel_results(
        [results1, results2], max_results=10
    )

    # Verify deduplication (should have 3 unique results)
    assert len(merged) == 3


@pytest.mark.asyncio
async def test_graceful_degradation(aggregator_parallel):
    """Test graceful degradation on agent failure."""

    class FailingAgent:
        async def search(self, query: str, **kwargs):
            raise Exception("Agent failed")

    # Replace one agent with failing agent
    aggregator_parallel.web_agent = FailingAgent()

    state = {"query": "test query", "retrieved_docs": [], "action_history": []}

    actions = [
        ("vector_search", {"query": "test", "top_k": 5}),
        ("web_search", {"query": "test", "max_results": 3}),
    ]

    # Should not raise exception due to graceful degradation
    results = await aggregator_parallel._execute_parallel_with_timeout(actions, state)

    # Verify we got results (one success, one failure)
    assert len(results) == 2

    # Verify one succeeded and one failed
    successes = [r for r in results if r[2] is None]
    failures = [r for r in results if r[2] is not None]

    assert len(successes) == 1
    assert len(failures) == 1


@pytest.mark.asyncio
async def test_timeout_protection(aggregator_parallel):
    """Test timeout protection for slow agents."""

    class SlowAgent:
        async def search(self, query: str, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            return []

    # Replace agent with slow agent
    aggregator_parallel.web_agent = SlowAgent()
    aggregator_parallel.parallel_timeout = 1.0  # Short timeout

    state = {"query": "test query", "retrieved_docs": [], "action_history": []}

    actions = [
        ("vector_search", {"query": "test", "top_k": 5}),
        ("web_search", {"query": "test", "max_results": 3}),
    ]

    import time

    start = time.time()
    results = await aggregator_parallel._execute_parallel_with_timeout(actions, state)
    elapsed = time.time() - start

    # Should complete within timeout
    assert elapsed < 2.0

    # Verify timeout was caught
    timeouts = [r for r in results if isinstance(r[2], TimeoutError)]
    assert len(timeouts) == 1


@pytest.mark.asyncio
async def test_complex_query_uses_parallel(aggregator_parallel):
    """Test that complex queries trigger parallel execution."""
    # Complex query (should trigger parallel execution)
    complex_query = "Analyze and compare the evolution of RAG systems from 2020 to 2024"

    complexity = aggregator_parallel._analyze_query_complexity(complex_query)
    assert complexity == "complex"


@pytest.mark.asyncio
async def test_simple_query_skips_parallel(aggregator_parallel):
    """Test that simple queries skip parallel execution."""
    # Simple query (should not trigger parallel execution)
    simple_query = "What is RAG?"

    complexity = aggregator_parallel._analyze_query_complexity(simple_query)
    assert complexity == "simple"


@pytest.mark.asyncio
async def test_configuration_from_settings():
    """Test that configuration is properly loaded from settings."""
    aggregator = AggregatorAgentOptimized(
        llm_manager=MockLLM(),
        memory_manager=MockMemory(),
        vector_agent=MockVectorAgent(),
        local_agent=MockLocalAgent(),
        search_agent=MockWebAgent(),
        enable_parallel=settings.ENABLE_PARALLEL_AGENTS,
        parallel_timeout=settings.PARALLEL_AGENT_TIMEOUT,
        max_parallel_workers=settings.PARALLEL_MAX_WORKERS,
    )

    assert aggregator.enable_parallel == settings.ENABLE_PARALLEL_AGENTS
    assert aggregator.parallel_timeout == settings.PARALLEL_AGENT_TIMEOUT
    assert aggregator.max_parallel_workers == settings.PARALLEL_MAX_WORKERS


@pytest.mark.asyncio
async def test_parallel_vs_sequential_performance():
    """Test performance difference between parallel and sequential execution."""
    # Create both aggregators
    parallel_agg = AggregatorAgentOptimized(
        llm_manager=MockLLM(),
        memory_manager=MockMemory(),
        vector_agent=MockVectorAgent(),
        local_agent=MockLocalAgent(),
        search_agent=MockWebAgent(),
        enable_parallel=True,
    )

    sequential_agg = AggregatorAgentOptimized(
        llm_manager=MockLLM(),
        memory_manager=MockMemory(),
        vector_agent=MockVectorAgent(),
        local_agent=MockLocalAgent(),
        search_agent=MockWebAgent(),
        enable_parallel=False,
    )

    state = {"query": "test query", "retrieved_docs": [], "action_history": []}

    actions = [
        ("vector_search", {"query": "test", "top_k": 5}),
        ("web_search", {"query": "test", "max_results": 3}),
    ]

    # Measure parallel execution
    import time

    start = time.time()
    await parallel_agg._execute_parallel_with_timeout(actions, state)
    parallel_time = time.time() - start

    # Sequential would take 0.3 + 0.4 = 0.7s
    sequential_time = 0.7

    # Verify parallel is faster
    speedup = sequential_time / parallel_time
    assert speedup > 1.3  # At least 30% faster


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
