"""
Integration tests for workflow execution.

These tests verify the WorkflowExecutor functionality including:
- Sequential workflow execution
- Parallel execution
- Conditional branching
- Error handling and retry mechanisms
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock
from sqlalchemy.orm import Session

from backend.services.agent_builder.workflow_executor import WorkflowExecutor, ExecutionContext
from backend.services.llm_manager import LLMManager
from backend.memory.manager import MemoryManager
from backend.services.agent_builder.variable_resolver import VariableResolver
from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
from backend.services.agent_builder.tool_registry import ToolRegistry
from backend.models.agent import AgentStep


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager."""
    manager = Mock(spec=LLMManager)
    manager.generate = AsyncMock(return_value="Test LLM response")
    return manager


@pytest.fixture
def mock_memory_manager():
    """Mock memory manager."""
    return Mock(spec=MemoryManager)


@pytest.fixture
def mock_variable_resolver():
    """Mock variable resolver."""
    return Mock(spec=VariableResolver)


@pytest.fixture
def mock_knowledgebase_service():
    """Mock knowledgebase service."""
    return Mock(spec=KnowledgebaseService)


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry."""
    return Mock(spec=ToolRegistry)


@pytest.fixture
def workflow_executor(
    mock_db,
    mock_llm_manager,
    mock_memory_manager,
    mock_variable_resolver,
    mock_knowledgebase_service,
    mock_tool_registry
):
    """Create WorkflowExecutor instance with mocked dependencies."""
    return WorkflowExecutor(
        db=mock_db,
        llm_manager=mock_llm_manager,
        memory_manager=mock_memory_manager,
        variable_resolver=mock_variable_resolver,
        knowledgebase_service=mock_knowledgebase_service,
        tool_registry=mock_tool_registry
    )


@pytest.fixture
def simple_workflow():
    """Create a simple sequential workflow."""
    workflow = Mock()
    workflow.id = "workflow_001"
    workflow.name = "Simple Sequential Workflow"
    workflow.updated_at = datetime.now()
    workflow.graph_definition = {
        "nodes": [
            {
                "id": "node_1",
                "type": "block",
                "block_id": "block_001",
                "name": "First Block"
            },
            {
                "id": "node_2",
                "type": "block",
                "block_id": "block_002",
                "name": "Second Block"
            }
        ],
        "edges": [
            {
                "type": "normal",
                "source": "node_1",
                "target": "node_2"
            }
        ],
        "entry_point": "node_1",
        "finish_points": ["node_2"]
    }
    return workflow


@pytest.fixture
def execution_context():
    """Create execution context."""
    return ExecutionContext(
        execution_id="exec_001",
        user_id="user_001",
        workflow_id="workflow_001",
        session_id="session_001",
        input_data={"query": "test query"},
        variables={"test_var": "test_value"}
    )


@pytest.mark.asyncio
async def test_simple_sequential_workflow_execution(
    workflow_executor,
    simple_workflow,
    execution_context,
    mock_db
):
    """Test simple sequential workflow execution."""
    # Mock block loading
    mock_block_1 = Mock()
    mock_block_1.id = "block_001"
    mock_block_1.name = "First Block"
    mock_block_1.block_type = "llm"
    mock_block_1.configuration = {"prompt_template": "Test prompt"}
    
    mock_block_2 = Mock()
    mock_block_2.id = "block_002"
    mock_block_2.name = "Second Block"
    mock_block_2.block_type = "llm"
    mock_block_2.configuration = {"prompt_template": "Test prompt 2"}
    
    # Mock database queries
    mock_db.query = Mock(return_value=Mock(
        filter=Mock(return_value=Mock(
            first=Mock(side_effect=[mock_block_1, mock_block_2])
        ))
    ))
    
    # Execute workflow
    steps = []
    async for step in workflow_executor.execute_workflow(
        workflow=simple_workflow,
        input_data={"query": "test query"},
        context=execution_context
    ):
        steps.append(step)
        assert isinstance(step, AgentStep)
    
    # Verify steps were generated
    assert len(steps) > 0
    
    # Verify start step
    assert any(step.type == "planning" for step in steps)


@pytest.mark.asyncio
async def test_parallel_execution(workflow_executor, execution_context):
    """Test parallel execution with multiple branches."""
    # Create parallel branches
    branches = [
        {"id": "branch_1", "type": "block", "block_id": "block_001"},
        {"id": "branch_2", "type": "block", "block_id": "block_002"},
        {"id": "branch_3", "type": "block", "block_id": "block_003"}
    ]
    
    state = {
        "input": {"query": "test"},
        "context": execution_context.to_dict(),
        "variables": {},
        "steps": []
    }
    
    # Mock block loading and execution
    workflow_executor._load_block = AsyncMock(return_value=Mock(
        id="block_001",
        name="Test Block",
        block_type="llm",
        configuration={}
    ))
    
    workflow_executor._execute_block = AsyncMock(return_value={
        "output": "test output",
        "block_id": "block_001"
    })
    
    # Execute parallel branches
    result_state = await workflow_executor.execute_parallel_branches(branches, state)
    
    # Verify results
    assert "parallel_results" in result_state
    assert len(result_state["parallel_results"]) == 3


@pytest.mark.asyncio
async def test_conditional_branching(workflow_executor):
    """Test conditional branching with Python expressions."""
    # Test condition evaluation
    state = {
        "value": 10,
        "variables": {"threshold": 5}
    }
    
    # Test positive condition
    result = workflow_executor._evaluate_condition("state['value'] > 5", state)
    assert result is True
    
    # Test negative condition
    result = workflow_executor._evaluate_condition("state['value'] < 5", state)
    assert result is False
    
    # Test with variables
    result = workflow_executor._evaluate_condition("state['value'] > threshold", state)
    assert result is True


@pytest.mark.asyncio
async def test_error_handling_with_retry(workflow_executor, mock_db):
    """Test error handling and retry mechanisms."""
    # Create mock block that fails first time, succeeds second time
    mock_block = Mock()
    mock_block.id = "block_001"
    mock_block.name = "Test Block"
    mock_block.block_type = "llm"
    mock_block.configuration = {
        "error_handling": {
            "retry_enabled": True,
            "retry_count": 3,
            "timeout": 5.0
        }
    }
    
    # Mock block executor to fail once then succeed
    call_count = 0
    
    async def mock_execute_block(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("Simulated connection error")
        return {"output": "success", "block_id": "block_001"}
    
    workflow_executor.block_executor.execute_block = mock_execute_block
    
    # Execute block with retry
    result = await workflow_executor._execute_block(
        block=mock_block,
        block_input={"query": "test"},
        state={"context": {}}
    )
    
    # Verify retry worked
    assert result["output"] == "success"
    assert call_count == 2  # Failed once, succeeded on retry


@pytest.mark.asyncio
async def test_error_handling_with_fallback(workflow_executor):
    """Test error handling with fallback value."""
    # Create mock block with fallback
    mock_block = Mock()
    mock_block.id = "block_001"
    mock_block.name = "Test Block"
    mock_block.block_type = "llm"
    mock_block.configuration = {
        "error_handling": {
            "retry_enabled": False,
            "fallback_value": "fallback response"
        }
    }
    
    # Mock block executor to always fail
    async def mock_execute_block(*args, **kwargs):
        raise Exception("Simulated error")
    
    workflow_executor.block_executor.execute_block = mock_execute_block
    
    # Execute block with fallback
    result = await workflow_executor._execute_block(
        block=mock_block,
        block_input={"query": "test"},
        state={"context": {}}
    )
    
    # Verify fallback was used
    assert result["output"] == "fallback response"
    assert result["fallback"] is True


@pytest.mark.asyncio
async def test_execution_timeout(workflow_executor):
    """Test execution timeout handling."""
    # Create mock block with short timeout
    mock_block = Mock()
    mock_block.id = "block_001"
    mock_block.name = "Test Block"
    mock_block.block_type = "llm"
    mock_block.configuration = {
        "error_handling": {
            "retry_enabled": False,
            "timeout": 0.1,  # Very short timeout
            "fallback_value": "timeout fallback"
        }
    }
    
    # Mock block executor to take too long
    async def mock_execute_block(*args, **kwargs):
        await asyncio.sleep(1.0)  # Longer than timeout
        return {"output": "should not reach here"}
    
    workflow_executor.block_executor.execute_block = mock_execute_block
    
    # Execute block with timeout
    result = await workflow_executor._execute_block(
        block=mock_block,
        block_input={"query": "test"},
        state={"context": {}}
    )
    
    # Verify fallback was used due to timeout
    assert result["output"] == "timeout fallback"
    assert result["fallback"] is True
