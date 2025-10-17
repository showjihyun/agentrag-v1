"""
Integration tests for MilvusManager.

These tests require a running Milvus instance and test actual database operations:
- Collection creation and schema validation
- Insert, search, and delete operations
- Connection error handling
- End-to-end workflows

Requirements: 1.1, 1.3

To run these tests, ensure Milvus is running:
    docker-compose up -d milvus

Then run:
    pytest backend/tests/integration/test_milvus_integration.py -v
"""

import pytest
import asyncio
import time
from datetime import datetime
from pymilvus import connections, utility, MilvusException

from backend.services.milvus import MilvusManager, SearchResult
from backend.models.milvus_schema import (
    get_document_collection_schema,
    get_ltm_collection_schema,
)
from backend.config import settings


# Test configuration
TEST_HOST = settings.MILVUS_HOST
TEST_PORT = settings.MILVUS_PORT
TEST_COLLECTION = "test_integration_collection"
TEST_EMBEDDING_DIM = 384


@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def milvus_manager():
    """Create a MilvusManager instance for testing with automatic cleanup."""
    manager = MilvusManager(
        host=TEST_HOST,
        port=TEST_PORT,
        collection_name=TEST_COLLECTION,
        embedding_dim=TEST_EMBEDDING_DIM,
        max_retries=3,
        retry_delay=1.0,
    )

    try:
        manager.connect()
    except RuntimeError as e:
        pytest.skip(f"Milvus not available: {str(e)}")

    yield manager

    # Cleanup
    try:
        if utility.has_collection(TEST_COLLECTION, using=manager._connection_alias):
            utility.drop_collection(TEST_COLLECTION, using=manager._connection_alias)
    except Exception as e:
        print(f"Warning: Cleanup failed: {str(e)}")
    finally:
        manager.disconnect()


@pytest.fixture
def sample_embeddings():
    """Generate sample embeddings for testing."""
    return [
        [0.1] * TEST_EMBEDDING_DIM,
        [0.2] * TEST_EMBEDDING_DIM,
        [0.3] * TEST_EMBEDDING_DIM,
        [0.4] * TEST_EMBEDDING_DIM,
        [0.5] * TEST_EMBEDDING_DIM,
    ]


@pytest.fixture
def sample_metadata():
    """Generate sample metadata for testing."""
    timestamp = int(datetime.now().timestamp())
    return [
        {
            "id": f"chunk_{i}",
            "document_id": f"doc_{i // 2}",
            "text": f"This is test chunk number {i} with some content.",
            "chunk_index": i % 2,
            "document_name": f"test_document_{i // 2}.pdf",
            "file_type": "pdf",
            "upload_date": timestamp,
            "author": "",
            "creation_date": 0,
            "language": "",
            "keywords": "",
        }
        for i in range(5)
    ]


class TestMilvusConnection:
    """Test Milvus connection management - Requirement 1.1"""

    def test_connect_success(self):
        """Test successful connection to Milvus."""
        manager = MilvusManager(
            host=TEST_HOST, port=TEST_PORT, collection_name=TEST_COLLECTION
        )
        try:
            manager.connect()
            assert manager.is_connected()
        except RuntimeError:
            pytest.skip("Milvus not available")
        finally:
            manager.disconnect()

    def test_connect_invalid_host(self):
        """Test connection failure with invalid host."""
        manager = MilvusManager(
            host="invalid-host-12345",
            port=TEST_PORT,
            collection_name=TEST_COLLECTION,
            max_retries=1,
            retry_delay=0.1,
        )
        with pytest.raises(RuntimeError, match="Failed to connect"):
            manager.connect()

    def test_health_check_connected(self, milvus_manager):
        """Test health check when connected."""
        health = milvus_manager.health_check()
        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["host"] == TEST_HOST


class TestCollectionOperations:
    """Test collection creation and schema validation - Requirement 1.1"""

    def test_create_collection_default_schema(self, milvus_manager):
        """Test creating collection with default schema."""
        collection = milvus_manager.create_collection()
        assert collection is not None
        assert collection.name == TEST_COLLECTION

        # Verify schema fields
        schema = collection.schema
        field_names = [field.name for field in schema.fields]
        assert all(
            f in field_names
            for f in ["id", "document_id", "text", "embedding", "chunk_index"]
        )

    def test_create_collection_custom_schema(self, milvus_manager):
        """Test creating collection with custom schema."""
        custom_schema = get_ltm_collection_schema(TEST_EMBEDDING_DIM)
        collection = milvus_manager.create_collection(schema=custom_schema)
        assert collection is not None

        schema = collection.schema
        field_names = [field.name for field in schema.fields]
        assert all(
            f in field_names
            for f in ["query", "query_embedding", "response", "session_id"]
        )


class TestInsertOperations:
    """Test embedding insertion operations - Requirement 1.1"""

    @pytest.mark.asyncio
    async def test_insert_embeddings_success(
        self, milvus_manager, sample_embeddings, sample_metadata
    ):
        """Test successful insertion of embeddings."""
        milvus_manager.create_collection()
        ids = await milvus_manager.insert_embeddings(
            embeddings=sample_embeddings, metadata=sample_metadata
        )
        assert len(ids) == len(sample_embeddings)
        assert all(isinstance(id, str) for id in ids)

    @pytest.mark.asyncio
    async def test_insert_wrong_dimension(self, milvus_manager):
        """Test insertion fails with wrong embedding dimension."""
        milvus_manager.create_collection()
        wrong_embeddings = [[0.1, 0.2, 0.3]]
        metadata = [
            {
                "id": "test",
                "document_id": "doc",
                "text": "test",
                "chunk_index": 0,
                "document_name": "test.pdf",
                "file_type": "pdf",
                "upload_date": int(datetime.now().timestamp()),
                "author": "",
                "creation_date": 0,
                "language": "",
                "keywords": "",
            }
        ]
        with pytest.raises(ValueError, match="dimension"):
            await milvus_manager.insert_embeddings(
                embeddings=wrong_embeddings, metadata=metadata
            )


class TestSearchOperations:
    """Test vector similarity search operations - Requirement 1.3"""

    @pytest.mark.asyncio
    async def test_search_success(
        self, milvus_manager, sample_embeddings, sample_metadata
    ):
        """Test successful similarity search."""
        milvus_manager.create_collection()
        await milvus_manager.insert_embeddings(
            embeddings=sample_embeddings, metadata=sample_metadata
        )

        query_embedding = sample_embeddings[0]
        results = await milvus_manager.search(query_embedding=query_embedding, top_k=3)

        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)
        if results:
            assert results[0].score >= 0.99  # Very high similarity for exact match

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, milvus_manager, sample_embeddings, sample_metadata
    ):
        """Test search with filter expression - Requirement 1.3"""
        milvus_manager.create_collection()
        await milvus_manager.insert_embeddings(
            embeddings=sample_embeddings, metadata=sample_metadata
        )

        query_embedding = sample_embeddings[0]
        results = await milvus_manager.search(
            query_embedding=query_embedding, top_k=5, filters='document_id == "doc_0"'
        )
        assert all(r.document_id == "doc_0" for r in results)

    @pytest.mark.asyncio
    async def test_search_top_k(
        self, milvus_manager, sample_embeddings, sample_metadata
    ):
        """Test search respects top_k parameter - Requirement 1.3"""
        milvus_manager.create_collection()
        await milvus_manager.insert_embeddings(
            embeddings=sample_embeddings, metadata=sample_metadata
        )

        query_embedding = sample_embeddings[0]
        for k in [1, 2, 3, 5]:
            results = await milvus_manager.search(
                query_embedding=query_embedding, top_k=k
            )
            assert len(results) <= k


class TestDeleteOperations:
    """Test document deletion operations - Requirement 1.1"""

    @pytest.mark.asyncio
    async def test_delete_by_document_id(
        self, milvus_manager, sample_embeddings, sample_metadata
    ):
        """Test deleting all chunks for a document."""
        milvus_manager.create_collection()
        await milvus_manager.insert_embeddings(
            embeddings=sample_embeddings, metadata=sample_metadata
        )

        collection = milvus_manager.get_collection()
        collection.load()
        initial_count = collection.num_entities

        deleted_count = await milvus_manager.delete_by_document_id("doc_0")
        assert deleted_count == 2

        collection.flush()
        time.sleep(0.5)
        collection.load()
        assert collection.num_entities == initial_count - 2

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, milvus_manager):
        """Test deleting a document that doesn't exist."""
        milvus_manager.create_collection()
        deleted_count = await milvus_manager.delete_by_document_id("nonexistent_doc")
        assert deleted_count == 0


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows - Requirements 1.1, 1.3"""

    @pytest.mark.asyncio
    async def test_complete_document_lifecycle(self, milvus_manager):
        """Test complete lifecycle: insert, search, delete."""
        milvus_manager.create_collection()

        # Insert
        embeddings = [[0.1] * TEST_EMBEDDING_DIM, [0.2] * TEST_EMBEDDING_DIM]
        timestamp = int(datetime.now().timestamp())
        metadata = [
            {
                "id": f"chunk_{i}",
                "document_id": "lifecycle_doc",
                "text": f"Chunk {i}",
                "chunk_index": i,
                "document_name": "lifecycle.pdf",
                "file_type": "pdf",
                "upload_date": timestamp,
                "author": "",
                "creation_date": 0,
                "language": "",
                "keywords": "",
            }
            for i in range(2)
        ]

        ids = await milvus_manager.insert_embeddings(
            embeddings=embeddings, metadata=metadata
        )
        assert len(ids) == 2

        # Search
        results = await milvus_manager.search(query_embedding=embeddings[0], top_k=5)
        assert any(r.document_id == "lifecycle_doc" for r in results)

        # Delete
        deleted = await milvus_manager.delete_by_document_id("lifecycle_doc")
        assert deleted == 2

        # Verify deletion
        results_after = await milvus_manager.search(
            query_embedding=embeddings[0],
            top_k=5,
            filters='document_id == "lifecycle_doc"',
        )
        assert len(results_after) == 0


class TestErrorHandling:
    """Test error handling in various scenarios - Requirement 1.1"""

    @pytest.mark.asyncio
    async def test_insert_without_collection(self, milvus_manager):
        """Test insert fails gracefully without collection."""
        embeddings = [[0.1] * TEST_EMBEDDING_DIM]
        metadata = [
            {
                "id": "test",
                "document_id": "doc",
                "text": "test",
                "chunk_index": 0,
                "document_name": "test.pdf",
                "file_type": "pdf",
                "upload_date": int(datetime.now().timestamp()),
                "author": "",
                "creation_date": 0,
                "language": "",
                "keywords": "",
            }
        ]
        with pytest.raises(RuntimeError):
            await milvus_manager.insert_embeddings(
                embeddings=embeddings, metadata=metadata
            )

    def test_operations_without_connection(self):
        """Test operations fail without connection."""
        manager = MilvusManager(
            host=TEST_HOST, port=TEST_PORT, collection_name=TEST_COLLECTION
        )
        with pytest.raises(RuntimeError, match="Not connected"):
            manager.create_collection()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
