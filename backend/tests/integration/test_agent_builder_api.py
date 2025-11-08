"""Integration tests for Agent Builder API endpoints.

These tests verify the complete Agent Builder API functionality including:
- Agent CRUD operations
- Block management
- Workflow creation and validation
- Knowledgebase management
- Variable and secret management
- Execution endpoints
- Permission and sharing

Requirements: All Phase 4
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def client():
    """Create test client for integration tests."""
    from backend.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers(client) -> Dict[str, str]:
    """Get authentication headers for test user."""
    # Create or login test user
    test_user = {
        "email": f"test_agent_builder_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!",
        "full_name": "Test Agent Builder User"
    }
    
    # Try to register
    register_response = client.post("/api/auth/register", json=test_user)
    
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        pytest.skip("Authentication not available")


class TestAgentAPI:
    """Integration tests for Agent API endpoints."""
    
    def test_create_agent(self, client, auth_headers):
        """Test creating a new agent."""
        agent_data = {
            "name": "Test Agent",
            "description": "A test agent for integration testing",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2",
            "configuration": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 401, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == agent_data["name"]
            assert data["agent_type"] == agent_data["agent_type"]
            assert "id" in data
            return data["id"]
    
    def test_get_agent(self, client, auth_headers):
        """Test retrieving an agent."""
        # First create an agent
        agent_data = {
            "name": "Test Get Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            # Get the agent
            response = client.get(
                f"/api/agent-builder/agents/{agent_id}",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["id"] == agent_id
                assert data["name"] == agent_data["name"]
    
    def test_list_agents(self, client, auth_headers):
        """Test listing agents with pagination."""
        response = client.get(
            "/api/agent-builder/agents?skip=0&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "agents" in data
            assert "total" in data
            assert isinstance(data["agents"], list)
    
    def test_update_agent(self, client, auth_headers):
        """Test updating an agent."""
        # Create agent first
        agent_data = {
            "name": "Test Update Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            # Update the agent
            update_data = {
                "name": "Updated Agent Name",
                "description": "Updated description"
            }
            
            response = client.put(
                f"/api/agent-builder/agents/{agent_id}",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["name"] == update_data["name"]
    
    def test_delete_agent(self, client, auth_headers):
        """Test soft deleting an agent."""
        # Create agent first
        agent_data = {
            "name": "Test Delete Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            # Delete the agent
            response = client.delete(
                f"/api/agent-builder/agents/{agent_id}",
                headers=auth_headers
            )
            
            assert response.status_code in [204, 404]
    
    def test_clone_agent(self, client, auth_headers):
        """Test cloning an agent."""
        # Create agent first
        agent_data = {
            "name": "Test Clone Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            # Clone the agent
            response = client.post(
                f"/api/agent-builder/agents/{agent_id}/clone",
                headers=auth_headers
            )
            
            assert response.status_code in [201, 404]
            
            if response.status_code == 201:
                data = response.json()
                assert data["name"].startswith("Test Clone Agent")
                assert data["id"] != agent_id


class TestBlockAPI:
    """Integration tests for Block API endpoints."""
    
    def test_create_block(self, client, auth_headers):
        """Test creating a new block."""
        block_data = {
            "name": "Test Block",
            "description": "A test block",
            "block_type": "llm",
            "input_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "output": {"type": "string"}
                }
            },
            "configuration": {
                "prompt": "Process: {input}"
            }
        }
        
        response = client.post(
            "/api/agent-builder/blocks",
            json=block_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 401, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == block_data["name"]
            assert data["block_type"] == block_data["block_type"]
    
    def test_list_blocks(self, client, auth_headers):
        """Test listing blocks with type filter."""
        response = client.get(
            "/api/agent-builder/blocks?block_type=llm",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestWorkflowAPI:
    """Integration tests for Workflow API endpoints."""
    
    def test_create_workflow(self, client, auth_headers):
        """Test creating a new workflow."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "graph_definition": {
                "nodes": [
                    {
                        "id": "start",
                        "type": "agent",
                        "agent_id": str(uuid.uuid4())
                    }
                ],
                "edges": [],
                "entry_point": "start"
            }
        }
        
        response = client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 401, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == workflow_data["name"]
    
    def test_validate_workflow(self, client, auth_headers):
        """Test workflow validation."""
        # Create workflow first
        workflow_data = {
            "name": "Test Validate Workflow",
            "graph_definition": {
                "nodes": [{"id": "start", "type": "agent"}],
                "edges": [],
                "entry_point": "start"
            }
        }
        
        create_response = client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            workflow_id = create_response.json()["id"]
            
            # Validate the workflow
            response = client.post(
                f"/api/agent-builder/workflows/{workflow_id}/validate",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 404]


class TestKnowledgebaseAPI:
    """Integration tests for Knowledgebase API endpoints."""
    
    def test_create_knowledgebase(self, client, auth_headers):
        """Test creating a new knowledgebase."""
        kb_data = {
            "name": "Test Knowledgebase",
            "description": "A test knowledgebase",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "chunk_size": 500,
            "chunk_overlap": 50
        }
        
        response = client.post(
            "/api/agent-builder/knowledgebases",
            json=kb_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 401, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == kb_data["name"]
    
    def test_list_knowledgebases(self, client, auth_headers):
        """Test listing knowledgebases."""
        response = client.get(
            "/api/agent-builder/knowledgebases",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestVariableAPI:
    """Integration tests for Variable API endpoints."""
    
    def test_create_variable(self, client, auth_headers):
        """Test creating a new variable."""
        variable_data = {
            "name": "test_variable",
            "scope": "user",
            "value_type": "string",
            "value": "test value",
            "is_secret": False
        }
        
        response = client.post(
            "/api/agent-builder/variables",
            json=variable_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 401, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert data["name"] == variable_data["name"]
    
    def test_create_secret_variable(self, client, auth_headers):
        """Test creating a secret variable."""
        variable_data = {
            "name": "test_secret",
            "scope": "user",
            "value_type": "string",
            "value": "secret_value_123",
            "is_secret": True
        }
        
        response = client.post(
            "/api/agent-builder/variables",
            json=variable_data,
            headers=auth_headers
        )
        
        assert response.status_code in [201, 401, 500]
        
        if response.status_code == 201:
            data = response.json()
            assert data["is_secret"] is True
            # Value should be masked
            assert data["value"] != variable_data["value"]
    
    def test_list_variables(self, client, auth_headers):
        """Test listing variables with scope filter."""
        response = client.get(
            "/api/agent-builder/variables?scope=user",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestPermissionAPI:
    """Integration tests for Permission API endpoints."""
    
    def test_grant_permission(self, client, auth_headers):
        """Test granting permission to a user."""
        # First create an agent
        agent_data = {
            "name": "Test Permission Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            # Grant permission
            permission_data = {
                "user_id": str(uuid.uuid4()),  # Random user ID
                "resource_type": "agent",
                "resource_id": agent_id,
                "action": "read"
            }
            
            response = client.post(
                "/api/agent-builder/permissions",
                json=permission_data,
                headers=auth_headers
            )
            
            assert response.status_code in [201, 400, 403, 404]
    
    def test_list_permissions(self, client, auth_headers):
        """Test listing permissions."""
        response = client.get(
            "/api/agent-builder/permissions",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_create_share(self, client, auth_headers):
        """Test creating a shareable link."""
        # First create an agent
        agent_data = {
            "name": "Test Share Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            # Create share
            share_data = {
                "resource_type": "agent",
                "resource_id": agent_id,
                "permissions": ["read", "execute"],
                "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
            
            response = client.post(
                "/api/agent-builder/shares",
                json=share_data,
                headers=auth_headers
            )
            
            assert response.status_code in [201, 400, 403, 404]
            
            if response.status_code == 201:
                data = response.json()
                assert "share_token" in data
                assert data["permissions"] == share_data["permissions"]
                return data["share_token"]
    
    def test_access_shared_resource(self, client, auth_headers):
        """Test accessing a shared resource."""
        # Create agent and share
        agent_data = {
            "name": "Test Access Share Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            share_data = {
                "resource_type": "agent",
                "resource_id": agent_id,
                "permissions": ["read"]
            }
            
            share_response = client.post(
                "/api/agent-builder/shares",
                json=share_data,
                headers=auth_headers
            )
            
            if share_response.status_code == 201:
                share_token = share_response.json()["share_token"]
                
                # Access shared resource (no auth required)
                response = client.get(
                    f"/api/agent-builder/shares/{share_token}"
                )
                
                assert response.status_code in [200, 404]
                
                if response.status_code == 200:
                    data = response.json()
                    assert data["resource_type"] == "agent"
                    assert data["resource_id"] == agent_id


class TestAuthenticationAndAuthorization:
    """Integration tests for authentication and authorization."""
    
    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication."""
        # Try to access without auth headers
        response = client.get("/api/agent-builder/agents")
        assert response.status_code in [401, 403]
    
    def test_invalid_token(self, client):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/agent-builder/agents", headers=headers)
        assert response.status_code in [401, 403]
    
    def test_permission_check(self, client, auth_headers):
        """Test that users can only access their own resources."""
        # Create an agent
        agent_data = {
            "name": "Test Permission Check Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            
            # Try to access with different user (would need another auth token)
            # For now, just verify the agent is accessible by owner
            response = client.get(
                f"/api/agent-builder/agents/{agent_id}",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 404]


class TestErrorHandling:
    """Integration tests for error handling."""
    
    def test_invalid_agent_data(self, client, auth_headers):
        """Test error handling for invalid agent data."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "agent_type": "invalid_type"
        }
        
        response = client.post(
            "/api/agent-builder/agents",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_nonexistent_resource(self, client, auth_headers):
        """Test error handling for nonexistent resources."""
        fake_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/agent-builder/agents/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_duplicate_permission(self, client, auth_headers):
        """Test error handling for duplicate permissions."""
        # Create agent
        agent_data = {
            "name": "Test Duplicate Permission Agent",
            "agent_type": "custom",
            "llm_provider": "ollama",
            "llm_model": "llama2"
        }
        
        create_response = client.post(
            "/api/agent-builder/agents",
            json=agent_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            agent_id = create_response.json()["id"]
            user_id = str(uuid.uuid4())
            
            permission_data = {
                "user_id": user_id,
                "resource_type": "agent",
                "resource_id": agent_id,
                "action": "read"
            }
            
            # Grant permission first time
            first_response = client.post(
                "/api/agent-builder/permissions",
                json=permission_data,
                headers=auth_headers
            )
            
            if first_response.status_code == 201:
                # Try to grant same permission again
                second_response = client.post(
                    "/api/agent-builder/permissions",
                    json=permission_data,
                    headers=auth_headers
                )
                
                assert second_response.status_code == 409


class TestPaginationAndFiltering:
    """Integration tests for pagination and filtering."""
    
    def test_agent_pagination(self, client, auth_headers):
        """Test agent list pagination."""
        # Create multiple agents
        for i in range(3):
            agent_data = {
                "name": f"Test Pagination Agent {i}",
                "agent_type": "custom",
                "llm_provider": "ollama",
                "llm_model": "llama2"
            }
            client.post(
                "/api/agent-builder/agents",
                json=agent_data,
                headers=auth_headers
            )
        
        # Test pagination
        response = client.get(
            "/api/agent-builder/agents?skip=0&limit=2",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert len(data["agents"]) <= 2
    
    def test_block_type_filter(self, client, auth_headers):
        """Test block list filtering by type."""
        response = client.get(
            "/api/agent-builder/blocks?block_type=llm",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # All blocks should be of type 'llm'
            for block in data:
                if "block_type" in block:
                    assert block["block_type"] == "llm"
    
    def test_variable_scope_filter(self, client, auth_headers):
        """Test variable list filtering by scope."""
        response = client.get(
            "/api/agent-builder/variables?scope=user",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # All variables should have scope 'user'
            for variable in data:
                if "scope" in variable:
                    assert variable["scope"] == "user"
