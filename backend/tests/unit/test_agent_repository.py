"""Unit tests for AgentRepository."""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.repositories.agent_repository import (
    AgentRepository,
    AgentVersionRepository,
    AgentToolRepository,
    AgentKnowledgebaseRepository
)
from backend.db.models.agent_builder import Agent, AgentVersion, AgentTool, AgentKnowledgebase


class TestAgentRepository:
    """Test AgentRepository methods."""
    
    def test_create_agent(self, db_session: Session):
        """Test creating an agent."""
        repo = AgentRepository(db_session)
        
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="Test Agent",
            description="Test Description",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            configuration={},
            is_public=False
        )
        
        created = repo.create(agent)
        
        assert created.id == agent.id
        assert created.name == "Test Agent"
        assert created.agent_type == "custom"
        assert created.llm_provider == "ollama"
    
    def test_find_by_id(self, db_session: Session):
        """Test finding agent by ID."""
        repo = AgentRepository(db_session)
        
        # Create agent
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        repo.create(agent)
        db_session.commit()
        
        # Find by ID
        found = repo.find_by_id(agent.id)
        
        assert found is not None
        assert found.id == agent.id
        assert found.name == "Test Agent"
    
    def test_find_by_id_not_found(self, db_session: Session):
        """Test finding non-existent agent."""
        repo = AgentRepository(db_session)
        
        found = repo.find_by_id(str(uuid.uuid4()))
        
        assert found is None
    
    def test_find_by_id_exclude_deleted(self, db_session: Session):
        """Test that soft-deleted agents are excluded."""
        repo = AgentRepository(db_session)
        
        # Create and soft delete agent
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            deleted_at=datetime.utcnow()
        )
        repo.create(agent)
        db_session.commit()
        
        # Should not find deleted agent
        found = repo.find_by_id(agent.id)
        
        assert found is None
        
        # Should find with include_deleted=True
        found_with_deleted = repo.find_by_id(agent.id, include_deleted=True)
        
        assert found_with_deleted is not None
        assert found_with_deleted.id == agent.id
    
    def test_find_by_user(self, db_session: Session):
        """Test finding agents by user ID."""
        repo = AgentRepository(db_session)
        user_id = str(uuid.uuid4())
        
        # Create multiple agents for user
        for i in range(3):
            agent = Agent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=f"Test Agent {i}",
                agent_type="custom",
                llm_provider="ollama",
                llm_model="llama3.1"
            )
            repo.create(agent)
        
        db_session.commit()
        
        # Find by user
        agents = repo.find_by_user(user_id)
        
        assert len(agents) == 3
        assert all(a.user_id == user_id for a in agents)
    
    def test_find_by_user_with_filters(self, db_session: Session):
        """Test finding agents with filters."""
        repo = AgentRepository(db_session)
        user_id = str(uuid.uuid4())
        
        # Create agents with different types
        agent1 = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Custom Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            is_public=False
        )
        agent2 = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Template Agent",
            agent_type="template_based",
            llm_provider="openai",
            llm_model="gpt-4",
            is_public=True
        )
        repo.create(agent1)
        repo.create(agent2)
        db_session.commit()
        
        # Filter by type
        custom_agents = repo.find_by_user(user_id, agent_type="custom")
        assert len(custom_agents) == 1
        assert custom_agents[0].agent_type == "custom"
        
        # Filter by public status
        public_agents = repo.find_by_user(user_id, is_public=True)
        assert len(public_agents) == 1
        assert public_agents[0].is_public is True
    
    def test_update_agent(self, db_session: Session):
        """Test updating an agent."""
        repo = AgentRepository(db_session)
        
        # Create agent
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="Original Name",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        repo.create(agent)
        db_session.commit()
        
        # Update agent
        agent.name = "Updated Name"
        updated = repo.update(agent)
        db_session.commit()
        
        assert updated.name == "Updated Name"
        assert updated.updated_at is not None
    
    def test_soft_delete_agent(self, db_session: Session):
        """Test soft deleting an agent."""
        repo = AgentRepository(db_session)
        
        # Create agent
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        repo.create(agent)
        db_session.commit()
        
        # Soft delete
        deleted = repo.soft_delete(agent)
        db_session.commit()
        
        assert deleted.deleted_at is not None
        
        # Should not find in normal query
        found = repo.find_by_id(agent.id)
        assert found is None
    
    def test_count_by_user(self, db_session: Session):
        """Test counting agents by user."""
        repo = AgentRepository(db_session)
        user_id = str(uuid.uuid4())
        
        # Create agents
        for i in range(5):
            agent = Agent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=f"Test Agent {i}",
                agent_type="custom",
                llm_provider="ollama",
                llm_model="llama3.1"
            )
            repo.create(agent)
        
        db_session.commit()
        
        count = repo.count_by_user(user_id)
        
        assert count == 5
    
    def test_exists(self, db_session: Session):
        """Test checking if agent exists."""
        repo = AgentRepository(db_session)
        
        # Create agent
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        repo.create(agent)
        db_session.commit()
        
        assert repo.exists(agent.id) is True
        assert repo.exists(str(uuid.uuid4())) is False
    
    def test_search_agents(self, db_session: Session):
        """Test searching agents."""
        repo = AgentRepository(db_session)
        user_id = str(uuid.uuid4())
        
        # Create agents with searchable names
        agent1 = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Customer Support Agent",
            description="Helps with customer queries",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            is_public=True
        )
        agent2 = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Sales Assistant",
            description="Assists with sales",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            is_public=True
        )
        repo.create(agent1)
        repo.create(agent2)
        db_session.commit()
        
        # Search by name
        results = repo.search("Customer", user_id=user_id)
        assert len(results) == 1
        assert "Customer" in results[0].name
        
        # Search by description
        results = repo.search("sales", user_id=user_id)
        assert len(results) >= 1


class TestAgentToolRepository:
    """Test AgentToolRepository methods."""
    
    def test_create_agent_tool(self, db_session: Session):
        """Test creating agent-tool association."""
        repo = AgentToolRepository(db_session)
        
        agent_tool = AgentTool(
            id=str(uuid.uuid4()),
            agent_id=str(uuid.uuid4()),
            tool_id="vector_search",
            configuration={},
            order=0
        )
        
        created = repo.create(agent_tool)
        
        assert created.id == agent_tool.id
        assert created.tool_id == "vector_search"
    
    def test_find_by_agent(self, db_session: Session):
        """Test finding tools by agent."""
        repo = AgentToolRepository(db_session)
        agent_id = str(uuid.uuid4())
        
        # Create multiple tools
        for i, tool_id in enumerate(["vector_search", "web_search", "local_data"]):
            agent_tool = AgentTool(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                tool_id=tool_id,
                configuration={},
                order=i
            )
            repo.create(agent_tool)
        
        db_session.commit()
        
        tools = repo.find_by_agent(agent_id)
        
        assert len(tools) == 3
        assert tools[0].order == 0
        assert tools[1].order == 1
        assert tools[2].order == 2
    
    def test_delete_by_agent(self, db_session: Session):
        """Test deleting all tools for an agent."""
        repo = AgentToolRepository(db_session)
        agent_id = str(uuid.uuid4())
        
        # Create tools
        for tool_id in ["vector_search", "web_search"]:
            agent_tool = AgentTool(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                tool_id=tool_id,
                configuration={},
                order=0
            )
            repo.create(agent_tool)
        
        db_session.commit()
        
        # Delete all
        count = repo.delete_by_agent(agent_id)
        db_session.commit()
        
        assert count == 2
        
        # Verify deleted
        tools = repo.find_by_agent(agent_id)
        assert len(tools) == 0


# Pytest fixtures
@pytest.fixture
def db_session():
    """Create a test database session."""
    from backend.db.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
