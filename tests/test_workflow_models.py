"""
Standalone unit tests for workflow models
Run directly: python tests/test_workflow_models.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from models.agent_builder import (
    WorkflowNodeCreate,
    WorkflowEdgeCreate,
    WorkflowCreate
)


def test_valid_node_creation():
    """Test creating a valid node"""
    node = WorkflowNodeCreate(
        id="node_1",
        node_type="start",
        position_x=100.0,
        position_y=100.0,
        configuration={"label": "Start"}
    )
    
    assert node.id == "node_1"
    assert node.node_type == "start"
    print("✓ Valid node creation")


def test_tool_node_with_parameters():
    """Test tool node with parameters"""
    node = WorkflowNodeCreate(
        id="tool_1",
        node_type="tool",
        position_x=200.0,
        position_y=200.0,
        configuration={
            "label": "OpenAI Chat",
            "tool_id": "openai_chat",
            "parameters": {
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7
            }
        }
    )
    
    assert node.node_type == "tool"
    assert node.configuration["tool_id"] == "openai_chat"
    print("✓ Tool node with parameters")


def test_valid_edge_creation():
    """Test creating a valid edge"""
    edge = WorkflowEdgeCreate(
        id="edge_1",
        source_node_id="node_1",
        target_node_id="node_2",
        edge_type="normal"
    )
    
    assert edge.id == "edge_1"
    assert edge.source_node_id == "node_1"
    print("✓ Valid edge creation")


def test_simple_workflow():
    """Test creating a simple workflow"""
    workflow = WorkflowCreate(
        name="Test Workflow",
        description="A simple test workflow",
        nodes=[
            WorkflowNodeCreate(
                id="start_1",
                node_type="start",
                position_x=100.0,
                position_y=100.0,
                configuration={"label": "Start"}
            ),
            WorkflowNodeCreate(
                id="end_1",
                node_type="end",
                position_x=300.0,
                position_y=100.0,
                configuration={"label": "End"}
            )
        ],
        edges=[
            WorkflowEdgeCreate(
                id="e1",
                source_node_id="start_1",
                target_node_id="end_1",
                edge_type="normal"
            )
        ],
        entry_point="start_1"
    )
    
    assert workflow.name == "Test Workflow"
    assert len(workflow.nodes) == 2
    assert len(workflow.edges) == 1
    print("✓ Simple workflow creation")


def test_tool_configurations():
    """Test various tool configurations"""
    configs = [
        {
            "name": "OpenAI Chat",
            "tool_id": "openai_chat",
            "parameters": {
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        },
        {
            "name": "Slack",
            "tool_id": "slack",
            "parameters": {
                "action": "send_message",
                "channel": "#general"
            }
        },
        {
            "name": "HTTP Request",
            "tool_id": "http_request",
            "parameters": {
                "method": "GET",
                "url": "https://api.example.com"
            }
        },
        {
            "name": "Vector Search",
            "tool_id": "vector_search",
            "parameters": {
                "query": "test",
                "top_k": 5,
                "score_threshold": 0.7
            }
        },
        {
            "name": "Python Code",
            "tool_id": "python_code",
            "parameters": {
                "code": "return {'result': 'success'}"
            }
        }
    ]
    
    for config in configs:
        node = WorkflowNodeCreate(
            id=f"tool_{config['tool_id']}",
            node_type="tool",
            position_x=100.0,
            position_y=100.0,
            configuration=config
        )
        assert node.configuration["tool_id"] == config["tool_id"]
    
    print(f"✓ All {len(configs)} tool configurations valid")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Workflow Models Unit Tests")
    print("="*60 + "\n")
    
    tests = [
        test_valid_node_creation,
        test_tool_node_with_parameters,
        test_valid_edge_creation,
        test_simple_workflow,
        test_tool_configurations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
