"""Unit tests for AgentServiceRefactored."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid

from backend.services.agent_builder.agent_service_refactored import AgentServiceRefactored
from backend.models.agent_builder import AgentCreate, AgentUpdate
from backend.db.models.agent_builder import Agent
from backend.exceptions.agent_builder import (
    AgentNotFoundException,
    AgentValidationException,
    AgentToolNotFoundException
)


class TestAgentServiceRefactored:
    """Test AgentServiceRefactored methods."""
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    @patch('backend.services.agent_builder.agent_service_refactored.transaction')
    def test_create_agent_success(self, mock_transaction, mock_repo_class):
        """Test successful agent creation."""
        # Setup mocks
        db_mock = Mock()
        cache_mock = Mock()
        event_bus_mock = Mock()
        
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        # Mock transaction context manager
        mock_transaction.return_value.__enter__ = Mock()
        mock_transaction.return_value.__exit__ = Mock(return_value=False)
        
        # Create service
        service = AgentServiceRefactored(db_mock, cache_mock, None, event_bus_mock)
        service.agent_repo = repo_mock
        
        # Mock repository methods
        agent_mock = Mock(spec=Agent)
        agent_mock.id = str(uuid.uuid4())
        agent_mock.name = "Test Agent"
        agent_mock.user_id = str(uuid.uuid4())
        repo_mock.create.return_value = agent_mock
        
        # Create agent data
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=[],
            knowledgebase_ids=[]
        )
        
        # Call method
        result = service.create_agent(str(uuid.uuid4()), agent_data)
        
        # Assertions
        assert result is not None
        repo_mock.create.assert_called_once()
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    def test_create_agent_validation_error(self, mock_repo_class):
        """Test agent creation with validation error."""
        db_mock = Mock()
        service = AgentServiceRefactored(db_mock)
        
        # Invalid data (name too short)
        agent_data = AgentCreate(
            name="ab",  # Too short
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        # Should raise validation exception
        with pytest.raises(AgentValidationException):
            service.create_agent(str(uuid.uuid4()), agent_data)
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    def test_get_agent_success(self, mock_repo_class):
        """Test successful agent retrieval."""
        db_mock = Mock()
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        service = AgentServiceRefactored(db_mock)
        service.agent_repo = repo_mock
        
        # Mock agent
        agent_mock = Mock(spec=Agent)
        agent_mock.id = str(uuid.uuid4())
        repo_mock.find_by_id.return_value = agent_mock
        
        # Call method
        result = service.get_agent(agent_mock.id)
        
        # Assertions
        assert result == agent_mock
        repo_mock.find_by_id.assert_called_once_with(agent_mock.id)
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    def test_get_agent_not_found(self, mock_repo_class):
        """Test agent not found."""
        db_mock = Mock()
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        service = AgentServiceRefactored(db_mock)
        service.agent_repo = repo_mock
        
        # Mock not found
        repo_mock.find_by_id.return_value = None
        
        # Should raise not found exception
        with pytest.raises(AgentNotFoundException):
            service.get_agent(str(uuid.uuid4()))
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    def test_list_agents(self, mock_repo_class):
        """Test listing agents."""
        db_mock = Mock()
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        service = AgentServiceRefactored(db_mock)
        service.agent_repo = repo_mock
        
        # Mock agents
        agents_mock = [Mock(spec=Agent) for _ in range(3)]
        repo_mock.find_by_user.return_value = agents_mock
        
        # Call method
        user_id = str(uuid.uuid4())
        result = service.list_agents(user_id=user_id)
        
        # Assertions
        assert len(result) == 3
        repo_mock.find_by_user.assert_called_once()
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    @patch('backend.services.agent_builder.agent_service_refactored.transaction')
    def test_delete_agent(self, mock_transaction, mock_repo_class):
        """Test agent deletion."""
        db_mock = Mock()
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        # Mock transaction
        mock_transaction.return_value.__enter__ = Mock()
        mock_transaction.return_value.__exit__ = Mock(return_value=False)
        
        service = AgentServiceRefactored(db_mock)
        service.agent_repo = repo_mock
        
        # Mock agent
        agent_mock = Mock(spec=Agent)
        agent_mock.id = str(uuid.uuid4())
        agent_mock.user_id = str(uuid.uuid4())
        repo_mock.find_by_id.return_value = agent_mock
        
        # Call method
        result = service.delete_agent(agent_mock.id)
        
        # Assertions
        assert result is True
        repo_mock.soft_delete.assert_called_once()


class TestAgentServiceCaching:
    """Test caching behavior."""
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    def test_get_agent_with_cache_hit(self, mock_repo_class):
        """Test cache hit scenario."""
        db_mock = Mock()
        cache_mock = Mock()
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        service = AgentServiceRefactored(db_mock, cache_mock)
        service.agent_repo = repo_mock
        
        # Mock cache hit
        agent_mock = Mock(spec=Agent)
        cache_mock.get_sync.return_value = agent_mock
        
        # Call method
        result = service.get_agent(str(uuid.uuid4()), use_cache=True)
        
        # Should return cached value without DB query
        assert result == agent_mock
        repo_mock.find_by_id.assert_not_called()
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    def test_get_agent_with_cache_miss(self, mock_repo_class):
        """Test cache miss scenario."""
        db_mock = Mock()
        cache_mock = Mock()
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        service = AgentServiceRefactored(db_mock, cache_mock)
        service.agent_repo = repo_mock
        
        # Mock cache miss
        cache_mock.get_sync.return_value = None
        
        # Mock DB query
        agent_mock = Mock(spec=Agent)
        agent_mock.id = str(uuid.uuid4())
        repo_mock.find_by_id.return_value = agent_mock
        
        # Call method
        result = service.get_agent(agent_mock.id, use_cache=True)
        
        # Should query DB and cache result
        assert result == agent_mock
        repo_mock.find_by_id.assert_called_once()
        cache_mock.set_sync.assert_called_once()


class TestAgentServiceEvents:
    """Test event publishing."""
    
    @patch('backend.services.agent_builder.agent_service_refactored.AgentRepository')
    @patch('backend.services.agent_builder.agent_service_refactored.transaction')
    def test_create_agent_publishes_event(self, mock_transaction, mock_repo_class):
        """Test that creating agent publishes event."""
        db_mock = Mock()
        event_bus_mock = Mock()
        repo_mock = Mock()
        mock_repo_class.return_value = repo_mock
        
        # Mock transaction
        mock_transaction.return_value.__enter__ = Mock()
        mock_transaction.return_value.__exit__ = Mock(return_value=False)
        
        service = AgentServiceRefactored(db_mock, None, None, event_bus_mock)
        service.agent_repo = repo_mock
        service._verify_tools_exist = Mock(return_value=[])
        service._verify_knowledgebases_exist = Mock(return_value=[])
        service._attach_tools = Mock()
        service._attach_knowledgebases = Mock()
        service._create_version = Mock()
        service._invalidate_agent_cache = Mock()
        
        # Mock agent creation
        agent_mock = Mock(spec=Agent)
        agent_mock.id = str(uuid.uuid4())
        agent_mock.name = "Test Agent"
        agent_mock.user_id = str(uuid.uuid4())
        repo_mock.create.return_value = agent_mock
        
        # Create agent
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        
        service.create_agent(str(uuid.uuid4()), agent_data)
        
        # Should publish event
        event_bus_mock.publish.assert_called()
