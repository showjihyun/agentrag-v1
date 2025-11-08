"""Tests for AgentExecutor service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.agent_builder.agent_executor import AgentExecutor
from backend.db.models.agent_builder import Agent, AgentExecution


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def agent_executor(mock_db):
    """Create AgentExecutor instance."""
    return AgentExecutor(mock_db)


@pytest.fixture
def sample_agent():
    """Sample agent for testing."""
    return Agent(
        id="test-agent-id",
        user_id="test-user",
        name="Test Agent",
        agent_type="custom",
        llm_provider="ollama",
        llm_model="llama3.1",
        configuration={}
    )


@pytest.mark.asyncio
async def test_execute_agent_success(agent_executor, mock_db, sample_agent):
    """Test successful agent execution."""
    # Mock agent service
    with patch.object(agent_executor.agent_service, 'get_agent', return_value=sample_agent):
        # Mock aggregator execution
        with patch('backend.services.agent_builder.agent_executor.AggregatorAgent') as mock_agg:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value={
                "output": "Test result",
                "llm_calls": 1,
                "total_tokens": 100,
                "tool_calls": 0
            })
            mock_agg.return_value = mock_instance
            
            # Execute
            result = await agent_executor.execute_agent(
                agent_id="test-agent-id",
                user_id="test-user",
                input_data={"query": "test query"}
            )
            
            # Verify execution was created
            assert mock_db.add.called
            assert mock_db.commit.called


@pytest.mark.asyncio
async def test_execute_agent_not_found(agent_executor):
    """Test agent execution with non-existent agent."""
    with patch.object(agent_executor.agent_service, 'get_agent', return_value=None):
        with pytest.raises(ValueError, match="Agent .* not found"):
            await agent_executor.execute_agent(
                agent_id="non-existent",
                user_id="test-user",
                input_data={"query": "test"}
            )


@pytest.mark.asyncio
async def test_execute_agent_with_variables(agent_executor, mock_db, sample_agent):
    """Test agent execution with variable resolution."""
    with patch.object(agent_executor.agent_service, 'get_agent', return_value=sample_agent):
        with patch.object(agent_executor.variable_resolver, 'resolve_variables', 
                         new_callable=AsyncMock, return_value="resolved value"):
            with patch('backend.services.agent_builder.agent_executor.AggregatorAgent') as mock_agg:
                mock_instance = AsyncMock()
                mock_instance.execute = AsyncMock(return_value={"output": "result"})
                mock_agg.return_value = mock_instance
                
                result = await agent_executor.execute_agent(
                    agent_id="test-agent-id",
                    user_id="test-user",
                    input_data={"query": "${variable}"},
                    variables={"variable": "test"}
                )
                
                # Verify variable resolution was called
                assert agent_executor.variable_resolver.resolve_variables.called


@pytest.mark.asyncio
async def test_execute_agent_failure_handling(agent_executor, mock_db, sample_agent):
    """Test agent execution failure handling."""
    with patch.object(agent_executor.agent_service, 'get_agent', return_value=sample_agent):
        with patch('backend.services.agent_builder.agent_executor.AggregatorAgent') as mock_agg:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(side_effect=Exception("Execution failed"))
            mock_agg.return_value = mock_instance
            
            with pytest.raises(Exception, match="Execution failed"):
                await agent_executor.execute_agent(
                    agent_id="test-agent-id",
                    user_id="test-user",
                    input_data={"query": "test"}
                )
            
            # Verify rollback was called
            assert mock_db.commit.called  # For marking as failed
