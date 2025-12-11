# Integration tests for Flows API

import pytest
from httpx import AsyncClient
from backend.main import app


class TestFlowsAPI:
    """Integration tests for Flows API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_agentflow(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating an Agentflow."""
        
        agentflow_data = {
            "name": "Test Agentflow",
            "description": "Integration test agentflow",
            "orchestration_type": "sequential",
            "supervisor_config": {
                "enabled": True,
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "max_iterations": 10,
                "decision_strategy": "llm_based"
            },
            "tags": ["test", "integration"]
        }
        
        response = await async_client.post(
            "/api/agent-builder/agentflows",
            json=agentflow_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Agentflow"
        assert data["flow_type"] == "agentflow"
        assert data["orchestration_type"] == "sequential"
        
        return data["id"]
    
    @pytest.mark.asyncio
    async def test_create_chatflow(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating a Chatflow."""
        
        chatflow_data = {
            "name": "Test Chatflow",
            "description": "Integration test chatflow",
            "chat_config": {
                "llm_provider": "openai",
                "llm_model": "gpt-3.5-turbo",
                "system_prompt": "You are a helpful assistant.",
                "temperature": 0.7,
                "max_tokens": 2000,
                "streaming": True
            },
            "memory_config": {
                "type": "buffer",
                "max_messages": 10
            },
            "tags": ["test", "integration"]
        }
        
        response = await async_client.post(
            "/api/agent-builder/chatflows",
            json=chatflow_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Chatflow"
        assert data["flow_type"] == "chatflow"
        
        return data["id"]
    
    @pytest.mark.asyncio
    async def test_get_flows(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting list of flows."""
        
        response = await async_client.get(
            "/api/agent-builder/flows",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
        assert "total" in data
        assert isinstance(data["flows"], list)
    
    @pytest.mark.asyncio
    async def test_get_agentflows_only(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting only Agentflows."""
        
        response = await async_client.get(
            "/api/agent-builder/agentflows",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
        
        # All flows should be agentflows
        for flow in data["flows"]:
            assert flow.get("flow_type") == "agentflow"
    
    @pytest.mark.asyncio
    async def test_get_chatflows_only(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting only Chatflows."""
        
        response = await async_client.get(
            "/api/agent-builder/chatflows",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "flows" in data
        
        # All flows should be chatflows
        for flow in data["flows"]:
            assert flow.get("flow_type") == "chatflow"
    
    @pytest.mark.asyncio
    async def test_get_flow_by_id(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting a specific flow by ID."""
        
        # Create a flow first
        flow_id = await self.test_create_agentflow(async_client, auth_headers)
        
        # Get the flow
        response = await async_client.get(
            f"/api/agent-builder/flows/{flow_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == flow_id
        assert data["name"] == "Test Agentflow"
    
    @pytest.mark.asyncio
    async def test_update_flow(self, async_client: AsyncClient, auth_headers: dict):
        """Test updating a flow."""
        
        # Create a flow first
        flow_id = await self.test_create_agentflow(async_client, auth_headers)
        
        # Update the flow
        update_data = {
            "name": "Updated Agentflow",
            "description": "Updated description"
        }
        
        response = await async_client.put(
            f"/api/agent-builder/flows/{flow_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Agentflow"
        assert data["description"] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_delete_flow(self, async_client: AsyncClient, auth_headers: dict):
        """Test deleting a flow."""
        
        # Create a flow first
        flow_id = await self.test_create_agentflow(async_client, auth_headers)
        
        # Delete the flow
        response = await async_client.delete(
            f"/api/agent-builder/flows/{flow_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify deletion
        response = await async_client.get(
            f"/api/agent-builder/flows/{flow_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_execute_flow(self, async_client: AsyncClient, auth_headers: dict):
        """Test executing a flow."""
        
        # Create a flow first
        flow_id = await self.test_create_agentflow(async_client, auth_headers)
        
        # Execute the flow
        execution_data = {
            "input_data": {
                "message": "Hello, world!"
            }
        }
        
        response = await async_client.post(
            f"/api/agent-builder/flows/{flow_id}/execute",
            json=execution_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["flow_id"] == flow_id
        assert data["status"] in ["pending", "running", "completed"]
    
    @pytest.mark.asyncio
    async def test_get_flow_executions(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting execution history for a flow."""
        
        # Create and execute a flow first
        flow_id = await self.test_create_agentflow(async_client, auth_headers)
        await self.test_execute_flow(async_client, auth_headers)
        
        # Get executions
        response = await async_client.get(
            f"/api/agent-builder/flows/{flow_id}/executions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "executions" in data
        assert "total" in data
        assert isinstance(data["executions"], list)
    
    @pytest.mark.asyncio
    async def test_filter_flows_by_search(self, async_client: AsyncClient, auth_headers: dict):
        """Test filtering flows by search query."""
        
        # Create flows with different names
        await self.test_create_agentflow(async_client, auth_headers)
        await self.test_create_chatflow(async_client, auth_headers)
        
        # Search for "Agentflow"
        response = await async_client.get(
            "/api/agent-builder/flows?search=Agentflow",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only return flows with "Agentflow" in name
        for flow in data["flows"]:
            assert "Agentflow" in flow["name"] or "agentflow" in flow.get("description", "").lower()
    
    @pytest.mark.asyncio
    async def test_filter_flows_by_tags(self, async_client: AsyncClient, auth_headers: dict):
        """Test filtering flows by tags."""
        
        # Create flows with tags
        await self.test_create_agentflow(async_client, auth_headers)
        
        # Filter by tag
        response = await async_client.get(
            "/api/agent-builder/flows?tags=test",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All flows should have "test" tag
        for flow in data["flows"]:
            assert "test" in flow.get("tags", [])
    
    @pytest.mark.asyncio
    async def test_pagination(self, async_client: AsyncClient, auth_headers: dict):
        """Test pagination of flows."""
        
        # Create multiple flows
        for i in range(5):
            await self.test_create_agentflow(async_client, auth_headers)
        
        # Get first page
        response = await async_client.get(
            "/api/agent-builder/flows?page=1&page_size=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["flows"]) <= 2


class TestEventStoreAPI:
    """Integration tests for Event Store API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_aggregate_events(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting events for an aggregate."""
        
        response = await async_client.get(
            "/api/events/aggregate/workflow-123",
            headers=auth_headers
        )
        
        # Should return 200 even if no events exist
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_replay_events(self, async_client: AsyncClient, auth_headers: dict):
        """Test replaying events (time-travel debugging)."""
        
        response = await async_client.get(
            "/api/events/replay/workflow-123?aggregate_type=Workflow&to_version=10",
            headers=auth_headers
        )
        
        # Should return 200 even if no events exist
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_get_audit_log(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting audit log."""
        
        response = await async_client.get(
            "/api/events/audit?limit=100",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total_count" in data
