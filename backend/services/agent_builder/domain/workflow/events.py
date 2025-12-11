"""
Workflow Domain Events

Events that occur within the Workflow bounded context.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for domain events."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID = field(default=None)
    aggregate_type: str = "Workflow"
    
    @property
    def event_type(self) -> str:
        return self.__class__.__name__


@dataclass
class WorkflowCreated(DomainEvent):
    """Event raised when a workflow is created."""
    user_id: UUID = None
    workflow_name: str = ""
    node_count: int = 0
    edge_count: int = 0
    is_public: bool = False


@dataclass
class WorkflowUpdated(DomainEvent):
    """Event raised when a workflow is updated."""
    user_id: UUID = None
    updated_fields: List[str] = field(default_factory=list)
    nodes_added: int = 0
    nodes_removed: int = 0
    edges_added: int = 0
    edges_removed: int = 0


@dataclass
class WorkflowDeleted(DomainEvent):
    """Event raised when a workflow is deleted."""
    user_id: UUID = None
    workflow_name: str = ""
    deletion_type: str = "soft"


@dataclass
class WorkflowExecutionStarted(DomainEvent):
    """Event raised when workflow execution starts."""
    execution_id: UUID = None
    user_id: UUID = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    trigger_type: str = "manual"  # manual, schedule, webhook, api


@dataclass
class WorkflowExecutionCompleted(DomainEvent):
    """Event raised when workflow execution completes."""
    execution_id: UUID = None
    user_id: UUID = None
    status: str = "completed"  # completed, failed, timeout, cancelled
    output_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    nodes_executed: int = 0
    error_message: Optional[str] = None


@dataclass
class NodeExecutionStarted(DomainEvent):
    """Event raised when a node starts execution."""
    aggregate_type: str = "WorkflowNode"
    execution_id: UUID = None
    node_id: str = ""
    node_type: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeExecutionCompleted(DomainEvent):
    """Event raised when a node completes execution."""
    aggregate_type: str = "WorkflowNode"
    execution_id: UUID = None
    node_id: str = ""
    node_type: str = ""
    status: str = "completed"
    output_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    error_message: Optional[str] = None


@dataclass
class WorkflowValidated(DomainEvent):
    """Event raised when a workflow is validated."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class WorkflowCloned(DomainEvent):
    """Event raised when a workflow is cloned."""
    source_workflow_id: UUID = None
    new_workflow_id: UUID = None
    user_id: UUID = None
    new_workflow_name: str = ""
