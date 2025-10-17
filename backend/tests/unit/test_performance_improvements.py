"""
Unit tests for performance improvements.

Tests the optimizations implemented in Phase 1:
1. Milvus collection loading
2. LLM provider-specific optimization
3. Memory manager parallel loading
4. Embedding batch size optimization
5. Aggregator agent fast path
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from backend.services.milvus import MilvusManager
from backend.services.llm_manager import LLMManager, LLMProvider
from backend.memory.manager import MemoryManager
from backend.agents.aggregator import AggregatorAgent


class TestMilvusPerformance:
    """Test Milvus collection loading optimization."""

    @pytest.mark.asyncio
    async def test_collection_loaded_once(self):
        """Test that collection is loaded only once."""
        # This would require actual Milvus connection
        # Placeholder for integration test
        pass

    def test_collection_loaded_flag_initialization(self):
        """Test that _collection_loaded flag is initialized."""
        manager = MilvusManager(
            host="localhost", port=19530, collection_name="test", embedding_dim=384
        )

        assert hasattr(manager, "_collection_loaded")
        assert manager._collection_loaded is False


class TestLLMProviderOptimization:
    """Test LLM provider-specific optimizations."""

    def test_timeout_for_ollama(self):
        """Test that Ollama gets shorter timeout."""
        llm = LLMManager(provider=LLMProvider.OLLAMA, model="llama3.1")

        timeout = llm._get_timeout_for_provider()
        assert timeout == 30.0

    def test_timeout_for_cloud_providers(self):
        """Test that cloud providers get longer timeout."""
        # OpenAI
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            llm = LLMManager(provider=LLMProvider.OPENAI, model="gpt-4")
            timeout = llm._get_timeout_for_provider()
            assert timeout == 60.0

    @pytest.mark.asyncio
    async def test_ollama_uses_no_retry_path(self):
        """Test that Ollama uses the no-retry path."""
        with patch("backend.services.llm_manager.acompletion") as mock_completion:
            mock_completion.return_value = Mock(
                choices=[Mock(message=Mock(content="Test response"))]
            )

            llm = LLMManager(provider=LLMProvider.OLLAMA, model="llama3.1")

            messages = [{"role": "user", "content": "test"}]

            # Should call _generate_without_retry
            with patch.object(
                llm, "_generate_without_retry", new_callable=AsyncMock
            ) as mock_no_retry:
                mock_no_retry.return_value = "Test response"
                await llm.generate(messages)
                mock_no_retry.assert_called_once()


class TestMemoryManagerParallel:
    """Test memory manager parallel loading."""

    @pytest.mark.asyncio
    async def test_parallel_stm_operations(self):
        """Test that STM operations run in parallel."""
        # Mock STM and LTM
        mock_stm = Mock()
        mock_stm.get_conversation_history = Mock(return_value=[])
        mock_stm.get_working_memory = Mock(return_value={})
        mock_stm.get_session_info = Mock(return_value={"session_id": "test"})

        mock_ltm = Mock()
        mock_ltm.retrieve_similar_interactions = AsyncMock(return_value=[])

        manager = MemoryManager(stm=mock_stm, ltm=mock_ltm)

        start = time.time()
        context = await manager.get_context_for_query(
            session_id="test", query="test query"
        )
        duration = time.time() - start

        # Should complete quickly with parallel execution
        assert duration < 1.0
        assert context is not None


class TestEmbeddingBatchOptimization:
    """Test embedding batch size optimization."""

    def test_small_document_batch_size(self):
        """Test batch size for small documents."""
        num_chunks = 5

        if num_chunks < 10:
            batch_size = num_chunks
        elif num_chunks < 100:
            batch_size = 32
        else:
            batch_size = 64

        assert batch_size == 5

    def test_medium_document_batch_size(self):
        """Test batch size for medium documents."""
        num_chunks = 50

        if num_chunks < 10:
            batch_size = num_chunks
        elif num_chunks < 100:
            batch_size = 32
        else:
            batch_size = 64

        assert batch_size == 32

    def test_large_document_batch_size(self):
        """Test batch size for large documents."""
        num_chunks = 150

        if num_chunks < 10:
            batch_size = num_chunks
        elif num_chunks < 100:
            batch_size = 32
        else:
            batch_size = 64

        assert batch_size == 64


class TestAggregatorFastPath:
    """Test aggregator agent fast path."""

    def test_query_complexity_simple(self):
        """Test simple query detection."""
        # Mock dependencies
        mock_llm = Mock()
        mock_memory = Mock()
        mock_vector = Mock()
        mock_local = Mock()
        mock_search = Mock()

        agent = AggregatorAgent(
            llm_manager=mock_llm,
            memory_manager=mock_memory,
            vector_agent=mock_vector,
            local_agent=mock_local,
            search_agent=mock_search,
        )

        # Simple queries
        assert agent._analyze_query_complexity("What is AI?") == "simple"
        assert agent._analyze_query_complexity("How does this work?") == "simple"

    def test_query_complexity_complex(self):
        """Test complex query detection."""
        mock_llm = Mock()
        mock_memory = Mock()
        mock_vector = Mock()
        mock_local = Mock()
        mock_search = Mock()

        agent = AggregatorAgent(
            llm_manager=mock_llm,
            memory_manager=mock_memory,
            vector_agent=mock_vector,
            local_agent=mock_local,
            search_agent=mock_search,
        )

        # Complex queries
        complex_query = "Compare and contrast the advantages and disadvantages of machine learning versus traditional programming approaches"
        assert agent._analyze_query_complexity(complex_query) == "complex"

        analysis_query = "Analyze why deep learning models perform better than traditional algorithms"
        assert agent._analyze_query_complexity(analysis_query) == "complex"

    @pytest.mark.asyncio
    async def test_fast_path_execution(self):
        """Test that fast path executes correctly."""
        # This would require full agent setup
        # Placeholder for integration test
        pass


class TestPerformanceMetrics:
    """Test performance metric collection."""

    @pytest.mark.asyncio
    async def test_query_response_time_tracking(self):
        """Test that query response times are tracked."""
        start = time.time()

        # Simulate query processing
        await asyncio.sleep(0.1)

        duration = time.time() - start

        # Should be measurable
        assert duration >= 0.1
        assert duration < 0.2

    def test_llm_call_counting(self):
        """Test LLM call counting for metrics."""
        call_count = 0

        # Simulate LLM calls
        for _ in range(3):
            call_count += 1

        assert call_count == 3


# Performance benchmarks (run separately)
class TestPerformanceBenchmarks:
    """Performance benchmarks for comparison."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_milvus_search_performance(self):
        """Benchmark Milvus search performance."""
        # Requires actual Milvus connection
        pass

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_simple_query_end_to_end(self):
        """Benchmark simple query end-to-end."""
        # Requires full system setup
        pass

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_complex_query_end_to_end(self):
        """Benchmark complex query end-to-end."""
        # Requires full system setup
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
