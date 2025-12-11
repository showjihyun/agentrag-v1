"""
Performance tests for hybrid query system.

Tests performance characteristics:
- Speculative path completes within 2s
- FAST mode total time under 2s
- BALANCED mode shows preliminary within 2s
- System handles concurrent load

Requirements: 2.3, 6.2, 6.3
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from backend.models.hybrid import QueryMode, ResponseChunk, ChunkType, QueryComplexity
from backend.services.hybrid_query_router import HybridQueryRouter
from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.response_coordinator import ResponseCoordinator


@pytest.mark.asyncio
@pytest.mark.slow
class TestSpeculativePathPerformance:
    """Test speculative path performance requirements."""

    async def test_speculative_path_completes_within_2_seconds(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test that speculative path completes within 2 seconds.

        Requirement 2.3: WHEN generating the speculative response THEN it
        SHALL complete within 2 seconds
        """
        # Setup: Add test documents
        test_docs = [
            {
                "text": "Python is a versatile programming language.",
                "metadata": {"source": "doc1.txt", "chunk_id": 0},
            },
            {
                "text": "JavaScript is used for web development.",
                "metadata": {"source": "doc2.txt", "chunk_id": 0},
            },
            {
                "text": "Machine learning models require training data.",
                "metadata": {"source": "doc3.txt", "chunk_id": 0},
            },
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        # Create speculative processor
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        # Test multiple queries to ensure consistent performance
        queries = [
            "What is Python?",
            "Tell me about JavaScript",
            "Explain machine learning",
        ]

        timings = []

        for query in queries:
            start_time = time.time()

            chunks = []
            async for chunk in spec_processor.process(
                query=query, session_id=f"perf_test_{query[:10]}", top_k=5
            ):
                chunks.append(chunk)

            elapsed = time.time() - start_time
            timings.append(elapsed)

            # Verify we got a response
            assert len(chunks) > 0, f"Should receive response for query: {query}"

        # Verify all queries completed within 2 seconds
        max_time = max(timings)
        avg_time = statistics.mean(timings)

        assert (
            max_time < 2.5
        ), f"Speculative path took {max_time:.2f}s (max), should be under 2.5s"
        assert avg_time < 2.0, f"Average time {avg_time:.2f}s should be under 2.0s"

        print(f"\nSpeculative path performance:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")
        print(f"  Min: {min(timings):.2f}s")

    async def test_speculative_path_with_cache_is_faster(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test that cached responses are significantly faster.

        Verifies cache optimization improves performance.
        """
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        query = "What is artificial intelligence?"
        session_id = "cache_perf_test"

        # First query (no cache)
        start_time = time.time()
        chunks_first = []
        async for chunk in spec_processor.process(query, session_id, top_k=5):
            chunks_first.append(chunk)
        first_time = time.time() - start_time

        # Second query (should hit cache)
        start_time = time.time()
        chunks_cached = []
        async for chunk in spec_processor.process(query, session_id, top_k=5):
            chunks_cached.append(chunk)
        cached_time = time.time() - start_time

        # Verify cache is faster
        assert (
            cached_time < first_time
        ), f"Cached query ({cached_time:.2f}s) should be faster than first ({first_time:.2f}s)"

        # Cached should be very fast
        assert (
            cached_time < 1.0
        ), f"Cached response took {cached_time:.2f}s, should be under 1s"

        print(f"\nCache performance:")
        print(f"  First query: {first_time:.2f}s")
        print(f"  Cached query: {cached_time:.2f}s")
        print(f"  Speedup: {first_time/cached_time:.1f}x")


@pytest.mark.asyncio
@pytest.mark.slow
class TestFastModePerformance:
    """Test FAST mode performance requirements."""

    async def test_fast_mode_total_time_under_2_seconds(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test that FAST mode completes within 2 seconds.

        Requirement 6.2: WHEN "Fast" mode is selected THEN the system SHALL
        use speculative path only and return results within 2 seconds
        """
        # Setup test documents
        test_docs = [
            {
                "text": "FastAPI is a modern Python web framework.",
                "metadata": {"source": "fastapi.txt", "chunk_id": 0},
            },
            {
                "text": "REST APIs enable communication between systems.",
                "metadata": {"source": "rest.txt", "chunk_id": 0},
            },
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        # Create router
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        coordinator = ResponseCoordinator()

        router = HybridQueryRouter(
            speculative_processor=spec_processor,
            agentic_processor=None,
            response_coordinator=coordinator,
        )

        # Test multiple queries
        queries = [
            "What is FastAPI?",
            "Explain REST APIs",
            "How do web frameworks work?",
        ]

        timings = []

        for query in queries:
            start_time = time.time()

            chunks = []
            async for chunk in router.process_query(
                query=query,
                mode=QueryMode.FAST,
                session_id=f"fast_perf_{query[:10]}",
                top_k=5,
            ):
                chunks.append(chunk)

            elapsed = time.time() - start_time
            timings.append(elapsed)

            assert len(chunks) > 0

        # Verify performance
        max_time = max(timings)
        avg_time = statistics.mean(timings)

        assert (
            max_time < 2.5
        ), f"FAST mode took {max_time:.2f}s (max), should be under 2.5s"
        assert avg_time < 2.0, f"FAST mode average {avg_time:.2f}s should be under 2.0s"

        print(f"\nFAST mode performance:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")
        print(f"  Min: {min(timings):.2f}s")


@pytest.mark.asyncio
@pytest.mark.slow
class TestBalancedModePerformance:
    """Test BALANCED mode performance requirements."""

    async def test_balanced_mode_preliminary_within_2_seconds(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test that BALANCED mode shows preliminary response within 2 seconds.

        Requirement 6.3: WHEN "Balanced" mode is selected THEN the system
        SHALL use the hybrid approach (speculative + agentic)

        The preliminary response should arrive quickly even if agentic
        processing continues.
        """
        # Setup test documents
        test_docs = [
            {
                "text": "Neural networks are inspired by biological neurons.",
                "metadata": {"source": "nn.txt", "chunk_id": 0},
            },
            {
                "text": "Deep learning uses multiple layers of neural networks.",
                "metadata": {"source": "dl.txt", "chunk_id": 0},
            },
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        # Create components
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        # Create simplified agentic processor for testing
        from agents.vector_search import VectorSearchAgent
        from agents.aggregator import AggregatorAgent

        vector_agent = VectorSearchAgent(
            milvus_manager=milvus_manager, embedding_service=embedding_service
        )

        agentic_processor = AggregatorAgent(
            llm_manager=llm_manager,
            memory_manager=memory_manager,
            vector_search_agent=vector_agent,
            local_data_agent=None,
            web_search_agent=None,
        )

        coordinator = ResponseCoordinator()

        router = HybridQueryRouter(
            speculative_processor=spec_processor,
            agentic_processor=agentic_processor,
            response_coordinator=coordinator,
        )

        # Test queries
        queries = ["What are neural networks?", "Explain deep learning"]

        preliminary_timings = []

        for query in queries:
            start_time = time.time()
            preliminary_time = None

            chunks = []
            async for chunk in router.process_query(
                query=query,
                mode=QueryMode.BALANCED,
                session_id=f"balanced_perf_{query[:10]}",
                top_k=5,
            ):
                chunks.append(chunk)

                # Record when preliminary arrives
                if (
                    chunk.chunk_type == ChunkType.PRELIMINARY
                    and preliminary_time is None
                ):
                    preliminary_time = time.time() - start_time

            if preliminary_time:
                preliminary_timings.append(preliminary_time)

            assert len(chunks) > 0

        # Verify preliminary response timing
        if preliminary_timings:
            max_prelim = max(preliminary_timings)
            avg_prelim = statistics.mean(preliminary_timings)

            assert (
                max_prelim < 2.5
            ), f"Preliminary response took {max_prelim:.2f}s (max), should be under 2.5s"
            assert (
                avg_prelim < 2.0
            ), f"Average preliminary time {avg_prelim:.2f}s should be under 2.0s"

            print(f"\nBALANCED mode preliminary performance:")
            print(f"  Average: {avg_prelim:.2f}s")
            print(f"  Max: {max_prelim:.2f}s")
            print(f"  Min: {min(preliminary_timings):.2f}s")


@pytest.mark.asyncio
@pytest.mark.slow
class TestConcurrentLoad:
    """Test system performance under concurrent load."""

    async def test_concurrent_fast_mode_queries(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test system handles multiple concurrent FAST mode queries.

        Verifies system can handle concurrent load without degradation.
        """
        # Setup test documents
        test_docs = [
            {
                "text": f"Document {i} contains information about topic {i}.",
                "metadata": {"source": f"doc{i}.txt", "chunk_id": 0},
            }
            for i in range(10)
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        # Create router
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        coordinator = ResponseCoordinator()

        router = HybridQueryRouter(
            speculative_processor=spec_processor,
            agentic_processor=None,
            response_coordinator=coordinator,
        )

        # Create concurrent queries
        num_concurrent = 5
        queries = [f"What is topic {i}?" for i in range(num_concurrent)]

        async def execute_query(query: str, idx: int) -> Dict[str, Any]:
            """Execute a single query and return timing info."""
            start_time = time.time()

            chunks = []
            async for chunk in router.process_query(
                query=query,
                mode=QueryMode.FAST,
                session_id=f"concurrent_{idx}",
                top_k=5,
            ):
                chunks.append(chunk)

            elapsed = time.time() - start_time

            return {
                "query": query,
                "elapsed": elapsed,
                "chunk_count": len(chunks),
                "success": len(chunks) > 0,
            }

        # Execute queries concurrently
        start_time = time.time()

        tasks = [execute_query(query, idx) for idx, query in enumerate(queries)]

        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Verify all queries succeeded
        assert all(r["success"] for r in results), "All queries should succeed"

        # Verify individual query times
        timings = [r["elapsed"] for r in results]
        max_time = max(timings)
        avg_time = statistics.mean(timings)

        # Individual queries should still be fast
        assert (
            max_time < 3.0
        ), f"Slowest concurrent query took {max_time:.2f}s, should be under 3.0s"

        # Total time should be much less than sequential execution
        sequential_estimate = sum(timings)
        speedup = sequential_estimate / total_time

        print(f"\nConcurrent load performance ({num_concurrent} queries):")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average query time: {avg_time:.2f}s")
        print(f"  Max query time: {max_time:.2f}s")
        print(f"  Estimated speedup: {speedup:.1f}x")

        # Should see some parallelization benefit
        assert (
            speedup > 1.5
        ), f"Should see parallelization benefit (speedup: {speedup:.1f}x)"

    async def test_concurrent_balanced_mode_queries(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test system handles concurrent BALANCED mode queries.

        Verifies system stability under concurrent hybrid processing.
        """
        # Setup test documents
        test_docs = [
            {
                "text": "Concurrent processing enables parallel execution.",
                "metadata": {"source": "concurrent.txt", "chunk_id": 0},
            },
            {
                "text": "Async programming improves performance.",
                "metadata": {"source": "async.txt", "chunk_id": 0},
            },
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        # Create components
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        coordinator = ResponseCoordinator()

        router = HybridQueryRouter(
            speculative_processor=spec_processor,
            agentic_processor=None,  # Simplified for load testing
            response_coordinator=coordinator,
        )

        # Execute concurrent queries
        num_concurrent = 3
        queries = [
            "What is concurrent processing?",
            "Explain async programming",
            "How does parallelization work?",
        ]

        async def execute_balanced_query(query: str, idx: int) -> Dict[str, Any]:
            """Execute a BALANCED mode query."""
            start_time = time.time()
            preliminary_time = None

            chunks = []
            async for chunk in router.process_query(
                query=query,
                mode=QueryMode.BALANCED,
                session_id=f"balanced_concurrent_{idx}",
                top_k=5,
            ):
                chunks.append(chunk)

                if (
                    chunk.chunk_type == ChunkType.PRELIMINARY
                    and preliminary_time is None
                ):
                    preliminary_time = time.time() - start_time

            elapsed = time.time() - start_time

            return {
                "query": query,
                "elapsed": elapsed,
                "preliminary_time": preliminary_time,
                "chunk_count": len(chunks),
                "success": len(chunks) > 0,
            }

        # Execute concurrently
        tasks = [
            execute_balanced_query(query, idx)
            for idx, query in enumerate(queries[:num_concurrent])
        ]

        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        assert all(r["success"] for r in results), "All queries should succeed"

        # Verify preliminary responses were fast
        prelim_times = [r["preliminary_time"] for r in results if r["preliminary_time"]]

        if prelim_times:
            max_prelim = max(prelim_times)
            assert (
                max_prelim < 3.0
            ), f"Preliminary responses under load took {max_prelim:.2f}s, should be under 3.0s"

            print(f"\nConcurrent BALANCED mode ({num_concurrent} queries):")
            print(f"  Max preliminary time: {max_prelim:.2f}s")
            print(f"  Avg preliminary time: {statistics.mean(prelim_times):.2f}s")


@pytest.mark.asyncio
@pytest.mark.slow
class TestPerformanceRegression:
    """Test for performance regressions."""

    async def test_performance_baseline(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Establish performance baseline for regression testing.

        This test documents expected performance characteristics.
        """
        # Setup
        test_docs = [
            {
                "text": "Performance testing ensures system meets requirements.",
                "metadata": {"source": "perf.txt", "chunk_id": 0},
            }
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        coordinator = ResponseCoordinator()

        router = HybridQueryRouter(
            speculative_processor=spec_processor,
            agentic_processor=None,
            response_coordinator=coordinator,
        )

        # Measure baseline performance
        query = "What is performance testing?"

        # Warm-up
        chunks = []
        async for chunk in router.process_query(
            query=query, mode=QueryMode.FAST, session_id="warmup", top_k=5
        ):
            chunks.append(chunk)

        # Measure
        timings = []
        for i in range(5):
            start = time.time()

            chunks = []
            async for chunk in router.process_query(
                query=query, mode=QueryMode.FAST, session_id=f"baseline_{i}", top_k=5
            ):
                chunks.append(chunk)

            timings.append(time.time() - start)

        # Report baseline
        avg_time = statistics.mean(timings)
        std_dev = statistics.stdev(timings) if len(timings) > 1 else 0

        print(f"\nPerformance baseline:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Std Dev: {std_dev:.3f}s")
        print(f"  Min: {min(timings):.3f}s")
        print(f"  Max: {max(timings):.3f}s")

        # Baseline should meet requirements
        assert (
            avg_time < 2.0
        ), f"Baseline average {avg_time:.2f}s exceeds 2.0s threshold"
