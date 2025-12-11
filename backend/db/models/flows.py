"""Flow models for Agentflow and Chatflow."""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    Float,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.db.database import Base


class FlowType(str, enum.Enum):
    """Flow type enumeration."""
    AGENTFLOW = "agentflow"
    CHATFLOW = "chatflow"


class OrchestrationTypeEnum(str, enum.Enum):
    """Orchestration type for Agentflows."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"


class MemoryTypeEnum(str, enum.Enum):
    """Memory type for Chatflows."""
    BUFFER = "buffer"
    SUMMARY = "summary"
    VECTOR = "vector"
    HYBRID = "hybrid"


class RetrievalStrategyEnum(str, enum.Enum):
    """RAG retrieval strategy."""
    SIMILARITY = "similarity"
    MMR = "mmr"
    HYBRID = "hybrid"


# ============================================================================
# AGENTFLOW MODELS
# ============================================================================


class Agentflow(Base):
    """Agentflow model for multi-agent systems."""

    __tablename__ = "agentflows"

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
    
    # Orchestration Configuration
    orchestration_type = Column(
        String(50),
        nullable=False,
        default="sequential",
    )
    supervisor_config = Column(JSONB, default=dict)
    communication_protocol = Column(String(50), default="direct")  # direct, broadcast, pubsub

    # Graph Definition
    graph_definition = Column(JSONB, nullable=False, default=dict)

    # Metadata
    version = Column(String(50), default="1.0.0")
    tags = Column(JSONB, default=list)
    category = Column(String(100))

    # Visibility & Status
    is_public = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)

    # Statistics
    execution_count = Column(Integer, default=0)
    last_execution_status = Column(String(50))
    last_execution_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    agents = relationship("AgentflowAgent", back_populates="agentflow", cascade="all, delete-orphan")
    executions = relationship("FlowExecution", back_populates="agentflow", cascade="all, delete-orphan",
                             foreign_keys="FlowExecution.agentflow_id")

    __table_args__ = (
        Index("ix_agentflows_user_active", "user_id", "is_active"),
        Index("ix_agentflows_user_created", "user_id", "created_at"),
        CheckConstraint(
            "orchestration_type IN ('sequential', 'parallel', 'hierarchical', 'adaptive')",
            name="check_orchestration_type_valid",
        ),
    )

    def __repr__(self):
        return f"<Agentflow(id={self.id}, name={self.name}, type={self.orchestration_type})>"


class AgentflowAgent(Base):
    """Agent configuration within an Agentflow."""

    __tablename__ = "agentflow_agents"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    agentflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agentflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Agent Configuration
    name = Column(String(255), nullable=False)
    role = Column(String(255))
    description = Column(Text)
    capabilities = Column(JSONB, default=list)
    
    # Execution Settings
    priority = Column(Integer, default=1)
    max_retries = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=60)
    dependencies = Column(JSONB, default=list)  # List of agent IDs this depends on

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agentflow = relationship("Agentflow", back_populates="agents")

    __table_args__ = (
        Index("ix_agentflow_agents_flow_priority", "agentflow_id", "priority"),
    )

    def __repr__(self):
        return f"<AgentflowAgent(id={self.id}, name={self.name}, role={self.role})>"


# ============================================================================
# CHATFLOW MODELS
# ============================================================================


class Chatflow(Base):
    """Chatflow model for chat assistants."""

    __tablename__ = "chatflows"

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

    # Chat Configuration
    chat_config = Column(JSONB, nullable=False, default=dict)
    # Expected structure:
    # {
    #   "llm_provider": "ollama",
    #   "llm_model": "llama3.1",
    #   "system_prompt": "...",
    #   "temperature": 0.7,
    #   "max_tokens": 2048,
    #   "streaming": true,
    #   "welcome_message": "...",
    #   "suggested_questions": []
    # }

    # Memory Configuration
    memory_config = Column(JSONB, default=dict)
    # Expected structure:
    # {
    #   "type": "buffer",
    #   "max_messages": 20,
    #   "summary_threshold": null,
    #   "vector_store_id": null
    # }

    # RAG Configuration
    rag_config = Column(JSONB, default=dict)
    # Expected structure:
    # {
    #   "enabled": false,
    #   "knowledgebase_ids": [],
    #   "retrieval_strategy": "hybrid",
    #   "top_k": 5,
    #   "score_threshold": 0.7,
    #   "reranking_enabled": true,
    #   "reranking_model": null
    # }

    # Graph Definition (for visual builder)
    graph_definition = Column(JSONB, nullable=False, default=dict)

    # Metadata
    version = Column(String(50), default="1.0.0")
    tags = Column(JSONB, default=list)
    category = Column(String(100))

    # Visibility & Status
    is_public = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)

    # Statistics
    execution_count = Column(Integer, default=0)
    last_execution_status = Column(String(50))
    last_execution_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    tools = relationship("ChatflowTool", back_populates="chatflow", cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="chatflow", cascade="all, delete-orphan")
    executions = relationship("FlowExecution", back_populates="chatflow", cascade="all, delete-orphan",
                             foreign_keys="FlowExecution.chatflow_id")

    __table_args__ = (
        Index("ix_chatflows_user_active", "user_id", "is_active"),
        Index("ix_chatflows_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<Chatflow(id={self.id}, name={self.name})>"


class ChatflowTool(Base):
    """Tool configuration within a Chatflow."""

    __tablename__ = "chatflow_tools"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    chatflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_id = Column(
        String(100),
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Tool Configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    configuration = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    chatflow = relationship("Chatflow", back_populates="tools")

    __table_args__ = (
        UniqueConstraint("chatflow_id", "tool_id", name="uq_chatflow_tool"),
    )

    def __repr__(self):
        return f"<ChatflowTool(chatflow_id={self.chatflow_id}, tool_id={self.tool_id})>"


class ChatSession(Base):
    """Chat session for Chatflow conversations."""

    __tablename__ = "chat_sessions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    chatflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Session Information
    session_token = Column(String(255), unique=True, index=True)
    title = Column(String(255))
    
    # Memory State
    memory_state = Column(JSONB, default=dict)
    message_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime)

    # Relationships
    chatflow = relationship("Chatflow", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_sessions_chatflow_updated", "chatflow_id", "updated_at"),
    )

    def __repr__(self):
        return f"<ChatSession(id={self.id}, chatflow_id={self.chatflow_id})>"


class ChatMessage(Base):
    """Chat message within a session."""

    __tablename__ = "chat_messages"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message Content
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    
    # Message Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word conflict)
    message_metadata = Column(JSONB, default=dict)
    # Can include: tool_calls, tool_results, sources, tokens_used, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
        CheckConstraint(
            "role IN ('user', 'assistant', 'system', 'tool')",
            name="check_message_role_valid",
        ),
    )

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role})>"


# ============================================================================
# FLOW EXECUTION MODELS
# ============================================================================


class FlowExecution(Base):
    """Unified execution model for both Agentflows and Chatflows."""

    __tablename__ = "flow_executions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys (one of these will be set)
    agentflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agentflows.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    chatflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatflows.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Execution Type
    flow_type = Column(String(50), nullable=False)  # agentflow, chatflow
    flow_name = Column(String(255))

    # Execution Data
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    
    # Status
    status = Column(String(50), nullable=False, default="pending", index=True)
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Metrics
    metrics = Column(JSONB, default=dict)
    # Expected structure:
    # {
    #   "total_nodes": 0,
    #   "completed_nodes": 0,
    #   "failed_nodes": 0,
    #   "skipped_nodes": 0,
    #   "llm_calls": 0,
    #   "llm_tokens": 0,
    #   "tool_calls": 0,
    #   "estimated_cost": 0
    # }

    # Relationships
    agentflow = relationship("Agentflow", back_populates="executions", foreign_keys=[agentflow_id])
    chatflow = relationship("Chatflow", back_populates="executions", foreign_keys=[chatflow_id])
    node_executions = relationship("NodeExecution", back_populates="flow_execution", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="flow_execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_flow_executions_user_status", "user_id", "status"),
        Index("ix_flow_executions_started", "started_at"),
        CheckConstraint(
            "flow_type IN ('agentflow', 'chatflow')",
            name="check_flow_type_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="check_flow_execution_status_valid",
        ),
    )

    def __repr__(self):
        return f"<FlowExecution(id={self.id}, type={self.flow_type}, status={self.status})>"


class NodeExecution(Base):
    """Individual node execution within a flow."""

    __tablename__ = "node_executions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    flow_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("flow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Node Information
    node_id = Column(String(255), nullable=False)
    node_type = Column(String(100), nullable=False)
    node_label = Column(String(255))

    # Execution Data
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    
    # Status
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Relationships
    flow_execution = relationship("FlowExecution", back_populates="node_executions")

    __table_args__ = (
        Index("ix_node_executions_flow_status", "flow_execution_id", "status"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
            name="check_node_execution_status_valid",
        ),
    )

    def __repr__(self):
        return f"<NodeExecution(id={self.id}, node_id={self.node_id}, status={self.status})>"


class ExecutionLog(Base):
    """Execution log entries."""

    __tablename__ = "execution_logs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    flow_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("flow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Log Information
    level = Column(String(20), nullable=False, default="info")  # debug, info, warn, error
    message = Column(Text, nullable=False)
    log_metadata = Column(JSONB, default=dict)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    flow_execution = relationship("FlowExecution", back_populates="logs")

    __table_args__ = (
        Index("ix_execution_logs_flow_timestamp", "flow_execution_id", "timestamp"),
        CheckConstraint(
            "level IN ('debug', 'info', 'warn', 'error')",
            name="check_log_level_valid",
        ),
    )

    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, level={self.level})>"


# ============================================================================
# API KEY MODELS
# ============================================================================
# NOTE: APIKey model is defined in backend/db/models/api_keys.py
# Import it from there if needed: from backend.db.models.api_keys import APIKey


# ============================================================================
# MARKETPLACE MODELS
# ============================================================================


class MarketplaceItem(Base):
    """Marketplace item for sharing flows and tools."""

    __tablename__ = "marketplace_items"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Item Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    item_type = Column(String(50), nullable=False)  # agentflow, chatflow, workflow, tool, template
    
    # Reference to actual item
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    reference_type = Column(String(50), nullable=False)

    # Metadata
    category = Column(String(100), index=True)
    tags = Column(JSONB, default=list)
    preview_image = Column(String(500))

    # Ratings & Stats
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    install_count = Column(Integer, default=0)

    # Status
    is_featured = Column(Boolean, default=False, index=True)
    is_official = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True, index=True)
    price = Column(String(20), default="free")  # free, premium

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_marketplace_items_type_category", "item_type", "category"),
        Index("ix_marketplace_items_featured", "is_featured", "is_published"),
        CheckConstraint(
            "item_type IN ('agentflow', 'chatflow', 'workflow', 'tool', 'template')",
            name="check_marketplace_item_type_valid",
        ),
        CheckConstraint("rating >= 0.0 AND rating <= 5.0", name="check_marketplace_rating_range"),
    )

    def __repr__(self):
        return f"<MarketplaceItem(id={self.id}, name={self.name}, type={self.item_type})>"


# ============================================================================
# FLOW TEMPLATE MODELS
# ============================================================================


class FlowTemplate(Base):
    """Flow template for pre-configured flows."""

    __tablename__ = "flow_templates"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys (optional - for user-created templates)
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    flow_type = Column(String(50), nullable=False)  # agentflow, chatflow
    category = Column(String(100), index=True)
    icon = Column(String(50))  # Emoji or icon name

    # Template Configuration
    configuration = Column(JSONB, nullable=False)
    # For agentflow: orchestration_type, supervisor_config, graph_definition
    # For chatflow: chat_config, memory_config, rag_config, graph_definition

    # Metadata
    tags = Column(JSONB, default=list)
    use_case_examples = Column(JSONB, default=list)
    requirements = Column(JSONB, default=list)  # Required tools, knowledgebases, etc.

    # Status
    is_system = Column(Boolean, default=False, index=True)  # System-provided templates
    is_published = Column(Boolean, default=True, index=True)
    
    # Statistics
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_flow_templates_type_category", "flow_type", "category"),
        Index("ix_flow_templates_system_published", "is_system", "is_published"),
        CheckConstraint(
            "flow_type IN ('agentflow', 'chatflow')",
            name="check_flow_template_type_valid",
        ),
        CheckConstraint("rating >= 0.0 AND rating <= 5.0", name="check_flow_template_rating_range"),
    )

    def __repr__(self):
        return f"<FlowTemplate(id={self.id}, name={self.name}, type={self.flow_type})>"


# ============================================================================
# TOKEN USAGE & COST TRACKING MODELS
# ============================================================================


class TokenUsage(Base):
    """Token usage tracking for LLM calls."""

    __tablename__ = "token_usages"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flow_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("flow_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Context
    workflow_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    node_id = Column(String(255))
    node_type = Column(String(100))

    # Model Information
    provider = Column(String(100), nullable=False)  # openai, anthropic, ollama, etc.
    model = Column(String(100), nullable=False)

    # Token Counts
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)

    # Cost
    cost_usd = Column(Float, nullable=False, default=0.0)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_token_usages_user_created", "user_id", "created_at"),
        Index("ix_token_usages_user_model", "user_id", "model"),
        Index("ix_token_usages_workflow", "workflow_id", "created_at"),
    )

    def __repr__(self):
        return f"<TokenUsage(id={self.id}, model={self.model}, tokens={self.total_tokens})>"


class ModelPricing(Base):
    """Model pricing configuration."""

    __tablename__ = "model_pricings"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Model Information
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)

    # Pricing (per 1K tokens)
    input_price_per_1k = Column(Float, nullable=False, default=0.0)
    output_price_per_1k = Column(Float, nullable=False, default=0.0)

    # Metadata
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "model", name="uq_model_pricing"),
        Index("ix_model_pricings_provider_model", "provider", "model"),
    )

    def __repr__(self):
        return f"<ModelPricing(provider={self.provider}, model={self.model})>"


# ============================================================================
# EMBED CONFIGURATION MODELS
# ============================================================================


class EmbedConfig(Base):
    """Embed widget configuration for Chatflows."""

    __tablename__ = "embed_configs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    chatflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Embed Settings
    embed_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Appearance
    theme = Column(String(50), default="light")  # light, dark, auto
    primary_color = Column(String(20), default="#6366f1")
    position = Column(String(50), default="bottom-right")  # bottom-right, bottom-left, etc.
    
    # Widget Configuration
    widget_title = Column(String(255))
    welcome_message = Column(Text)
    placeholder_text = Column(String(255), default="메시지를 입력하세요...")
    
    # Branding
    show_branding = Column(Boolean, default=True)
    custom_css = Column(Text)
    
    # Access Control
    allowed_domains = Column(JSONB, default=list)  # Empty = allow all
    rate_limit_per_ip = Column(Integer, default=100)  # Requests per hour
    
    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_embed_configs_chatflow_active", "chatflow_id", "is_active"),
        Index("ix_embed_configs_token", "embed_token"),
    )

    def __repr__(self):
        return f"<EmbedConfig(id={self.id}, chatflow_id={self.chatflow_id})>"


class MarketplaceReview(Base):
    """Reviews for marketplace items."""

    __tablename__ = "marketplace_reviews"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("marketplace_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Review Content
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("item_id", "user_id", name="uq_marketplace_review_user"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_review_rating_range"),
        Index("ix_marketplace_reviews_item_created", "item_id", "created_at"),
    )

    def __repr__(self):
        return f"<MarketplaceReview(id={self.id}, item_id={self.item_id}, rating={self.rating})>"
