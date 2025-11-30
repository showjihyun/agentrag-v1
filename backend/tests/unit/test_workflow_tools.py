"""
Unit tests for workflow tools configuration
Tests Pydantic models without external dependencies
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from models.agent_builder import (
    WorkflowNodeCreate,
    WorkflowEdgeCreate,
    WorkflowCreate
)


class TestWorkflowNodeValidation:
    """Test workflow node validation"""
    
    def test_valid_node_creation(self):
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
        assert node.position_x == 100.0
        assert node.position_y == 100.0
    
    def test_tool_node_with_parameters(self):
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
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        )
        
        assert node.node_type == "tool"
        assert node.configuration["tool_id"] == "openai_chat"
        assert node.configuration["parameters"]["model"] == "gpt-4-turbo-preview"
    
    def test_condition_node(self):
        """Test condition node configuration"""
        node = WorkflowNodeCreate(
            id="condition_1",
            node_type="condition",
            position_x=300.0,
            position_y=300.0,
            configuration={
                "label": "Check Value",
                "parameters": {
                    "operator": "greater_than",
                    "condition": "input.get('value', 0) > 50"
                }
            }
        )
        
        assert node.node_type == "condition"
        assert "condition" in node.configuration["parameters"]


class TestWorkflowEdgeValidation:
    """Test workflow edge validation"""
    
    def test_valid_edge_creation(self):
        """Test creating a valid edge"""
        edge = WorkflowEdgeCreate(
            id="edge_1",
            source_node_id="node_1",
            target_node_id="node_2",
            edge_type="normal"
        )
        
        assert edge.id == "edge_1"
        assert edge.source_node_id == "node_1"
        assert edge.target_node_id == "node_2"
        assert edge.edge_type == "normal"
    
    def test_conditional_edge(self):
        """Test conditional edge"""
        edge = WorkflowEdgeCreate(
            id="edge_2",
            source_node_id="condition_1",
            target_node_id="node_3",
            edge_type="conditional",
            condition="result == True",
            source_handle="true"
        )
        
        assert edge.edge_type == "conditional"
        assert edge.condition == "result == True"
        assert edge.source_handle == "true"


class TestWorkflowCreation:
    """Test complete workflow creation"""
    
    def test_simple_workflow(self):
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
        assert workflow.entry_point == "start_1"
    
    def test_workflow_with_tools(self):
        """Test workflow with tool nodes"""
        workflow = WorkflowCreate(
            name="Tool Workflow",
            description="Workflow with tools",
            nodes=[
                WorkflowNodeCreate(
                    id="start_1",
                    node_type="start",
                    position_x=100.0,
                    position_y=100.0,
                    configuration={}
                ),
                WorkflowNodeCreate(
                    id="python_1",
                    node_type="tool",
                    position_x=300.0,
                    position_y=100.0,
                    configuration={
                        "tool_id": "python_code",
                        "parameters": {
                            "code": "return {'result': 'success'}"
                        }
                    }
                ),
                WorkflowNodeCreate(
                    id="end_1",
                    node_type="end",
                    position_x=500.0,
                    position_y=100.0,
                    configuration={}
                )
            ],
            edges=[
                WorkflowEdgeCreate(
                    id="e1",
                    source_node_id="start_1",
                    target_node_id="python_1"
                ),
                WorkflowEdgeCreate(
                    id="e2",
                    source_node_id="python_1",
                    target_node_id="end_1"
                )
            ],
            entry_point="start_1"
        )
        
        assert len(workflow.nodes) == 3
        assert workflow.nodes[1].configuration["tool_id"] == "python_code"


class TestToolConfigurations:
    """Test specific tool configurations"""
    
    def test_openai_chat_config(self):
        """Test OpenAI Chat configuration"""
        config = {
            "tool_id": "openai_chat",
            "parameters": {
                "model": "gpt-4-turbo-preview",
                "system_message": "You are a helpful assistant",
                "prompt": "Explain {{input}}",
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            }
        }
        
        assert config["tool_id"] == "openai_chat"
        assert config["parameters"]["model"] == "gpt-4-turbo-preview"
        assert 0 <= config["parameters"]["temperature"] <= 2
        assert config["parameters"]["max_tokens"] > 0
    
    def test_slack_config(self):
        """Test Slack configuration"""
        config = {
            "tool_id": "slack",
            "parameters": {
                "action": "send_message",
                "channel": "#general",
                "message": "Test message",
                "bot_token": "xoxb-test-token"
            }
        }
        
        assert config["tool_id"] == "slack"
        assert config["parameters"]["action"] == "send_message"
        assert config["parameters"]["channel"].startswith("#")
    
    def test_http_request_config(self):
        """Test HTTP Request configuration"""
        config = {
            "tool_id": "http_request",
            "parameters": {
                "method": "GET",
                "url": "https://api.example.com/data",
                "headers": [
                    {"key": "Accept", "value": "application/json"}
                ],
                "query_params": [],
                "timeout": 30
            }
        }
        
        assert config["tool_id"] == "http_request"
        assert config["parameters"]["method"] in ["GET", "POST", "PUT", "DELETE", "PATCH"]
        assert config["parameters"]["url"].startswith("http")
    
    def test_vector_search_config(self):
        """Test Vector Search configuration"""
        config = {
            "tool_id": "vector_search",
            "parameters": {
                "query": "{{input.query}}",
                "collection_name": "documents",
                "top_k": 5,
                "score_threshold": 0.7
            }
        }
        
        assert config["tool_id"] == "vector_search"
        assert config["parameters"]["top_k"] > 0
        assert 0 <= config["parameters"]["score_threshold"] <= 1
    
    def test_python_code_config(self):
        """Test Python Code configuration"""
        config = {
            "tool_id": "python_code",
            "parameters": {
                "code": "return {'result': input.get('value') * 2}",
                "timeout": 30,
                "allow_imports": True
            }
        }
        
        assert config["tool_id"] == "python_code"
        assert "code" in config["parameters"]
        assert config["parameters"]["timeout"] > 0
    
    def test_condition_config(self):
        """Test Condition configuration"""
        config = {
            "parameters": {
                "operator": "greater_than",
                "variable": "input",
                "condition": "input.get('value', 0) > 50"
            }
        }
        
        assert config["parameters"]["operator"] in [
            "equals", "not_equals", "greater_than", "less_than",
            "contains", "starts_with", "ends_with", "is_empty",
            "is_not_empty", "custom"
        ]
    
    def test_schedule_trigger_config(self):
        """Test Schedule Trigger configuration"""
        config = {
            "parameters": {
                "preset": "every_hour",
                "cron": "0 * * * *",
                "timezone": "UTC"
            }
        }
        
        assert config["parameters"]["cron"]
        assert config["parameters"]["timezone"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
