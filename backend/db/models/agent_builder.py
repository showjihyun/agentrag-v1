"""Agent Builder database models."""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    BigInteger,
    DateTime,
    Text,
    Float,
    ForeignKey,
    JSON,
    LargeBinary,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.db.database import Base


# ============================================================================
# AGENT MODELS
# ============================================================================


class Agent(Base):
    """Custom agent model."""

    __tablename__ = "agents"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("prompt_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Agent Configuration
    agent_type = Column(String(50), nullable=False, index=True)  # custom, template_based
    llm_provider = Column(String(100), nullable=False)  # ollama, openai, claude
    llm_model = Column(String(100), nullable=False)
    configuration = Column(JSON, default=dict)  # Agent-specific config

    # Visibility
    is_public = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft delete

    # Relationships
    versions = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan")
    tools = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")
    knowledgebases = relationship("AgentKnowledgebase", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_agents_user_type", "user_id", "agent_type"),
        Index("ix_agents_user_created", "user_id", "created_at"),
        CheckConstraint(
            "agent_type IN ('custom', 'template_based')",
            name="check_agent_type_valid",
        ),
    )

    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, type={self.agent_type})>"


class AgentVersion(Base):
    """Agent version history model."""

    __tablename__ = "agent_versions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Version Information
    version_number = Column(String(50), nullable=False)  # Semantic versioning (e.g., 1.0.0)
    configuration = Column(JSON, nullable=False)  # Snapshot of agent config
    change_description = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    agent = relationship("Agent", back_populates="versions")

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_agent_versions_agent_created", "agent_id", "created_at"),
    )

    def __repr__(self):
        return f"<AgentVersion(id={self.id}, agent_id={self.agent_id}, version={self.version_number})>"


class Tool(Base):
    """Tool registry model."""

    __tablename__ = "tools"

    # Primary Key
    id = Column(String(100), primary_key=True)  # e.g., "vector_search"

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)  # search, database, file, api, etc.

    # Schema
    input_schema = Column(JSON, nullable=False)  # JSON Schema for inputs
    output_schema = Column(JSON)  # JSON Schema for outputs

    # Implementation
    implementation_type = Column(String(50), nullable=False)  # langchain, custom, builtin
    implementation_ref = Column(String(500))  # Reference to implementation (module.class)

    # Configuration
    requires_auth = Column(Boolean, default=False)
    is_builtin = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    agent_tools = relationship("AgentTool", back_populates="tool", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "implementation_type IN ('langchain', 'custom', 'builtin')",
            name="check_tool_implementation_type_valid",
        ),
    )

    def __repr__(self):
        return f"<Tool(id={self.id}, name={self.name}, category={self.category})>"


class AgentTool(Base):
    """Agent-Tool association model."""

    __tablename__ = "agent_tools"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_id = Column(
        String(100),
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Configuration
    configuration = Column(JSON, default=dict)  # Tool-specific config for this agent
    order = Column(Integer, default=0)  # Execution order

    # Relationships
    agent = relationship("Agent", back_populates="tools")
    tool = relationship("Tool", back_populates="agent_tools")

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_agent_tools_agent_order", "agent_id", "order"),
        UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool"),
    )

    def __repr__(self):
        return f"<AgentTool(agent_id={self.agent_id}, tool_id={self.tool_id})>"


class AgentTemplate(Base):
    """Agent template model for pre-configured agents."""

    __tablename__ = "agent_templates"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)  # rag, research, analysis, etc.

    # Template Configuration
    configuration = Column(JSON, nullable=False)  # Default agent configuration
    required_tools = Column(JSON, default=list)  # List of required tool IDs

    # Metadata
    use_case_examples = Column(JSON, default=list)  # List of example use cases
    is_published = Column(Boolean, default=False, index=True)
    rating = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("rating >= 0.0 AND rating <= 5.0", name="check_rating_range"),
        CheckConstraint("usage_count >= 0", name="check_usage_count_positive"),
    )

    def __repr__(self):
        return f"<AgentTemplate(id={self.id}, name={self.name}, category={self.category})>"


class PromptTemplate(Base):
    """Prompt template model for reusable prompts."""

    __tablename__ = "prompt_templates"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # NULL for system templates
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_text = Column(Text, nullable=False)

    # Metadata
    variables = Column(JSON, default=list)  # List of variable names
    is_system = Column(Boolean, default=False, index=True)
    category = Column(String(100), index=True)  # react, chain_of_thought, rag, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    versions = relationship("PromptTemplateVersion", back_populates="prompt_template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name={self.name})>"


class PromptTemplateVersion(Base):
    """Prompt template version history model."""

    __tablename__ = "prompt_template_versions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    prompt_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("prompt_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version Information
    version_number = Column(String(50), nullable=False)
    template_text = Column(Text, nullable=False)
    change_description = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    prompt_template = relationship("PromptTemplate", back_populates="versions")

    def __repr__(self):
        return f"<PromptTemplateVersion(id={self.id}, version={self.version_number})>"



# ============================================================================
# BLOCK MODELS
# ============================================================================


class Block(Base):
    """Reusable block model."""

    __tablename__ = "blocks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Block Configuration
    block_type = Column(String(50), nullable=False, index=True)  # llm, tool, logic, composite
    input_schema = Column(JSON, nullable=False)  # JSON Schema for inputs
    output_schema = Column(JSON, nullable=False)  # JSON Schema for outputs
    configuration = Column(JSON, default=dict)  # Block-specific config
    implementation = Column(Text)  # Code or config (for logic blocks)

    # Visibility
    is_public = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    versions = relationship("BlockVersion", back_populates="block", cascade="all, delete-orphan")
    test_cases = relationship("BlockTestCase", back_populates="block", cascade="all, delete-orphan")
    parent_dependencies = relationship(
        "BlockDependency",
        foreign_keys="BlockDependency.parent_block_id",
        back_populates="parent_block",
        cascade="all, delete-orphan"
    )
    child_dependencies = relationship(
        "BlockDependency",
        foreign_keys="BlockDependency.child_block_id",
        back_populates="child_block",
        cascade="all, delete-orphan"
    )

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_blocks_user_type", "user_id", "block_type"),
        Index("ix_blocks_user_public", "user_id", "is_public"),
        UniqueConstraint("user_id", "name", name="uq_block_name_per_user"),
        CheckConstraint(
            "block_type IN ('llm', 'tool', 'logic', 'composite')",
            name="check_block_type_valid",
        ),
    )

    def __repr__(self):
        return f"<Block(id={self.id}, name={self.name}, type={self.block_type})>"


class BlockVersion(Base):
    """Block version history model."""

    __tablename__ = "block_versions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version Information
    version_number = Column(String(50), nullable=False)  # Semantic versioning
    configuration = Column(JSON, nullable=False)  # Snapshot of block config
    implementation = Column(Text)  # Snapshot of implementation
    is_breaking_change = Column(Boolean, default=False)
    change_description = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    block = relationship("Block", back_populates="versions")

    # Indexes
    __table_args__ = (
        Index("ix_block_versions_block_created", "block_id", "created_at"),
    )

    def __repr__(self):
        return f"<BlockVersion(id={self.id}, block_id={self.block_id}, version={self.version_number})>"


class BlockDependency(Base):
    """Block dependency model for composite blocks."""

    __tablename__ = "block_dependencies"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    parent_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Dependency Configuration
    version_constraint = Column(String(100))  # Semantic version constraint (e.g., ">=1.0.0,<2.0.0")

    # Relationships
    parent_block = relationship(
        "Block",
        foreign_keys=[parent_block_id],
        back_populates="parent_dependencies"
    )
    child_block = relationship(
        "Block",
        foreign_keys=[child_block_id],
        back_populates="child_dependencies"
    )

    # Indexes and Constraints
    __table_args__ = (
        UniqueConstraint("parent_block_id", "child_block_id", name="uq_block_dependency"),
    )

    def __repr__(self):
        return f"<BlockDependency(parent={self.parent_block_id}, child={self.child_block_id})>"


class BlockTestCase(Base):
    """Block test case model."""

    __tablename__ = "block_test_cases"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Test Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    input_data = Column(JSON, nullable=False)
    expected_output = Column(JSON, nullable=False)
    assertions = Column(JSON, default=list)  # List of assertion rules

    # Test Results
    last_run_at = Column(DateTime)
    last_run_status = Column(String(50))  # passed, failed, error
    last_run_error = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    block = relationship("Block", back_populates="test_cases")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "last_run_status IS NULL OR last_run_status IN ('passed', 'failed', 'error')",
            name="check_test_status_valid",
        ),
    )

    def __repr__(self):
        return f"<BlockTestCase(id={self.id}, name={self.name}, status={self.last_run_status})>"



# ============================================================================
# WORKFLOW MODELS
# ============================================================================


class Workflow(Base):
    """Workflow model for agent orchestration."""

    __tablename__ = "workflows"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Workflow Configuration
    graph_definition = Column(JSON, nullable=False)  # LangGraph StateGraph definition
    compiled_graph = Column(LargeBinary)  # Pickled compiled graph (cached)

    # Visibility
    is_public = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    blocks = relationship("AgentBlock", back_populates="workflow", cascade="all, delete-orphan")
    agent_edges = relationship("AgentEdge", back_populates="workflow", cascade="all, delete-orphan")
    schedules = relationship("WorkflowSchedule", back_populates="workflow", cascade="all, delete-orphan")
    webhooks = relationship("WorkflowWebhook", back_populates="workflow", cascade="all, delete-orphan")
    subflows = relationship("WorkflowSubflow", back_populates="workflow", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_workflows_user_public", "user_id", "is_public"),
    )

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name})>"


class WorkflowNode(Base):
    """Workflow node model."""

    __tablename__ = "workflow_nodes"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Node Information
    node_type = Column(String(50), nullable=False)  # agent, block, control
    node_ref_id = Column(UUID(as_uuid=True))  # Reference to agent_id or block_id

    # Position (for visual designer)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)

    # Configuration
    configuration = Column(JSON, default=dict)

    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")
    source_edges = relationship(
        "WorkflowEdge",
        foreign_keys="WorkflowEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan"
    )
    target_edges = relationship(
        "WorkflowEdge",
        foreign_keys="WorkflowEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "node_type IN ('agent', 'block', 'control')",
            name="check_node_type_valid",
        ),
    )

    def __repr__(self):
        return f"<WorkflowNode(id={self.id}, type={self.node_type})>"


class WorkflowEdge(Base):
    """Workflow edge model for connections between nodes."""

    __tablename__ = "workflow_edges"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Edge Configuration
    edge_type = Column(String(50), default="normal")  # normal, conditional
    condition = Column(Text)  # Python expression for conditional edges

    # Relationships
    workflow = relationship("Workflow", back_populates="edges")
    source_node = relationship(
        "WorkflowNode",
        foreign_keys=[source_node_id],
        back_populates="source_edges"
    )
    target_node = relationship(
        "WorkflowNode",
        foreign_keys=[target_node_id],
        back_populates="target_edges"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "edge_type IN ('normal', 'conditional')",
            name="check_edge_type_valid",
        ),
    )

    def __repr__(self):
        return f"<WorkflowEdge(id={self.id}, type={self.edge_type})>"


class WorkflowExecution(Base):
    """Workflow execution model."""

    __tablename__ = "workflow_executions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Execution Information
    session_id = Column(String(255), index=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_context = Column(JSON)

    # Status
    status = Column(String(50), nullable=False, index=True)  # running, completed, failed, timeout
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")

    # Constraints
    __table_args__ = (
        Index("ix_workflow_executions_user_status", "user_id", "status"),
        Index("ix_workflow_executions_workflow_started", "workflow_id", "started_at"),
        CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'timeout', 'cancelled')",
            name="check_workflow_execution_status_valid",
        ),
        CheckConstraint("duration_ms >= 0", name="check_workflow_duration_positive"),
    )

    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, status={self.status})>"


class AgentBlock(Base):
    """Agent block model for visual workflow blocks."""

    __tablename__ = "agent_blocks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Block Information
    type = Column(String(50), nullable=False, index=True)  # openai, http, condition, loop, parallel, etc.
    name = Column(String(255), nullable=False)

    # Position (for visual designer)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)

    # Configuration
    config = Column(JSON, nullable=False, default=dict)  # Block-specific configuration
    sub_blocks = Column(JSON, nullable=False, default=dict)  # SubBlock values (inputs, dropdowns, etc.)
    inputs = Column(JSON, nullable=False, default=dict)  # Input schema
    outputs = Column(JSON, nullable=False, default=dict)  # Output schema

    # Status
    enabled = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="blocks")
    source_edges = relationship(
        "AgentEdge",
        foreign_keys="AgentEdge.source_block_id",
        back_populates="source_block",
        cascade="all, delete-orphan"
    )
    target_edges = relationship(
        "AgentEdge",
        foreign_keys="AgentEdge.target_block_id",
        back_populates="target_block",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_agent_blocks_workflow_type", "workflow_id", "type"),
        Index("ix_agent_blocks_workflow_enabled", "workflow_id", "enabled"),
    )

    def __repr__(self):
        return f"<AgentBlock(id={self.id}, type={self.type}, name={self.name})>"


class AgentEdge(Base):
    """Agent edge model for connections between blocks."""

    __tablename__ = "agent_edges"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Edge Configuration
    source_handle = Column(String(50))  # Output handle on source block
    target_handle = Column(String(50))  # Input handle on target block

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="agent_edges")
    source_block = relationship(
        "AgentBlock",
        foreign_keys=[source_block_id],
        back_populates="source_edges"
    )
    target_block = relationship(
        "AgentBlock",
        foreign_keys=[target_block_id],
        back_populates="target_edges"
    )

    # Indexes
    __table_args__ = (
        Index("ix_agent_edges_workflow", "workflow_id"),
        Index("ix_agent_edges_source", "source_block_id"),
        Index("ix_agent_edges_target", "target_block_id"),
    )

    def __repr__(self):
        return f"<AgentEdge(id={self.id}, source={self.source_block_id}, target={self.target_block_id})>"


class WorkflowSchedule(Base):
    """Workflow schedule model for cron-based triggers."""

    __tablename__ = "workflow_schedules"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schedule Configuration
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    input_data = Column(JSON, default=dict)  # Default input for scheduled executions

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Execution Tracking
    last_execution_at = Column(DateTime)
    next_execution_at = Column(DateTime, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="schedules")

    # Indexes
    __table_args__ = (
        Index("ix_workflow_schedules_workflow_active", "workflow_id", "is_active"),
        Index("ix_workflow_schedules_next_execution", "is_active", "next_execution_at"),
    )

    def __repr__(self):
        return f"<WorkflowSchedule(id={self.id}, workflow_id={self.workflow_id}, active={self.is_active})>"


class WorkflowWebhook(Base):
    """Workflow webhook model for webhook-based triggers."""

    __tablename__ = "workflow_webhooks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Webhook Configuration
    webhook_path = Column(String(255), unique=True, nullable=False, index=True)  # Unique URL path
    webhook_secret = Column(String(255))  # For signature verification
    http_method = Column(String(10), default="POST", nullable=False)  # POST, GET, PUT, etc.

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Execution Tracking
    last_triggered_at = Column(DateTime)
    trigger_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="webhooks")

    # Constraints
    __table_args__ = (
        Index("ix_workflow_webhooks_workflow_active", "workflow_id", "is_active"),
        CheckConstraint(
            "http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')",
            name="check_webhook_method_valid",
        ),
        CheckConstraint("trigger_count >= 0", name="check_trigger_count_positive"),
    )

    def __repr__(self):
        return f"<WorkflowWebhook(id={self.id}, path={self.webhook_path}, active={self.is_active})>"


class WorkflowSubflow(Base):
    """Workflow subflow model for loops and parallel execution structures."""

    __tablename__ = "workflow_subflows"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Subflow Configuration
    subflow_type = Column(String(50), nullable=False, index=True)  # loop, parallel
    configuration = Column(JSON, nullable=False, default=dict)  # Type-specific config

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="subflows")

    # Constraints
    __table_args__ = (
        Index("ix_workflow_subflows_workflow_type", "workflow_id", "subflow_type"),
        Index("ix_workflow_subflows_parent_block", "parent_block_id"),
        CheckConstraint(
            "subflow_type IN ('loop', 'parallel')",
            name="check_subflow_type_valid",
        ),
    )

    def __repr__(self):
        return f"<WorkflowSubflow(id={self.id}, type={self.subflow_type}, parent={self.parent_block_id})>"



# ============================================================================
# KNOWLEDGEBASE MODELS
# ============================================================================


class Knowledgebase(Base):
    """Knowledgebase model for agent-specific document collections."""

    __tablename__ = "knowledgebases"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Milvus Configuration
    milvus_collection_name = Column(String(255), unique=True, nullable=False, index=True)
    embedding_model = Column(String(100), nullable=False)

    # Chunking Configuration
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    documents = relationship("KnowledgebaseDocument", back_populates="knowledgebase", cascade="all, delete-orphan")
    versions = relationship("KnowledgebaseVersion", back_populates="knowledgebase", cascade="all, delete-orphan")
    agent_links = relationship("AgentKnowledgebase", back_populates="knowledgebase", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("chunk_size > 0", name="check_chunk_size_positive"),
        CheckConstraint("chunk_overlap >= 0", name="check_chunk_overlap_positive"),
    )

    def __repr__(self):
        return f"<Knowledgebase(id={self.id}, name={self.name})>"


class KnowledgebaseDocument(Base):
    """Association between knowledgebase and documents."""

    __tablename__ = "knowledgebase_documents"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledgebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledgebases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    removed_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    knowledgebase = relationship("Knowledgebase", back_populates="documents")

    # Indexes and Constraints
    __table_args__ = (
        UniqueConstraint("knowledgebase_id", "document_id", name="uq_kb_document"),
    )

    def __repr__(self):
        return f"<KnowledgebaseDocument(kb={self.knowledgebase_id}, doc={self.document_id})>"


class KnowledgebaseVersion(Base):
    """Knowledgebase version history model."""

    __tablename__ = "knowledgebase_versions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    knowledgebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledgebases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version Information
    version_number = Column(Integer, nullable=False)
    document_snapshot = Column(JSON, nullable=False)  # List of document IDs

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    knowledgebase = relationship("Knowledgebase", back_populates="versions")

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_kb_versions_kb_created", "knowledgebase_id", "created_at"),
        CheckConstraint("version_number > 0", name="check_kb_version_positive"),
    )

    def __repr__(self):
        return f"<KnowledgebaseVersion(id={self.id}, version={self.version_number})>"


class AgentKnowledgebase(Base):
    """Association between agents and knowledgebases."""

    __tablename__ = "agent_knowledgebases"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    knowledgebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledgebases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Configuration
    priority = Column(Integer, default=0)  # For ranking multiple KBs

    # Relationships
    agent = relationship("Agent", back_populates="knowledgebases")
    knowledgebase = relationship("Knowledgebase", back_populates="agent_links")

    # Indexes and Constraints
    __table_args__ = (
        UniqueConstraint("agent_id", "knowledgebase_id", name="uq_agent_kb"),
        Index("ix_agent_kb_agent_priority", "agent_id", "priority"),
    )

    def __repr__(self):
        return f"<AgentKnowledgebase(agent={self.agent_id}, kb={self.knowledgebase_id})>"



# ============================================================================
# VARIABLE AND SECRET MODELS
# ============================================================================


class Variable(Base):
    """Variable model for configuration management."""

    __tablename__ = "variables"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    name = Column(String(255), nullable=False, index=True)

    # Scope
    scope = Column(String(50), nullable=False, index=True)  # global, workspace, user, agent
    scope_id = Column(UUID(as_uuid=True), index=True)  # ID of workspace, user, or agent

    # Value
    value_type = Column(String(50), nullable=False)  # string, number, boolean, json
    value = Column(Text)  # Stored as string, parsed based on type

    # Security
    is_secret = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft delete

    # Relationships
    secret = relationship("Secret", back_populates="variable", uselist=False, cascade="all, delete-orphan")

    # Indexes and Constraints
    __table_args__ = (
        UniqueConstraint("name", "scope", "scope_id", name="uq_variable_scope"),
        Index("ix_variables_scope_id", "scope", "scope_id"),
        CheckConstraint(
            "scope IN ('global', 'workspace', 'user', 'agent')",
            name="check_variable_scope_valid",
        ),
        CheckConstraint(
            "value_type IN ('string', 'number', 'boolean', 'json')",
            name="check_variable_type_valid",
        ),
    )

    def __repr__(self):
        return f"<Variable(id={self.id}, name={self.name}, scope={self.scope})>"


class Secret(Base):
    """Secret model for encrypted variable values."""

    __tablename__ = "secrets"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    variable_id = Column(
        UUID(as_uuid=True),
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Encrypted Value
    encrypted_value = Column(Text, nullable=False)  # AES-256 encrypted
    encryption_key_id = Column(String(100))  # Key rotation support

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    variable = relationship("Variable", back_populates="secret")

    def __repr__(self):
        return f"<Secret(id={self.id}, variable_id={self.variable_id})>"



# ============================================================================
# EXECUTION MODELS
# ============================================================================


class AgentExecution(Base):
    """Agent execution model."""

    __tablename__ = "agent_executions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Execution Information
    session_id = Column(String(255), index=True)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_context = Column(JSON)

    # Status
    status = Column(String(50), nullable=False, index=True)  # running, completed, failed, timeout, cancelled
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Relationships
    agent = relationship("Agent", back_populates="executions")
    steps = relationship("ExecutionStep", back_populates="execution", cascade="all, delete-orphan")
    metrics = relationship("ExecutionMetrics", back_populates="execution", uselist=False, cascade="all, delete-orphan")

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_agent_executions_agent_started", "agent_id", "started_at"),
        Index("ix_agent_executions_user_status", "user_id", "status"),
        Index("ix_agent_executions_status_started", "status", "started_at"),
        CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'timeout', 'cancelled')",
            name="check_agent_execution_status_valid",
        ),
        CheckConstraint("duration_ms >= 0", name="check_agent_duration_positive"),
    )

    def __repr__(self):
        return f"<AgentExecution(id={self.id}, agent_id={self.agent_id}, status={self.status})>"


class ExecutionStep(Base):
    """Execution step model for tracking agent execution steps."""

    __tablename__ = "execution_steps"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Step Information
    step_number = Column(Integer, nullable=False)
    step_type = Column(String(50), nullable=False)  # thought, action, observation, response, error
    content = Column(Text)
    step_metadata = Column(JSON, default=dict)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    execution = relationship("AgentExecution", back_populates="steps")

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_execution_steps_execution_number", "execution_id", "step_number"),
        Index("ix_execution_steps_execution_timestamp", "execution_id", "timestamp"),
        CheckConstraint("step_number >= 0", name="check_step_number_positive"),
    )

    def __repr__(self):
        return f"<ExecutionStep(id={self.id}, execution_id={self.execution_id}, step={self.step_number})>"


class ExecutionMetrics(Base):
    """Execution metrics model for performance tracking."""

    __tablename__ = "execution_metrics"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_executions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # LLM Metrics
    llm_call_count = Column(Integer, default=0)
    llm_total_tokens = Column(Integer, default=0)
    llm_prompt_tokens = Column(Integer, default=0)
    llm_completion_tokens = Column(Integer, default=0)

    # Tool Metrics
    tool_call_count = Column(Integer, default=0)
    tool_total_duration_ms = Column(Integer, default=0)

    # Cache Metrics
    cache_hit_count = Column(Integer, default=0)
    cache_miss_count = Column(Integer, default=0)

    # Relationships
    execution = relationship("AgentExecution", back_populates="metrics")

    # Constraints
    __table_args__ = (
        CheckConstraint("llm_call_count >= 0", name="check_llm_call_count_positive"),
        CheckConstraint("llm_total_tokens >= 0", name="check_llm_tokens_positive"),
        CheckConstraint("tool_call_count >= 0", name="check_tool_call_count_positive"),
        CheckConstraint("tool_total_duration_ms >= 0", name="check_tool_duration_positive"),
        CheckConstraint("cache_hit_count >= 0", name="check_cache_hit_positive"),
        CheckConstraint("cache_miss_count >= 0", name="check_cache_miss_positive"),
    )

    def __repr__(self):
        return f"<ExecutionMetrics(id={self.id}, execution_id={self.execution_id})>"


class ExecutionSchedule(Base):
    """Execution schedule model for recurring agent executions."""

    __tablename__ = "execution_schedules"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schedule Configuration
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")
    input_data = Column(JSON)

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Execution Tracking
    last_execution_at = Column(DateTime)
    next_execution_at = Column(DateTime, index=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_execution_schedules_agent_active", "agent_id", "is_active"),
        Index("ix_execution_schedules_next_execution", "is_active", "next_execution_at"),
    )

    def __repr__(self):
        return f"<ExecutionSchedule(id={self.id}, agent_id={self.agent_id}, active={self.is_active})>"



# ============================================================================
# PERMISSION AND AUDIT MODELS
# ============================================================================


class Permission(Base):
    """Permission model for fine-grained access control."""

    __tablename__ = "permissions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    granted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Resource Information
    resource_type = Column(String(50), nullable=False, index=True)  # agent, block, workflow, knowledgebase
    resource_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # read, write, execute, delete, share, admin

    # Timestamp
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes and Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "resource_type", "resource_id", "action", name="uq_permission"),
        Index("ix_permissions_resource", "resource_type", "resource_id"),
        Index("ix_permissions_user_resource", "user_id", "resource_type", "resource_id"),
        CheckConstraint(
            "resource_type IN ('agent', 'block', 'workflow', 'knowledgebase')",
            name="check_permission_resource_type_valid",
        ),
        CheckConstraint(
            "action IN ('read', 'write', 'execute', 'delete', 'share', 'admin')",
            name="check_permission_action_valid",
        ),
    )

    def __repr__(self):
        return f"<Permission(user={self.user_id}, resource={self.resource_type}:{self.resource_id}, action={self.action})>"


class ResourceShare(Base):
    """Resource share model for shareable links."""

    __tablename__ = "resource_shares"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Resource Information
    resource_type = Column(String(50), nullable=False, index=True)  # agent, block, workflow, knowledgebase
    resource_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Share Configuration
    share_token = Column(String(255), unique=True, nullable=False, index=True)
    permissions = Column(JSON, nullable=False)  # List of allowed actions

    # Expiration
    expires_at = Column(DateTime, index=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes and Constraints
    __table_args__ = (
        Index("ix_resource_shares_resource", "resource_type", "resource_id"),
        CheckConstraint(
            "resource_type IN ('agent', 'block', 'workflow', 'knowledgebase')",
            name="check_share_resource_type_valid",
        ),
    )

    def __repr__(self):
        return f"<ResourceShare(id={self.id}, resource={self.resource_type}:{self.resource_id})>"


class AuditLog(Base):
    """Audit log model for tracking user actions."""

    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Action Information
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, execute, etc.
    resource_type = Column(String(50), index=True)  # agent, block, workflow, etc.
    resource_id = Column(UUID(as_uuid=True), index=True)

    # Details
    details = Column(JSON, default=dict)

    # Request Information
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(String(500))

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_action_timestamp", "action", "timestamp"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user_id})>"


# ============================================================================
# MEMORY MANAGEMENT MODELS
# ============================================================================


class AgentMemory(Base):
    """Agent memory storage for STM, LTM, Episodic, and Semantic memory."""
    __tablename__ = "agent_memories"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Memory Type
    type = Column(String(20), nullable=False)  # short_term, long_term, episodic, semantic

    # Content
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, default=dict)

    # Importance and Access
    importance = Column(String(10), default="medium")  # low, medium, high
    access_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime)

    # Indexes
    __table_args__ = (
        Index("ix_agent_memory_type", "agent_id", "type"),
        Index("ix_agent_memory_importance", "agent_id", "importance"),
        Index("ix_agent_memory_created", "agent_id", "created_at"),
        CheckConstraint(
            "type IN ('short_term', 'long_term', 'episodic', 'semantic')",
            name="ck_memory_type"
        ),
        CheckConstraint(
            "importance IN ('low', 'medium', 'high')",
            name="ck_memory_importance"
        ),
    )

    def __repr__(self):
        return f"<AgentMemory(id={self.id}, type={self.type}, agent={self.agent_id})>"


class MemorySettings(Base):
    """Memory management settings for agents."""
    __tablename__ = "memory_settings"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key (one-to-one with Agent)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Retention Settings
    short_term_retention_hours = Column(Integer, default=24)
    auto_cleanup = Column(Boolean, default=True)

    # Consolidation Settings
    auto_consolidation = Column(Boolean, default=True)
    consolidation_threshold = Column(Integer, default=100)

    # Storage Settings
    enable_compression = Column(Boolean, default=True)
    max_memory_size_mb = Column(Integer, default=1000)
    importance_threshold = Column(String(10), default="low")  # low, medium, high

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MemorySettings(agent={self.agent_id})>"


# ============================================================================
# COST MANAGEMENT MODELS
# ============================================================================


class CostRecord(Base):
    """Cost tracking for agent executions."""
    __tablename__ = "cost_records"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    execution_id = Column(UUID(as_uuid=True), index=True)

    # Cost Details
    model = Column(String(50), nullable=False)
    tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)  # Using Float for simplicity

    # Metadata
    meta_data = Column(JSON, default=dict)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index("ix_cost_agent_timestamp", "agent_id", "timestamp"),
        Index("ix_cost_model_timestamp", "model", "timestamp"),
        Index("ix_cost_execution", "execution_id"),
    )

    def __repr__(self):
        return f"<CostRecord(id={self.id}, model={self.model}, cost={self.cost})>"


class BudgetSettings(Base):
    """Budget configuration for cost management."""
    __tablename__ = "budget_settings"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key (one-to-one with Agent, nullable for global settings)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), unique=True)

    # Budget Settings
    monthly_budget = Column(Float, default=1000.0)
    alert_threshold_percentage = Column(Integer, default=80)

    # Alert Settings
    enable_email_alerts = Column(Boolean, default=True)
    enable_auto_stop = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BudgetSettings(agent={self.agent_id}, budget={self.monthly_budget})>"


# ============================================================================
# BRANCH MANAGEMENT MODELS
# ============================================================================


class WorkflowBranch(Base):
    """Git-style branches for workflows."""
    __tablename__ = "workflow_branches"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # Branch Details
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Status
    is_main = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    commit_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Unique Constraint
    __table_args__ = (
        UniqueConstraint("workflow_id", "name", name="uq_workflow_branch_name"),
        Index("ix_workflow_branch_workflow", "workflow_id"),
    )

    def __repr__(self):
        return f"<WorkflowBranch(id={self.id}, name={self.name}, workflow={self.workflow_id})>"


class BranchCommit(Base):
    """Commit history for workflow branches."""
    __tablename__ = "branch_commits"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    branch_id = Column(UUID(as_uuid=True), ForeignKey("workflow_branches.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # Commit Details
    message = Column(Text, nullable=False)
    snapshot = Column(JSON, nullable=False)  # Full workflow state
    changes_count = Column(Integer, default=0)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_branch_commit_branch", "branch_id", "created_at"),
    )

    def __repr__(self):
        return f"<BranchCommit(id={self.id}, branch={self.branch_id})>"


# ============================================================================
# COLLABORATION MODELS
# ============================================================================


class CollaborationSession(Base):
    """Active collaboration sessions for real-time editing."""
    __tablename__ = "collaboration_sessions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Resource Reference
    resource_type = Column(String(20), nullable=False)  # agent, workflow, block
    resource_id = Column(UUID(as_uuid=True), nullable=False)

    # User Reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Session Details
    color = Column(String(7))  # Hex color for user cursor
    cursor_position = Column(JSON)
    selection = Column(JSON)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_collab_resource", "resource_type", "resource_id"),
        Index("ix_collab_user", "user_id"),
        Index("ix_collab_last_seen", "last_seen"),
    )

    def __repr__(self):
        return f"<CollaborationSession(id={self.id}, user={self.user_id}, resource={self.resource_type}:{self.resource_id})>"


class ResourceLock(Base):
    """Resource locks for preventing concurrent edits."""
    __tablename__ = "resource_locks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Resource Reference
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=False)

    # Lock Owner
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Lock Details
    locked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Unique Constraint (one lock per resource)
    __table_args__ = (
        UniqueConstraint("resource_type", "resource_id", name="uq_resource_lock"),
        Index("ix_resource_lock_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<ResourceLock(resource={self.resource_type}:{self.resource_id}, user={self.user_id})>"


# ============================================================================
# API KEY MANAGEMENT
# ============================================================================


class UserAPIKey(Base):
    """User API key storage for external services."""
    __tablename__ = "user_api_keys"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Service Information
    service_name = Column(String(100), nullable=False)  # e.g., "youtube", "openai", "google"
    service_display_name = Column(String(200), nullable=False)  # e.g., "YouTube Data API"
    
    # API Key (encrypted)
    encrypted_api_key = Column(Text, nullable=False)
    
    # Metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_used_at = Column(DateTime)
    
    # Usage Statistics
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "service_name", name="uq_user_service_api_key"),
        Index("ix_user_api_keys_user_service", "user_id", "service_name"),
        Index("ix_user_api_keys_active", "is_active"),
    )

    def __repr__(self):
        return f"<UserAPIKey(user={self.user_id}, service={self.service_name})>"
