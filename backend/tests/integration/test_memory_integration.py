"""Integration tests for memory system (STM, LTM, and MemoryManager)."""

import pytest
import asyncio
import time
from datetime import datetime
from backend.memory import ShortTermMemory, LongTermMemory, MemoryManager
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService
from backend.config import settings


@pytest.fixture
def embedding_service():
    """Create embedding service for tests."""
    return EmbeddingService(model_name=settings.EMBEDDING_MODEL)


@pytest.fixture
def stm():
    """Create Short-Term Memory instance for tests."""
    try:
        stm = ShortTermMemory(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ttl=60,  # Short TTL for tests
        )
        yield stm
        stm.close()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
async def ltm(embedding_service):
    """Create Long-Term Memory instance for tests."""
    try:
        # Create Milvus manager for LTM collection
        milvus = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=f"test_ltm_{int(time.time())}",
            embedding_dim=embedding_service.dimension,
        )

        milvus.connect()
        milvus.create_collection(drop_existing=True)

        ltm = LongTermMemory(milvus_manager=milvus, embedding_service=embedding_service)

        yield ltm

        # Cleanup
        milvus.disconnect()

    except Exception as e:
        pytest.skip(f"Milvus not available: {e}")


@pytest.fixture
async def memory_manager(stm, ltm):
    """Create MemoryManager instance for tests."""
    return MemoryManager(
        stm=stm, ltm=ltm, max_history_length=10, ltm_similarity_threshold=0.5
    )


class TestSTMIntegration:
    """Integration tests for Short-Term Memory."""

    def test_stm_message_storage_and_retrieval(self, stm):
        """Test storing and retrieving messages."""
        session_id = f"test_session_{int(time.time())}"

        # Add messages
        stm.add_message(session_id, "user", "What is machine learning?")
        stm.add_message(session_id, "assistant", "Machine learning is...")
        stm.add_message(session_id, "user", "Tell me more")

        # Retrieve history
        history = stm.get_conversation_history(session_id)

        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[2]["role"] == "user"

        # Cleanup
        stm.clear_session(session_id)

    def test_stm_working_memory(self, stm):
        """Test working memory storage and retrieval."""
        session_id = f"test_session_{int(time.time())}"

        # Store working memory
        stm.store_working_memory(session_id, "current_task", "searching")
        stm.store_working_memory(session_id, "documents_found", 5)

        # Retrieve specific key
        task = stm.get_working_memory(session_id, "current_task")
        assert task == "searching"

        # Retrieve all working memory
        all_memory = stm.get_working_memory(session_id)
        assert len(all_memory) == 2
        assert all_memory["documents_found"] == 5

        # Cleanup
        stm.clear_session(session_id)

    def test_stm_ttl_expiration(self, stm):
        """Test TTL expiration (requires short TTL)."""
        # Create STM with very short TTL
        short_ttl_stm = ShortTermMemory(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, ttl=2
        )  # 2 seconds

        session_id = f"test_session_{int(time.time())}"

        # Add message
        short_ttl_stm.add_message(session_id, "user", "Test message")

        # Verify it exists
        info = short_ttl_stm.get_session_info(session_id)
        assert info["message_count"] == 1
        assert info["messages_ttl"] > 0

        # Wait for expiration
        time.sleep(3)

        # Verify it's expired
        info = short_ttl_stm.get_session_info(session_id)
        assert info["message_count"] == 0

        short_ttl_stm.close()

    def test_stm_session_info(self, stm):
        """Test getting session information."""
        session_id = f"test_session_{int(time.time())}"

        # Add data
        stm.add_message(session_id, "user", "Hello")
        stm.store_working_memory(session_id, "key1", "value1")

        # Get info
        info = stm.get_session_info(session_id)

        assert info["session_id"] == session_id
        assert info["message_count"] == 1
        assert len(info["working_memory_keys"]) == 1
        assert info["exists"] is True

        # Cleanup
        stm.clear_session(session_id)


class TestLTMIntegration:
    """Integration tests for Long-Term Memory."""

    @pytest.mark.asyncio
    async def test_ltm_store_and_retrieve_interaction(self, ltm):
        """Test storing and retrieving interactions."""
        # Store interaction
        interaction_id = await ltm.store_interaction(
            query="What is deep learning?",
            response="Deep learning is a subset of machine learning...",
            session_id="session1",
            success_score=0.9,
            source_count=3,
            action_count=2,
        )

        assert interaction_id is not None
        assert interaction_id.startswith("ltm_")

        # Retrieve similar interactions
        similar = await ltm.retrieve_similar_interactions(
            query="Tell me about deep learning", top_k=5, min_success_score=0.7
        )

        assert len(similar) > 0
        assert similar[0].query == "What is deep learning?"
        assert similar[0].success_score == 0.9

    @pytest.mark.asyncio
    async def test_ltm_similarity_search(self, ltm):
        """Test similarity search for interactions."""
        # Store multiple interactions
        await ltm.store_interaction(
            query="What is neural network?",
            response="A neural network is...",
            session_id="s1",
            success_score=0.95,
        )

        await ltm.store_interaction(
            query="How does backpropagation work?",
            response="Backpropagation is...",
            session_id="s2",
            success_score=0.85,
        )

        await ltm.store_interaction(
            query="What is the weather today?",
            response="I don't have weather data",
            session_id="s3",
            success_score=0.3,
        )

        # Search for neural network related queries
        similar = await ltm.retrieve_similar_interactions(
            query="Explain neural networks", top_k=3, min_success_score=0.7
        )

        # Should find the high-scoring neural network interactions
        assert len(similar) >= 1
        assert any("neural" in s.query.lower() for s in similar)

    @pytest.mark.asyncio
    async def test_ltm_store_and_retrieve_patterns(self, ltm):
        """Test storing and retrieving learned patterns."""
        # Store pattern
        pattern_id = await ltm.store_learned_pattern(
            pattern_type="query_strategy",
            pattern_data={"steps": ["search", "analyze", "synthesize"]},
            description="Effective strategy for research queries",
            success_score=0.9,
        )

        assert pattern_id is not None
        assert pattern_id.startswith("pattern_")

        # Retrieve patterns
        patterns = await ltm.retrieve_patterns(
            pattern_type="query_strategy", min_success_score=0.8, limit=10
        )

        assert len(patterns) > 0
        assert patterns[0]["type"] == "query_strategy"
        assert patterns[0]["success_score"] >= 0.8

    @pytest.mark.asyncio
    async def test_ltm_stats(self, ltm):
        """Test getting LTM statistics."""
        # Store some interactions
        await ltm.store_interaction(
            query="Test query 1", response="Test response 1", session_id="s1"
        )

        await ltm.store_interaction(
            query="Test query 2", response="Test response 2", session_id="s2"
        )

        # Get stats
        stats = ltm.get_stats()

        assert stats["status"] == "healthy"
        assert stats["total_interactions"] >= 2
        assert "embedding_dimension" in stats


class TestMemoryManagerIntegration:
    """Integration tests for MemoryManager."""

    @pytest.mark.asyncio
    async def test_memory_manager_get_context(self, memory_manager):
        """Test getting combined memory context."""
        session_id = f"test_session_{int(time.time())}"

        # Add some STM data
        memory_manager.stm.add_message(session_id, "user", "What is AI?")
        memory_manager.stm.add_message(session_id, "assistant", "AI is...")
        memory_manager.stm.store_working_memory(session_id, "topic", "AI")

        # Store similar interaction in LTM
        await memory_manager.ltm.store_interaction(
            query="Explain artificial intelligence",
            response="Artificial intelligence is...",
            session_id="old_session",
            success_score=0.9,
        )

        # Get context
        context = await memory_manager.get_context_for_query(
            session_id=session_id,
            query="Tell me more about AI",
            include_similar_interactions=True,
        )

        assert len(context.recent_history) == 2
        assert context.working_memory["topic"] == "AI"
        assert len(context.similar_interactions) > 0

        # Cleanup
        memory_manager.stm.clear_session(session_id)

    @pytest.mark.asyncio
    async def test_memory_manager_consolidate(self, memory_manager):
        """Test memory consolidation from STM to LTM."""
        session_id = f"test_session_{int(time.time())}"

        # Consolidate memory
        interaction_id = await memory_manager.consolidate_memory(
            session_id=session_id,
            query="What is machine learning?",
            response="Machine learning is a field of AI...",
            success=True,
            metadata={"source_count": 5, "action_count": 3, "has_citations": True},
        )

        assert interaction_id is not None

        # Verify it's in STM
        history = memory_manager.stm.get_conversation_history(session_id)
        assert len(history) == 2  # User + assistant messages

        # Verify it's in LTM
        similar = await memory_manager.ltm.retrieve_similar_interactions(
            query="machine learning", top_k=5
        )
        assert len(similar) > 0

        # Cleanup
        memory_manager.stm.clear_session(session_id)

    @pytest.mark.asyncio
    async def test_memory_manager_working_memory(self, memory_manager):
        """Test working memory operations through manager."""
        session_id = f"test_session_{int(time.time())}"

        # Add working memory
        await memory_manager.add_working_memory(
            session_id=session_id, key="current_step", value="analyzing"
        )

        # Retrieve working memory
        value = await memory_manager.get_working_memory(
            session_id=session_id, key="current_step"
        )

        assert value == "analyzing"

        # Cleanup
        memory_manager.stm.clear_session(session_id)

    @pytest.mark.asyncio
    async def test_memory_manager_patterns(self, memory_manager):
        """Test pattern storage and retrieval through manager."""
        # Store pattern
        pattern_id = await memory_manager.store_pattern(
            pattern_type="workflow",
            pattern_data={"steps": ["plan", "execute", "reflect"]},
            description="Standard agent workflow pattern",
            success_score=0.95,
        )

        assert pattern_id is not None

        # Retrieve patterns
        patterns = await memory_manager.get_relevant_patterns(
            pattern_type="workflow", limit=5
        )

        assert len(patterns) > 0
        assert patterns[0]["type"] == "workflow"

    @pytest.mark.asyncio
    async def test_memory_manager_stats(self, memory_manager):
        """Test getting memory statistics."""
        stats = memory_manager.get_memory_stats()

        assert "stm" in stats
        assert "ltm" in stats
        assert "config" in stats

        assert stats["stm"]["status"] in ["healthy", "unhealthy"]
        assert stats["config"]["max_history_length"] == 10

    @pytest.mark.asyncio
    async def test_memory_context_summary(self, memory_manager):
        """Test memory context summary generation."""
        session_id = f"test_session_{int(time.time())}"

        # Add data
        memory_manager.stm.add_message(session_id, "user", "Test")

        # Get context
        context = await memory_manager.get_context_for_query(
            session_id=session_id, query="Test query"
        )

        summary = context.get_summary()
        assert "recent messages" in summary.lower()

        # Cleanup
        memory_manager.stm.clear_session(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
