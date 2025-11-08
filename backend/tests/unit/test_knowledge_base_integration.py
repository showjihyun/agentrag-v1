"""
Knowledge Base Integration Tests.

Tests for Knowledge Base block, Milvus connector, and search service integration.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.core.blocks.knowledge_base_block import (
    KnowledgeBaseBlock,
    KnowledgeBaseUploadBlock,
)
from backend.core.blocks import BlockRegistry, BlockExecutionError
from backend.core.knowledge_base.milvus_connector import MilvusConnector
from backend.core.knowledge_base.search_service import SearchService


# ============================================================================
# Milvus Connector Tests
# ============================================================================

class TestMilvusConnector:
    """Tests for MilvusConnector."""

    @patch("backend.core.knowledge_base.milvus_connector.connections")
    @patch("backend.core.knowledge_base.milvus_connector.utility")
    @patch("backend.core.knowledge_base.milvus_connector.Collection")
    def test_connect_success(self, mock_collection, mock_utility, mock_connections):
        """Test successful Milvus connection."""
        # Setup mocks
        mock_utility.has_collection.return_value = True
        mock_collection_instance = Mock()
        mock_collection.return_value = mock_collection_instance
        
        # Create connector
        connector = MilvusConnector()
        
        # Connect
        result = connector.connect()
        
        # Verify
        assert result is True
        assert connector._connected is True
        mock_connections.connect.assert_called_once()
        mock_collection_instance.load.assert_called_once()

    @patch("backend.core.knowledge_base.milvus_connector.connections")
    @patch("backend.core.knowledge_base.milvus_connector.utility")
    def test_connect_collection_not_found(self, mock_utility, mock_connections):
        """Test connection failure when collection doesn't exist."""
        # Setup mocks
        mock_utility.has_collection.return_value = False
        
        # Create connector
        connector = MilvusConnector()
        
        # Connect should raise error
        with pytest.raises(RuntimeError) as exc_info:
            connector.connect()
        
        assert "does not exist" in str(exc_info.value)

    @patch("backend.core.knowledge_base.milvus_connector.connections")
    def test_disconnect(self, mock_connections):
        """Test Milvus disconnection."""
        # Create connector
        connector = MilvusConnector()
        connector._connected = True
        connector._collection = Mock()
        
        # Disconnect
        connector.disconnect()
        
        # Verify
        assert connector._connected is False
        assert connector._collection is None
        mock_connections.disconnect.assert_called_once()

    def test_build_filter_expression_string(self):
        """Test building filter expression with string values."""
        connector = MilvusConnector()
        
        filters = {"author": "John Doe", "language": "en"}
        expr = connector._build_filter_expression(filters)
        
        assert 'author == "John Doe"' in expr
        assert 'language == "en"' in expr
        assert "&&" in expr

    def test_build_filter_expression_numeric(self):
        """Test building filter expression with numeric values."""
        connector = MilvusConnector()
        
        filters = {"chunk_index": 5, "upload_date": 1234567890}
        expr = connector._build_filter_expression(filters)
        
        assert "chunk_index == 5" in expr
        assert "upload_date == 1234567890" in expr

    def test_build_filter_expression_list(self):
        """Test building filter expression with list values."""
        connector = MilvusConnector()
        
        filters = {"language": ["en", "ko", "ja"]}
        expr = connector._build_filter_expression(filters)
        
        assert "language in" in expr
        assert '"en"' in expr
        assert '"ko"' in expr

    def test_build_filter_expression_range(self):
        """Test building filter expression with range queries."""
        connector = MilvusConnector()
        
        filters = {
            "upload_date": {"$gte": 1000000, "$lte": 2000000},
            "chunk_index": {"$gt": 0, "$lt": 100}
        }
        expr = connector._build_filter_expression(filters)
        
        assert "upload_date >= 1000000" in expr
        assert "upload_date <= 2000000" in expr
        assert "chunk_index > 0" in expr
        assert "chunk_index < 100" in expr

    def test_build_filter_expression_empty(self):
        """Test building filter expression with empty filters."""
        connector = MilvusConnector()
        
        expr = connector._build_filter_expression({})
        assert expr == ""
        
        expr = connector._build_filter_expression(None)
        assert expr == ""

    @patch("backend.core.knowledge_base.milvus_connector.connections")
    @patch("backend.core.knowledge_base.milvus_connector.utility")
    @patch("backend.core.knowledge_base.milvus_connector.Collection")
    def test_search_basic(self, mock_collection_class, mock_utility, mock_connections):
        """Test basic vector search."""
        # Setup mocks
        mock_utility.has_collection.return_value = True
        mock_collection = Mock()
        mock_collection.num_entities = 1000
        mock_collection_class.return_value = mock_collection
        
        # Mock search results
        mock_hit = Mock()
        mock_hit.id = "doc1"
        mock_hit.score = 0.95
        mock_hit.distance = 0.05
        mock_hit.entity.get = Mock(side_effect=lambda x: {
            "text": "Sample text",
            "document_name": "test.pdf",
            "author": "John Doe"
        }.get(x))
        
        mock_collection.search.return_value = [[mock_hit]]
        
        # Create connector and connect
        connector = MilvusConnector()
        connector.connect()
        
        # Perform search
        query_embedding = [0.1] * 384
        results = connector.search(
            query_embedding=query_embedding,
            top_k=5,
            output_fields=["text", "document_name", "author"]
        )
        
        # Verify
        assert len(results) == 1
        assert results[0]["id"] == "doc1"
        assert results[0]["score"] == 0.95
        assert results[0]["text"] == "Sample text"
        assert results[0]["document_name"] == "test.pdf"

    @patch("backend.core.knowledge_base.milvus_connector.connections")
    @patch("backend.core.knowledge_base.milvus_connector.utility")
    @patch("backend.core.knowledge_base.milvus_connector.Collection")
    def test_search_with_filters(self, mock_collection_class, mock_utility, mock_connections):
        """Test vector search with metadata filters."""
        # Setup mocks
        mock_utility.has_collection.return_value = True
        mock_collection = Mock()
        mock_collection.num_entities = 1000
        mock_collection_class.return_value = mock_collection
        
        mock_collection.search.return_value = [[]]
        
        # Create connector and connect
        connector = MilvusConnector()
        connector.connect()
        
        # Perform search with filters
        query_embedding = [0.1] * 384
        filters = {"author": "John Doe", "language": "en"}
        
        results = connector.search(
            query_embedding=query_embedding,
            top_k=5,
            filters=filters,
            output_fields=["text"]
        )
        
        # Verify search was called with filter expression
        call_args = mock_collection.search.call_args
        assert call_args[1]["expr"] is not None
        assert 'author == "John Doe"' in call_args[1]["expr"]


# ============================================================================
# Search Service Tests
# ============================================================================

class TestSearchService:
    """Tests for SearchService."""

    @pytest.mark.asyncio
    @patch("backend.core.knowledge_base.search_service.get_milvus_connector")
    @patch("backend.core.knowledge_base.search_service.get_embedding_workflow")
    async def test_search_basic(self, mock_embedding_workflow, mock_connector):
        """Test basic semantic search."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector_instance.search.return_value = [
            {
                "id": "doc1",
                "score": 0.95,
                "text": "Machine learning is a subset of AI",
                "document_name": "ml_guide.pdf",
                "document_id": "doc123",
                "chunk_index": 0,
                "file_type": "pdf",
                "author": "John Doe",
                "keywords": "AI, ML",
                "language": "en",
            }
        ]
        mock_connector.return_value = mock_connector_instance
        
        mock_embedding_instance = Mock()
        mock_embedding_instance.generate_embedding = AsyncMock(
            return_value=[0.1] * 384
        )
        mock_embedding_workflow.return_value = mock_embedding_instance
        
        # Create service
        service = SearchService()
        
        # Perform search
        results = await service.search(
            query="What is machine learning?",
            top_k=5,
            include_metadata=True
        )
        
        # Verify
        assert len(results) == 1
        assert results[0]["text"] == "Machine learning is a subset of AI"
        assert results[0]["score"] == 0.95
        assert "metadata" in results[0]
        assert results[0]["metadata"]["author"] == "John Doe"

    @pytest.mark.asyncio
    @patch("backend.core.knowledge_base.search_service.get_milvus_connector")
    @patch("backend.core.knowledge_base.search_service.get_embedding_workflow")
    async def test_search_with_filters(self, mock_embedding_workflow, mock_connector):
        """Test search with metadata filters."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector_instance.search.return_value = []
        mock_connector.return_value = mock_connector_instance
        
        mock_embedding_instance = Mock()
        mock_embedding_instance.generate_embedding = AsyncMock(
            return_value=[0.1] * 384
        )
        mock_embedding_workflow.return_value = mock_embedding_instance
        
        # Create service
        service = SearchService()
        
        # Perform search with filters
        filters = {"author": "John Doe", "language": "en"}
        results = await service.search(
            query="test query",
            top_k=5,
            filters=filters
        )
        
        # Verify filters were passed
        mock_connector_instance.search.assert_called_once()
        call_args = mock_connector_instance.search.call_args
        assert call_args[1]["filters"] == filters

    @pytest.mark.asyncio
    @patch("backend.core.knowledge_base.search_service.get_milvus_connector")
    @patch("backend.core.knowledge_base.search_service.get_embedding_workflow")
    async def test_search_with_ranking(self, mock_embedding_workflow, mock_connector):
        """Test search with custom ranking."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector_instance.search.return_value = [
            {
                "id": "doc1",
                "score": 0.9,
                "text": "Old document",
                "document_name": "old.pdf",
                "document_id": "doc1",
                "chunk_index": 0,
                "file_type": "pdf",
                "author": "John",
                "keywords": "",
                "language": "en",
                "upload_date": 1000000,
            },
            {
                "id": "doc2",
                "score": 0.8,
                "text": "New document",
                "document_name": "new.pdf",
                "document_id": "doc2",
                "chunk_index": 0,
                "file_type": "pdf",
                "author": "Jane",
                "keywords": "",
                "language": "en",
                "upload_date": 2000000,
            }
        ]
        mock_connector.return_value = mock_connector_instance
        
        mock_embedding_instance = Mock()
        mock_embedding_instance.generate_embedding = AsyncMock(
            return_value=[0.1] * 384
        )
        mock_embedding_workflow.return_value = mock_embedding_instance
        
        # Create service
        service = SearchService()
        
        # Test recency ranking
        results = await service.search_with_ranking(
            query="test",
            top_k=2,
            ranking_method="recency"
        )
        
        # Newer document should be first
        assert results[0]["document_name"] == "new.pdf"
        assert results[1]["document_name"] == "old.pdf"

    def test_format_search_results(self):
        """Test search result formatting."""
        service = SearchService()
        
        raw_results = [
            {
                "id": "doc1",
                "score": 0.95,
                "text": "Sample text",
                "document_name": "test.pdf",
                "document_id": "doc123",
                "chunk_index": 0,
                "file_type": "pdf",
                "author": "John Doe",
                "keywords": "AI, ML",
                "language": "en",
            }
        ]
        
        # With metadata
        formatted = service._format_search_results(raw_results, include_metadata=True)
        assert len(formatted) == 1
        assert "metadata" in formatted[0]
        assert formatted[0]["metadata"]["author"] == "John Doe"
        
        # Without metadata
        formatted = service._format_search_results(raw_results, include_metadata=False)
        assert "metadata" not in formatted[0]

    def test_hybrid_ranking(self):
        """Test hybrid ranking algorithm."""
        service = SearchService()
        
        results = [
            {
                "score": 0.9,
                "metadata": {"upload_date": 1000000},
                "text": "Old but relevant"
            },
            {
                "score": 0.7,
                "metadata": {"upload_date": 2000000},
                "text": "New but less relevant"
            }
        ]
        
        ranked = service._hybrid_ranking(results)
        
        # Should have hybrid_score
        assert "hybrid_score" in ranked[0]
        assert "hybrid_score" in ranked[1]


# ============================================================================
# Knowledge Base Block Tests
# ============================================================================

class TestKnowledgeBaseBlock:
    """Tests for KnowledgeBaseBlock."""

    def test_block_registration(self):
        """Test Knowledge Base block is registered."""
        assert BlockRegistry.is_registered("knowledge_base")
        
        config = BlockRegistry.get_block_config("knowledge_base")
        assert config["name"] == "Knowledge Base"
        assert config["category"] == "tools"

    @pytest.mark.asyncio
    @patch("backend.core.blocks.knowledge_base_block.get_search_service")
    @patch("backend.core.blocks.knowledge_base_block.get_milvus_connector")
    async def test_execute_basic_search(self, mock_connector, mock_search_service):
        """Test basic Knowledge Base block execution."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector.return_value = mock_connector_instance
        
        mock_service = Mock()
        mock_service.search = AsyncMock(return_value=[
            {
                "text": "Machine learning result",
                "score": 0.95,
                "document_name": "ml.pdf"
            }
        ])
        mock_search_service.return_value = mock_service
        
        # Create block
        block = KnowledgeBaseBlock(
            block_id="test_kb",
            sub_blocks={
                "kb_config": {
                    "query": "What is machine learning?",
                    "topK": 5
                }
            }
        )
        
        # Execute
        result = await block.execute(
            inputs={},
            context={}
        )
        
        # Verify
        assert result["count"] == 1
        assert len(result["results"]) == 1
        assert result["query"] == "What is machine learning?"
        assert result["results"][0]["text"] == "Machine learning result"

    @pytest.mark.asyncio
    @patch("backend.core.blocks.knowledge_base_block.get_search_service")
    @patch("backend.core.blocks.knowledge_base_block.get_milvus_connector")
    async def test_execute_with_filters(self, mock_connector, mock_search_service):
        """Test Knowledge Base block with metadata filters."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector.return_value = mock_connector_instance
        
        mock_service = Mock()
        mock_service.search = AsyncMock(return_value=[])
        mock_search_service.return_value = mock_service
        
        # Create block with filters
        block = KnowledgeBaseBlock(
            block_id="test_kb",
            sub_blocks={
                "kb_config": {
                    "query": "test query",
                    "topK": 5,
                    "filters": {"author": "John Doe", "language": "en"}
                }
            }
        )
        
        # Execute
        result = await block.execute(
            inputs={},
            context={}
        )
        
        # Verify filters were passed
        mock_service.search.assert_called_once()
        call_args = mock_service.search.call_args
        assert call_args[1]["filters"] == {"author": "John Doe", "language": "en"}

    @pytest.mark.asyncio
    @patch("backend.core.blocks.knowledge_base_block.get_search_service")
    @patch("backend.core.blocks.knowledge_base_block.get_milvus_connector")
    async def test_execute_with_ranking(self, mock_connector, mock_search_service):
        """Test Knowledge Base block with custom ranking."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector.return_value = mock_connector_instance
        
        mock_service = Mock()
        mock_service.search_with_ranking = AsyncMock(return_value=[])
        mock_search_service.return_value = mock_service
        
        # Create block with ranking
        block = KnowledgeBaseBlock(
            block_id="test_kb",
            sub_blocks={
                "kb_config": {
                    "query": "test query",
                    "topK": 5
                },
                "ranking_method": "hybrid"
            }
        )
        
        # Execute
        result = await block.execute(
            inputs={},
            context={}
        )
        
        # Verify ranking method was used
        mock_service.search_with_ranking.assert_called_once()
        call_args = mock_service.search_with_ranking.call_args
        assert call_args[1]["ranking_method"] == "hybrid"

    @pytest.mark.asyncio
    async def test_execute_missing_query(self):
        """Test Knowledge Base block fails without query."""
        block = KnowledgeBaseBlock(
            block_id="test_kb",
            sub_blocks={}
        )
        
        # Execute should fail
        with pytest.raises(BlockExecutionError) as exc_info:
            await block.execute(
                inputs={},
                context={}
            )
        
        assert "query is required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("backend.core.blocks.knowledge_base_block.get_search_service")
    @patch("backend.core.blocks.knowledge_base_block.get_milvus_connector")
    async def test_execute_json_filters(self, mock_connector, mock_search_service):
        """Test Knowledge Base block with JSON string filters."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector.return_value = mock_connector_instance
        
        mock_service = Mock()
        mock_service.search = AsyncMock(return_value=[])
        mock_search_service.return_value = mock_service
        
        # Create block with JSON string filters
        block = KnowledgeBaseBlock(
            block_id="test_kb",
            sub_blocks={
                "kb_config": {
                    "query": "test",
                    "topK": 5,
                    "filters": '{"author": "John Doe"}'
                }
            }
        )
        
        # Execute
        result = await block.execute(
            inputs={},
            context={}
        )
        
        # Verify filters were parsed
        call_args = mock_service.search.call_args
        assert call_args[1]["filters"] == {"author": "John Doe"}

    @pytest.mark.asyncio
    @patch("backend.core.blocks.knowledge_base_block.get_search_service")
    @patch("backend.core.blocks.knowledge_base_block.get_milvus_connector")
    async def test_execute_input_override(self, mock_connector, mock_search_service):
        """Test Knowledge Base block with input override."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector.return_value = mock_connector_instance
        
        mock_service = Mock()
        mock_service.search = AsyncMock(return_value=[])
        mock_search_service.return_value = mock_service
        
        # Create block
        block = KnowledgeBaseBlock(
            block_id="test_kb",
            sub_blocks={
                "kb_config": {
                    "query": "default query",
                    "topK": 5
                }
            }
        )
        
        # Execute with input override
        result = await block.execute(
            inputs={
                "query": "override query",
                "top_k": 10
            },
            context={}
        )
        
        # Verify override was used
        call_args = mock_service.search.call_args
        assert call_args[1]["query"] == "override query"
        assert call_args[1]["top_k"] == 10


# ============================================================================
# Knowledge Base Upload Block Tests
# ============================================================================

class TestKnowledgeBaseUploadBlock:
    """Tests for KnowledgeBaseUploadBlock."""

    def test_upload_block_registration(self):
        """Test Knowledge Base Upload block is registered."""
        assert BlockRegistry.is_registered("knowledge_base_upload")
        
        config = BlockRegistry.get_block_config("knowledge_base_upload")
        assert config["name"] == "Upload to Knowledge Base"
        assert config["category"] == "tools"

    @pytest.mark.asyncio
    async def test_execute_missing_file(self):
        """Test upload block fails without file."""
        block = KnowledgeBaseUploadBlock(
            block_id="test_upload",
            sub_blocks={}
        )
        
        # Execute should fail
        with pytest.raises(BlockExecutionError) as exc_info:
            await block.execute(
                inputs={},
                context={}
            )
        
        assert "file_content or file_path is required" in str(exc_info.value).lower()


# ============================================================================
# Integration Tests
# ============================================================================

class TestKnowledgeBaseIntegration:
    """Integration tests for Knowledge Base workflow."""

    @pytest.mark.asyncio
    @patch("backend.core.blocks.knowledge_base_block.get_search_service")
    @patch("backend.core.blocks.knowledge_base_block.get_milvus_connector")
    async def test_workflow_search_execution(self, mock_connector, mock_search_service):
        """Test Knowledge Base block in workflow context."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector.return_value = mock_connector_instance
        
        mock_service = Mock()
        mock_service.search = AsyncMock(return_value=[
            {
                "text": "Result 1",
                "score": 0.95,
                "document_name": "doc1.pdf",
                "metadata": {"author": "John"}
            },
            {
                "text": "Result 2",
                "score": 0.85,
                "document_name": "doc2.pdf",
                "metadata": {"author": "Jane"}
            }
        ])
        mock_search_service.return_value = mock_service
        
        # Create block
        block = BlockRegistry.create_block_instance(
            "knowledge_base",
            block_id="kb_search",
            config={},
            sub_blocks={
                "kb_config": {
                    "query": "test query",
                    "topK": 5
                }
            }
        )
        
        # Execute in workflow context
        context = {
            "workflow_id": "test_workflow",
            "execution_id": "exec_123",
            "variables": {}
        }
        
        result = await block.execute(
            inputs={},
            context=context
        )
        
        # Verify workflow-compatible output
        assert "results" in result
        assert "count" in result
        assert "query" in result
        assert result["count"] == 2
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    @patch("backend.core.blocks.knowledge_base_block.get_search_service")
    @patch("backend.core.blocks.knowledge_base_block.get_milvus_connector")
    async def test_multiple_searches_in_workflow(self, mock_connector, mock_search_service):
        """Test multiple Knowledge Base searches in same workflow."""
        # Setup mocks
        mock_connector_instance = Mock()
        mock_connector_instance._connected = True
        mock_connector.return_value = mock_connector_instance
        
        mock_service = Mock()
        mock_service.search = AsyncMock(return_value=[])
        mock_search_service.return_value = mock_service
        
        # Create two blocks
        block1 = KnowledgeBaseBlock(
            block_id="kb1",
            sub_blocks={"kb_config": {"query": "query 1", "topK": 5}}
        )
        
        block2 = KnowledgeBaseBlock(
            block_id="kb2",
            sub_blocks={"kb_config": {"query": "query 2", "topK": 3}}
        )
        
        # Execute both
        context = {"workflow_id": "test", "execution_id": "exec"}
        
        result1 = await block1.execute(inputs={}, context=context)
        result2 = await block2.execute(inputs={}, context=context)
        
        # Verify both executed
        assert result1["query"] == "query 1"
        assert result2["query"] == "query 2"
        assert mock_service.search.call_count == 2
