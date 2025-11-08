"""Unit tests for Agent Builder service layer.

These tests verify the core functionality of Agent Builder services
including AgentService, ToolRegistry, VariableResolver, BlockService,
WorkflowService, and KnowledgebaseService with mocked database.
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

# Set environment variables to avoid import errors
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("MILVUS_HOST", "localhost")
os.environ.setdefault("MILVUS_PORT", "19530")

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
)
from backend.models.agent_builder import (
    AgentCreate,
    AgentUpdate,
    BlockCreate,
    BlockUpdate,
    WorkflowCreate,
    KnowledgebaseCreate,
    VariableCreate,
    ExecutionContext,
)
from backend.services.agent_builder.agent_service import AgentService
from backend.services.agent_builder.tool_registry import ToolRegistry
from backend.services.agent_builder.variable_resolver import VariableResolver
from backend.services.agent_builder.block_service import BlockService
from backend.services.agent_builder.workflow_service import WorkflowService
from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService


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


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.setex = Mock()
    redis_mock.delete = Mock()
    redis_mock.keys = Mock(return_value=[])
    return redis_mock


# ============================================================================
# AgentService Tests
# ============================================================================

class TestAgentService:
    """Tests for AgentService."""
    
    def test_create_agent_basic(self, db_session):
        """Test creating a basic agent."""
        service = AgentService(db_session)
        
        agent_data = AgentCreate(
            name="Test Agent",
            description="A test agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=[],
            knowledgebase_ids=[]
        )
        
        agent = service.create_agent(
            user_id="user123",
            agent_data=agent_data
        )
        
        assert agent.id is not None
        assert agent.name == "Test Agent"
        assert agent.agent_type == "custom"
        assert agent.user_id == "user123"
        assert agent.llm_provider == "ollama"
        assert agent.llm_model == "llama3.1"
        assert agent.created_at is not None
    
    def test_create_agent_with_tools(self, db_session):
        """Test creating an agent with tools."""
        service = AgentService(db_session)
        
        # Create a tool first
        tool = Tool(
            id="tool1",
            name="Test Tool",
            description="A test tool",
            category="test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            implementation_type="langchain",
            implementation_ref="test.Tool",
            is_builtin=True
        )
        db_session.add(tool)
        db_session.commit()
        
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=["tool1"]
        )
        
        agent = service.create_agent(
            user_id="user123",
            agent_data=agent_data
        )
        
        # Verify tool was attached
        agent_tools = db_session.query(AgentTool).filter(
            AgentTool.agent_id == agent.id
        ).all()
        
        assert len(agent_tools) == 1
        assert agent_tools[0].tool_id == "tool1"
    
    def test_get_agent(self, db_session):
        """Test getting an agent by ID."""
        service = AgentService(db_session)
        
        # Create agent
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        created_agent = service.create_agent("user123", agent_data)
        
        # Get agent
        retrieved_agent = service.get_agent(created_agent.id)
        
        assert retrieved_agent is not None
        assert retrieved_agent.id == created_agent.id
        assert retrieved_agent.name == "Test Agent"
    
    def test_get_agent_not_found(self, db_session):
        """Test getting a non-existent agent."""
        service = AgentService(db_session)
        
        agent = service.get_agent("nonexistent")
        
        assert agent is None
    
    def test_update_agent(self, db_session):
        """Test updating an agent."""
        service = AgentService(db_session)
        
        # Create agent
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        agent = service.create_agent("user123", agent_data)
        
        # Update agent
        update_data = AgentUpdate(
            name="Updated Agent",
            description="Updated description"
        )
        updated_agent = service.update_agent(
            agent.id,
            update_data,
            "user123"
        )
        
        assert updated_agent is not None
        assert updated_agent.name == "Updated Agent"
        assert updated_agent.description == "Updated description"
    
    def test_delete_agent(self, db_session):
        """Test soft deleting an agent."""
        service = AgentService(db_session)
        
        # Create agent
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        agent = service.create_agent("user123", agent_data)
        
        # Delete agent
        result = service.delete_agent(agent.id)
        
        assert result is True
        
        # Verify soft delete
        deleted_agent = db_session.query(Agent).filter(
            Agent.id == agent.id
        ).first()
        assert deleted_agent.deleted_at is not None
        
        # Verify get_agent doesn't return deleted agent
        retrieved = service.get_agent(agent.id)
        assert retrieved is None
    
    def test_list_agents(self, db_session):
        """Test listing agents with filters."""
        service = AgentService(db_session)
        
        # Create multiple agents
        for i in range(3):
            agent_data = AgentCreate(
                name=f"Agent {i}",
                agent_type="custom",
                llm_provider="ollama",
                llm_model="llama3.1"
            )
            service.create_agent(f"user{i % 2}", agent_data)
        
        # List all agents
        all_agents = service.list_agents()
        assert len(all_agents) == 3
        
        # List agents for specific user
        user0_agents = service.list_agents(user_id="user0")
        assert len(user0_agents) == 2
        
        user1_agents = service.list_agents(user_id="user1")
        assert len(user1_agents) == 1
    
    def test_clone_agent(self, db_session):
        """Test cloning an agent."""
        service = AgentService(db_session)
        
        # Create original agent
        agent_data = AgentCreate(
            name="Original Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            configuration={"key": "value"}
        )
        original = service.create_agent("user1", agent_data)
        
        # Clone agent
        cloned = service.clone_agent(
            original.id,
            "user2",
            "Cloned Agent"
        )
        
        assert cloned is not None
        assert cloned.id != original.id
        assert cloned.name == "Cloned Agent"
        assert cloned.user_id == "user2"
        assert cloned.llm_provider == original.llm_provider
        assert cloned.configuration == original.configuration
        assert cloned.is_public is False
    
    def test_export_agent(self, db_session):
        """Test exporting an agent."""
        service = AgentService(db_session)
        
        # Create agent
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            configuration={"key": "value"}
        )
        agent = service.create_agent("user123", agent_data)
        
        # Export agent
        export_data = service.export_agent(agent.id)
        
        assert export_data is not None
        assert export_data["agent"]["name"] == "Test Agent"
        assert export_data["agent"]["llm_provider"] == "ollama"
        assert "tools" in export_data
        assert "knowledgebases" in export_data
        assert "versions" in export_data
    
    def test_import_agent(self, db_session):
        """Test importing an agent."""
        service = AgentService(db_session)
        
        # Import data
        import_data = {
            "agent": {
                "name": "Imported Agent",
                "description": "An imported agent",
                "agent_type": "custom",
                "llm_provider": "ollama",
                "llm_model": "llama3.1",
                "configuration": {"key": "value"}
            },
            "tools": [],
            "knowledgebases": []
        }
        
        agent = service.import_agent("user123", import_data)
        
        assert agent is not None
        assert agent.name == "Imported Agent"
        assert agent.user_id == "user123"
        assert agent.configuration == {"key": "value"}


# ============================================================================
# ToolRegistry Tests
# ============================================================================

class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    def test_initialize_builtin_tools(self, db_session):
        """Test initialization of built-in tools."""
        registry = ToolRegistry(db_session)
        
        # Verify built-in tools were created
        tools = db_session.query(Tool).filter(Tool.is_builtin == True).all()
        
        assert len(tools) > 0
        
        # Check for specific tools
        tool_ids = [t.id for t in tools]
        assert "vector_search" in tool_ids
        assert "web_search" in tool_ids
        assert "file_operation" in tool_ids
    
    def test_get_tool(self, db_session):
        """Test getting a tool by ID."""
        registry = ToolRegistry(db_session)
        
        # Get built-in tool
        tool = registry.get_tool("file_operation")
        
        assert tool is not None
        assert hasattr(tool, "name")
        assert hasattr(tool, "_run")
    
    def test_get_tool_not_found(self, db_session):
        """Test getting a non-existent tool."""
        registry = ToolRegistry(db_session)
        
        with pytest.raises(ValueError, match="Tool not found"):
            registry.get_tool("nonexistent_tool")
    
    def test_list_tools(self, db_session):
        """Test listing tools."""
        registry = ToolRegistry(db_session)
        
        # List all tools
        all_tools = registry.list_tools()
        assert len(all_tools) > 0
        
        # List by category
        search_tools = registry.list_tools(category="search")
        assert len(search_tools) > 0
        
        # List built-in only
        builtin_tools = registry.list_tools(builtin_only=True)
        assert all(t.is_builtin for t in builtin_tools)
    
    def test_validate_tool_input(self, db_session):
        """Test tool input validation."""
        registry = ToolRegistry(db_session)
        
        # Valid input
        valid_input = {"query": "test query"}
        assert registry.validate_tool_input("vector_search", valid_input) is True
        
        # Invalid input (missing required field)
        invalid_input = {"top_k": 10}
        assert registry.validate_tool_input("vector_search", invalid_input) is False


# ============================================================================
# VariableResolver Tests
# ============================================================================

class TestVariableResolver:
    """Tests for VariableResolver."""
    
    @pytest.mark.asyncio
    async def test_resolve_variable_global(self, db_session):
        """Test resolving a global variable."""
        resolver = VariableResolver(db_session)
        
        # Create global variable
        var = Variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="test_value",
            value_type="string"
        )
        db_session.add(var)
        db_session.commit()
        
        # Resolve variable
        context = ExecutionContext(
            user_id="user123",
            agent_id="agent123",
            execution_id="exec123"
        )
        
        value = await resolver.resolve_variable("test_var", context)
        
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_resolve_variable_scope_precedence(self, db_session):
        """Test variable resolution with scope precedence."""
        resolver = VariableResolver(db_session)
        
        # Create variables at different scopes
        global_var = Variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="global_value",
            value_type="string"
        )
        user_var = Variable(
            name="test_var",
            scope="user",
            scope_id="user123",
            value="user_value",
            value_type="string"
        )
        agent_var = Variable(
            name="test_var",
            scope="agent",
            scope_id="agent123",
            value="agent_value",
            value_type="string"
        )
        
        db_session.add_all([global_var, user_var, agent_var])
        db_session.commit()
        
        # Resolve variable (should get agent-level value)
        context = ExecutionContext(
            user_id="user123",
            agent_id="agent123",
            execution_id="exec123"
        )
        
        value = await resolver.resolve_variable("test_var", context)
        
        assert value == "agent_value"
    
    @pytest.mark.asyncio
    async def test_resolve_variable_not_found(self, db_session):
        """Test resolving a non-existent variable."""
        resolver = VariableResolver(db_session)
        
        context = ExecutionContext(
            user_id="user123",
            agent_id="agent123",
            execution_id="exec123"
        )
        
        with pytest.raises(ValueError, match="Variable not found"):
            await resolver.resolve_variable("nonexistent", context)
    
    @pytest.mark.asyncio
    async def test_resolve_variables_in_template(self, db_session):
        """Test resolving variables in a template string."""
        resolver = VariableResolver(db_session)
        
        # Create variables
        var1 = Variable(
            name="name",
            scope="global",
            scope_id=None,
            value="John",
            value_type="string"
        )
        var2 = Variable(
            name="age",
            scope="global",
            scope_id=None,
            value="30",
            value_type="number"
        )
        
        db_session.add_all([var1, var2])
        db_session.commit()
        
        # Resolve template
        template = "Hello ${name}, you are ${age} years old."
        context = ExecutionContext(
            user_id="user123",
            agent_id="agent123",
            execution_id="exec123"
        )
        
        resolved = await resolver.resolve_variables(template, context)
        
        assert resolved == "Hello John, you are 30 years old."
    
    @pytest.mark.asyncio
    async def test_resolve_variables_with_defaults(self, db_session):
        """Test resolving variables with default values."""
        resolver = VariableResolver(db_session)
        
        # Create one variable
        var = Variable(
            name="name",
            scope="global",
            scope_id=None,
            value="John",
            value_type="string"
        )
        db_session.add(var)
        db_session.commit()
        
        # Resolve template with default for missing variable
        template = "Hello ${name}, your role is ${role}."
        context = ExecutionContext(
            user_id="user123",
            agent_id="agent123",
            execution_id="exec123"
        )
        default_values = {"role": "admin"}
        
        resolved = await resolver.resolve_variables(
            template,
            context,
            default_values
        )
        
        assert resolved == "Hello John, your role is admin."
    
    def test_create_variable(self, db_session):
        """Test creating a variable."""
        resolver = VariableResolver(db_session)
        
        var = resolver.create_variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="test_value",
            value_type="string",
            is_secret=False
        )
        
        assert var.id is not None
        assert var.name == "test_var"
        assert var.scope == "global"
        assert var.value == "test_value"
    
    def test_create_variable_duplicate(self, db_session):
        """Test creating a duplicate variable."""
        resolver = VariableResolver(db_session)
        
        # Create first variable
        resolver.create_variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="value1",
            value_type="string"
        )
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            resolver.create_variable(
                name="test_var",
                scope="global",
                scope_id=None,
                value="value2",
                value_type="string"
            )
    
    def test_update_variable(self, db_session):
        """Test updating a variable."""
        resolver = VariableResolver(db_session)
        
        # Create variable
        var = resolver.create_variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="old_value",
            value_type="string"
        )
        
        # Update variable
        updated = resolver.update_variable(
            var.id,
            value="new_value"
        )
        
        assert updated.value == "new_value"
    
    def test_delete_variable(self, db_session):
        """Test deleting a variable."""
        resolver = VariableResolver(db_session)
        
        # Create variable
        var = resolver.create_variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="test_value",
            value_type="string"
        )
        
        # Delete variable
        result = resolver.delete_variable(var.id)
        
        assert result is True
        
        # Verify soft delete
        deleted_var = db_session.query(Variable).filter(
            Variable.id == var.id
        ).first()
        assert deleted_var.deleted_at is not None
    
    def test_list_variables(self, db_session):
        """Test listing variables."""
        resolver = VariableResolver(db_session)
        
        # Create variables
        resolver.create_variable(
            name="var1",
            scope="global",
            scope_id=None,
            value="value1",
            value_type="string"
        )
        resolver.create_variable(
            name="var2",
            scope="user",
            scope_id="user123",
            value="value2",
            value_type="string"
        )
        
        # List all variables
        all_vars = resolver.list_variables()
        assert len(all_vars) == 2
        
        # List by scope
        global_vars = resolver.list_variables(scope="global")
        assert len(global_vars) == 1
        assert global_vars[0].name == "var1"
    
    def test_parse_value_types(self, db_session):
        """Test parsing different value types."""
        resolver = VariableResolver(db_session)
        
        # String
        assert resolver._parse_value("hello", "string") == "hello"
        
        # Number (int)
        assert resolver._parse_value("42", "number") == 42
        
        # Number (float)
        assert resolver._parse_value("3.14", "number") == 3.14
        
        # Boolean
        assert resolver._parse_value("true", "boolean") is True
        assert resolver._parse_value("false", "boolean") is False
        
        # JSON
        import json
        json_value = resolver._parse_value('{"key": "value"}', "json")
        assert json_value == {"key": "value"}


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestServiceErrorHandling:
    """Tests for service error handling."""
    
    def test_agent_service_handles_invalid_tool(self, db_session):
        """Test AgentService handles invalid tool IDs gracefully."""
        service = AgentService(db_session)
        
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=["nonexistent_tool"]
        )
        
        # Should not raise exception, just skip invalid tool
        agent = service.create_agent("user123", agent_data)
        
        assert agent is not None
        
        # Verify no tools were attached
        agent_tools = db_session.query(AgentTool).filter(
            AgentTool.agent_id == agent.id
        ).all()
        assert len(agent_tools) == 0
    
    def test_variable_resolver_handles_cache_errors(self, db_session, mock_redis):
        """Test VariableResolver handles cache errors gracefully."""
        # Make cache raise exception
        mock_redis.get.side_effect = Exception("Cache error")
        
        resolver = VariableResolver(db_session, mock_redis)
        
        # Create variable
        var = Variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="test_value",
            value_type="string"
        )
        db_session.add(var)
        db_session.commit()
        
        # Should still work despite cache error
        context = ExecutionContext(
            user_id="user123",
            agent_id="agent123",
            execution_id="exec123"
        )
        
        import asyncio
        value = asyncio.run(resolver.resolve_variable("test_var", context))
        
        assert value == "test_value"


# ============================================================================
# Validation Tests
# ============================================================================

class TestServiceValidation:
    """Tests for service input validation."""
    
    def test_agent_service_validates_required_fields(self, db_session):
        """Test AgentService validates required fields."""
        service = AgentService(db_session)
        
        # Missing required fields should be caught by Pydantic
        with pytest.raises(Exception):
            agent_data = AgentCreate(
                name="",  # Empty name
                agent_type="custom",
                llm_provider="ollama",
                llm_model="llama3.1"
            )
    
    def test_variable_resolver_validates_value_types(self, db_session):
        """Test VariableResolver validates value types."""
        resolver = VariableResolver(db_session)
        
        # Create variable with invalid JSON
        var = Variable(
            name="test_var",
            scope="global",
            scope_id=None,
            value="invalid json {",
            value_type="json"
        )
        
        # Should handle gracefully and return original value
        parsed = resolver._parse_value(var.value, var.value_type)
        assert parsed == "invalid json {"




# ============================================================================
# BlockService Tests
# ============================================================================

class TestBlockService:
    """Tests for BlockService."""
    
    def test_create_block(self, db_session):
        """Test creating a block."""
        service = BlockService(db_session)
        
        block_data = BlockCreate(
            name="Test Block",
            description="A test block",
            block_type="llm",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
            configuration={"prompt": "Process: {text}"}
        )
        
        block = service.create_block("user123", block_data)
        
        assert block.id is not None
        assert block.name == "Test Block"
        assert block.block_type == "llm"
        assert block.user_id == "user123"
    
    def test_get_block(self, db_session):
        """Test getting a block by ID."""
        service = BlockService(db_session)
        
        # Create block
        block_data = BlockCreate(
            name="Test Block",
            block_type="tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )
        created_block = service.create_block("user123", block_data)
        
        # Get block
        retrieved_block = service.get_block(created_block.id)
        
        assert retrieved_block is not None
        assert retrieved_block.id == created_block.id
        assert retrieved_block.name == "Test Block"
    
    def test_update_block(self, db_session):
        """Test updating a block."""
        service = BlockService(db_session)
        
        # Create block
        block_data = BlockCreate(
            name="Test Block",
            block_type="llm",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )
        block = service.create_block("user123", block_data)
        
        # Update block
        update_data = BlockUpdate(
            name="Updated Block",
            description="Updated description"
        )
        updated_block = service.update_block(block.id, update_data)
        
        assert updated_block is not None
        assert updated_block.name == "Updated Block"
        assert updated_block.description == "Updated description"
    
    def test_delete_block(self, db_session):
        """Test deleting a block."""
        service = BlockService(db_session)
        
        # Create block
        block_data = BlockCreate(
            name="Test Block",
            block_type="llm",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )
        block = service.create_block("user123", block_data)
        
        # Delete block
        result = service.delete_block(block.id)
        
        assert result is True
        
        # Verify deletion
        deleted_block = service.get_block(block.id)
        assert deleted_block is None
    
    def test_list_blocks(self, db_session):
        """Test listing blocks with filters."""
        service = BlockService(db_session)
        
        # Create blocks of different types
        for block_type in ["llm", "tool", "logic"]:
            block_data = BlockCreate(
                name=f"{block_type} Block",
                block_type=block_type,
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            )
            service.create_block("user123", block_data)
        
        # List all blocks
        all_blocks = service.list_blocks()
        assert len(all_blocks) == 3
        
        # List by type
        llm_blocks = service.list_blocks(block_type="llm")
        assert len(llm_blocks) == 1
        assert llm_blocks[0].block_type == "llm"


# ============================================================================
# WorkflowService Tests
# ============================================================================

class TestWorkflowService:
    """Tests for WorkflowService."""
    
    def test_create_workflow(self, db_session):
        """Test creating a workflow."""
        service = WorkflowService(db_session)
        
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            description="A test workflow",
            graph_definition={
                "nodes": [
                    {"id": "node1", "type": "agent", "agent_id": "agent1"},
                    {"id": "node2", "type": "agent", "agent_id": "agent2"}
                ],
                "edges": [
                    {"source": "node1", "target": "node2", "type": "normal"}
                ],
                "entry_point": "node1"
            }
        )
        
        workflow = service.create_workflow("user123", workflow_data)
        
        assert workflow.id is not None
        assert workflow.name == "Test Workflow"
        assert workflow.user_id == "user123"
        assert "nodes" in workflow.graph_definition
        assert "edges" in workflow.graph_definition
    
    def test_get_workflow(self, db_session):
        """Test getting a workflow by ID."""
        service = WorkflowService(db_session)
        
        # Create workflow
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            graph_definition={"nodes": [], "edges": [], "entry_point": "start"}
        )
        created_workflow = service.create_workflow("user123", workflow_data)
        
        # Get workflow
        retrieved_workflow = service.get_workflow(created_workflow.id)
        
        assert retrieved_workflow is not None
        assert retrieved_workflow.id == created_workflow.id
        assert retrieved_workflow.name == "Test Workflow"
    
    def test_update_workflow(self, db_session):
        """Test updating a workflow."""
        service = WorkflowService(db_session)
        
        # Create workflow
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            graph_definition={"nodes": [], "edges": [], "entry_point": "start"}
        )
        workflow = service.create_workflow("user123", workflow_data)
        
        # Update workflow
        update_data = WorkflowUpdate(
            name="Updated Workflow",
            description="Updated description"
        )
        updated_workflow = service.update_workflow(workflow.id, update_data)
        
        assert updated_workflow is not None
        assert updated_workflow.name == "Updated Workflow"
        assert updated_workflow.description == "Updated description"
    
    def test_delete_workflow(self, db_session):
        """Test deleting a workflow."""
        service = WorkflowService(db_session)
        
        # Create workflow
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            graph_definition={"nodes": [], "edges": [], "entry_point": "start"}
        )
        workflow = service.create_workflow("user123", workflow_data)
        
        # Delete workflow
        result = service.delete_workflow(workflow.id)
        
        assert result is True
        
        # Verify deletion
        deleted_workflow = service.get_workflow(workflow.id)
        assert deleted_workflow is None
    
    def test_validate_workflow_no_cycles(self, db_session):
        """Test workflow validation detects cycles."""
        from backend.models.agent_builder import WorkflowNodeCreate, WorkflowEdgeCreate
        
        service = WorkflowService(db_session)
        
        # Valid workflow (no cycles)
        nodes = [
            WorkflowNodeCreate(id="node1", node_type="agent", node_ref_id="agent1"),
            WorkflowNodeCreate(id="node2", node_type="agent", node_ref_id="agent2"),
            WorkflowNodeCreate(id="node3", node_type="agent", node_ref_id="agent3")
        ]
        edges = [
            WorkflowEdgeCreate(id="edge1", source_node_id="node1", target_node_id="node2", edge_type="normal"),
            WorkflowEdgeCreate(id="edge2", source_node_id="node2", target_node_id="node3", edge_type="normal")
        ]
        
        result = service.validate_workflow_definition(nodes, edges, "node1")
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_workflow_with_cycle(self, db_session):
        """Test workflow validation detects cycles."""
        from backend.models.agent_builder import WorkflowNodeCreate, WorkflowEdgeCreate
        
        service = WorkflowService(db_session)
        
        # Workflow with cycle
        nodes = [
            WorkflowNodeCreate(id="node1", node_type="agent", node_ref_id="agent1"),
            WorkflowNodeCreate(id="node2", node_type="agent", node_ref_id="agent2")
        ]
        edges = [
            WorkflowEdgeCreate(id="edge1", source_node_id="node1", target_node_id="node2", edge_type="normal"),
            WorkflowEdgeCreate(id="edge2", source_node_id="node2", target_node_id="node1", edge_type="normal")  # Creates cycle
        ]
        
        result = service.validate_workflow_definition(nodes, edges, "node1")
        
        assert result.is_valid is False
        assert any("cycle" in error.lower() for error in result.errors)


# ============================================================================
# KnowledgebaseService Tests
# ============================================================================

class TestKnowledgebaseService:
    """Tests for KnowledgebaseService."""
    
    @patch('backend.services.agent_builder.knowledgebase_service.MilvusService')
    def test_create_knowledgebase(self, mock_milvus, db_session):
        """Test creating a knowledgebase."""
        # Mock Milvus service
        mock_milvus_instance = Mock()
        mock_milvus_instance.create_collection = AsyncMock()
        mock_milvus.return_value = mock_milvus_instance
        
        service = KnowledgebaseService(db_session, mock_milvus_instance)
        
        kb_data = KnowledgebaseCreate(
            name="Test KB",
            description="A test knowledgebase",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            chunk_size=500,
            chunk_overlap=50
        )
        
        import asyncio
        kb = asyncio.run(service.create_knowledgebase("user123", kb_data))
        
        assert kb.id is not None
        assert kb.name == "Test KB"
        assert kb.user_id == "user123"
        assert kb.milvus_collection_name is not None
    
    @patch('backend.services.agent_builder.knowledgebase_service.MilvusService')
    def test_get_knowledgebase(self, mock_milvus, db_session):
        """Test getting a knowledgebase by ID."""
        mock_milvus_instance = Mock()
        mock_milvus_instance.create_collection = AsyncMock()
        mock_milvus.return_value = mock_milvus_instance
        
        service = KnowledgebaseService(db_session, mock_milvus_instance)
        
        # Create knowledgebase
        kb_data = KnowledgebaseCreate(
            name="Test KB",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        import asyncio
        created_kb = asyncio.run(service.create_knowledgebase("user123", kb_data))
        
        # Get knowledgebase
        retrieved_kb = service.get_knowledgebase(created_kb.id)
        
        assert retrieved_kb is not None
        assert retrieved_kb.id == created_kb.id
        assert retrieved_kb.name == "Test KB"
    
    @patch('backend.services.agent_builder.knowledgebase_service.MilvusService')
    def test_delete_knowledgebase(self, mock_milvus, db_session):
        """Test deleting a knowledgebase."""
        mock_milvus_instance = Mock()
        mock_milvus_instance.create_collection = AsyncMock()
        mock_milvus_instance.delete_collection = AsyncMock()
        mock_milvus.return_value = mock_milvus_instance
        
        service = KnowledgebaseService(db_session, mock_milvus_instance)
        
        # Create knowledgebase
        kb_data = KnowledgebaseCreate(
            name="Test KB",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        import asyncio
        kb = asyncio.run(service.create_knowledgebase("user123", kb_data))
        
        # Delete knowledgebase
        result = asyncio.run(service.delete_knowledgebase(kb.id))
        
        assert result is True
        
        # Verify deletion
        deleted_kb = service.get_knowledgebase(kb.id)
        assert deleted_kb is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestServiceIntegration:
    """Integration tests for multiple services working together."""
    
    def test_agent_with_tools_and_variables(self, db_session):
        """Test creating an agent with tools and using variables."""
        # Initialize services
        agent_service = AgentService(db_session)
        tool_registry = ToolRegistry(db_session)
        variable_resolver = VariableResolver(db_session)
        
        # Create variable
        variable_resolver.create_variable(
            name="api_key",
            scope="user",
            scope_id="user123",
            value="secret_key_123",
            value_type="string",
            is_secret=True
        )
        
        # Get available tools
        tools = tool_registry.list_tools(builtin_only=True)
        assert len(tools) > 0
        
        # Create agent with tools
        agent_data = AgentCreate(
            name="API Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tool_ids=[tools[0].id],
            prompt_template="Use API key: ${api_key}"
        )
        
        agent = agent_service.create_agent("user123", agent_data)
        
        assert agent is not None
        assert agent.configuration.get("prompt_template") is not None
        
        # Resolve variables in prompt
        context = ExecutionContext(
            user_id="user123",
            agent_id=agent.id,
            execution_id="exec123"
        )
        
        import asyncio
        resolved_prompt = asyncio.run(
            variable_resolver.resolve_variables(
                agent.configuration["prompt_template"],
                context
            )
        )
        
        assert "secret_key_123" in resolved_prompt
    
    def test_workflow_with_agents_and_blocks(self, db_session):
        """Test creating a workflow with agents and blocks."""
        # Initialize services
        agent_service = AgentService(db_session)
        block_service = BlockService(db_session)
        workflow_service = WorkflowService(db_session)
        
        # Create agent
        agent_data = AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1"
        )
        agent = agent_service.create_agent("user123", agent_data)
        
        # Create block
        block_data = BlockCreate(
            name="Test Block",
            block_type="llm",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )
        block = block_service.create_block("user123", block_data)
        
        # Create workflow with agent and block
        workflow_data = WorkflowCreate(
            name="Test Workflow",
            graph_definition={
                "nodes": [
                    {"id": "agent_node", "type": "agent", "agent_id": agent.id},
                    {"id": "block_node", "type": "block", "block_id": block.id}
                ],
                "edges": [
                    {"source": "agent_node", "target": "block_node", "type": "normal"}
                ],
                "entry_point": "agent_node"
            }
        )
        
        workflow = workflow_service.create_workflow("user123", workflow_data)
        
        assert workflow is not None
        assert len(workflow.graph_definition["nodes"]) == 2
        assert len(workflow.graph_definition["edges"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
