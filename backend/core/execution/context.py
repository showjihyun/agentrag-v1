"""Execution context for workflow execution.

This module provides the ExecutionContext dataclass that maintains state
during workflow execution, including block outputs, variables, and logs.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class BlockState:
    """State of a block during execution."""
    
    block_id: str
    block_type: str
    executed: bool = False
    success: bool = False
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "executed": self.executed,
            "success": self.success,
            "outputs": self.outputs,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
        }


@dataclass
class BlockLog:
    """Log entry for a block execution."""
    
    block_id: str
    block_type: str
    block_name: str
    timestamp: datetime
    success: bool
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_type: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "block_name": self.block_name,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "error_type": self.error_type,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class ParallelExecution:
    """State for parallel execution."""
    
    block_id: str
    parallel_count: int
    completed_count: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ExecutionContext:
    """
    Context for workflow execution.
    
    Maintains state during workflow execution including block outputs,
    variables, execution logs, and control flow state.
    """
    
    # Identifiers
    workflow_id: str
    execution_id: str
    user_id: str
    
    # Trigger information
    trigger: str = "manual"  # manual, webhook, schedule, api, chat
    
    # Block execution state
    block_states: Dict[str, BlockState] = field(default_factory=dict)
    block_logs: List[BlockLog] = field(default_factory=list)
    
    # Variables
    environment_variables: Dict[str, Any] = field(default_factory=dict)
    workflow_variables: Dict[str, Any] = field(default_factory=dict)
    
    # Control flow state
    loop_iterations: Dict[str, int] = field(default_factory=dict)
    parallel_executions: Dict[str, ParallelExecution] = field(default_factory=dict)
    decisions: Dict[str, str] = field(default_factory=dict)  # For routing/branching
    
    # Execution metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, timeout
    error_message: Optional[str] = None
    
    # Cost tracking
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost: float = 0.0
    
    # File tracking
    files: Dict[str, Any] = field(default_factory=dict)
    
    def get_block_output(self, block_id: str, output_key: Optional[str] = None) -> Any:
        """
        Get output from a previously executed block.
        
        Args:
            block_id: Block identifier
            output_key: Specific output key (optional, returns all outputs if None)
            
        Returns:
            Block output value or dict of all outputs
        """
        if block_id not in self.block_states:
            logger.warning(f"Block {block_id} not found in execution context")
            return None
        
        block_state = self.block_states[block_id]
        
        if not block_state.executed:
            logger.warning(f"Block {block_id} has not been executed yet")
            return None
        
        if output_key:
            return block_state.outputs.get(output_key)
        
        return block_state.outputs
    
    def set_block_output(self, block_id: str, outputs: Dict[str, Any]):
        """
        Set output for a block.
        
        Args:
            block_id: Block identifier
            outputs: Output dictionary
        """
        if block_id in self.block_states:
            self.block_states[block_id].outputs = outputs
            self.block_states[block_id].executed = True
            self.block_states[block_id].success = True
        else:
            logger.warning(f"Block {block_id} not found in execution context")
    
    def resolve_variable(self, variable_name: str) -> Any:
        """
        Resolve a variable value.
        
        Looks up variables in the following order:
        1. Workflow variables
        2. Environment variables
        
        Args:
            variable_name: Variable name
            
        Returns:
            Variable value or None if not found
        """
        # Check workflow variables first
        if variable_name in self.workflow_variables:
            return self.workflow_variables[variable_name]
        
        # Check environment variables
        if variable_name in self.environment_variables:
            return self.environment_variables[variable_name]
        
        logger.warning(f"Variable {variable_name} not found in context")
        return None
    
    def resolve_template(self, template: str) -> str:
        """
        Resolve a template string with variables.
        
        Supports {{variable_name}} syntax.
        
        Args:
            template: Template string
            
        Returns:
            Resolved string
        """
        import re
        
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self.resolve_variable(var_name)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(r'\{\{([^}]+)\}\}', replace_var, template)
    
    def add_log(
        self,
        block_id: str,
        block_type: str,
        block_name: str,
        success: bool,
        inputs: Dict[str, Any] = None,
        outputs: Dict[str, Any] = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Add a log entry for block execution.
        
        Args:
            block_id: Block identifier
            block_type: Block type
            block_name: Block name
            success: Whether execution was successful
            inputs: Block inputs
            outputs: Block outputs
            error: Error message if failed
            error_type: Error type if failed
            duration_ms: Execution duration in milliseconds
            metadata: Additional metadata
        """
        log_entry = BlockLog(
            block_id=block_id,
            block_type=block_type,
            block_name=block_name,
            timestamp=datetime.utcnow(),
            success=success,
            inputs=inputs or {},
            outputs=outputs or {},
            error=error,
            error_type=error_type,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        self.block_logs.append(log_entry)
    
    def update_token_usage(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0
    ):
        """
        Update token usage and cost.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost: Estimated cost
        """
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.estimated_cost += cost
    
    def add_file(self, file_id: str, file_metadata: Dict[str, Any]):
        """
        Add file metadata to context.
        
        Args:
            file_id: File identifier
            file_metadata: File metadata
        """
        self.files[file_id] = file_metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "trigger": self.trigger,
            "block_states": {
                block_id: state.to_dict()
                for block_id, state in self.block_states.items()
            },
            "block_logs": [log.to_dict() for log in self.block_logs],
            "environment_variables": self.environment_variables,
            "workflow_variables": self.workflow_variables,
            "loop_iterations": self.loop_iterations,
            "decisions": self.decisions,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error_message": self.error_message,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "estimated_cost": self.estimated_cost,
            "files": self.files,
        }
    
    def to_json(self) -> str:
        """
        Convert context to JSON string.
        
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        """
        Create ExecutionContext from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            ExecutionContext instance
        """
        context = cls(
            workflow_id=data["workflow_id"],
            execution_id=data["execution_id"],
            user_id=data["user_id"],
            trigger=data.get("trigger", "manual"),
        )
        
        # Restore block states
        for block_id, state_data in data.get("block_states", {}).items():
            context.block_states[block_id] = BlockState(
                block_id=state_data["block_id"],
                block_type=state_data["block_type"],
                executed=state_data["executed"],
                success=state_data["success"],
                outputs=state_data["outputs"],
                error=state_data.get("error"),
                started_at=datetime.fromisoformat(state_data["started_at"]) if state_data.get("started_at") else None,
                completed_at=datetime.fromisoformat(state_data["completed_at"]) if state_data.get("completed_at") else None,
                duration_ms=state_data.get("duration_ms"),
            )
        
        # Restore other fields
        context.environment_variables = data.get("environment_variables", {})
        context.workflow_variables = data.get("workflow_variables", {})
        context.loop_iterations = data.get("loop_iterations", {})
        context.decisions = data.get("decisions", {})
        context.status = data.get("status", "running")
        context.error_message = data.get("error_message")
        context.total_tokens = data.get("total_tokens", 0)
        context.prompt_tokens = data.get("prompt_tokens", 0)
        context.completion_tokens = data.get("completion_tokens", 0)
        context.estimated_cost = data.get("estimated_cost", 0.0)
        context.files = data.get("files", {})
        
        if data.get("started_at"):
            context.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            context.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return context
