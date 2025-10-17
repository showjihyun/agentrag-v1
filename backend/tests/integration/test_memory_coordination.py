"""
Integration tests for memory coordination between speculative and agentic paths.

Tests:
- STM usage in speculative path
- Memory consolidation from both paths
- Context loading and saving

Requirements: 9.1, 9.2, 9.3, 9.4, 9.6
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.services.speculative_processor import SpeculativeProcessor
from backend.agents.aggregator import AggregatorAgent
from backend.memory.stm import ShortTermMemory
from backend.memory.manager import MemoryManager
from backend.models.hybrid import SpeculativeResponse
from backend.models.query import SearchResult as QuerySearchResult


@pytest.fixture
def mock_stm():
    """Create a mock ShortTermMemory instance."""
    stm = Mock(spec=ShortTermMemory)
    stm.get_conversation_history = Mock(
        return_value=[
            {
                "role": "user",
                "content": "What is machine learning?",
                "timestamp": datetime.now().isoformat(),
                "metadata": {},
            },
            {
                "role": "assistant",
                "content": "Machine learning is a subset of AI...",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"path": "speculative"},
            },
        ]
    )
    stm.add_message = Mock()
    stm.store_working_memory = Mock()
    stm.get_working_memory = Mock(return_value={})
    stm.get_session_info = Mock(
        return_value={"session_id": "test_session", "message_count": 2, "exists": True}
    )
    return stm


@pytest.fixture
def mock_memory_manager(mock_stm):
    """Create a mock MemoryManager instance."""
    manager = Mock(spec=MemoryManager)
    manager.stm = mock_stm

    # Mock get_context_for_query
    async def mock_get_context():
        from backend.memory.manager import MemoryContext

        return MemoryContext(
            recent_history=mock_stm.get_conversation_history("test_session"),
            similar_interactions=[],
            working_memory={},
            session_info={"session_id": "test_session"},
        )

    manager.get_context_for_query = AsyncMock(side_effect=mock_get_context)
    manager.consolidate_memory = AsyncMock(return_value="interaction_123")
    manager.add_working_memory = AsyncMock()
    manager.get_working_memory = AsyncMock(return_value={})

    return manager


@pytest.fixture
def mock_embedding_service():
    """Create a mock EmbeddingService."""
    service = Mock()
    service.embed_text = Mock(return_value=[0.1] * 768)
    return service


@pytest.fixture
def mock_milvus_manager():
    """Create a mock MilvusManager."""
    manager = Mock()

    async def mock_search(*args, **kwargs):
        from backend.services.milvus import SearchResult

        return [
            SearchResult(
                id="chunk_1",
                document_id="doc_1",
                document_name="test_doc.txt",
                text="Machine learning is a method of data analysis.",
                score=0.95,
                metadata={},
            )
        ]

    manager.search = AsyncMock(side_effect=mock_search)
    return manager


@pytest.fixture
def mock_llm_manager():
    """Create a mock LLMManager."""
    manager = Mock()
    manager.generate = AsyncMock(
        return_value="Machine learning is a subset of artificial intelligence."
    )
    return manager


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock()
    client.zadd = AsyncMock()
    client.zcard = AsyncMock(return_value=0)
    return client


@pytest.fixture
def speculative_processor(
    mock_embedding_service,
    mock_milvus_manager,
    mock_llm_manager,
    mock_redis_client,
    mock_stm,
):
    """Create a SpeculativeProcessor with mocked dependencies."""
    return SpeculativeProcessor(
        embedding_service=mock_embedding_service,
        milvus_manager=mock_milvus_manager,
        llm_manager=mock_llm_manager,
        redis_client=mock_redis_client,
        stm=mock_stm,
    )


class TestSpeculativeProcessorSTMIntegration:
    """Test STM usage in speculative path."""

    @pytest.mark.asyncio
    async def test_loads_conversation_context(self, speculative_processor, mock_stm):
        """
        Test that SpeculativeProcessor loads conversation context from STM.

        Requirements: 9.1
        """
        # Process query with session ID
        response = await speculative_processor.process(
            query="Tell me more about neural networks",
            session_id="test_session",
            top_k=5,
        )

        # Verify STM was queried for conversation history
        mock_stm.get_conversation_history.assert_called_once()
        call_args = mock_stm.get_conversation_history.call_args
        assert call_args[1]["session_id"] == "test_session"

        # Verify response was generated
        assert response is not None
        assert isinstance(response, SpeculativeResponse)

    @pytest.mark.asyncio
    async def test_includes_context_in_llm_prompt(
        self, speculative_processor, mock_llm_manager, mock_stm
    ):
        """
        Test that conversation history is included in LLM prompt.

        Requirements: 9.2
        """
        # Process query
        await speculative_processor.process(
            query="What about deep learning?", session_id="test_session", top_k=5
        )

        # Verify LLM was called
        assert mock_llm_manager.generate.called

        # Get the prompt that was sent to LLM
        call_args = mock_llm_manager.generate.call_args
        messages = call_args[0][0]

        # Check that user prompt contains conversation context
        user_message = next(m for m in messages if m["role"] == "user")
        assert (
            "Recent conversation" in user_message["content"]
            or "User:" in user_message["content"]
        )

    @pytest.mark.asyncio
    async def test_saves_results_to_stm_with_path_marker(
        self, speculative_processor, mock_stm
    ):
        """
        Test that speculative results are saved to STM with path marker.

        Requirements: 9.2, 9.6
        """
        # Process query
        response = await speculative_processor.process(
            query="Explain supervised learning", session_id="test_session", top_k=5
        )

        # Verify messages were added to STM
        assert mock_stm.add_message.call_count >= 2  # User query + assistant response

        # Check user message
        user_call = mock_stm.add_message.call_args_list[0]
        assert user_call[1]["session_id"] == "test_session"
        assert user_call[1]["role"] == "user"
        assert user_call[1]["content"] == "Explain supervised learning"
        assert user_call[1]["metadata"]["path"] == "speculative"

        # Check assistant message
        assistant_call = mock_stm.add_message.call_args_list[1]
        assert assistant_call[1]["session_id"] == "test_session"
        assert assistant_call[1]["role"] == "assistant"
        assert assistant_call[1]["metadata"]["path"] == "speculative"
        assert "confidence_score" in assistant_call[1]["metadata"]

    @pytest.mark.asyncio
    async def test_handles_missing_stm_gracefully(
        self,
        mock_embedding_service,
        mock_milvus_manager,
        mock_llm_manager,
        mock_redis_client,
    ):
        """
        Test that processor works without STM (graceful degradation).

        Requirements: 9.1
        """
        # Create processor without STM
        processor = SpeculativeProcessor(
            embedding_service=mock_embedding_service,
            milvus_manager=mock_milvus_manager,
            llm_manager=mock_llm_manager,
            redis_client=mock_redis_client,
            stm=None,  # No STM
        )

        # Process query - should not fail
        response = await processor.process(
            query="What is AI?", session_id="test_session", top_k=5
        )

        # Verify response was generated
        assert response is not None
        assert isinstance(response, SpeculativeResponse)


class TestAggregatorAgentSpeculativeIntegration:
    """Test AggregatorAgent incorporation of speculative results."""

    @pytest.fixture
    def mock_vector_agent(self):
        """Create a mock VectorSearchAgent."""
        agent = Mock()

        async def mock_search(*args, **kwargs):
            return [
                QuerySearchResult(
                    chunk_id="chunk_2",
                    document_id="doc_2",
                    document_name="ml_guide.pdf",
                    text="Neural networks are computing systems inspired by biological neural networks.",
                    score=0.92,
                    metadata={},
                )
            ]

        agent.search = AsyncMock(side_effect=mock_search)
        return agent

    @pytest.fixture
    def mock_local_agent(self):
        """Create a mock LocalDataAgent."""
        agent = Mock()
        agent.read_file = AsyncMock(return_value="File content")
        agent.query_database = AsyncMock(return_value=[])
        return agent

    @pytest.fixture
    def mock_search_agent(self):
        """Create a mock WebSearchAgent."""
        agent = Mock()
        agent.search = AsyncMock(return_value=[])
        return agent

    @pytest.fixture
    def aggregator_agent(
        self,
        mock_llm_manager,
        mock_memory_manager,
        mock_vector_agent,
        mock_local_agent,
        mock_search_agent,
    ):
        """Create an AggregatorAgent with mocked dependencies."""
        return AggregatorAgent(
            llm_manager=mock_llm_manager,
            memory_manager=mock_memory_manager,
            vector_agent=mock_vector_agent,
            local_agent=mock_local_agent,
            search_agent=mock_search_agent,
            max_iterations=5,
        )

    @pytest.mark.asyncio
    async def test_accepts_speculative_findings(
        self, aggregator_agent, mock_memory_manager
    ):
        """
        Test that AggregatorAgent accepts speculative findings as initial context.

        Requirements: 9.3
        """
        # Create speculative results
        speculative_results = {
            "response": "Machine learning is a subset of AI.",
            "confidence_score": 0.85,
            "sources": [
                {
                    "chunk_id": "chunk_1",
                    "document_id": "doc_1",
                    "document_name": "ml_intro.txt",
                    "text": "Machine learning enables computers to learn.",
                    "score": 0.95,
                    "metadata": {},
                }
            ],
        }

        # Process query with speculative results
        steps = []
        async for step in aggregator_agent.process_query(
            query="What is machine learning?",
            session_id="test_session",
            top_k=10,
            speculative_results=speculative_results,
        ):
            steps.append(step)

        # Verify speculative results were incorporated
        # Check for a step mentioning speculative findings
        speculative_steps = [
            s
            for s in steps
            if "speculative" in s.content.lower()
            or s.metadata.get("step") == "incorporate_speculative"
        ]

        assert (
            len(speculative_steps) > 0
        ), "No steps found incorporating speculative results"

    @pytest.mark.asyncio
    async def test_merges_speculative_with_agentic_results(
        self, aggregator_agent, mock_memory_manager
    ):
        """
        Test that speculative results are merged with agentic reasoning.

        Requirements: 9.3, 9.4
        """
        # Create speculative results
        speculative_results = {
            "response": "Quick answer about ML.",
            "confidence_score": 0.75,
            "sources": [
                {
                    "chunk_id": "spec_chunk",
                    "document_id": "spec_doc",
                    "document_name": "quick_ref.txt",
                    "text": "ML is AI subset.",
                    "score": 0.88,
                    "metadata": {},
                }
            ],
        }

        # Process query
        steps = []
        async for step in aggregator_agent.process_query(
            query="Explain machine learning",
            session_id="test_session",
            top_k=10,
            speculative_results=speculative_results,
        ):
            steps.append(step)

        # Find the final response step
        response_steps = [s for s in steps if s.type == "response"]
        assert len(response_steps) > 0, "No response step found"

        final_response = response_steps[-1]

        # Verify metadata indicates speculative results were used
        assert final_response.metadata.get("has_speculative") is not None

    @pytest.mark.asyncio
    async def test_marks_memory_with_contributing_paths(
        self, aggregator_agent, mock_memory_manager
    ):
        """
        Test that final memory entries are marked with contributing paths.

        Requirements: 9.4, 9.6
        """
        # Create speculative results
        speculative_results = {
            "response": "Initial response.",
            "confidence_score": 0.80,
            "sources": [],
        }

        # Process query
        steps = []
        async for step in aggregator_agent.process_query(
            query="Test query",
            session_id="test_session",
            top_k=10,
            speculative_results=speculative_results,
        ):
            steps.append(step)

        # Verify consolidate_memory was called
        assert mock_memory_manager.consolidate_memory.called

        # Check the metadata passed to consolidate_memory
        call_args = mock_memory_manager.consolidate_memory.call_args
        metadata = call_args[1]["metadata"]

        # Verify contributing paths are marked
        assert "contributing_paths" in metadata
        assert "speculative" in metadata["contributing_paths"]
        assert metadata["path"] in ["hybrid", "speculative", "agentic"]


class TestMemoryCoordinationEndToEnd:
    """End-to-end tests for memory coordination."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_memory(
        self, speculative_processor, mock_stm, mock_memory_manager
    ):
        """
        Test complete workflow: speculative processing -> STM save -> context loading.

        Requirements: 9.1, 9.2, 9.6
        """
        session_id = "e2e_test_session"

        # Step 1: Process query with speculative processor
        response1 = await speculative_processor.process(
            query="What is deep learning?", session_id=session_id, top_k=5
        )

        # Verify first query was saved to STM
        assert mock_stm.add_message.called

        # Step 2: Process follow-up query (should load context)
        mock_stm.reset_mock()
        response2 = await speculative_processor.process(
            query="How does it differ from traditional ML?",
            session_id=session_id,
            top_k=5,
        )

        # Verify conversation history was loaded
        mock_stm.get_conversation_history.assert_called()

        # Verify follow-up was also saved
        assert mock_stm.add_message.called

    @pytest.mark.asyncio
    async def test_context_preservation_across_paths(
        self, speculative_processor, mock_stm, mock_memory_manager
    ):
        """
        Test that context is preserved when transitioning from speculative to agentic path.

        Requirements: 9.3, 9.4
        """
        session_id = "context_test_session"

        # Simulate speculative path saving to STM
        await speculative_processor.process(
            query="Initial query", session_id=session_id, top_k=5
        )

        # Verify STM has the conversation
        assert mock_stm.add_message.called

        # Now simulate agentic path loading context
        context = await mock_memory_manager.get_context_for_query(
            session_id=session_id, query="Follow-up query"
        )

        # Verify context includes recent history
        assert len(context.recent_history) > 0

        # Verify some messages have speculative path marker
        speculative_messages = [
            msg
            for msg in context.recent_history
            if msg.get("metadata", {}).get("path") == "speculative"
        ]
        assert len(speculative_messages) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
