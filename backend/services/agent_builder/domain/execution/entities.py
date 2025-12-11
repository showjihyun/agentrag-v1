"""
Execution Domain Entities
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .value_objects import ExecutionStatus, StepType, ExecutionResult, ExecutionMetrics, TokenUsage


@dataclass
class ExecutionStepEntity:
    """Execution step entity."""
    id: UUID
    execution_id: UUID
    step_number: int
    step_type: StepType
    node_id: Optional[str] = None
    content: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: ExecutionStatus = ExecutionStatus.COMPLETED
    duration_ms: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "execution_id": str(self.execution_id),
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "node_id": self.node_id,
            "content": self.content,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ExecutionEntity:
    """Execution domain entity."""
    id: UUID
    workflow_id: UUID
    user_id: UUID
    status: ExecutionStatus = ExecutionStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    steps: List[ExecutionStepEntity] = field(default_factory=list)
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    token_usage: List[TokenUsage] = field(default_factory=list)
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    current_node_id: Optional[str] = None
    parent_execution_id: Optional[UUID] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def duration_ms(self) -> int:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return 0
    
    @property
    def is_running(self) -> bool:
        return self.status == ExecutionStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        return self.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, 
                               ExecutionStatus.TIMEOUT, ExecutionStatus.CANCELLED)
    
    @property
    def is_successful(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def total_tokens(self) -> int:
        return sum(t.total_tokens for t in self.token_usage)
    
    @property
    def total_cost_usd(self) -> float:
        return sum(t.cost_usd for t in self.token_usage)
    
    def start(self) -> None:
        """Start the execution."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, output: Dict[str, Any]) -> None:
        """Complete the execution successfully."""
        self.status = ExecutionStatus.COMPLETED
        self.output_data = output
        self.completed_at = datetime.utcnow()
    
    def fail(self, error_message: str, error_code: Optional[str] = None) -> None:
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        self.error_code = error_code
        self.completed_at = datetime.utcnow()
    
    def timeout(self) -> None:
        """Mark execution as timed out."""
        self.status = ExecutionStatus.TIMEOUT
        self.error_message = "Execution timed out"
        self.completed_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel the execution."""
        self.status = ExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def pause(self) -> None:
        """Pause the execution (e.g., waiting for approval)."""
        self.status = ExecutionStatus.PAUSED
    
    def add_step(self, step: ExecutionStepEntity) -> None:
        """Add an execution step."""
        self.steps.append(step)
    
    def add_token_usage(self, usage: TokenUsage) -> None:
        """Add token usage record."""
        self.token_usage.append(usage)
    
    def update_metrics(self, **kwargs) -> None:
        """Update execution metrics."""
        current = self.metrics.to_dict()
        current.update(kwargs)
        self.metrics = ExecutionMetrics(**current)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id),
            "user_id": str(self.user_id),
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "execution_context": self.execution_context,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "current_node_id": self.current_node_id,
            "duration_ms": self.duration_ms,
            "metrics": self.metrics.to_dict(),
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
        }
