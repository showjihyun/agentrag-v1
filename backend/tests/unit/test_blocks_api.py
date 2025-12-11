"""
Unit Tests for Blocks API

Tests the Block management endpoints after DDD migration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from fastapi import HTTPException

from backend.api.agent_builder.blocks import (
    create_block,
    get_block,
    update_block,
    delete_block,
    list_blocks,
    test_block,
    get_block_versions,
)
from backend.services.agent_builder.shared.errors import NotFoundError, ValidationError


class TestCreateBlock:
    """Test create_block endpoint."""
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_create_block_success(self, mock_facade_class):
        """Test successful block creation."""
        # Setup
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        mock_block = Mock()
        mock_block.id = uuid4()
        mock_block.user_id = mock_user.id
        mock_block.name = "Test Block"
        mock_block.description = "Test Description"
        mock_block.block_type = "llm"
        mock_block.input_schema = {}
        mock_block.output_schema = {}
        mock_block.configuration = {}
        mock_block.implementation = "test"
        mock_block.is_public = False
        mock_block.created_at = "2025-01-01"
        mock_block.updated_at = "2025-01-01"
        
        mock_facade.create_block.return_value = mock_block
        mock_facade_class.return_value = mock_facade
        
        block_data = Mock()
        block_data.name = "Test Block"
        
        # Execute
        result = create_block(block_data, mock_user, mock_db)
        
        # Assert
        assert result.id == str(mock_block.id)
        assert result.name == "Test Block"
        mock_facade.create_block.assert_called_once()
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_create_block_validation_error(self, mock_facade_class):
        """Test block creation with validation error."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        mock_facade.create_block.side_effect = ValidationError("Invalid data")
        mock_facade_class.return_value = mock_facade
        
        block_data = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            create_block(block_data, mock_user, mock_db)
        
        assert exc_info.value.status_code == 400


class TestGetBlock:
    """Test get_block endpoint."""
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_get_block_success(self, mock_facade_class):
        """Test successful block retrieval."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        mock_block = Mock()
        block_id = str(uuid4())
        mock_block.id = block_id
        mock_block.user_id = mock_user.id
        mock_block.name = "Test Block"
        mock_block.description = "Test"
        mock_block.block_type = "llm"
        mock_block.input_schema = {}
        mock_block.output_schema = {}
        mock_block.configuration = {}
        mock_block.implementation = "test"
        mock_block.is_public = False
        mock_block.created_at = "2025-01-01"
        mock_block.updated_at = "2025-01-01"
        
        mock_facade.get_block.return_value = mock_block
        mock_facade_class.return_value = mock_facade
        
        result = get_block(block_id, mock_user, mock_db)
        
        assert result.id == block_id
        assert result.name == "Test Block"
        mock_facade.get_block.assert_called_once_with(block_id)
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_get_block_not_found(self, mock_facade_class):
        """Test getting non-existent block."""
        mock_db = Mock()
        mock_user = Mock()
        
        mock_facade = Mock()
        mock_facade.get_block.side_effect = NotFoundError("Block not found")
        mock_facade_class.return_value = mock_facade
        
        with pytest.raises(HTTPException) as exc_info:
            get_block(str(uuid4()), mock_user, mock_db)
        
        assert exc_info.value.status_code == 404
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_get_block_permission_denied(self, mock_facade_class):
        """Test getting block without permission."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        mock_block = Mock()
        mock_block.user_id = uuid4()  # Different user
        mock_block.is_public = False
        
        mock_facade.get_block.return_value = mock_block
        mock_facade_class.return_value = mock_facade
        
        with pytest.raises(HTTPException) as exc_info:
            get_block(str(uuid4()), mock_user, mock_db)
        
        assert exc_info.value.status_code == 403


class TestUpdateBlock:
    """Test update_block endpoint."""
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_update_block_success(self, mock_facade_class):
        """Test successful block update."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        
        # Existing block
        existing_block = Mock()
        existing_block.user_id = mock_user.id
        
        # Updated block
        updated_block = Mock()
        block_id = str(uuid4())
        updated_block.id = block_id
        updated_block.user_id = mock_user.id
        updated_block.name = "Updated Block"
        updated_block.description = "Updated"
        updated_block.block_type = "llm"
        updated_block.input_schema = {}
        updated_block.output_schema = {}
        updated_block.configuration = {}
        updated_block.implementation = "test"
        updated_block.is_public = False
        updated_block.created_at = "2025-01-01"
        updated_block.updated_at = "2025-01-02"
        
        mock_facade.get_block.return_value = existing_block
        mock_facade.update_block.return_value = updated_block
        mock_facade_class.return_value = mock_facade
        
        block_data = Mock()
        result = update_block(block_id, block_data, mock_user, mock_db)
        
        assert result.name == "Updated Block"
        mock_facade.update_block.assert_called_once()
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_update_block_not_owner(self, mock_facade_class):
        """Test updating block by non-owner."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        existing_block = Mock()
        existing_block.user_id = uuid4()  # Different user
        
        mock_facade.get_block.return_value = existing_block
        mock_facade_class.return_value = mock_facade
        
        with pytest.raises(HTTPException) as exc_info:
            update_block(str(uuid4()), Mock(), mock_user, mock_db)
        
        assert exc_info.value.status_code == 403


class TestDeleteBlock:
    """Test delete_block endpoint."""
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_delete_block_success(self, mock_facade_class):
        """Test successful block deletion."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        existing_block = Mock()
        existing_block.user_id = mock_user.id
        
        mock_facade.get_block.return_value = existing_block
        mock_facade_class.return_value = mock_facade
        
        result = delete_block(str(uuid4()), mock_user, mock_db)
        
        assert result.status_code == 204
        mock_facade.delete_block.assert_called_once()
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_delete_block_not_found(self, mock_facade_class):
        """Test deleting non-existent block."""
        mock_db = Mock()
        mock_user = Mock()
        
        mock_facade = Mock()
        mock_facade.get_block.side_effect = NotFoundError("Block not found")
        mock_facade_class.return_value = mock_facade
        
        with pytest.raises(HTTPException) as exc_info:
            delete_block(str(uuid4()), mock_user, mock_db)
        
        assert exc_info.value.status_code == 404


class TestListBlocks:
    """Test list_blocks endpoint."""
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_list_blocks_success(self, mock_facade_class):
        """Test successful block listing."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        mock_blocks = []
        for i in range(3):
            block = Mock()
            block.id = uuid4()
            block.user_id = mock_user.id
            block.name = f"Block {i}"
            block.description = f"Description {i}"
            block.block_type = "llm"
            block.input_schema = {}
            block.output_schema = {}
            block.configuration = {}
            block.implementation = "test"
            block.is_public = False
            block.created_at = "2025-01-01"
            block.updated_at = "2025-01-01"
            mock_blocks.append(block)
        
        mock_facade.list_blocks.return_value = mock_blocks
        mock_facade_class.return_value = mock_facade
        
        result = list_blocks(
            skip=0,
            limit=50,
            block_type=None,
            search=None,
            include_public=False,
            current_user=mock_user,
            db=mock_db,
        )
        
        assert result.total == 3
        assert len(result.blocks) == 3
        mock_facade.list_blocks.assert_called()


class TestTestBlock:
    """Test test_block endpoint."""
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    @pytest.mark.asyncio
    async def test_test_block_success(self, mock_facade_class):
        """Test successful block testing."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        
        # Block
        mock_block = Mock()
        mock_block.user_id = mock_user.id
        mock_block.is_public = False
        
        # Test result
        mock_result = Mock()
        mock_result.success = True
        mock_result.output = {"result": "success"}
        
        mock_facade.get_block.return_value = mock_block
        mock_facade.test_block = MagicMock(return_value=mock_result)
        mock_facade_class.return_value = mock_facade
        
        test_request = Mock()
        result = await test_block(str(uuid4()), test_request, mock_user, mock_db)
        
        assert result == mock_result
        mock_facade.test_block.assert_called_once()


class TestGetBlockVersions:
    """Test get_block_versions endpoint."""
    
    @patch('backend.api.agent_builder.blocks.AgentBuilderFacade')
    def test_get_block_versions_success(self, mock_facade_class):
        """Test successful version retrieval."""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = uuid4()
        
        mock_facade = Mock()
        
        # Block
        mock_block = Mock()
        mock_block.user_id = mock_user.id
        mock_block.is_public = False
        
        # Versions
        mock_versions = [Mock(), Mock()]
        
        mock_facade.get_block.return_value = mock_block
        mock_facade.get_block_versions.return_value = mock_versions
        mock_facade_class.return_value = mock_facade
        
        result = get_block_versions(str(uuid4()), mock_user, mock_db)
        
        assert result == mock_versions
        mock_facade.get_block_versions.assert_called_once()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
