"""
Unit Tests for AgentBuilderFacade

Tests the Facade pattern implementation for Agent Builder services.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.shared.errors import NotFoundError, ValidationError


class TestAgentBuilderFacade:
    """Test AgentBuilderFacade initialization and properties."""
    
    def test_facade_initialization(self):
        """Test facade initializes correctly."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        assert facade.db == db
        assert facade._workflow_service is None
        assert facade._agent_service is None
        assert facade._execution_service is None
        assert facade._block_service is None
    
    def test_workflows_property_lazy_initialization(self):
        """Test workflows property lazy initialization."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        # First access should initialize
        workflows = facade.workflows
        assert workflows is not None
        assert facade._workflow_service is not None
        
        # Second access should return same instance
        workflows2 = facade.workflows
        assert workflows is workflows2
    
    def test_agents_property_lazy_initialization(self):
        """Test agents property lazy initialization."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        agents = facade.agents
        assert agents is not None
        assert facade._agent_service is not None
    
    def test_executions_property_lazy_initialization(self):
        """Test executions property lazy initialization."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        executions = facade.executions
        assert executions is not None
        assert facade._execution_service is not None
    
    @patch('backend.services.agent_builder.facade.BlockService')
    def test_blocks_property_lazy_initialization(self, mock_service_class):
        """Test blocks property lazy initialization."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        blocks = facade.blocks
        assert blocks is not None
        assert facade._block_service is not None


class TestWorkflowOperations:
    """Test workflow operations through Facade."""
    
    @patch('backend.services.agent_builder.facade.WorkflowApplicationService')
    def test_create_workflow(self, mock_service_class):
        """Test creating a workflow through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        # Mock the service
        mock_service = Mock()
        mock_workflow = Mock()
        mock_workflow.id = str(uuid4())
        mock_workflow.name = "Test Workflow"
        mock_service.create_workflow.return_value = mock_workflow
        mock_service_class.return_value = mock_service
        
        # Create workflow
        result = facade.create_workflow(
            user_id=str(uuid4()),
            name="Test Workflow",
            nodes=[{"id": "start", "node_type": "start", "config": {}}],
            edges=[],
        )
        
        assert result == mock_workflow
        mock_service.create_workflow.assert_called_once()
    
    @patch('backend.services.agent_builder.facade.WorkflowApplicationService')
    def test_get_workflow(self, mock_service_class):
        """Test getting a workflow through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_workflow = Mock()
        workflow_id = str(uuid4())
        mock_workflow.id = workflow_id
        mock_service.get_workflow.return_value = mock_workflow
        mock_service_class.return_value = mock_service
        
        result = facade.get_workflow(workflow_id)
        
        assert result == mock_workflow
        mock_service.get_workflow.assert_called_once_with(workflow_id)
    
    @patch('backend.services.agent_builder.facade.WorkflowApplicationService')
    def test_get_workflow_not_found(self, mock_service_class):
        """Test getting a non-existent workflow raises NotFoundError."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        workflow_id = str(uuid4())
        mock_service.get_workflow.side_effect = NotFoundError("Workflow", workflow_id)
        mock_service_class.return_value = mock_service
        
        with pytest.raises(NotFoundError):
            facade.get_workflow(workflow_id)


class TestAgentOperations:
    """Test agent operations through Facade."""
    
    @patch('backend.services.agent_builder.facade.AgentApplicationService')
    def test_create_agent(self, mock_service_class):
        """Test creating an agent through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_agent = Mock()
        mock_agent.id = str(uuid4())
        mock_agent.name = "Test Agent"
        mock_service.create_agent.return_value = mock_agent
        mock_service_class.return_value = mock_service
        
        result = facade.create_agent(
            user_id=str(uuid4()),
            name="Test Agent",
            agent_type="assistant",
        )
        
        assert result == mock_agent
        mock_service.create_agent.assert_called_once()
    
    @patch('backend.services.agent_builder.facade.AgentApplicationService')
    def test_get_agent(self, mock_service_class):
        """Test getting an agent through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_agent = Mock()
        agent_id = str(uuid4())
        mock_agent.id = agent_id
        mock_service.get_agent.return_value = mock_agent
        mock_service_class.return_value = mock_service
        
        result = facade.get_agent(agent_id)
        
        assert result == mock_agent
        mock_service.get_agent.assert_called_once_with(agent_id)


class TestBlockOperations:
    """Test block operations through Facade."""
    
    @patch('backend.services.agent_builder.facade.BlockService')
    def test_create_block(self, mock_service_class):
        """Test creating a block through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_block = Mock()
        mock_block.id = str(uuid4())
        mock_block.name = "Test Block"
        mock_service.create_block.return_value = mock_block
        mock_service_class.return_value = mock_service
        
        block_data = Mock()
        result = facade.create_block(
            user_id=str(uuid4()),
            block_data=block_data,
        )
        
        assert result == mock_block
        mock_service.create_block.assert_called_once()
    
    @patch('backend.services.agent_builder.facade.BlockService')
    def test_get_block(self, mock_service_class):
        """Test getting a block through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_block = Mock()
        block_id = str(uuid4())
        mock_block.id = block_id
        mock_service.get_block.return_value = mock_block
        mock_service_class.return_value = mock_service
        
        result = facade.get_block(block_id)
        
        assert result == mock_block
        mock_service.get_block.assert_called_once_with(block_id)
    
    @patch('backend.services.agent_builder.facade.BlockService')
    def test_update_block(self, mock_service_class):
        """Test updating a block through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_block = Mock()
        block_id = str(uuid4())
        mock_block.id = block_id
        mock_service.update_block.return_value = mock_block
        mock_service_class.return_value = mock_service
        
        block_data = Mock()
        result = facade.update_block(block_id, block_data)
        
        assert result == mock_block
        mock_service.update_block.assert_called_once_with(block_id, block_data)
    
    @patch('backend.services.agent_builder.facade.BlockService')
    def test_delete_block(self, mock_service_class):
        """Test deleting a block through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        block_id = str(uuid4())
        facade.delete_block(block_id)
        
        mock_service.delete_block.assert_called_once_with(block_id)
    
    @patch('backend.services.agent_builder.facade.BlockService')
    def test_list_blocks(self, mock_service_class):
        """Test listing blocks through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_blocks = [Mock(), Mock(), Mock()]
        mock_service.list_blocks.return_value = mock_blocks
        mock_service_class.return_value = mock_service
        
        result = facade.list_blocks(user_id=str(uuid4()))
        
        assert result == mock_blocks
        mock_service.list_blocks.assert_called_once()


class TestExecutionOperations:
    """Test execution operations through Facade."""
    
    @patch('backend.services.agent_builder.facade.WorkflowApplicationService')
    @pytest.mark.asyncio
    async def test_execute_workflow(self, mock_service_class):
        """Test executing a workflow through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_result = Mock()
        mock_result.status = "completed"
        
        # Create async mock
        async def mock_execute(*args, **kwargs):
            return mock_result
        
        mock_service.execute_workflow = mock_execute
        mock_service_class.return_value = mock_service
        
        workflow_id = str(uuid4())
        result = await facade.execute_workflow(
            workflow_id=workflow_id,
            input_data={"test": "data"},
            user_id=str(uuid4()),
        )
        
        assert result == mock_result
    
    @patch('backend.services.agent_builder.facade.ExecutionApplicationService')
    def test_get_execution(self, mock_service_class):
        """Test getting an execution through facade."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_service = Mock()
        mock_execution = Mock()
        execution_id = str(uuid4())
        mock_execution.id = execution_id
        mock_service.get_execution.return_value = mock_execution
        mock_service_class.return_value = mock_service
        
        result = facade.get_execution(execution_id)
        
        assert result == mock_execution
        mock_service.get_execution.assert_called_once_with(execution_id)


class TestCQRSHandlers:
    """Test CQRS handler access through Facade."""
    
    @patch('backend.services.agent_builder.facade.WorkflowCommandHandler')
    def test_workflow_commands_property(self, mock_handler_class):
        """Test workflow commands property."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        result = facade.workflow_commands
        
        assert result == mock_handler
        mock_handler_class.assert_called_once_with(db)
    
    @patch('backend.services.agent_builder.facade.WorkflowQueryHandler')
    def test_workflow_queries_property(self, mock_handler_class):
        """Test workflow queries property."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        result = facade.workflow_queries
        
        assert result == mock_handler
        mock_handler_class.assert_called_once_with(db)
    
    @patch('backend.services.agent_builder.facade.AgentCommandHandler')
    def test_agent_commands_property(self, mock_handler_class):
        """Test agent commands property."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        result = facade.agent_commands
        
        assert result == mock_handler
        mock_handler_class.assert_called_once_with(db)
    
    @patch('backend.services.agent_builder.facade.AgentQueryHandler')
    def test_agent_queries_property(self, mock_handler_class):
        """Test agent queries property."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        
        result = facade.agent_queries
        
        assert result == mock_handler
        mock_handler_class.assert_called_once_with(db)


class TestLegacyExecutorAdapter:
    """Test legacy executor adapter."""
    
    @patch('backend.services.agent_builder.facade.get_executor')
    def test_get_legacy_executor_unified(self, mock_get_executor):
        """Test getting unified executor."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_executor = Mock()
        mock_get_executor.return_value = mock_executor
        
        result = facade.get_legacy_executor(use_unified=True)
        
        assert result == mock_executor
        mock_get_executor.assert_called_once_with(db, use_unified=True)
    
    @patch('backend.services.agent_builder.facade.get_executor')
    def test_get_legacy_executor_legacy(self, mock_get_executor):
        """Test getting legacy executor."""
        db = Mock()
        facade = AgentBuilderFacade(db)
        
        mock_executor = Mock()
        mock_get_executor.return_value = mock_executor
        
        result = facade.get_legacy_executor(use_unified=False)
        
        assert result == mock_executor
        mock_get_executor.assert_called_once_with(db, use_unified=False)


class TestFacadeHelperFunction:
    """Test get_facade helper function."""
    
    @patch('backend.services.agent_builder.facade.AgentBuilderFacade')
    def test_get_facade(self, mock_facade_class):
        """Test get_facade helper function."""
        from backend.services.agent_builder.facade import get_facade
        
        db = Mock()
        mock_facade = Mock()
        mock_facade_class.return_value = mock_facade
        
        result = get_facade(db)
        
        assert result == mock_facade
        mock_facade_class.assert_called_once_with(db)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
