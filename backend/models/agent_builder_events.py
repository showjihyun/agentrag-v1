"""Agent Builder Event Definitions for Event Sourcing."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from backend.models.events import DomainEvent


# ============================================================================
# AGENT EVENTS
# ============================================================================

class AgentCreatedEvent(DomainEvent):
    """Event emitted when an agent is created."""
    
    event_type: str = "agent.created"
    agent_id: str
    user_id: str
    agent_name: str
    agent_type: str
    llm_provider: str
    llm_model: str
    tool_ids: List[str] = Field(default_factory=list)
    knowledgebase_ids: List[str] = Field(default_factory=list)
    is_public: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdatedEvent(DomainEvent):
    """Event emitted when an agent is updated."""
    
    event_type: str = "agent.updated"
    agent_id: str
    user_id: str
    updated_fields: List[str]
    previous_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    significant_change: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentDeletedEvent(DomainEvent):
    """Event emitted when an agent is deleted."""
    
    event_type: str = "agent.deleted"
    agent_id: str
    user_id: str
    agent_name: str
    deletion_type: str = "soft"  # soft or hard
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentClonedEvent(DomainEvent):
    """Event emitted when an agent is cloned."""
    
    event_type: str = "agent.cloned"
    source_agent_id: str
    new_agent_id: str
    user_id: str
    new_agent_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionStartedEvent(DomainEvent):
    """Event emitted when agent execution starts."""
    
    event_type: str = "agent.execution.started"
    execution_id: str
    agent_id: str
    user_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionCompletedEvent(DomainEvent):
    """Event emitted when agent execution completes."""
    
    event_type: str = "agent.execution.completed"
    execution_id: str
    agent_id: str
    user_id: str
    status: str  # completed, failed, timeout
    duration_ms: int
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# WORKFLOW EVENTS
# ============================================================================

class WorkflowCreatedEvent(DomainEvent):
    """Event emitted when a workflow is created."""
    
    event_type: str = "workflow.created"
    workflow_id: str
    user_id: str
    workflow_name: str
    node_count: int
    edge_count: int
    entry_point: str
    is_public: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowUpdatedEvent(DomainEvent):
    """Event emitted when a workflow is updated."""
    
    event_type: str = "workflow.updated"
    workflow_id: str
    user_id: str
    updated_fields: List[str]
    structure_changed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDeletedEvent(DomainEvent):
    """Event emitted when a workflow is deleted."""
    
    event_type: str = "workflow.deleted"
    workflow_id: str
    user_id: str
    workflow_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionStartedEvent(DomainEvent):
    """Event emitted when workflow execution starts."""
    
    event_type: str = "workflow.execution.started"
    execution_id: str
    workflow_id: str
    user_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionCompletedEvent(DomainEvent):
    """Event emitted when workflow execution completes."""
    
    event_type: str = "workflow.execution.completed"
    execution_id: str
    workflow_id: str
    user_id: str
    status: str  # completed, failed, timeout
    duration_ms: int
    steps_executed: int
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowValidationFailedEvent(DomainEvent):
    """Event emitted when workflow validation fails."""
    
    event_type: str = "workflow.validation.failed"
    workflow_id: Optional[str] = None
    user_id: str
    errors: List[str]
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# BLOCK EVENTS
# ============================================================================

class BlockCreatedEvent(DomainEvent):
    """Event emitted when a block is created."""
    
    event_type: str = "block.created"
    block_id: str
    user_id: str
    block_name: str
    block_type: str  # llm, tool, logic, composite
    is_public: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlockUpdatedEvent(DomainEvent):
    """Event emitted when a block is updated."""
    
    event_type: str = "block.updated"
    block_id: str
    user_id: str
    updated_fields: List[str]
    is_breaking_change: bool = False
    new_version: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlockDeletedEvent(DomainEvent):
    """Event emitted when a block is deleted."""
    
    event_type: str = "block.deleted"
    block_id: str
    user_id: str
    block_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlockTestedEvent(DomainEvent):
    """Event emitted when a block is tested."""
    
    event_type: str = "block.tested"
    block_id: str
    user_id: str
    test_case_id: Optional[str] = None
    success: bool
    duration_ms: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlockVersionCreatedEvent(DomainEvent):
    """Event emitted when a new block version is created."""
    
    event_type: str = "block.version.created"
    block_id: str
    version_id: str
    version_number: str
    is_breaking_change: bool
    change_description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# TOOL EVENTS
# ============================================================================

class ToolAttachedEvent(DomainEvent):
    """Event emitted when a tool is attached to an agent."""
    
    event_type: str = "tool.attached"
    agent_id: str
    tool_id: str
    user_id: str
    order: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolDetachedEvent(DomainEvent):
    """Event emitted when a tool is detached from an agent."""
    
    event_type: str = "tool.detached"
    agent_id: str
    tool_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# KNOWLEDGEBASE EVENTS
# ============================================================================

class KnowledgebaseAttachedEvent(DomainEvent):
    """Event emitted when a knowledgebase is attached to an agent."""
    
    event_type: str = "knowledgebase.attached"
    agent_id: str
    knowledgebase_id: str
    user_id: str
    priority: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgebaseDetachedEvent(DomainEvent):
    """Event emitted when a knowledgebase is detached from an agent."""
    
    event_type: str = "knowledgebase.detached"
    agent_id: str
    knowledgebase_id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# PERMISSION EVENTS
# ============================================================================

class PermissionGrantedEvent(DomainEvent):
    """Event emitted when permission is granted."""
    
    event_type: str = "permission.granted"
    resource_type: str  # agent, workflow, block
    resource_id: str
    user_id: str
    granted_to_user_id: str
    action: str  # read, write, execute, delete
    granted_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PermissionRevokedEvent(DomainEvent):
    """Event emitted when permission is revoked."""
    
    event_type: str = "permission.revoked"
    resource_type: str
    resource_id: str
    user_id: str
    revoked_from_user_id: str
    action: str
    revoked_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# QUOTA EVENTS
# ============================================================================

class QuotaExceededEvent(DomainEvent):
    """Event emitted when quota is exceeded."""
    
    event_type: str = "quota.exceeded"
    user_id: str
    resource_type: str  # agents, workflows, blocks, executions
    current_count: int
    limit: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QuotaWarningEvent(DomainEvent):
    """Event emitted when quota threshold is reached."""
    
    event_type: str = "quota.warning"
    user_id: str
    resource_type: str
    current_count: int
    limit: int
    threshold_percentage: int  # e.g., 80, 90
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# ERROR EVENTS
# ============================================================================

class ValidationErrorEvent(DomainEvent):
    """Event emitted when validation fails."""
    
    event_type: str = "validation.error"
    resource_type: str
    resource_id: Optional[str] = None
    user_id: str
    errors: List[str]
    input_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionErrorEvent(DomainEvent):
    """Event emitted when execution fails."""
    
    event_type: str = "execution.error"
    resource_type: str  # agent, workflow, block
    resource_id: str
    execution_id: str
    user_id: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
