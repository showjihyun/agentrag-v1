"""
Basic validation tests for MilvusManager.

These tests verify the core functionality without requiring a running Milvus instance.
"""

import pytest
from backend.services.milvus import MilvusManager, SearchResult


def test_milvus_manager_initialization():
    """Test MilvusManager can be initialized with valid parameters."""
    manager = MilvusManager(
        host="localhost",
        port=19530,
        collection_name="test_collection",
        embedding_dim=384,
    )

    assert manager.host == "localhost"
    assert manager.port == 19530
    assert manager.collection_name == "test_collection"
    assert manager.embedding_dim == 384
    assert not manager.is_connected()


def test_milvus_manager_invalid_parameters():
    """Test MilvusManager raises errors for invalid parameters."""

    # Empty host
    with pytest.raises(ValueError, match="host cannot be empty"):
        MilvusManager(host="", port=19530)

    # Invalid port
    with pytest.raises(ValueError, match="port must be positive"):
        MilvusManager(host="localhost", port=-1)

    # Empty collection name
    with pytest.raises(ValueError, match="collection_name cannot be empty"):
        MilvusManager(host="localhost", port=19530, collection_name="")

    # Invalid embedding dimension
    with pytest.raises(ValueError, match="embedding_dim must be positive"):
        MilvusManager(host="localhost", port=19530, embedding_dim=-1)


def test_search_result_creation():
    """Test SearchResult can be created and converted to dict."""
    result = SearchResult(
        id="chunk_1",
        document_id="doc_1",
        text="This is a test chunk",
        score=0.95,
        document_name="test.pdf",
        chunk_index=0,
        metadata={"file_type": "pdf"},
    )

    assert result.id == "chunk_1"
    assert result.document_id == "doc_1"
    assert result.score == 0.95

    result_dict = result.to_dict()
    assert result_dict["id"] == "chunk_1"
    assert result_dict["score"] == 0.95
    assert result_dict["metadata"]["file_type"] == "pdf"


def test_milvus_manager_repr():
    """Test string representation of MilvusManager."""
    manager = MilvusManager(
        host="localhost", port=19530, collection_name="test_collection"
    )

    repr_str = repr(manager)
    assert "localhost" in repr_str
    assert "19530" in repr_str
    assert "test_collection" in repr_str
    assert "connected=False" in repr_str


def test_insert_embeddings_validation():
    """Test insert_embeddings validates inputs correctly."""
    manager = MilvusManager()

    # Empty embeddings
    with pytest.raises(ValueError, match="embeddings cannot be empty"):
        import asyncio

        asyncio.run(manager.insert_embeddings([], []))

    # Empty metadata
    with pytest.raises(ValueError, match="metadata cannot be empty"):
        import asyncio

        asyncio.run(manager.insert_embeddings([[0.1, 0.2]], []))

    # Length mismatch
    with pytest.raises(ValueError, match="length mismatch"):
        import asyncio

        asyncio.run(manager.insert_embeddings([[0.1, 0.2]], [{}, {}]))


def test_search_validation():
    """Test search validates inputs correctly."""
    manager = MilvusManager(embedding_dim=384)

    # Empty query embedding
    with pytest.raises(ValueError, match="query_embedding cannot be empty"):
        import asyncio

        asyncio.run(manager.search([]))

    # Wrong dimension
    with pytest.raises(ValueError, match="dimension.*does not match"):
        import asyncio

        asyncio.run(manager.search([0.1, 0.2]))  # Only 2 dims, expected 384

    # Invalid top_k
    with pytest.raises(ValueError, match="top_k must be positive"):
        import asyncio

        asyncio.run(manager.search([0.1] * 384, top_k=0))


def test_delete_validation():
    """Test delete_by_document_id validates inputs correctly."""
    manager = MilvusManager()

    # Empty document_id
    with pytest.raises(ValueError, match="document_id cannot be empty"):
        import asyncio

        asyncio.run(manager.delete_by_document_id(""))


if __name__ == "__main__":
    # Run basic validation
    print("Running MilvusManager validation tests...")

    test_milvus_manager_initialization()
    print("✓ Initialization test passed")

    test_milvus_manager_invalid_parameters()
    print("✓ Invalid parameters test passed")

    test_search_result_creation()
    print("✓ SearchResult test passed")

    test_milvus_manager_repr()
    print("✓ String representation test passed")

    test_insert_embeddings_validation()
    print("✓ Insert validation test passed")

    test_search_validation()
    print("✓ Search validation test passed")

    test_delete_validation()
    print("✓ Delete validation test passed")

    print("\n✅ All validation tests passed!")
