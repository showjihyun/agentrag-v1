"""Execution Domain Events"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base domain event."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID = field(default=None)
    aggregate_type: str = "Execution"


@dataclass
class ExecutionStarted(DomainEvent):
    """Event raised when execution starts."""
    workflow_id: UUID = None
    user_id: UUID = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    trigger_type: str = "manual"


@dataclass
class ExecutionCompleted(DomainEvent):
    """Event raised when execution completes."""
    workflow_id: UUID = None
    user_id: UUID = None
    status: str = "completed"
    output_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    nodes_executed: int = 0
    total_tokens: int = 0
    error_message: Optional[str] = None


@dataclass
class StepExecuted(DomainEvent):
    """Event raised when a step is executed."""
    aggregate_type: str = "ExecutionStep"
    execution_id: UUID = None
    step_number: int = 0
    step_type: str = ""
    node_id: Optional[str] = None
    status: str = "completed"
    duration_ms: int = 0
    error_message: Optional[str] = None


@dataclass
class ExecutionPaused(DomainEvent):
    """Event raised when execution is paused."""
    reason: str = ""
    current_node_id: Optional[str] = None


@dataclass
class ExecutionResumed(DomainEvent):
    """Event raised when execution is resumed."""
    resumed_by: UUID = None
    approval_data: Dict[str, Any] = field(default_factory=dict)
