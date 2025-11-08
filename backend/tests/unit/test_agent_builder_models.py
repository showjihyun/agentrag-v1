"""Tests for Agent Builder database models.

These tests verify the basic functionality of Agent Builder SQLAlchemy models
including creation, relationships, and constraints.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.db.database import Base
from backend.db.models.agent_builder import (
    Agent,
    AgentVersion,
    Tool,
    AgentTool,
    Block,
    BlockVersion,
    Workflow,
    WorkflowNode,
    Knowledgebase,
    Variable,
    Secret,
    AgentExecution,
    ExecutionStep,
    ExecutionMetrics,
    Permission,
)


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def test_agent_model_creation(db_session):
    """Test Agent model creation with required fields."""
    agent = Agent(
        name="Test Agent",
        agent_type="custom",
        llm_provider="ollama",
        llm_model="llama3.1",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    db_session.add(agent)
    db_session.commit()
    
    assert agent.id is not None
    assert agent.name == "Test Agent"
    assert agent.agent_type == "custom"
    assert agent.created_at is not None


def test_agent_soft_delete(db_session):
    """Test Agent soft delete functionality."""
    agent = Agent(
        name="Test Agent",
        agent_type="custom",
        llm_provider="ollama",
        llm_model="llama3.1",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    db_session.add(agent)
    db_session.commit()
    
    # Soft delete
    agent.deleted_at = datetime.utcnow()
    db_session.commit()
    
    assert agent.deleted_at is not None


def test_block_model_creation(db_session):
    """Test Block model creation with required fields."""
    block = Block(
        name="Test Block",
        block_type="llm",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        user_id="00000000-0000-0000-0000-000000000001",
    )
    db_session.add(block)
    db_session.commit()
    
    assert block.id is not None
    assert block.name == "Test Block"
    assert block.block_type == "llm"


def test_workflow_model_creation(db_session):
    """Test Workflow model creation with required fields."""
    workflow = Workflow(
        name="Test Workflow",
        graph_definition={"nodes": [], "edges": []},
        user_id="00000000-0000-0000-0000-000000000001",
    )
    db_session.add(workflow)
    db_session.commit()
    
    assert workflow.id is not None
    assert workflow.name == "Test Workflow"
    assert workflow.graph_definition is not None


def test_variable_model_creation(db_session):
    """Test Variable model creation with required fields."""
    variable = Variable(
        name="test_var",
        scope="global",
        value_type="string",
        value="test_value",
    )
    db_session.add(variable)
    db_session.commit()
    
    assert variable.id is not None
    assert variable.name == "test_var"
    assert variable.scope == "global"


def test_agent_execution_model_creation(db_session):
    """Test AgentExecution model creation with required fields."""
    # Create agent first
    agent = Agent(
        name="Test Agent",
        agent_type="custom",
        llm_provider="ollama",
        llm_model="llama3.1",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    db_session.add(agent)
    db_session.commit()
    
    # Create execution
    execution = AgentExecution(
        agent_id=agent.id,
        user_id="00000000-0000-0000-0000-000000000001",
        status="running",
    )
    db_session.add(execution)
    db_session.commit()
    
    assert execution.id is not None
    assert execution.status == "running"
    assert execution.started_at is not None
