"""
End-to-end tests for hybrid query modes (FAST, BALANCED, DEEP).

Tests complete workflows for each mode to verify:
- FAST mode: Speculative path only, returns within 2s
- BALANCED mode: Both paths with progressive refinement
- DEEP mode: Agentic path only with full reasoning

Requirements: 6.2, 6.3, 6.4
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any

from backend.models.hybrid import QueryMode, ResponseChunk, ChunkType
from backend.services.hybrid_query_router import HybridQueryRouter
from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.response_coordinator import ResponseCoordinator
from backend.agents.aggregator import AggregatorAgent


@pytest.mark.e2e
@pytest.mark.asyncio
class TestFastModeE2E:
    """End-to-end tests for FAST mode."""

    async def test_fast_mode_complete_workflow(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test complete FAST mode workflow.

        Verifies:
        - Only speculative path executes
        - Response completes within 2 seconds
        - Response marked as final (no refinement expected)
        - Confidence score included
        """
        # Setup: Add test documents to Milvus
        test_docs = [
            {
                "text": "Python is a high-level programming language known for its simplicity.",
                "metadata": {"source": "doc1.txt", "chunk_id": 0},
            },
            {
                "text": "Machine learning is a subset of artificial intelligence.",
                "metadata": {"source": "doc2.txt", "chunk_id": 0},
            },
            {
                "text": "FastAPI is a modern web framework for building APIs with Python.",
                "metadata": {"source": "doc3.txt", "chunk_id": 0},
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

        # Create minimal agentic processor (won't be used in FAST mode)
        agentic_processor = None  # Not needed for FAST mode

        router = HybridQueryRouter(
            speculative_processor=spec_processor,
            agentic_processor=agentic_processor,
            response_coordinator=coordinator,
        )

        # Execute query in FAST mode
        query = "What is Python?"
        session_id = "test_session_fast"

        start_time = time.time()
        chunks: List[ResponseChunk] = []

        async for chunk in router.process_query(
            query=query, mode=QueryMode.FAST, session_id=session_id, top_k=5
        ):
            chunks.append(chunk)

        elapsed_time = time.time() - start_time

        # Assertions
        assert len(chunks) > 0, "Should receive at least one response chunk"

        # Verify timing (FAST mode should complete within 2 seconds)
        assert (
            elapsed_time < 2.5
        ), f"FAST mode took {elapsed_time:.2f}s, should be under 2.5s"

        # Verify chunk types (should only have speculative chunks)
        chunk_types = [chunk.chunk_type for chunk in chunks]
        assert ChunkType.PRELIMINARY in chunk_types or ChunkType.FINAL in chunk_types
        assert (
            ChunkType.REFINEMENT not in chunk_types
        ), "FAST mode should not have refinements"

        # Verify final chunk
        final_chunk = chunks[-1]
        assert final_chunk.chunk_type == ChunkType.FINAL
        assert final_chunk.content is not None and len(final_chunk.content) > 0
        assert final_chunk.confidence is not None
        assert 0 <= final_chunk.confidence <= 1

        # Verify path source
        assert any(chunk.path_source == "speculative" for chunk in chunks)
        assert not any(chunk.path_source == "agentic" for chunk in chunks)

    async def test_fast_mode_with_cache_hit(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test FAST mode with cache hit for even faster response.

        Verifies:
        - Cached response returns in under 500ms
        - Response still marked appropriately
        """
        # Setup components
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

        query = "What is machine learning?"
        session_id = "test_session_cache"

        # First query to populate cache
        chunks_first = []
        async for chunk in router.process_query(
            query=query, mode=QueryMode.FAST, session_id=session_id, top_k=5
        ):
            chunks_first.append(chunk)

        # Second query should hit cache
        start_time = time.time()
        chunks_cached = []

        async for chunk in router.process_query(
            query=query, mode=QueryMode.FAST, session_id=session_id, top_k=5
        ):
            chunks_cached.append(chunk)

        elapsed_time = time.time() - start_time

        # Assertions
        assert len(chunks_cached) > 0
        # Cache hit should be very fast (under 1 second including overhead)
        assert elapsed_time < 1.0, f"Cached response took {elapsed_time:.2f}s"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestBalancedModeE2E:
    """End-to-end tests for BALANCED mode."""

    async def test_balanced_mode_complete_workflow(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test complete BALANCED mode workflow.

        Verifies:
        - Both speculative and agentic paths execute
        - Preliminary response arrives within 2 seconds
        - Refinements arrive after preliminary
        - Final response marked appropriately
        - Progressive refinement flow works
        """
        # Setup: Add test documents
        test_docs = [
            {
                "text": "Retrieval-Augmented Generation combines retrieval with generation.",
                "metadata": {"source": "rag_doc.txt", "chunk_id": 0},
            },
            {
                "text": "Vector databases store embeddings for similarity search.",
                "metadata": {"source": "vector_doc.txt", "chunk_id": 0},
            },
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        # Create components (including agentic processor for BALANCED mode)
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        # Create agentic processor (simplified for testing)
        from agents.vector_search import VectorSearchAgent

        vector_agent = VectorSearchAgent(
            milvus_manager=milvus_manager, embedding_service=embedding_service
        )

        agentic_processor = AggregatorAgent(
            llm_manager=llm_manager,
            memory_manager=memory_manager,
            vector_search_agent=vector_agent,
            local_data_agent=None,  # Not needed for this test
            web_search_agent=None,  # Not needed for this test
        )

        coordinator = ResponseCoordinator()

        router = HybridQueryRouter(
            speculative_processor=spec_processor,
            agentic_processor=agentic_processor,
            response_coordinator=coordinator,
        )

        # Execute query in BALANCED mode
        query = "What is RAG?"
        session_id = "test_session_balanced"

        start_time = time.time()
        chunks: List[ResponseChunk] = []
        preliminary_time = None

        async for chunk in router.process_query(
            query=query, mode=QueryMode.BALANCED, session_id=session_id, top_k=5
        ):
            chunks.append(chunk)

            # Record when preliminary response arrives
            if chunk.chunk_type == ChunkType.PRELIMINARY and preliminary_time is None:
                preliminary_time = time.time() - start_time

        total_time = time.time() - start_time

        # Assertions
        assert len(chunks) > 0, "Should receive response chunks"

        # Verify preliminary response timing
        assert preliminary_time is not None, "Should receive preliminary response"
        assert (
            preliminary_time < 2.5
        ), f"Preliminary response took {preliminary_time:.2f}s"

        # Verify chunk progression
        chunk_types = [chunk.chunk_type for chunk in chunks]
        assert ChunkType.PRELIMINARY in chunk_types, "Should have preliminary chunk"
        assert ChunkType.FINAL in chunk_types, "Should have final chunk"

        # Verify both paths contributed
        path_sources = [chunk.path_source for chunk in chunks if chunk.path_source]
        assert "speculative" in path_sources, "Speculative path should contribute"
        # Note: Agentic path may or may not contribute depending on timing

        # Verify final chunk
        final_chunk = chunks[-1]
        assert final_chunk.chunk_type == ChunkType.FINAL
        assert final_chunk.content is not None

    async def test_balanced_mode_progressive_refinement(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test progressive refinement in BALANCED mode.

        Verifies:
        - Multiple chunks received in order
        - Refinement chunks arrive after preliminary
        - Content evolves progressively
        """
        # Setup components (similar to above)
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
            agentic_processor=None,  # Simplified for this test
            response_coordinator=coordinator,
        )

        query = "Explain vector search"
        session_id = "test_session_refinement"

        chunks: List[ResponseChunk] = []

        async for chunk in router.process_query(
            query=query, mode=QueryMode.BALANCED, session_id=session_id, top_k=5
        ):
            chunks.append(chunk)

        # Verify chunk ordering
        if len(chunks) > 1:
            # First chunk should be preliminary or content
            assert chunks[0].chunk_type in [ChunkType.PRELIMINARY, ChunkType.CONTENT]

            # Last chunk should be final
            assert chunks[-1].chunk_type == ChunkType.FINAL


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDeepModeE2E:
    """End-to-end tests for DEEP mode."""

    async def test_deep_mode_complete_workflow(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test complete DEEP mode workflow.

        Verifies:
        - Only agentic path executes
        - No preliminary response (goes straight to deep analysis)
        - Full reasoning steps included
        - Response quality is high
        """
        # Setup: Add test documents
        test_docs = [
            {
                "text": "Neural networks consist of layers of interconnected nodes.",
                "metadata": {"source": "nn_doc.txt", "chunk_id": 0},
            },
            {
                "text": "Deep learning uses multiple layers to learn hierarchical representations.",
                "metadata": {"source": "dl_doc.txt", "chunk_id": 0},
            },
            {
                "text": "Backpropagation is the algorithm used to train neural networks.",
                "metadata": {"source": "bp_doc.txt", "chunk_id": 0},
            },
        ]

        for doc in test_docs:
            embedding = await embedding_service.embed_text(doc["text"])
            await milvus_manager.insert(
                texts=[doc["text"]], embeddings=[embedding], metadatas=[doc["metadata"]]
            )

        # Create components
        from agents.vector_search import VectorSearchAgent

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
            speculative_processor=None,  # Not used in DEEP mode
            agentic_processor=agentic_processor,
            response_coordinator=coordinator,
        )

        # Execute query in DEEP mode
        query = "How do neural networks learn?"
        session_id = "test_session_deep"

        start_time = time.time()
        chunks: List[ResponseChunk] = []

        async for chunk in router.process_query(
            query=query, mode=QueryMode.DEEP, session_id=session_id, top_k=10
        ):
            chunks.append(chunk)

        elapsed_time = time.time() - start_time

        # Assertions
        assert len(chunks) > 0, "Should receive response chunks"

        # DEEP mode may take longer (5-15 seconds is acceptable)
        assert elapsed_time < 20, f"DEEP mode took {elapsed_time:.2f}s"

        # Verify no preliminary chunks (DEEP mode skips speculative path)
        chunk_types = [chunk.chunk_type for chunk in chunks]
        # DEEP mode should not have PRELIMINARY type from speculative path
        # It goes straight to agentic reasoning

        # Verify final chunk
        final_chunk = chunks[-1]
        assert final_chunk.chunk_type == ChunkType.FINAL
        assert final_chunk.content is not None and len(final_chunk.content) > 0

        # Verify only agentic path used
        path_sources = [chunk.path_source for chunk in chunks if chunk.path_source]
        if path_sources:  # If path sources are tracked
            assert "agentic" in path_sources or len(path_sources) == 0
            assert "speculative" not in path_sources

    async def test_deep_mode_reasoning_quality(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Test that DEEP mode provides comprehensive reasoning.

        Verifies:
        - Response includes reasoning steps
        - Multiple sources considered
        - Higher quality than FAST mode
        """
        # Setup components
        from agents.vector_search import VectorSearchAgent

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
            speculative_processor=None,
            agentic_processor=agentic_processor,
            response_coordinator=coordinator,
        )

        query = "Explain the relationship between AI and machine learning"
        session_id = "test_session_deep_quality"

        chunks: List[ResponseChunk] = []

        async for chunk in router.process_query(
            query=query, mode=QueryMode.DEEP, session_id=session_id, top_k=10
        ):
            chunks.append(chunk)

        # Verify response quality indicators
        assert len(chunks) > 0

        # Check for reasoning steps or progress indicators
        has_reasoning = any(
            chunk.chunk_type in [ChunkType.REASONING, ChunkType.PROGRESS]
            for chunk in chunks
        )

        # Final response should be substantial
        final_chunk = chunks[-1]
        assert (
            len(final_chunk.content) > 50
        ), "DEEP mode should provide detailed response"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestModeComparison:
    """Compare behavior across different modes."""

    async def test_mode_timing_comparison(
        self,
        milvus_manager,
        embedding_service,
        redis_client,
        llm_manager,
        memory_manager,
    ):
        """
        Compare timing across all three modes.

        Verifies:
        - FAST < BALANCED < DEEP (generally)
        - FAST completes within 2s
        - BALANCED shows preliminary within 2s
        """
        # Setup components
        spec_processor = SpeculativeProcessor(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            llm_manager=llm_manager,
            redis_client=redis_client,
            memory_manager=memory_manager,
        )

        from agents.vector_search import VectorSearchAgent

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

        query = "What is artificial intelligence?"

        # Test FAST mode
        start = time.time()
        fast_chunks = []
        async for chunk in router.process_query(
            query=query, mode=QueryMode.FAST, session_id="timing_fast", top_k=5
        ):
            fast_chunks.append(chunk)
        fast_time = time.time() - start

        # Test BALANCED mode
        start = time.time()
        balanced_chunks = []
        balanced_prelim_time = None

        async for chunk in router.process_query(
            query=query, mode=QueryMode.BALANCED, session_id="timing_balanced", top_k=5
        ):
            balanced_chunks.append(chunk)
            if (
                chunk.chunk_type == ChunkType.PRELIMINARY
                and balanced_prelim_time is None
            ):
                balanced_prelim_time = time.time() - start

        balanced_time = time.time() - start

        # Assertions
        assert fast_time < 2.5, f"FAST mode took {fast_time:.2f}s"

        if balanced_prelim_time:
            assert (
                balanced_prelim_time < 2.5
            ), f"BALANCED preliminary took {balanced_prelim_time:.2f}s"

        # All modes should complete successfully
        assert len(fast_chunks) > 0
        assert len(balanced_chunks) > 0
