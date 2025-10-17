"""
Integration tests for backward compatibility.

Tests that the hybrid system maintains compatibility with:
- Existing memory data (STM and LTM)
- Document index in Milvus
- Cache functionality
- Legacy API requests

Requirements: 12.5
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from config import settings
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService
from backend.memory.stm import ShortTermMemory
from backend.memory.ltm import LongTermMemory
from backend.memory.manager import MemoryManager
from backend.services.search_cache import SearchCacheManager


class TestMemoryCompatibility:
    """Test compatibility with existing memory data."""

    @pytest.mark.asyncio
    async def test_stm_data_compatibility(self, redis_client):
        """
        Test that existing STM data can be read and used.

        Requirements: 12.5
        """
        # Create STM instance
        stm = ShortTermMemory(redis_client=redis_client)

        # Simulate existing conversation data
        session_id = "test_session_legacy"

        # Add legacy-format messages
        await stm.add_message(
            session_id=session_id, role="user", content="What is machine learning?"
        )

        await stm.add_message(
            session_id=session_id,
            role="assistant",
            content="Machine learning is a subset of AI...",
        )

        # Verify we can retrieve the data
        history = await stm.get_conversation_history(session_id)

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert "machine learning" in history[0]["content"].lower()

        # Verify we can add new messages to existing conversation
        await stm.add_message(
            session_id=session_id, role="user", content="Tell me more"
        )

        history = await stm.get_conversation_history(session_id)
        assert len(history) == 3

        # Cleanup
        await stm.clear_session(session_id)

    @pytest.mark.asyncio
    async def test_ltm_data_compatibility(self, redis_client, milvus_manager):
        """
        Test that existing LTM data can be read and used.

        Requirements: 12.5
        """
        # Create LTM instance
        embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
        ltm = LongTermMemory(
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
            redis_client=redis_client,
        )

        # Simulate existing memory entry
        session_id = "test_session_ltm"

        # Store a memory
        await ltm.store_interaction(
            session_id=session_id,
            query="What is deep learning?",
            response="Deep learning uses neural networks...",
            sources=[],
            metadata={"timestamp": datetime.now().isoformat()},
        )

        # Verify we can retrieve it
        memories = await ltm.retrieve_relevant_memories(
            query="neural networks", session_id=session_id, top_k=5
        )

        assert len(memories) > 0
        assert any("deep learning" in m.get("query", "").lower() for m in memories)

        # Cleanup
        await ltm.clear_session_memories(session_id)

    @pytest.mark.asyncio
    async def test_memory_manager_compatibility(self, redis_client, milvus_manager):
        """
        Test that MemoryManager works with existing data.

        Requirements: 12.5
        """
        # Create memory manager
        embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
        memory_manager = MemoryManager(
            redis_client=redis_client,
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
        )

        session_id = "test_session_manager"

        # Add conversation history
        await memory_manager.add_to_stm(
            session_id=session_id, role="user", content="Explain transformers"
        )

        await memory_manager.add_to_stm(
            session_id=session_id,
            role="assistant",
            content="Transformers are neural network architectures...",
        )

        # Get context (should work with existing data)
        context = await memory_manager.get_context(
            session_id=session_id, query="transformers"
        )

        assert "conversation_history" in context
        assert len(context["conversation_history"]) == 2

        # Cleanup
        await memory_manager.clear_session(session_id)


class TestDocumentIndexCompatibility:
    """Test compatibility with existing document index."""

    @pytest.mark.asyncio
    async def test_existing_documents_readable(self, milvus_manager, embedding_service):
        """
        Test that existing documents in Milvus can be read and searched.

        Requirements: 12.5
        """
        # Insert a test document (simulating existing data)
        test_chunks = [
            {
                "chunk_id": "legacy_doc_chunk_1",
                "document_id": "legacy_doc_1",
                "document_name": "legacy_document.txt",
                "text": "This is a legacy document about artificial intelligence.",
                "metadata": {"source": "legacy_system"},
            }
        ]

        # Generate embeddings
        texts = [chunk["text"] for chunk in test_chunks]
        embeddings = embedding_service.encode(texts)

        # Insert into Milvus
        for chunk, embedding in zip(test_chunks, embeddings):
            milvus_manager.insert(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
                document_name=chunk["document_name"],
                text=chunk["text"],
                embedding=embedding.tolist(),
                metadata=chunk["metadata"],
            )

        # Verify we can search for it
        query_embedding = embedding_service.encode(["artificial intelligence"])[0]
        results = milvus_manager.search(
            query_embedding=query_embedding.tolist(), top_k=5
        )

        assert len(results) > 0
        assert any("legacy_doc" in r.get("chunk_id", "") for r in results)

        # Cleanup
        milvus_manager.delete_by_filter(f'document_id == "legacy_doc_1"')

    @pytest.mark.asyncio
    async def test_document_metadata_preserved(self, milvus_manager, embedding_service):
        """
        Test that document metadata is preserved and accessible.

        Requirements: 12.5
        """
        # Insert document with metadata
        chunk_id = "meta_test_chunk_1"
        document_id = "meta_test_doc_1"

        text = "Test document with metadata"
        embedding = embedding_service.encode([text])[0]

        metadata = {
            "author": "Test Author",
            "date": "2024-01-01",
            "category": "test",
            "legacy_field": "legacy_value",
        }

        milvus_manager.insert(
            chunk_id=chunk_id,
            document_id=document_id,
            document_name="test_meta.txt",
            text=text,
            embedding=embedding.tolist(),
            metadata=metadata,
        )

        # Search and verify metadata
        query_embedding = embedding_service.encode(["test document"])[0]
        results = milvus_manager.search(
            query_embedding=query_embedding.tolist(), top_k=5
        )

        # Find our document
        our_result = next((r for r in results if r.get("chunk_id") == chunk_id), None)
        assert our_result is not None

        # Verify metadata is preserved
        result_metadata = our_result.get("metadata", {})
        assert result_metadata.get("author") == "Test Author"
        assert result_metadata.get("legacy_field") == "legacy_value"

        # Cleanup
        milvus_manager.delete_by_filter(f'document_id == "{document_id}"')


class TestCacheCompatibility:
    """Test that cache doesn't break existing functionality."""

    @pytest.mark.asyncio
    async def test_cache_disabled_fallback(
        self, redis_client, milvus_manager, embedding_service
    ):
        """
        Test that system works when cache is disabled.

        Requirements: 12.5
        """
        # Create cache manager with cache disabled
        cache_manager = SearchCacheManager(
            redis_client=redis_client, enabled=False
        )  # Explicitly disable

        # Verify cache operations don't break anything
        query = "test query"
        query_embedding = embedding_service.encode([query])[0]

        # Try to get from cache (should return None)
        cached = await cache_manager.get_cached_results(
            query_embedding=query_embedding.tolist(), top_k=10
        )
        assert cached is None

        # Try to cache results (should not raise error)
        test_results = [{"chunk_id": "test_1", "text": "test", "score": 0.9}]

        await cache_manager.cache_results(
            query_embedding=query_embedding.tolist(), top_k=10, results=test_results
        )

        # Verify it's still not cached (because disabled)
        cached = await cache_manager.get_cached_results(
            query_embedding=query_embedding.tolist(), top_k=10
        )
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_with_existing_data(self, redis_client):
        """
        Test that cache works alongside existing Redis data.

        Requirements: 12.5
        """
        # Create cache manager
        cache_manager = SearchCacheManager(redis_client=redis_client, enabled=True)

        # Add some existing data to Redis (simulating legacy data)
        await redis_client.set("legacy_key_1", "legacy_value_1")
        await redis_client.set("legacy_key_2", "legacy_value_2")

        # Verify legacy data is still accessible
        value1 = await redis_client.get("legacy_key_1")
        assert value1 == "legacy_value_1"

        # Use cache (should not interfere with legacy data)
        query_embedding = [0.1] * 768
        test_results = [{"chunk_id": "test", "score": 0.9}]

        await cache_manager.cache_results(
            query_embedding=query_embedding, top_k=10, results=test_results
        )

        # Verify legacy data is still intact
        value2 = await redis_client.get("legacy_key_2")
        assert value2 == "legacy_value_2"

        # Verify cache works
        cached = await cache_manager.get_cached_results(
            query_embedding=query_embedding, top_k=10
        )
        assert cached is not None

        # Cleanup
        await redis_client.delete("legacy_key_1", "legacy_key_2")


class TestHybridModeDisabled:
    """Test system behavior when hybrid mode is disabled."""

    @pytest.mark.asyncio
    async def test_system_works_without_hybrid_components(
        self, redis_client, milvus_manager
    ):
        """
        Test that system works when ENABLE_SPECULATIVE_RAG=false.

        Requirements: 12.1, 12.5
        """
        # This test verifies that the system can operate without
        # hybrid components initialized

        # Create basic components (without hybrid)
        embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)

        # Verify basic operations work
        text = "Test document"
        embedding = embedding_service.encode([text])[0]

        assert embedding is not None
        assert len(embedding) == embedding_service.dimension

        # Verify Milvus operations work
        chunk_id = "no_hybrid_test_1"
        milvus_manager.insert(
            chunk_id=chunk_id,
            document_id="no_hybrid_doc",
            document_name="test.txt",
            text=text,
            embedding=embedding.tolist(),
            metadata={},
        )

        # Search
        results = milvus_manager.search(query_embedding=embedding.tolist(), top_k=5)

        assert len(results) > 0

        # Cleanup
        milvus_manager.delete_by_filter(f'chunk_id == "{chunk_id}"')

    @pytest.mark.asyncio
    async def test_memory_works_without_hybrid(self, redis_client, milvus_manager):
        """
        Test that memory system works without hybrid components.

        Requirements: 12.5
        """
        # Create memory components
        embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
        memory_manager = MemoryManager(
            redis_client=redis_client,
            milvus_manager=milvus_manager,
            embedding_service=embedding_service,
        )

        session_id = "no_hybrid_session"

        # Test STM
        await memory_manager.add_to_stm(
            session_id=session_id, role="user", content="Test message"
        )

        context = await memory_manager.get_context(session_id=session_id, query="test")

        assert "conversation_history" in context
        assert len(context["conversation_history"]) == 1

        # Cleanup
        await memory_manager.clear_session(session_id)


# Fixtures


@pytest.fixture
async def redis_client():
    """Create Redis client for testing."""
    import redis.asyncio as redis

    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )

    yield client

    await client.close()


@pytest.fixture
def milvus_manager():
    """Create Milvus manager for testing."""
    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)

    manager = MilvusManager(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        collection_name=f"{settings.MILVUS_COLLECTION_NAME}_test",
        embedding_dim=embedding_service.dimension,
    )

    manager.connect()

    yield manager

    # Cleanup
    try:
        manager.drop_collection()
    except:
        pass

    manager.disconnect()


@pytest.fixture
def embedding_service():
    """Create embedding service for testing."""
    return EmbeddingService(model_name=settings.EMBEDDING_MODEL)
