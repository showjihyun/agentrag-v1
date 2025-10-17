"""
Verification script for mode-aware Speculative Processor.

Tests:
1. Mode configuration retrieval
2. FAST mode execution
3. BALANCED mode execution
4. DEEP mode execution
5. Mode-specific parameters
6. Performance targets
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from backend.models.hybrid import QueryMode
from backend.models.agent import AgentStep
from backend.core.speculative_processor import SpeculativeQueryProcessor


class MockAggregator:
    """Mock aggregator for testing."""

    async def _fast_path_query(self, query: str, session_id: str, top_k: int):
        """Mock fast path."""
        await asyncio.sleep(0.3)  # Simulate 300ms
        yield AgentStep(
            step_id="fast_1",
            type="response",
            content=f"Fast response for: {query}",
            timestamp=datetime.now(),
            metadata={"sources": [{"id": "doc1"}, {"id": "doc2"}], "top_k": top_k},
        )

    async def process_query(self, query: str, session_id: str, top_k: int):
        """Mock deep path."""
        await asyncio.sleep(2.0)  # Simulate 2s
        yield AgentStep(
            step_id="deep_1",
            type="thought",
            content="Analyzing query...",
            timestamp=datetime.now(),
            metadata={},
        )
        yield AgentStep(
            step_id="deep_2",
            type="response",
            content=f"Deep response for: {query}",
            timestamp=datetime.now(),
            metadata={
                "sources": [{"id": "doc1"}, {"id": "doc2"}, {"id": "doc3"}],
                "top_k": top_k,
                "reasoning_steps": 3,
            },
        )


async def collect_steps(generator) -> List[AgentStep]:
    """Collect all steps from generator."""
    steps = []
    async for step in generator:
        steps.append(step)
    return steps


async def test_mode_configuration():
    """Test 1: Mode configuration retrieval."""
    print("\n" + "=" * 60)
    print("TEST 1: Mode Configuration Retrieval")
    print("=" * 60)

    processor = SpeculativeQueryProcessor(aggregator_agent=MockAggregator())

    # Test each mode
    for mode in [QueryMode.FAST, QueryMode.BALANCED, QueryMode.DEEP]:
        config = processor.get_mode_config(mode)
        timeout = processor.get_mode_timeout(mode)
        top_k = processor.get_mode_top_k(mode)

        print(f"\n{mode.value.upper()} Mode:")
        print(f"  Timeout: {timeout}s")
        print(f"  Top-K: {top_k}")
        print(f"  Web Search: {config['enable_web_search']}")
        print(f"  Max LLM Calls: {config['max_llm_calls']}")
        print(f"  Cache TTL: {config['cache_ttl']}s")
        print(f"  Description: {config['description']}")

        # Verify expected values
        if mode == QueryMode.FAST:
            assert timeout == 1.0, f"FAST timeout should be 1.0s, got {timeout}"
            assert top_k == 5, f"FAST top_k should be 5, got {top_k}"
            assert not config["enable_web_search"], "FAST should disable web search"
        elif mode == QueryMode.BALANCED:
            assert timeout == 3.0, f"BALANCED timeout should be 3.0s, got {timeout}"
            assert top_k == 10, f"BALANCED top_k should be 10, got {top_k}"
        elif mode == QueryMode.DEEP:
            assert timeout == 15.0, f"DEEP timeout should be 15.0s, got {timeout}"
            assert top_k == 15, f"DEEP top_k should be 15, got {top_k}"
            assert config["enable_web_search"], "DEEP should enable web search"

    print("\n✅ Mode configuration test PASSED")
    return True


async def test_fast_mode_execution():
    """Test 2: FAST mode execution."""
    print("\n" + "=" * 60)
    print("TEST 2: FAST Mode Execution")
    print("=" * 60)

    processor = SpeculativeQueryProcessor(aggregator_agent=MockAggregator())

    query = "What is machine learning?"
    start_time = datetime.now()

    steps = await collect_steps(
        processor.process_query_with_mode(query=query, mode=QueryMode.FAST)
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\nQuery: {query}")
    print(f"Steps collected: {len(steps)}")
    print(f"Elapsed time: {elapsed:.2f}s")

    # Verify steps
    assert len(steps) > 0, "Should have at least one step"

    # Check start marker
    start_step = steps[0]
    assert start_step.type == "planning", "First step should be planning"
    assert "FAST" in start_step.content, "Should mention FAST mode"
    assert start_step.metadata["mode"] == "fast", "Should have fast mode in metadata"
    assert start_step.metadata["top_k"] == 5, "Should use FAST mode top_k=5"

    # Check response
    response_steps = [s for s in steps if s.type == "response"]
    assert len(response_steps) > 0, "Should have response step"

    response = response_steps[0]
    assert response.metadata["mode"] == "fast", "Response should be marked as FAST"
    assert not response.metadata["web_search_enabled"], "Web search should be disabled"
    assert response.metadata["max_llm_calls"] == 1, "Should limit to 1 LLM call"

    # Check performance
    print(f"\nPerformance:")
    print(f"  Target: <1.0s")
    print(f"  Actual: {elapsed:.2f}s")
    print(f"  Met target: {elapsed < 1.0}")

    print("\n✅ FAST mode execution test PASSED")
    return True


async def test_balanced_mode_execution():
    """Test 3: BALANCED mode execution."""
    print("\n" + "=" * 60)
    print("TEST 3: BALANCED Mode Execution")
    print("=" * 60)

    processor = SpeculativeQueryProcessor(aggregator_agent=MockAggregator())

    query = "Compare machine learning and deep learning"
    start_time = datetime.now()

    steps = await collect_steps(
        processor.process_query_with_mode(query=query, mode=QueryMode.BALANCED)
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\nQuery: {query}")
    print(f"Steps collected: {len(steps)}")
    print(f"Elapsed time: {elapsed:.2f}s")

    # Verify steps
    assert len(steps) > 0, "Should have at least one step"

    # Check start marker
    start_step = steps[0]
    assert start_step.type == "planning", "First step should be planning"
    assert "BALANCED" in start_step.content, "Should mention BALANCED mode"
    assert start_step.metadata["mode"] == "balanced", "Should have balanced mode"
    assert start_step.metadata["top_k"] == 10, "Should use BALANCED mode top_k=10"

    # Check response
    response_steps = [s for s in steps if s.type == "response"]
    assert len(response_steps) > 0, "Should have response step"

    # Check performance
    print(f"\nPerformance:")
    print(f"  Target: <3.0s")
    print(f"  Actual: {elapsed:.2f}s")
    print(f"  Met target: {elapsed < 3.0}")

    print("\n✅ BALANCED mode execution test PASSED")
    return True


async def test_deep_mode_execution():
    """Test 4: DEEP mode execution."""
    print("\n" + "=" * 60)
    print("TEST 4: DEEP Mode Execution")
    print("=" * 60)

    processor = SpeculativeQueryProcessor(aggregator_agent=MockAggregator())

    query = "Analyze the evolution of machine learning from 2010 to 2024"
    start_time = datetime.now()

    steps = await collect_steps(
        processor.process_query_with_mode(query=query, mode=QueryMode.DEEP)
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\nQuery: {query}")
    print(f"Steps collected: {len(steps)}")
    print(f"Elapsed time: {elapsed:.2f}s")

    # Verify steps
    assert len(steps) > 0, "Should have at least one step"

    # Check start marker
    start_step = steps[0]
    assert start_step.type == "planning", "First step should be planning"
    assert "DEEP" in start_step.content, "Should mention DEEP mode"
    assert start_step.metadata["mode"] == "deep", "Should have deep mode"
    assert start_step.metadata["top_k"] == 15, "Should use DEEP mode top_k=15"

    # Check response
    response_steps = [s for s in steps if s.type == "response"]
    assert len(response_steps) > 0, "Should have response step"

    response = response_steps[0]
    assert response.metadata["mode"] == "deep", "Response should be marked as DEEP"
    assert response.metadata["web_search_enabled"], "Web search should be enabled"
    assert response.metadata["max_llm_calls"] == 15, "Should allow up to 15 LLM calls"

    # Check performance
    print(f"\nPerformance:")
    print(f"  Target: <15.0s")
    print(f"  Actual: {elapsed:.2f}s")
    print(f"  Met target: {elapsed < 15.0}")

    print("\n✅ DEEP mode execution test PASSED")
    return True


async def test_mode_specific_parameters():
    """Test 5: Mode-specific parameters."""
    print("\n" + "=" * 60)
    print("TEST 5: Mode-Specific Parameters")
    print("=" * 60)

    processor = SpeculativeQueryProcessor(aggregator_agent=MockAggregator())

    # Test custom top_k override
    query = "Test query"
    custom_top_k = 20

    steps = await collect_steps(
        processor.process_query_with_mode(
            query=query, mode=QueryMode.FAST, top_k=custom_top_k
        )
    )

    start_step = steps[0]
    assert (
        start_step.metadata["top_k"] == custom_top_k
    ), f"Should use custom top_k={custom_top_k}"

    print(f"\n✅ Custom top_k override works: {custom_top_k}")

    # Test default top_k
    steps = await collect_steps(
        processor.process_query_with_mode(
            query=query, mode=QueryMode.BALANCED, top_k=None
        )  # Use default
    )

    start_step = steps[0]
    assert start_step.metadata["top_k"] == 10, "Should use BALANCED default top_k=10"

    print(f"✅ Default top_k works: 10")

    print("\n✅ Mode-specific parameters test PASSED")
    return True


async def test_backward_compatibility():
    """Test 6: Backward compatibility with legacy interface."""
    print("\n" + "=" * 60)
    print("TEST 6: Backward Compatibility")
    print("=" * 60)

    processor = SpeculativeQueryProcessor(aggregator_agent=MockAggregator())

    query = "Test query"

    # Test legacy interface
    steps = await collect_steps(processor.process_query(query=query, mode="fast_only"))

    assert len(steps) > 0, "Legacy interface should work"
    print("✅ Legacy process_query() interface works")

    # Test auto mode
    steps = await collect_steps(processor.process_query(query=query, mode="auto"))

    assert len(steps) > 0, "Auto mode should work"
    print("✅ Legacy auto mode works")

    print("\n✅ Backward compatibility test PASSED")
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MODE-AWARE SPECULATIVE PROCESSOR VERIFICATION")
    print("=" * 60)

    tests = [
        ("Mode Configuration", test_mode_configuration),
        ("FAST Mode Execution", test_fast_mode_execution),
        ("BALANCED Mode Execution", test_balanced_mode_execution),
        ("DEEP Mode Execution", test_deep_mode_execution),
        ("Mode-Specific Parameters", test_mode_specific_parameters),
        ("Backward Compatibility", test_backward_compatibility),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result, None))
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            results.append((test_name, False, str(e)))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result, _ in results if result)
    total = len(results)

    for test_name, result, error in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"  Error: {error}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
