"""
Integration tests for Memory Management API
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.db.models.agent_builder import Agent, AgentMemory, MemorySettings


@pytest.fixture
async def test_agent(db: Session):
    """Create a test agent"""
    agent = Agent(
        id=uuid4(),
        name="Test Agent",
        description="Test agent for memory tests",
        type="conversational",
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        system_prompt="You are a test agent",
        is_active=True
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    yield agent
    
    # Cleanup
    db.delete(agent)
    db.commit()


@pytest.fixture
async def test_memories(db: Session, test_agent):
    """Create test memories"""
    memories = []
    
    for i in range(5):
        memory = AgentMemory(
            id=uuid4(),
            agent_id=test_agent.id,
            type=["short_term", "long_term", "episodic", "semantic"][i % 4],
            content=f"Test memory content {i}",
            metadata={"test": True},
            importance=["low", "medium", "high"][i % 3],
            access_count=i
        )
        db.add(memory)
        memories.append(memory)
    
    db.commit()
    
    yield memories
    
    # Cleanup
    for memory in memories:
        db.delete(memory)
    db.commit()


@pytest.mark.asyncio
async def test_get_memory_stats(client: AsyncClient, test_agent, test_memories):
    """Test getting memory statistics"""
    response = await client.get(
        f"/api/agent-builder/agents/{test_agent.id}/memory/stats"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "short_term" in data
    assert "long_term" in data
    assert "episodic" in data
    assert "semantic" in data
    assert "total_size_mb" in data
    assert data["short_term"]["count"] >= 0
    assert data["long_term"]["count"] >= 0


@pytest.mark.asyncio
async def test_get_memories(client: AsyncClient, test_agent, test_memories):
    """Test getting memories list"""
    response = await client.get(
        f"/api/agent-builder/agents/{test_agent.id}/memory",
        params={"limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check memory structure
    memory = data[0]
    assert "id" in memory
    assert "type" in memory
    assert "content" in memory
    assert "importance" in memory


@pytest.mark.asyncio
async def test_get_memories_filtered(client: AsyncClient, test_agent, test_memories):
    """Test getting memories with type filter"""
    response = await client.get(
        f"/api/agent-builder/agents/{test_agent.id}/memory",
        params={"memory_type": "semantic", "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned memories should be semantic
    for memory in data:
        assert memory["type"] == "semantic"


@pytest.mark.asyncio
async def test_search_memories(client: AsyncClient, test_agent, test_memories):
    """Test semantic memory search"""
    response = await client.post(
        f"/api/agent-builder/agents/{test_agent.id}/memory/search",
        json={
            "query": "test",
            "top_k": 5
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    
    # Check search result structure
    if len(data) > 0:
        result = data[0]
        assert "memory" in result
        assert "relevance_score" in result
        assert 0 <= result["relevance_score"] <= 1


@pytest.mark.asyncio
async def test_delete_memory(client: AsyncClient, test_agent, test_memories, db: Session):
    """Test deleting a memory"""
    memory_to_delete = test_memories[0]
    
    response = await client.delete(
        f"/api/agent-builder/agents/{test_agent.id}/memory/{memory_to_delete.id}"
    )
    
    assert response.status_code == 204
    
    # Verify deletion
    db.refresh(test_agent)
    deleted_memory = db.query(AgentMemory).filter(
        AgentMemory.id == memory_to_delete.id
    ).first()
    
    assert deleted_memory is None


@pytest.mark.asyncio
async def test_get_memory_timeline(client: AsyncClient, test_agent, test_memories):
    """Test getting memory timeline"""
    response = await client.get(
        f"/api/agent-builder/agents/{test_agent.id}/memory/timeline",
        params={"limit": 20}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    
    # Check timeline event structure
    if len(data) > 0:
        event = data[0]
        assert "id" in event
        assert "type" in event
        assert "memory_id" in event
        assert "timestamp" in event
        assert event["type"] in ["created", "accessed", "updated", "consolidated"]


@pytest.mark.asyncio
async def test_get_memory_settings(client: AsyncClient, test_agent):
    """Test getting memory settings"""
    response = await client.get(
        f"/api/agent-builder/agents/{test_agent.id}/memory/settings"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "short_term_retention_hours" in data
    assert "auto_cleanup" in data
    assert "auto_consolidation" in data
    assert "consolidation_threshold" in data
    assert "enable_compression" in data
    assert "max_memory_size_mb" in data


@pytest.mark.asyncio
async def test_update_memory_settings(client: AsyncClient, test_agent, db: Session):
    """Test updating memory settings"""
    new_settings = {
        "short_term_retention_hours": 48,
        "auto_cleanup": True,
        "auto_consolidation": True,
        "consolidation_threshold": 150,
        "enable_compression": True,
        "max_memory_size_mb": 2000,
        "importance_threshold": "medium"
    }
    
    response = await client.put(
        f"/api/agent-builder/agents/{test_agent.id}/memory/settings",
        json=new_settings
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["short_term_retention_hours"] == 48
    assert data["consolidation_threshold"] == 150
    assert data["max_memory_size_mb"] == 2000
    
    # Verify in database
    settings = db.query(MemorySettings).filter(
        MemorySettings.agent_id == test_agent.id
    ).first()
    
    assert settings is not None
    assert settings.short_term_retention_hours == 48


@pytest.mark.asyncio
async def test_consolidate_memories(client: AsyncClient, test_agent, test_memories):
    """Test manual memory consolidation"""
    response = await client.post(
        f"/api/agent-builder/agents/{test_agent.id}/memory/consolidate"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "consolidated_count" in data
    assert "estimated_time_seconds" in data


@pytest.mark.asyncio
async def test_invalid_agent_id(client: AsyncClient):
    """Test with invalid agent ID"""
    response = await client.get(
        "/api/agent-builder/agents/invalid-uuid/memory/stats"
    )
    
    assert response.status_code == 400
    assert "Invalid agent ID" in response.json()["detail"]


@pytest.mark.asyncio
async def test_nonexistent_agent(client: AsyncClient):
    """Test with non-existent agent"""
    fake_id = uuid4()
    
    response = await client.get(
        f"/api/agent-builder/agents/{fake_id}/memory/stats"
    )
    
    # Should return empty stats, not error
    assert response.status_code == 200
    data = response.json()
    assert data["short_term"]["count"] == 0
