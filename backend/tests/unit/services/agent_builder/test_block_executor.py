"""Tests for BlockExecutor service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from backend.services.agent_builder.block_executor import BlockExecutor
from backend.db.models.agent_builder import Block


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def block_executor(mock_db):
    """Create BlockExecutor instance."""
    return BlockExecutor(mock_db)


@pytest.fixture
def sample_llm_block():
    """Sample LLM block for testing."""
    return Block(
        id="test-llm-block",
        user_id="test-user",
        name="Test LLM Block",
        block_type="llm",
        configuration={
            "llm_provider": "ollama",
            "llm_model": "llama3.1",
            "prompt_template": "Answer: {input}",
            "temperature": 0.7
        }
    )


@pytest.fixture
def sample_composite_block():
    """Sample composite block for testing."""
    return Block(
        id="test-composite-block",
        user_id="test-user",
        name="Test Composite Block",
        block_type="composite",
        configuration={
            "workflow_definition": {
                "nodes": [],
                "edges": [],
                "entry_point": "start"
            }
        }
    )


@pytest.mark.asyncio
async def test_execute_composite_block(block_executor, sample_composite_block):
    """Test composite block execution."""
    with patch('backend.services.agent_builder.block_executor.WorkflowExecutor') as mock_wf:
        mock_instance = Mock()
        mock_instance.execute_workflow = AsyncMock(return_value={
            "output": "workflow result",
            "steps": []
        })
        mock_wf.return_value = mock_instance
        
        result = await block_executor._execute_composite_block(
            block=sample_composite_block,
            input_data={"input": "test"},
            context={"execution_id": "test-exec", "user_id": "test-user"}
        )
        
        assert result["block_type"] == "composite"
        assert "output" in result
        assert mock_instance.execute_workflow.called


@pytest.mark.asyncio
async def test_execute_composite_block_missing_definition(block_executor):
    """Test composite block without workflow definition."""
    block = Block(
        id="test-block",
        user_id="test-user",
        name="Test Block",
        block_type="composite",
        configuration={}
    )
    
    with pytest.raises(ValueError, match="missing workflow_definition"):
        await block_executor._execute_composite_block(
            block=block,
            input_data={},
            context={}
        )
