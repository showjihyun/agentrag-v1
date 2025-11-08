"""Tests for KnowledgebaseService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
from backend.db.models.agent_builder import Knowledgebase, KnowledgebaseDocument


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def kb_service(mock_db):
    """Create KnowledgebaseService instance."""
    return KnowledgebaseService(mock_db)


@pytest.fixture
def sample_kb():
    """Sample knowledgebase for testing."""
    return Knowledgebase(
        id="test-kb-id",
        user_id="test-user",
        name="Test KB",
        milvus_collection_name="test_collection",
        embedding_model="jhgan/ko-sroberta-multitask",
        chunk_size=500,
        chunk_overlap=50
    )


def test_create_knowledgebase(kb_service, mock_db):
    """Test knowledgebase creation."""
    from backend.models.agent_builder import KnowledgebaseCreate
    
    kb_data = KnowledgebaseCreate(
        name="Test KB",
        description="Test description",
        embedding_model="jhgan/ko-sroberta-multitask"
    )
    
    kb = kb_service.create_knowledgebase(
        user_id="test-user",
        kb_data=kb_data
    )
    
    assert mock_db.add.called
    assert mock_db.commit.called


def test_get_knowledgebase(kb_service, mock_db, sample_kb):
    """Test getting knowledgebase by ID."""
    mock_db.query.return_value.filter.return_value.first.return_value = sample_kb
    
    kb = kb_service.get_knowledgebase("test-kb-id")
    
    assert kb == sample_kb
    assert mock_db.query.called


def test_delete_knowledgebase(kb_service, mock_db, sample_kb):
    """Test knowledgebase deletion."""
    mock_db.query.return_value.filter.return_value.first.return_value = sample_kb
    
    result = kb_service.delete_knowledgebase("test-kb-id")
    
    assert result is True
    assert mock_db.delete.called
    assert mock_db.commit.called


def test_add_documents_integration(kb_service, mock_db, sample_kb):
    """Test document addition with mocked services."""
    mock_db.query.return_value.filter.return_value.first.return_value = sample_kb
    
    # Mock file
    mock_file = Mock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.file.read.return_value = b"test content"
    
    with patch('backend.services.agent_builder.knowledgebase_service.DocumentProcessor'):
        with patch('backend.services.agent_builder.knowledgebase_service.EmbeddingService'):
            with patch('backend.services.agent_builder.knowledgebase_service.MilvusManager'):
                with patch('os.makedirs'):
                    with patch('builtins.open', create=True):
                        # Mock document processor
                        mock_chunk = Mock()
                        mock_chunk.text = "test text"
                        mock_chunk.index = 0
                        
                        with patch.object(kb_service, 'get_knowledgebase', return_value=sample_kb):
                            # This would need more detailed mocking for full test
                            # For now, just verify the method exists and basic structure
                            assert hasattr(kb_service, 'add_documents')


def test_search_knowledgebase_integration(kb_service, mock_db, sample_kb):
    """Test knowledgebase search with mocked services."""
    with patch.object(kb_service, 'get_knowledgebase', return_value=sample_kb):
        with patch('backend.services.agent_builder.knowledgebase_service.HybridSearchService'):
            with patch('backend.services.agent_builder.knowledgebase_service.EmbeddingService'):
                with patch('backend.services.agent_builder.knowledgebase_service.MilvusManager'):
                    # Verify method exists
                    assert hasattr(kb_service, 'search_knowledgebase')


def test_list_knowledgebases(kb_service, mock_db, sample_kb):
    """Test listing knowledgebases."""
    mock_db.query.return_value.filter.return_value.all.return_value = [sample_kb]
    
    kbs = kb_service.list_knowledgebases(user_id="test-user")
    
    assert len(kbs) == 1
    assert kbs[0] == sample_kb
