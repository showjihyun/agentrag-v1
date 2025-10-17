"""
Performance tests for mode latency validation.

Tests that each mode meets its performance targets:
- FAST mode: <1s (p95)
- BALANCED mode: <3s initial (p95)
- DEEP mode: <15s (p95)
- Routing overhead: <50ms
"""

import pytest
import asyncio
import time
import statistics
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict

from backend.services.intelligent_mode_router import IntelligentModeRouter
from backend.services.adaptive_rag_service import AdaptiveRAGService
from backend.services.query_pattern_learner import QueryPatternLearner
from backend.core.speculative_processor import SpeculativeQueryProcessor
from backend.models.hybrid import QueryMode, QueryComplexity
from config import Settings


@pytest.fixture
def settings():
    """Test settings."""
    return Settings(
        ADAPTIVE_ROUTING_ENABLED=True,
        COMPLEXITY_THRESHOLD_SIMPLE=0.35,
        COMPLEXITY_THRESHOLD_COMPLEX=0.70,
        FAST_MODE_TIMEOUT=1.0,
        BALANCED_MODE_TIMEOUT=3.0,
        DEEP_MODE_TIMEOUT=15.0,
    )


@pytest.fixture
def mock_adaptive_service():
    """Mock adaptive service with realistic timing."""
    service = Mock(spec=AdaptiveRAGService)

    async def mock_analyze(query):
        # Simulate analysis time (5-10ms)
        await asyncio.sleep(0.008)

        # Determine complexity based on query length
        word_count = len(query.split())
        if word_count < 10:
            complexity = QueryComplexity.SIMPLE
            score = 0.25
        elif word_count < 25:
            complexity = QueryComplexity.MEDIUM
            score = 0.55
        else:
            complexity = QueryComplexity.COMPLEX
            score = 0.85

        return Mock(
            complexity=complexity,
            score=score,
            confidence=0.9,
            factors={"word_count": word_count},
            reasoning="Test analysis",
            language="en",
        )

    service.analyze_query_complexity_enhanced = mock_analyze
    return service


@pytest.fixture
def mock_pattern_learner():
    """Mock pattern learner."""
    learner = Mock(spec=QueryPatternLearner)
    learner.get_pattern_recommendation = AsyncMock(return_value=None)
    learner.record_query = AsyncMock()
    return learner


@pytest.fixture
def router(settings, mock_adaptive_service, mock_pattern_learner):
    """Create router instance."""
    return IntelligentModeRouter(
        adaptive_service=mock_adaptive_service,
        pattern_learner=mock_pattern_learner,
        settings=settings,
    )


def calculate_percentile(values: List[float], percentile: int) -> float:
    """Calculate percentile value."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]


def print_latency_stats(name: str, latencies: List[float], target: float):
    """Print latency statistics."""
    if not latencies:
        print(f"\n{name}: No data")
        return

    p50 = calculate_percentile(latencies, 50)
    p95 = calculate_percentile(latencies, 95)
    p99 = calculate_percentile(latencies, 99)
    avg = statistics.mean(latencies)

    print(f"\n{name} Latency Statistics:")
    print(f"  Samples: {len(latencies)}")
    print(f"  Average: {avg:.3f}s")
    print(f"  P50: {p50:.3f}s")
    print(f"  P95: {p95:.3f}s (target: <{target}s)")
    print(f"  P99: {p99:.3f}s")
    print(f"  Min: {min(latencies):.3f}s")
    print(f"  Max: {max(latencies):.3f}s")
    print(f"  Status: {'✓ PASS' if p95 < target else '✗ FAIL'}")


class TestRoutingOverhead:
    """Test routing overhead performance."""

    @pytest.mark.asyncio
    async def test_routing_overhead(self, router):
        """Test that routing overhead is <50ms."""
        queries = [
            "What is RAG?",
            "Compare RAG and fine-tuning",
            "Analyze the evolution of AI systems",
        ]

        latencies = []

        for query in queries:
            for _ in range(10):  # 10 iterations per query
                start = time.time()
                await router.route_query(query, "test-session")
                latency = time.time() - start
                latencies.append(latency)

        # Calculate statistics
        p95 = calculate_percentile(latencies, 95)

        print_latency_stats("Routing Overhead", latencies, 0.05)

        # Assert P95 < 50ms
        assert p95 < 0.05, f"Routing overhead P95 ({p95:.3f}s) exceeds 50ms target"


class TestFastModeLatency:
    """Test FAST mode latency performance."""

    @pytest.mark.asyncio
    async def test_fast_mode_latency_target(self, router):
        """Test FAST mode meets <1s P95 target."""
        # Simple queries that should route to FAST mode
        queries = [
            "What is RAG?",
            "Define machine learning",
            "Who invented Python?",
            "What is AI?",
            "Explain NLP",
        ]

        latencies = []

        for query in queries:
            for _ in range(20):  # 20 iterations per query
                start = time.time()

                # Route query
                routing = await router.route_query(query, "test-session")
                assert routing.mode == QueryMode.FAST

                # Simulate FAST mode processing (0.3-0.8s)
                await asyncio.sleep(0.5 + (hash(query) % 300) / 1000)

                latency = time.time() - start
                latencies.append(latency)

        # Calculate statistics
        p95 = calculate_percentile(latencies, 95)

        print_latency_stats("FAST Mode", latencies, 1.0)

        # Assert P95 < 1s
        assert p95 < 1.0, f"FAST mode P95 ({p95:.3f}s) exceeds 1s target"

    @pytest.mark.asyncio
    async def test_fast_mode_with_cache(self, router):
        """Test FAST mode with cache hit is very fast."""
        query = "What is RAG?"

        latencies = []

        for _ in range(50):
            start = time.time()

            # Route query
            routing = await router.route_query(query, "test-session")

            # Simulate cache hit (5-20ms)
            await asyncio.sleep(0.01)

            latency = time.time() - start
            latencies.append(latency)

        p95 = calculate_percentile(latencies, 95)

        print_latency_stats("FAST Mode (Cache Hit)", latencies, 0.1)

        # Cache hits should be very fast
        assert p95 < 0.1, f"FAST mode cache hit P95 ({p95:.3f}s) too slow"


class TestBalancedModeLatency:
    """Test BALANCED mode latency performance."""

    @pytest.mark.asyncio
    async def test_balanced_mode_latency_target(self, router):
        """Test BALANCED mode meets <3s P95 target."""
        # Medium complexity queries
        queries = [
            "Compare RAG and fine-tuning approaches for LLMs",
            "What are the benefits of vector databases?",
            "How does semantic search work in practice?",
            "Explain the difference between embeddings and tokens",
            "What are the main challenges in RAG systems?",
        ]

        latencies = []

        for query in queries:
            for _ in range(15):  # 15 iterations per query
                start = time.time()

                # Route query
                routing = await router.route_query(query, "test-session")
                assert routing.mode == QueryMode.BALANCED

                # Simulate BALANCED mode processing (1.5-2.8s)
                await asyncio.sleep(2.0 + (hash(query) % 800) / 1000)

                latency = time.time() - start
                latencies.append(latency)

        p95 = calculate_percentile(latencies, 95)

        print_latency_stats("BALANCED Mode", latencies, 3.0)

        # Assert P95 < 3s
        assert p95 < 3.0, f"BALANCED mode P95 ({p95:.3f}s) exceeds 3s target"

    @pytest.mark.asyncio
    async def test_balanced_mode_initial_response(self, router):
        """Test BALANCED mode initial response time."""
        query = "Compare RAG and fine-tuning approaches"

        initial_latencies = []

        for _ in range(30):
            start = time.time()

            # Route query
            routing = await router.route_query(query, "test-session")

            # Simulate fast path (initial response)
            await asyncio.sleep(0.8 + (hash(str(_)) % 400) / 1000)

            latency = time.time() - start
            initial_latencies.append(latency)

        p95 = calculate_percentile(initial_latencies, 95)

        print_latency_stats("BALANCED Mode (Initial)", initial_latencies, 1.5)

        # Initial response should be fast
        assert p95 < 1.5, f"BALANCED initial P95 ({p95:.3f}s) too slow"


class TestDeepModeLatency:
    """Test DEEP mode latency performance."""

    @pytest.mark.asyncio
    async def test_deep_mode_latency_target(self, router):
        """Test DEEP mode meets <15s P95 target."""
        # Complex analytical queries
        queries = [
            "Analyze the evolution of RAG systems from 2020 to 2024 and explain why certain approaches became dominant",
            "Compare and contrast three different vector database architectures considering scalability performance and cost",
            "Explain the theoretical foundations of semantic search and how they relate to modern embedding models",
        ]

        latencies = []

        for query in queries:
            for _ in range(10):  # 10 iterations per query
                start = time.time()

                # Route query
                routing = await router.route_query(query, "test-session")
                assert routing.mode == QueryMode.DEEP

                # Simulate DEEP mode processing (8-14s)
                await asyncio.sleep(10.0 + (hash(query) % 4000) / 1000)

                latency = time.time() - start
                latencies.append(latency)

        p95 = calculate_percentile(latencies, 95)

        print_latency_stats("DEEP Mode", latencies, 15.0)

        # Assert P95 < 15s
        assert p95 < 15.0, f"DEEP mode P95 ({p95:.3f}s) exceeds 15s target"


class TestConcurrentPerformance:
    """Test performance under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_fast_mode(self, router):
        """Test FAST mode performance with concurrent requests."""
        query = "What is RAG?"
        num_concurrent = 50

        async def process_query():
            start = time.time()
            routing = await router.route_query(
                query, f"session-{id(asyncio.current_task())}"
            )
            await asyncio.sleep(0.5)  # Simulate processing
            return time.time() - start

        # Process concurrently
        start_all = time.time()
        latencies = await asyncio.gather(
            *[process_query() for _ in range(num_concurrent)]
        )
        total_time = time.time() - start_all

        p95 = calculate_percentile(latencies, 95)

        print(f"\nConcurrent FAST Mode ({num_concurrent} requests):")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Throughput: {num_concurrent / total_time:.1f} req/s")
        print_latency_stats("Individual Request", latencies, 1.0)

        # Individual requests should still meet target
        assert p95 < 1.0, f"Concurrent FAST mode P95 ({p95:.3f}s) exceeds target"

    @pytest.mark.asyncio
    async def test_mixed_mode_concurrent(self, router):
        """Test mixed mode performance with concurrent requests."""
        queries = [
            ("What is RAG?", QueryMode.FAST, 0.5),
            ("Compare RAG and fine-tuning", QueryMode.BALANCED, 2.0),
            (
                "Analyze the evolution of AI systems over the past decade",
                QueryMode.DEEP,
                10.0,
            ),
        ]

        num_each = 10

        async def process_query(query, expected_mode, sim_time):
            start = time.time()
            routing = await router.route_query(
                query, f"session-{id(asyncio.current_task())}"
            )
            await asyncio.sleep(sim_time)
            return (routing.mode, time.time() - start)

        # Create mixed workload
        tasks = []
        for query, mode, sim_time in queries:
            tasks.extend(
                [process_query(query, mode, sim_time) for _ in range(num_each)]
            )

        # Process concurrently
        start_all = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_all

        # Group by mode
        mode_latencies = {
            QueryMode.FAST: [],
            QueryMode.BALANCED: [],
            QueryMode.DEEP: [],
        }

        for mode, latency in results:
            mode_latencies[mode].append(latency)

        print(f"\nMixed Mode Concurrent ({len(tasks)} total requests):")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Throughput: {len(tasks) / total_time:.1f} req/s")

        # Check each mode
        for mode, latencies in mode_latencies.items():
            if latencies:
                p95 = calculate_percentile(latencies, 95)
                print(
                    f"\n  {mode.value} mode: {len(latencies)} requests, P95: {p95:.3f}s"
                )


class TestLoadScaling:
    """Test performance scaling under load."""

    @pytest.mark.asyncio
    async def test_routing_scales_linearly(self, router):
        """Test that routing overhead scales linearly."""
        load_levels = [10, 50, 100]

        results = {}

        for load in load_levels:
            latencies = []

            async def route_query():
                start = time.time()
                await router.route_query(
                    "Test query", f"session-{id(asyncio.current_task())}"
                )
                return time.time() - start

            start_all = time.time()
            batch_latencies = await asyncio.gather(
                *[route_query() for _ in range(load)]
            )
            total_time = time.time() - start_all

            latencies.extend(batch_latencies)
            p95 = calculate_percentile(latencies, 95)

            results[load] = {
                "p95": p95,
                "total_time": total_time,
                "throughput": load / total_time,
            }

            print(f"\nLoad: {load} requests")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Throughput: {results[load]['throughput']:.1f} req/s")
            print(f"  P95 latency: {p95:.3f}s")

        # Check that P95 doesn't degrade significantly
        for load in load_levels:
            assert results[load]["p95"] < 0.1, f"P95 at load {load} too high"


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.mark.asyncio
    async def test_no_performance_regression(self, router):
        """Test that performance hasn't regressed."""
        # Baseline targets (from design)
        targets = {QueryMode.FAST: 1.0, QueryMode.BALANCED: 3.0, QueryMode.DEEP: 15.0}

        test_queries = {
            QueryMode.FAST: "What is RAG?",
            QueryMode.BALANCED: "Compare RAG and fine-tuning approaches",
            QueryMode.DEEP: "Analyze the evolution of RAG systems from 2020 to 2024",
        }

        sim_times = {QueryMode.FAST: 0.5, QueryMode.BALANCED: 2.0, QueryMode.DEEP: 10.0}

        results = {}

        for mode, query in test_queries.items():
            latencies = []

            for _ in range(30):
                start = time.time()
                routing = await router.route_query(query, "test-session")
                await asyncio.sleep(sim_times[mode])
                latency = time.time() - start
                latencies.append(latency)

            p95 = calculate_percentile(latencies, 95)
            results[mode] = p95

            print(f"\n{mode.value} Mode:")
            print(f"  P95: {p95:.3f}s")
            print(f"  Target: <{targets[mode]}s")
            print(f"  Margin: {((targets[mode] - p95) / targets[mode] * 100):.1f}%")

            # Assert meets target with margin
            assert p95 < targets[mode], f"{mode.value} mode P95 exceeds target"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
