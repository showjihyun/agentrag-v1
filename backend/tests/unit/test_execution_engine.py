"""Tests for workflow execution engine."""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import uuid

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.core.execution import (
    ExecutionContext,
    BlockState,
    BlockLog,
    WorkflowExecutor,
    ExecutionError,
    WorkflowNotFoundError,
    CyclicDependencyError,
)
from backend.core.execution.condition_evaluator import ConditionEvaluator
from backend.core.execution.loop_executor import LoopExecutor
from backend.core.execution.parallel_executor import ParallelExecutor
from backend.core.execution.error_handler import ErrorHandler
from backend.core.execution.logger import ExecutionLogger


# ============================================================================
# ExecutionContext Tests
# ============================================================================

def test_execution_context_creation():
    """Test creating execution context."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789",
        trigger="manual"
    )
    
    assert context.workflow_id == "workflow_123"
    assert context.execution_id == "exec_456"
    assert context.user_id == "user_789"
    assert context.trigger == "manual"
    assert context.status == "running"
    assert len(context.block_states) == 0
    assert len(context.block_logs) == 0


def test_execution_context_block_output():
    """Test getting and setting block outputs."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789"
    )
    
    # Add block state
    context.block_states["block_1"] = BlockState(
        block_id="block_1",
        block_type="openai"
    )
    
    # Set output
    context.set_block_output("block_1", {"result": "Hello"})
    
    # Get output
    output = context.get_block_output("block_1")
    assert output == {"result": "Hello"}
    
    # Get specific output key
    result = context.get_block_output("block_1", "result")
    assert result == "Hello"


def test_execution_context_variable_resolution():
    """Test variable resolution."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789"
    )
    
    # Set variables
    context.workflow_variables = {"name": "John", "age": 30}
    context.environment_variables = {"env": "production"}
    
    # Resolve workflow variable
    assert context.resolve_variable("name") == "John"
    
    # Resolve environment variable
    assert context.resolve_variable("env") == "production"
    
    # Workflow variables take precedence
    context.workflow_variables["env"] = "development"
    assert context.resolve_variable("env") == "development"


def test_execution_context_template_resolution():
    """Test template string resolution."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789"
    )
    
    context.workflow_variables = {"name": "John", "city": "NYC"}
    
    # Resolve template
    template = "Hello {{name}} from {{city}}"
    resolved = context.resolve_template(template)
    assert resolved == "Hello John from NYC"


def test_execution_context_add_log():
    """Test adding log entries."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789"
    )
    
    # Add log
    context.add_log(
        block_id="block_1",
        block_type="openai",
        block_name="OpenAI Block",
        success=True,
        inputs={"prompt": "Hello"},
        outputs={"response": "Hi"},
        duration_ms=100
    )
    
    assert len(context.block_logs) == 1
    log = context.block_logs[0]
    assert log.block_id == "block_1"
    assert log.success is True
    assert log.duration_ms == 100


def test_execution_context_token_usage():
    """Test token usage tracking."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789"
    )
    
    # Update token usage
    context.update_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cost=0.01
    )
    
    assert context.prompt_tokens == 100
    assert context.completion_tokens == 50
    assert context.total_tokens == 150
    assert context.estimated_cost == 0.01
    
    # Update again
    context.update_token_usage(
        prompt_tokens=200,
        completion_tokens=100,
        cost=0.02
    )
    
    assert context.total_tokens == 450
    assert context.estimated_cost == 0.03


def test_execution_context_serialization():
    """Test context serialization to dict."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789",
        started_at=datetime.utcnow()
    )
    
    context.workflow_variables = {"test": "value"}
    context.block_states["block_1"] = BlockState(
        block_id="block_1",
        block_type="openai",
        executed=True,
        success=True
    )
    
    # Convert to dict
    data = context.to_dict()
    
    assert data["workflow_id"] == "workflow_123"
    assert data["execution_id"] == "exec_456"
    assert "block_1" in data["block_states"]
    assert data["workflow_variables"]["test"] == "value"


def test_execution_context_deserialization():
    """Test context deserialization from dict."""
    data = {
        "workflow_id": "workflow_123",
        "execution_id": "exec_456",
        "user_id": "user_789",
        "trigger": "manual",
        "block_states": {
            "block_1": {
                "block_id": "block_1",
                "block_type": "openai",
                "executed": True,
                "success": True,
                "outputs": {"result": "test"},
                "error": None,
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
            }
        },
        "workflow_variables": {"test": "value"},
        "status": "running",
    }
    
    # Create from dict
    context = ExecutionContext.from_dict(data)
    
    assert context.workflow_id == "workflow_123"
    assert context.execution_id == "exec_456"
    assert "block_1" in context.block_states
    assert context.workflow_variables["test"] == "value"


# ============================================================================
# WorkflowExecutor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_workflow_executor_load_workflow_not_found():
    """Test loading non-existent workflow."""
    # Mock database session
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    executor = WorkflowExecutor(mock_db)
    
    with pytest.raises(WorkflowNotFoundError):
        await executor.load_workflow("nonexistent_workflow")


@pytest.mark.asyncio
async def test_workflow_executor_topological_sort():
    """Test topological sort for block execution order."""
    from backend.db.models.agent_builder import AgentBlock, AgentEdge
    
    # Create mock blocks
    block1 = Mock(spec=AgentBlock)
    block1.id = uuid.uuid4()
    block1.type = "openai"
    
    block2 = Mock(spec=AgentBlock)
    block2.id = uuid.uuid4()
    block2.type = "http"
    
    block3 = Mock(spec=AgentBlock)
    block3.id = uuid.uuid4()
    block3.type = "condition"
    
    blocks = [block1, block2, block3]
    
    # Create mock edges: block1 -> block2 -> block3
    edge1 = Mock(spec=AgentEdge)
    edge1.source_block_id = block1.id
    edge1.target_block_id = block2.id
    
    edge2 = Mock(spec=AgentEdge)
    edge2.source_block_id = block2.id
    edge2.target_block_id = block3.id
    
    # Mock database session
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.all.return_value = [edge1, edge2]
    
    executor = WorkflowExecutor(mock_db)
    
    # Perform topological sort
    sorted_blocks = await executor.topological_sort("workflow_123", blocks)
    
    # Check order
    assert len(sorted_blocks) == 3
    assert sorted_blocks[0].id == block1.id
    assert sorted_blocks[1].id == block2.id
    assert sorted_blocks[2].id == block3.id


@pytest.mark.asyncio
async def test_workflow_executor_cyclic_dependency():
    """Test detection of cyclic dependencies."""
    from backend.db.models.agent_builder import AgentBlock, AgentEdge
    
    # Create mock blocks
    block1 = Mock(spec=AgentBlock)
    block1.id = uuid.uuid4()
    
    block2 = Mock(spec=AgentBlock)
    block2.id = uuid.uuid4()
    
    blocks = [block1, block2]
    
    # Create cyclic edges: block1 -> block2 -> block1
    edge1 = Mock(spec=AgentEdge)
    edge1.source_block_id = block1.id
    edge1.target_block_id = block2.id
    
    edge2 = Mock(spec=AgentEdge)
    edge2.source_block_id = block2.id
    edge2.target_block_id = block1.id
    
    # Mock database session
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.all.return_value = [edge1, edge2]
    
    executor = WorkflowExecutor(mock_db)
    
    # Should raise CyclicDependencyError
    with pytest.raises(CyclicDependencyError):
        await executor.topological_sort("workflow_123", blocks)


# ============================================================================
# ConditionEvaluator Tests
# ============================================================================

@pytest.mark.asyncio
async def test_condition_evaluator_path_selection():
    """Test condition path selection."""
    from backend.db.models.agent_builder import AgentEdge
    
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789"
    )
    
    # Set condition block output
    context.block_states["condition_1"] = BlockState(
        block_id="condition_1",
        block_type="condition",
        executed=True,
        success=True,
        outputs={"path": "true", "matched_condition": {"variable": "status", "operator": "==", "value": "success"}}
    )
    
    # Create mock edges
    edge_true = Mock(spec=AgentEdge)
    edge_true.source_block_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    edge_true.target_block_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    edge_true.source_handle = "true"
    
    edge_false = Mock(spec=AgentEdge)
    edge_false.source_block_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    edge_false.target_block_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    edge_false.source_handle = "false"
    
    edges = [edge_true, edge_false]
    
    # Evaluate and select path
    next_block_id = await ConditionEvaluator.evaluate_and_select_path(
        "condition_1",
        context,
        edges
    )
    
    # Should select the "true" path
    assert next_block_id == str(edge_true.target_block_id)
    assert context.decisions["condition_1"] == "true"


# ============================================================================
# ErrorHandler Tests
# ============================================================================

def test_error_handler_format_error_response():
    """Test error response formatting."""
    error = ValueError("Test error")
    
    response = ErrorHandler.format_error_response(error)
    
    assert response["success"] is False
    assert response["error"] == "Test error"
    assert response["error_type"] == "ValueError"
    assert "timestamp" in response


def test_error_handler_is_recoverable():
    """Test recoverable error detection."""
    # Recoverable errors
    assert ErrorHandler.is_recoverable_error(ConnectionError("Connection failed"))
    assert ErrorHandler.is_recoverable_error(TimeoutError("Timeout"))
    
    # Non-recoverable errors
    assert not ErrorHandler.is_recoverable_error(ValueError("Invalid value"))


def test_error_handler_retry_strategy():
    """Test retry strategy determination."""
    # Recoverable error
    error = ConnectionError("Connection failed")
    strategy = ErrorHandler.get_retry_strategy(error)
    
    assert strategy["should_retry"] is True
    assert strategy["max_retries"] > 0
    
    # Non-recoverable error
    error = ValueError("Invalid value")
    strategy = ErrorHandler.get_retry_strategy(error)
    
    assert strategy["should_retry"] is False


# ============================================================================
# ExecutionLogger Tests
# ============================================================================

def test_execution_logger_create_summary():
    """Test execution summary creation."""
    context = ExecutionContext(
        workflow_id="workflow_123",
        execution_id="exec_456",
        user_id="user_789",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    # Add some block states
    context.block_states["block_1"] = BlockState(
        block_id="block_1",
        block_type="openai",
        executed=True,
        success=True,
        duration_ms=100
    )
    
    context.block_states["block_2"] = BlockState(
        block_id="block_2",
        block_type="http",
        executed=True,
        success=False,
        duration_ms=50
    )
    
    context.total_tokens = 1000
    context.estimated_cost = 0.05
    
    # Create summary
    summary = ExecutionLogger.create_execution_summary(context)
    
    assert summary["workflow_id"] == "workflow_123"
    assert summary["execution_id"] == "exec_456"
    assert summary["blocks"]["total"] == 2
    assert summary["blocks"]["executed"] == 2
    assert summary["blocks"]["successful"] == 1
    assert summary["blocks"]["failed"] == 1
    assert summary["tokens"]["total"] == 1000
    assert summary["cost"]["estimated"] == 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
