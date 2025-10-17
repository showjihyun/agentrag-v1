"""
Unit tests for dependency injection container.
"""

import pytest
from backend.core.dependencies import ServiceContainer
from backend.services.embedding import EmbeddingService


@pytest.mark.asyncio
async def test_service_container_initialization():
    """Test that ServiceContainer initializes correctly."""
    container = ServiceContainer()

    # Should not be initialized yet
    assert not container._initialized

    # Initialize
    await container.initialize()

    # Should be initialized
    assert container._initialized

    # Cleanup
    await container.cleanup()

    # Should not be initialized after cleanup
    assert not container._initialized


@pytest.mark.asyncio
async def test_service_container_get_services():
    """Test getting services from container."""
    container = ServiceContainer()
    await container.initialize()

    try:
        # Get services
        embedding_service = container.get_embedding_service()
        assert embedding_service is not None
        assert isinstance(embedding_service, EmbeddingService)

        milvus_manager = container.get_milvus_manager()
        assert milvus_manager is not None

        llm_manager = container.get_llm_manager()
        assert llm_manager is not None

        document_processor = container.get_document_processor()
        assert document_processor is not None

        memory_manager = container.get_memory_manager()
        assert memory_manager is not None

        aggregator_agent = container.get_aggregator_agent()
        assert aggregator_agent is not None

    finally:
        await container.cleanup()


@pytest.mark.asyncio
async def test_service_container_error_before_init():
    """Test that getting services before initialization raises error."""
    container = ServiceContainer()

    with pytest.raises(RuntimeError, match="not initialized"):
        container.get_embedding_service()


@pytest.mark.asyncio
async def test_service_container_override():
    """Test overriding services for testing."""
    container = ServiceContainer()

    # Create mock embedding service
    mock_embedding = EmbeddingService(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Override
    container.set_embedding_service(mock_embedding)

    # Get service
    service = container.get_embedding_service()
    assert service is mock_embedding
