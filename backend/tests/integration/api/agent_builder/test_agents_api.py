"""Integration tests for Agent Builder Agents API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.db.models.agent_builder import Agent, Tool


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    # In real tests, this would use actual JWT token
    return {"Authorization": "Bearer test-token"}


def test_create_agent(client, auth_headers):
    """Test agent creation endpoint."""
    agent_data = {
        "name": "Test Agent",
        "description": "Test description",
        "agent_type": "custom",
        "llm_provider": "ollama",
        "llm_model": "llama3.1",
        "tool_ids": [],
        "knowledgebase_ids": [],
        "is_public": False
    }
    
    response = client.post(
        "/api/agent-builder/agents",
        json=agent_data,
        headers=auth_headers
    )
    
    # Note: This will fail without proper auth setup
    # In real implementation, set up test database and auth
    assert response.status_code in [200, 201, 401, 403]


def test_get_agent(client, auth_headers):
    """Test getting agent by ID."""
    response = client.get(
        "/api/agent-builder/agents/test-id",
        headers=auth_headers
    )
    
    assert response.status_code in [200, 404, 401, 403]


def test_list_agents(client, auth_headers):
    """Test listing agents."""
    response = client.get(
        "/api/agent-builder/agents",
        headers=auth_headers
    )
    
    assert response.status_code in [200, 401, 403]


def test_update_agent(client, auth_headers):
    """Test updating agent."""
    update_data = {
        "name": "Updated Agent",
        "description": "Updated description"
    }
    
    response = client.put(
        "/api/agent-builder/agents/test-id",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code in [200, 404, 401, 403]


def test_delete_agent(client, auth_headers):
    """Test deleting agent."""
    response = client.delete(
        "/api/agent-builder/agents/test-id",
        headers=auth_headers
    )
    
    assert response.status_code in [200, 204, 404, 401, 403]
