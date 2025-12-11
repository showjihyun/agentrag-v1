"""Execution Aggregate Root"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .entities import ExecutionEntity, ExecutionStepEntity
from .value_objects import ExecutionStatus, StepType, TokenUsage, ExecutionMetrics
from .events import DomainEvent, ExecutionStarted, ExecutionCompleted, StepExecuted


class ExecutionAggregate:
    """
    Execution Aggregate Root.
    
    Manages workflow execution lifecycle and step tracking.
    """
    
    def __init__(self, execution: ExecutionEntity):
        self._execution = execution
        self._events: List[DomainEvent] = []
        self._step_counter = len(execution.steps)
    
    @property
    def id(self) -> UUID:
        return self._execution.id
    
    @property
    def execution(self) -> ExecutionEntity:
        return self._execution
    
    @property
    def events(self) -> List[DomainEvent]:
        return self._events.copy()
    
    def clear_events(self) -> None:
        self._events.clear()
    
    # ========================================================================
    # FACTORY
    # ========================================================================
    
    @classmethod
    def create(
        cls,
        workflow_id: UUID,
        user_id: UUID,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
        parent_execution_id: Optional[UUID] = None,
        trigger_type: str = "manual",
    ) -> "ExecutionAggregate":
        """Create a new execution."""
        execution = ExecutionEntity(
            id=uuid4(),
            workflow_id=workflow_id,
            user_id=user_id,
            input_data=input_data,
            session_id=session_id,
            parent_execution_id=parent_execution_id,
            trace_id=str(uuid4()),
        )
        
        aggregate = cls(execution)
        
        aggregate._events.append(ExecutionStarted(
            aggregate_id=execution.id,
            workflow_id=workflow_id,
            user_id=user_id,
            input_data=input_data,
            trigger_type=trigger_type,
        ))
        
        return aggregate
    
    # ========================================================================
    # COMMANDS
    # ========================================================================
    
    def start(self) -> None:
        """Start the execution."""
        self._execution.start()
    
    def complete(self, output: Dict[str, Any]) -> None:
        """Complete the execution successfully."""
        self._execution.complete(output)
        
        self._events.append(ExecutionCompleted(
            aggregate_id=self._execution.id,
            workflow_id=self._execution.workflow_id,
            user_id=self._execution.user_id,
            status="completed",
            output_data=output,
            duration_ms=self._execution.duration_ms,
            nodes_executed=self._execution.metrics.nodes_executed,
            total_tokens=self._execution.total_tokens,
        ))
    
    def fail(self, error_message: str, error_code: Optional[str] = None) -> None:
        """Mark execution as failed."""
        self._execution.fail(error_message, error_code)
        
        self._events.append(ExecutionCompleted(
            aggregate_id=self._execution.id,
            workflow_id=self._execution.workflow_id,
            user_id=self._execution.user_id,
            status="failed",
            duration_ms=self._execution.duration_ms,
            error_message=error_message,
        ))
    
    def timeout(self) -> None:
        """Mark execution as timed out."""
        self._execution.timeout()
        
        self._events.append(ExecutionCompleted(
            aggregate_id=self._execution.id,
            workflow_id=self._execution.workflow_id,
            user_id=self._execution.user_id,
            status="timeout",
            duration_ms=self._execution.duration_ms,
            error_message="Execution timed out",
        ))
    
    def cancel(self) -> None:
        """Cancel the execution."""
        self._execution.cancel()
        
        self._events.append(ExecutionCompleted(
            aggregate_id=self._execution.id,
            workflow_id=self._execution.workflow_id,
            user_id=self._execution.user_id,
            status="cancelled",
            duration_ms=self._execution.duration_ms,
        ))
    
    def pause(self, reason: str = "") -> None:
        """Pause the execution."""
        self._execution.pause()
    
    def resume(self) -> None:
        """Resume the execution."""
        self._execution.status = ExecutionStatus.RUNNING
    
    # ========================================================================
    # STEP MANAGEMENT
    # ========================================================================
    
    def add_step(
        self,
        step_type: StepType,
        node_id: Optional[str] = None,
        content: str = "",
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        status: ExecutionStatus = ExecutionStatus.COMPLETED,
        duration_ms: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStepEntity:
        """Add an execution step."""
        self._step_counter += 1
        
        step = ExecutionStepEntity(
            id=uuid4(),
            execution_id=self._execution.id,
            step_number=self._step_counter,
            step_type=step_type,
            node_id=node_id,
            content=content,
            input_data=input_data or {},
            output_data=output_data or {},
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            metadata=metadata or {},
        )
        
        self._execution.add_step(step)
        self._execution.current_node_id = node_id
        
        self._events.append(StepExecuted(
            aggregate_id=step.id,
            execution_id=self._execution.id,
            step_number=self._step_counter,
            step_type=step_type.value,
            node_id=node_id,
            status=status.value,
            duration_ms=duration_ms,
            error_message=error_message,
        ))
        
        return step
    
    def record_node_start(self, node_id: str, node_type: str, input_data: Dict[str, Any]) -> ExecutionStepEntity:
        """Record node execution start."""
        return self.add_step(
            step_type=StepType.NODE_START,
            node_id=node_id,
            content=f"Starting node: {node_type}",
            input_data=input_data,
            status=ExecutionStatus.RUNNING,
        )
    
    def record_node_complete(
        self,
        node_id: str,
        output_data: Dict[str, Any],
        duration_ms: int,
    ) -> ExecutionStepEntity:
        """Record node execution completion."""
        # Update metrics
        current_metrics = self._execution.metrics.to_dict()
        current_metrics["nodes_executed"] = current_metrics.get("nodes_executed", 0) + 1
        self._execution.metrics = ExecutionMetrics(**current_metrics)
        
        return self.add_step(
            step_type=StepType.NODE_COMPLETE,
            node_id=node_id,
            content="Node completed",
            output_data=output_data,
            duration_ms=duration_ms,
        )
    
    def record_node_error(
        self,
        node_id: str,
        error_message: str,
        duration_ms: int,
    ) -> ExecutionStepEntity:
        """Record node execution error."""
        return self.add_step(
            step_type=StepType.NODE_ERROR,
            node_id=node_id,
            content=f"Node error: {error_message}",
            status=ExecutionStatus.FAILED,
            duration_ms=duration_ms,
            error_message=error_message,
        )
    
    def record_llm_call(
        self,
        node_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        provider: str,
        cost_usd: float = 0.0,
    ) -> None:
        """Record LLM call and token usage."""
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
            provider=provider,
            cost_usd=cost_usd,
        )
        self._execution.add_token_usage(usage)
        
        # Update metrics
        current_metrics = self._execution.metrics.to_dict()
        current_metrics["llm_call_count"] = current_metrics.get("llm_call_count", 0) + 1
        current_metrics["llm_total_tokens"] = current_metrics.get("llm_total_tokens", 0) + usage.total_tokens
        self._execution.metrics = ExecutionMetrics(**current_metrics)
        
        self.add_step(
            step_type=StepType.LLM_CALL,
            node_id=node_id,
            content=f"LLM call: {model}",
            metadata=usage.to_dict(),
        )
    
    def record_tool_call(
        self,
        node_id: str,
        tool_name: str,
        duration_ms: int,
        success: bool = True,
    ) -> None:
        """Record tool call."""
        # Update metrics
        current_metrics = self._execution.metrics.to_dict()
        current_metrics["tool_call_count"] = current_metrics.get("tool_call_count", 0) + 1
        current_metrics["tool_total_duration_ms"] = current_metrics.get("tool_total_duration_ms", 0) + duration_ms
        self._execution.metrics = ExecutionMetrics(**current_metrics)
        
        self.add_step(
            step_type=StepType.TOOL_CALL,
            node_id=node_id,
            content=f"Tool call: {tool_name}",
            status=ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED,
            duration_ms=duration_ms,
        )
