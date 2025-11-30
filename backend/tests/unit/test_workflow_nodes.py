"""
Unit tests for workflow node execution.

Tests each node type handler in WorkflowExecutor.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the executor
import sys
sys.path.insert(0, '.')


class MockWorkflow:
    """Mock workflow for testing."""
    def __init__(self, workflow_id: str = "test-workflow-123"):
        self.id = workflow_id
        self.graph_definition = {
            "nodes": [],
            "edges": [],
            "settings": {"timeout": 300}
        }


class MockDB:
    """Mock database session."""
    def query(self, *args):
        return self
    
    def filter(self, *args):
        return self
    
    def first(self):
        return None
    
    def add(self, obj):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass


@pytest.fixture
def mock_workflow():
    return MockWorkflow()


@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture
def executor(mock_workflow, mock_db):
    from backend.services.agent_builder.workflow_executor import WorkflowExecutor
    return WorkflowExecutor(mock_workflow, mock_db, execution_id="test-exec-123")


class TestStartEndNodes:
    """Tests for start and end nodes."""
    
    @pytest.mark.asyncio
    async def test_start_node_passes_data(self, executor):
        """Start node should pass through input data unchanged."""
        input_data = {"message": "hello", "count": 42}
        result = await executor._execute_start_node({}, input_data)
        assert result == input_data
    
    @pytest.mark.asyncio
    async def test_end_node_returns_data(self, executor):
        """End node should return final data unchanged."""
        final_data = {"result": "success", "output": [1, 2, 3]}
        result = await executor._execute_end_node({}, final_data)
        assert result == final_data
    
    @pytest.mark.asyncio
    async def test_trigger_node_passes_data(self, executor):
        """Trigger node should pass through data."""
        trigger_data = {"event": "webhook", "payload": {"key": "value"}}
        result = await executor._execute_trigger_node({}, trigger_data)
        assert result == trigger_data


class TestConditionNode:
    """Tests for condition node."""
    
    @pytest.mark.asyncio
    async def test_condition_true_branch(self, executor):
        """Condition evaluating to true should return true branch."""
        node_data = {"condition": "data.get('value') > 10"}
        input_data = {"value": 15}
        
        result = await executor._execute_condition_node(node_data, input_data)
        
        assert result["branch"] == "true"
        assert result["data"] == input_data
    
    @pytest.mark.asyncio
    async def test_condition_false_branch(self, executor):
        """Condition evaluating to false should return false branch."""
        node_data = {"condition": "data.get('value') > 10"}
        input_data = {"value": 5}
        
        result = await executor._execute_condition_node(node_data, input_data)
        
        assert result["branch"] == "false"
    
    @pytest.mark.asyncio
    async def test_condition_with_string_comparison(self, executor):
        """Condition with string comparison."""
        node_data = {"condition": "data.get('status') == 'active'"}
        input_data = {"status": "active"}
        
        result = await executor._execute_condition_node(node_data, input_data)
        
        assert result["branch"] == "true"
    
    @pytest.mark.asyncio
    async def test_condition_error_defaults_to_false(self, executor):
        """Invalid condition should default to false branch."""
        node_data = {"condition": "invalid_syntax[[["}
        input_data = {"value": 10}
        
        result = await executor._execute_condition_node(node_data, input_data)
        
        assert result["branch"] == "false"


class TestDelayNode:
    """Tests for delay node."""
    
    @pytest.mark.asyncio
    async def test_delay_node_waits(self, executor):
        """Delay node should wait for specified duration."""
        node_data = {"delayMs": 100}  # 100ms
        input_data = {"test": "data"}
        
        start_time = datetime.now()
        result = await executor._execute_delay_node(node_data, input_data)
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        assert elapsed >= 90  # Allow some tolerance
        assert result["delayed_data"] == input_data
        assert result["delay_ms"] == 100
    
    @pytest.mark.asyncio
    async def test_delay_node_default_duration(self, executor):
        """Delay node should use default 1000ms if not specified."""
        node_data = {}
        input_data = {"test": "data"}
        
        # Mock sleep to avoid actual waiting
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await executor._execute_delay_node(node_data, input_data)
            mock_sleep.assert_called_once_with(1.0)  # 1000ms = 1s


class TestFilterNode:
    """Tests for filter node."""
    
    @pytest.mark.asyncio
    async def test_filter_keep_mode(self, executor):
        """Filter in keep mode should keep matching items."""
        node_data = {
            "condition": "item.get('active') == True",
            "mode": "keep"
        }
        input_data = [
            {"name": "a", "active": True},
            {"name": "b", "active": False},
            {"name": "c", "active": True},
        ]
        
        result = await executor._execute_filter_node(node_data, input_data)
        
        assert len(result["filtered_data"]) == 2
        assert result["original_count"] == 3
        assert result["filtered_count"] == 2
    
    @pytest.mark.asyncio
    async def test_filter_remove_mode(self, executor):
        """Filter in remove mode should remove matching items."""
        node_data = {
            "condition": "item.get('active') == True",
            "mode": "remove"
        }
        input_data = [
            {"name": "a", "active": True},
            {"name": "b", "active": False},
            {"name": "c", "active": True},
        ]
        
        result = await executor._execute_filter_node(node_data, input_data)
        
        assert len(result["filtered_data"]) == 1
        assert result["filtered_data"][0]["name"] == "b"
    
    @pytest.mark.asyncio
    async def test_filter_no_condition_passes_through(self, executor):
        """Filter without condition should pass through data."""
        node_data = {}
        input_data = [{"a": 1}, {"b": 2}]
        
        result = await executor._execute_filter_node(node_data, input_data)
        
        assert result["filtered_data"] == input_data


class TestTransformNode:
    """Tests for transform node."""
    
    @pytest.mark.asyncio
    async def test_transform_expression(self, executor):
        """Transform with expression should evaluate correctly."""
        node_data = {
            "type": "expression",
            "expression": "{'doubled': data.get('value') * 2}"
        }
        input_data = {"value": 21}
        
        result = await executor._execute_transform_node(node_data, input_data)
        
        assert result == {"doubled": 42}
    
    @pytest.mark.asyncio
    async def test_transform_mapping(self, executor):
        """Transform with mapping should map fields correctly."""
        node_data = {
            "type": "mapping",
            "mappings": [
                {"source": "firstName", "target": "first_name"},
                {"source": "lastName", "target": "last_name"},
                {"source": "missing", "target": "default_field", "default": "N/A"},
            ]
        }
        input_data = {"firstName": "John", "lastName": "Doe"}
        
        result = await executor._execute_transform_node(node_data, input_data)
        
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["default_field"] == "N/A"


class TestSwitchNode:
    """Tests for switch node."""
    
    @pytest.mark.asyncio
    async def test_switch_matches_case(self, executor):
        """Switch should match correct case."""
        node_data = {
            "variable": "{{$json.status}}",
            "cases": [
                {"id": "case_active", "condition": "=== 'active'", "label": "Active"},
                {"id": "case_pending", "condition": "=== 'pending'", "label": "Pending"},
            ],
            "defaultCase": True
        }
        input_data = {"status": "active"}
        
        result = await executor._execute_switch_node(node_data, input_data)
        
        assert result["branch"] == "case_active"
        assert result["matched_case"] == "Active"
    
    @pytest.mark.asyncio
    async def test_switch_default_case(self, executor):
        """Switch should use default when no case matches."""
        node_data = {
            "variable": "{{$json.status}}",
            "cases": [
                {"id": "case_active", "condition": "=== 'active'"},
            ],
            "defaultCase": True
        }
        input_data = {"status": "unknown"}
        
        result = await executor._execute_switch_node(node_data, input_data)
        
        assert result["branch"] == "default"


class TestTriggerNodes:
    """Tests for trigger nodes."""
    
    @pytest.mark.asyncio
    async def test_manual_trigger(self, executor):
        """Manual trigger should return trigger metadata."""
        node_data = {"name": "My Manual Trigger"}
        input_data = {"user_input": "test"}
        
        result = await executor._execute_manual_trigger_node(node_data, input_data)
        
        assert result["trigger_type"] == "manual"
        assert result["trigger_name"] == "My Manual Trigger"
        assert result["data"] == input_data
        assert "triggered_at" in result
    
    @pytest.mark.asyncio
    async def test_webhook_trigger(self, executor):
        """Webhook trigger should return webhook metadata."""
        node_data = {"webhookId": "wh_123", "method": "POST"}
        input_data = {"body": {"key": "value"}}
        
        result = await executor._execute_webhook_trigger_node(node_data, input_data)
        
        assert result["trigger_type"] == "webhook"
        assert result["webhook_id"] == "wh_123"
        assert result["method"] == "POST"
    
    @pytest.mark.asyncio
    async def test_schedule_trigger(self, executor):
        """Schedule trigger should return schedule metadata."""
        node_data = {"cronExpression": "0 9 * * 1", "timezone": "UTC"}
        input_data = {}
        
        result = await executor._execute_schedule_trigger_node(node_data, input_data)
        
        assert result["trigger_type"] == "schedule"
        assert result["cron_expression"] == "0 9 * * 1"
        assert result["timezone"] == "UTC"


class TestMergeNode:
    """Tests for merge node."""
    
    @pytest.mark.asyncio
    async def test_merge_passes_through(self, executor):
        """Merge node should pass through data (simplified implementation)."""
        node_data = {"mode": "wait_all"}
        input_data = {"branch_result": "data"}
        
        result = await executor._execute_merge_node(node_data, input_data)
        
        assert result == input_data


class TestSafeEval:
    """Tests for safe expression evaluation."""
    
    def test_safe_eval_basic_comparison(self, executor):
        """Safe eval should handle basic comparisons."""
        result = executor._safe_eval("data.get('x') > 5", {"data": {"x": 10}})
        assert result is True
    
    def test_safe_eval_string_operations(self, executor):
        """Safe eval should handle string operations."""
        result = executor._safe_eval(
            "data.get('name').lower() == 'test'",
            {"data": {"name": "TEST"}}
        )
        assert result is True
    
    def test_safe_eval_list_operations(self, executor):
        """Safe eval should handle list operations."""
        result = executor._safe_eval(
            "len(data.get('items')) > 0",
            {"data": {"items": [1, 2, 3]}}
        )
        assert result is True
    
    def test_safe_eval_blocks_import(self, executor):
        """Safe eval should block import statements."""
        with pytest.raises(ValueError, match="Import"):
            executor._safe_eval("__import__('os')", {})
    
    def test_safe_eval_blocks_unsafe_functions(self, executor):
        """Safe eval should block unsafe function calls."""
        with pytest.raises(ValueError):
            executor._safe_eval("exec('print(1)')", {})


class TestConcurrencyControl:
    """Tests for concurrency control."""
    
    @pytest.mark.asyncio
    async def test_acquire_release_slot(self, executor):
        """Should acquire and release execution slots."""
        workflow_id = "test-workflow"
        
        # Acquire slot
        await executor._acquire_execution_slot(workflow_id)
        assert executor._active_executions.get(workflow_id, 0) == 1
        
        # Release slot
        await executor._release_execution_slot(workflow_id)
        assert executor._active_executions.get(workflow_id, 0) == 0
    
    def test_cleanup_stale_executions(self, executor):
        """Should clean up stale execution entries."""
        from backend.services.agent_builder.workflow_executor import WorkflowExecutor
        
        # Add some entries
        WorkflowExecutor._active_executions = {
            "wf1": 0,
            "wf2": 1,
            "wf3": 0,
        }
        
        cleaned = WorkflowExecutor.cleanup_stale_executions()
        
        assert cleaned == 2
        assert "wf1" not in WorkflowExecutor._active_executions
        assert "wf2" in WorkflowExecutor._active_executions
        assert "wf3" not in WorkflowExecutor._active_executions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
