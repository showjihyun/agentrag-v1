# End-to-End tests for Workflow functionality

import pytest
from httpx import AsyncClient
from backend.main import app


class TestWorkflowE2E:
    """End-to-end tests for workflow operations."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_lifecycle(self, async_client: AsyncClient, auth_headers: dict):
        """Test complete workflow lifecycle: create, update, execute, delete."""
        
        # 1. Create workflow
        workflow_data = {
            "name": "E2E Test Workflow",
            "description": "End-to-end test workflow",
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "data": {}
                },
                {
                    "id": "llm",
                    "type": "llm",
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "prompt": "Say hello"
                    }
                },
                {
                    "id": "end",
                    "type": "end",
                    "data": {}
                }
            ],
            "edges": [
                {"source": "start", "target": "llm"},
                {"source": "llm", "target": "end"}
            ]
        }
        
        response = await async_client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        workflow = response.json()
        workflow_id = workflow["id"]
        
        # 2. Get workflow
        response = await async_client.get(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "E2E Test Workflow"
        
        # 3. Update workflow
        update_data = {
            "name": "Updated E2E Workflow",
            "description": "Updated description"
        }
        response = await async_client.put(
            f"/api/agent-builder/workflows/{workflow_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated E2E Workflow"
        
        # 4. Execute workflow
        execution_data = {
            "input_data": {"message": "Hello"}
        }
        response = await async_client.post(
            f"/api/agent-builder/workflows/{workflow_id}/execute",
            json=execution_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        execution = response.json()
        execution_id = execution["id"]
        
        # 5. Get execution status
        response = await async_client.get(
            f"/api/agent-builder/executions/{execution_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] in ["running", "completed", "failed"]
        
        # 6. List workflows
        response = await async_client.get(
            "/api/agent-builder/workflows",
            headers=auth_headers
        )
        assert response.status_code == 200
        workflows = response.json()
        assert any(w["id"] == workflow_id for w in workflows)
        
        # 7. Delete workflow
        response = await async_client.delete(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 8. Verify deletion
        response = await async_client.get(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_workflow_with_conditions(self, async_client: AsyncClient, auth_headers: dict):
        """Test workflow with conditional logic."""
        
        workflow_data = {
            "name": "Conditional Workflow",
            "description": "Workflow with conditions",
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "data": {}
                },
                {
                    "id": "condition",
                    "type": "condition",
                    "data": {
                        "condition": "input.value > 10"
                    }
                },
                {
                    "id": "high",
                    "type": "llm",
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "prompt": "Value is high"
                    }
                },
                {
                    "id": "low",
                    "type": "llm",
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "prompt": "Value is low"
                    }
                },
                {
                    "id": "end",
                    "type": "end",
                    "data": {}
                }
            ],
            "edges": [
                {"source": "start", "target": "condition"},
                {"source": "condition", "target": "high", "condition": "true"},
                {"source": "condition", "target": "low", "condition": "false"},
                {"source": "high", "target": "end"},
                {"source": "low", "target": "end"}
            ]
        }
        
        response = await async_client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        workflow_id = response.json()["id"]
        
        # Test with high value
        response = await async_client.post(
            f"/api/agent-builder/workflows/{workflow_id}/execute",
            json={"input_data": {"value": 15}},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Test with low value
        response = await async_client.post(
            f"/api/agent-builder/workflows/{workflow_id}/execute",
            json={"input_data": {"value": 5}},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Cleanup
        await async_client.delete(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
    
    @pytest.mark.asyncio
    async def test_workflow_with_loop(self, async_client: AsyncClient, auth_headers: dict):
        """Test workflow with loop."""
        
        workflow_data = {
            "name": "Loop Workflow",
            "description": "Workflow with loop",
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "data": {}
                },
                {
                    "id": "loop",
                    "type": "loop",
                    "data": {
                        "items": "input.items",
                        "max_iterations": 5
                    }
                },
                {
                    "id": "process",
                    "type": "llm",
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "prompt": "Process item: {{item}}"
                    }
                },
                {
                    "id": "end",
                    "type": "end",
                    "data": {}
                }
            ],
            "edges": [
                {"source": "start", "target": "loop"},
                {"source": "loop", "target": "process"},
                {"source": "process", "target": "end"}
            ]
        }
        
        response = await async_client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        workflow_id = response.json()["id"]
        
        # Execute with items
        response = await async_client.post(
            f"/api/agent-builder/workflows/{workflow_id}/execute",
            json={"input_data": {"items": [1, 2, 3]}},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Cleanup
        await async_client.delete(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, async_client: AsyncClient, auth_headers: dict):
        """Test workflow error handling."""
        
        # Test with invalid workflow data
        invalid_data = {
            "name": "",  # Empty name
            "nodes": []  # No nodes
        }
        
        response = await async_client.post(
            "/api/agent-builder/workflows",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test with non-existent workflow
        response = await async_client.get(
            "/api/agent-builder/workflows/99999",
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Test execution without required input
        workflow_data = {
            "name": "Test Workflow",
            "nodes": [
                {"id": "start", "type": "start", "data": {}},
                {"id": "end", "type": "end", "data": {}}
            ],
            "edges": [{"source": "start", "target": "end"}]
        }
        
        response = await async_client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        workflow_id = response.json()["id"]
        
        response = await async_client.post(
            f"/api/agent-builder/workflows/{workflow_id}/execute",
            json={},  # Missing input_data
            headers=auth_headers
        )
        assert response.status_code in [400, 422]
        
        # Cleanup
        await async_client.delete(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=auth_headers
        )
