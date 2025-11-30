"""
Integration tests for workflow API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers"""
    # Create test user
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@workflow.com",
            "password": "testpass123",
            "username": "testuser"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
    else:
        # Try login if user exists
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@workflow.com",
                "password": "testpass123"
            }
        )
        token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


class TestWorkflowCRUD:
    """Test workflow CRUD operations"""
    
    def test_create_simple_workflow(self, client, auth_headers):
        """Test creating a simple workflow"""
        workflow_data = {
            "name": "Test Workflow",
            "description": "Integration test workflow",
            "nodes": [
                {
                    "id": "start_1",
                    "node_type": "start",
                    "position_x": 100.0,
                    "position_y": 100.0,
                    "configuration": {"label": "Start"}
                },
                {
                    "id": "end_1",
                    "node_type": "end",
                    "position_x": 300.0,
                    "position_y": 100.0,
                    "configuration": {"label": "End"}
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "source_node_id": "start_1",
                    "target_node_id": "end_1",
                    "edge_type": "normal"
                }
            ],
            "entry_point": "start_1",
            "is_public": False
        }
        
        response = client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert "id" in data
        
        return data["id"]
    
    def test_get_workflow(self, client, auth_headers):
        """Test retrieving a workflow"""
        # First create a workflow
        workflow_id = self.test_create_simple_workflow(client, auth_headers)
        
        # Then retrieve it
        response = client.get(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == "Test Workflow"
    
    def test_list_workflows(self, client, auth_headers):
        """Test listing workflows"""
        response = client.get(
            "/api/agent-builder/workflows",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_workflow(self, client, auth_headers):
        """Test updating a workflow"""
        # Create workflow
        workflow_id = self.test_create_simple_workflow(client, auth_headers)
        
        # Update it
        update_data = {
            "name": "Updated Workflow",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/agent-builder/workflows/{workflow_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Workflow"
    
    def test_delete_workflow(self, client, auth_headers):
        """Test deleting a workflow"""
        # Create workflow
        workflow_id = self.test_create_simple_workflow(client, auth_headers)
        
        # Delete it
        response = client.delete(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204


class TestWorkflowWithTools:
    """Test workflows with various tools"""
    
    def test_workflow_with_python_code(self, client, auth_headers):
        """Test workflow with Python code node"""
        workflow_data = {
            "name": "Python Code Workflow",
            "description": "Test Python code execution",
            "nodes": [
                {
                    "id": "start_1",
                    "node_type": "start",
                    "position_x": 100.0,
                    "position_y": 100.0,
                    "configuration": {}
                },
                {
                    "id": "python_1",
                    "node_type": "tool",
                    "position_x": 300.0,
                    "position_y": 100.0,
                    "configuration": {
                        "tool_id": "python_code",
                        "parameters": {
                            "code": "return {'result': 'success', 'value': 42}"
                        }
                    }
                },
                {
                    "id": "end_1",
                    "node_type": "end",
                    "position_x": 500.0,
                    "position_y": 100.0,
                    "configuration": {}
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "source_node_id": "start_1",
                    "target_node_id": "python_1"
                },
                {
                    "id": "e2",
                    "source_node_id": "python_1",
                    "target_node_id": "end_1"
                }
            ],
            "entry_point": "start_1"
        }
        
        response = client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["graph_definition"]["nodes"]) == 3
    
    def test_workflow_with_condition(self, client, auth_headers):
        """Test workflow with condition node"""
        workflow_data = {
            "name": "Condition Workflow",
            "description": "Test conditional branching",
            "nodes": [
                {
                    "id": "start_1",
                    "node_type": "start",
                    "position_x": 100.0,
                    "position_y": 200.0,
                    "configuration": {}
                },
                {
                    "id": "condition_1",
                    "node_type": "condition",
                    "position_x": 300.0,
                    "position_y": 200.0,
                    "configuration": {
                        "parameters": {
                            "condition": "input.get('value', 0) > 50"
                        }
                    }
                },
                {
                    "id": "end_1",
                    "node_type": "end",
                    "position_x": 500.0,
                    "position_y": 200.0,
                    "configuration": {}
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "source_node_id": "start_1",
                    "target_node_id": "condition_1"
                },
                {
                    "id": "e2",
                    "source_node_id": "condition_1",
                    "target_node_id": "end_1",
                    "source_handle": "true"
                }
            ],
            "entry_point": "start_1"
        }
        
        response = client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
    
    def test_workflow_with_parallel_merge(self, client, auth_headers):
        """Test workflow with parallel and merge nodes"""
        workflow_data = {
            "name": "Parallel Workflow",
            "description": "Test parallel execution and merge",
            "nodes": [
                {
                    "id": "start_1",
                    "node_type": "start",
                    "position_x": 100.0,
                    "position_y": 200.0,
                    "configuration": {}
                },
                {
                    "id": "parallel_1",
                    "node_type": "parallel",
                    "position_x": 300.0,
                    "position_y": 200.0,
                    "configuration": {}
                },
                {
                    "id": "task_1",
                    "node_type": "tool",
                    "position_x": 500.0,
                    "position_y": 100.0,
                    "configuration": {
                        "tool_id": "python_code",
                        "parameters": {"code": "return {'task': 1}"}
                    }
                },
                {
                    "id": "task_2",
                    "node_type": "tool",
                    "position_x": 500.0,
                    "position_y": 300.0,
                    "configuration": {
                        "tool_id": "python_code",
                        "parameters": {"code": "return {'task': 2}"}
                    }
                },
                {
                    "id": "merge_1",
                    "node_type": "merge",
                    "position_x": 700.0,
                    "position_y": 200.0,
                    "configuration": {
                        "parameters": {
                            "mode": "wait_all",
                            "input_count": 2
                        }
                    }
                },
                {
                    "id": "end_1",
                    "node_type": "end",
                    "position_x": 900.0,
                    "position_y": 200.0,
                    "configuration": {}
                }
            ],
            "edges": [
                {"id": "e1", "source_node_id": "start_1", "target_node_id": "parallel_1"},
                {"id": "e2", "source_node_id": "parallel_1", "target_node_id": "task_1"},
                {"id": "e3", "source_node_id": "parallel_1", "target_node_id": "task_2"},
                {"id": "e4", "source_node_id": "task_1", "target_node_id": "merge_1"},
                {"id": "e5", "source_node_id": "task_2", "target_node_id": "merge_1"},
                {"id": "e6", "source_node_id": "merge_1", "target_node_id": "end_1"}
            ],
            "entry_point": "start_1"
        }
        
        response = client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201


class TestToolsAPI:
    """Test tools API endpoints"""
    
    def test_list_tools(self, client):
        """Test listing available tools"""
        response = client.get("/api/agent-builder/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check for expected tools
        tool_ids = [tool["id"] for tool in data]
        assert "python_code" in tool_ids
        assert "http_request" in tool_ids
    
    def test_get_tool_config(self, client):
        """Test getting tool configuration"""
        response = client.get("/api/agent-builder/tools/python_code")
        
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == "python_code"
            assert "parameters" in data or "configuration" in data


class TestBlocksAPI:
    """Test blocks API endpoints"""
    
    def test_list_blocks(self, client):
        """Test listing available blocks"""
        response = client.get("/api/agent-builder/blocks")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
