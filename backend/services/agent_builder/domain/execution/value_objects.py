"""
Execution Value Objects
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"


class StepType(str, Enum):
    """Execution step type."""
    NODE_START = "node_start"
    NODE_COMPLETE = "node_complete"
    NODE_ERROR = "node_error"
    TOOL_CALL = "tool_call"
    LLM_CALL = "llm_call"
    CONDITION_EVAL = "condition_eval"
    LOOP_ITERATION = "loop_iteration"
    PARALLEL_BRANCH = "parallel_branch"
    HUMAN_APPROVAL = "human_approval"
    CHECKPOINT = "checkpoint"


@dataclass(frozen=True)
class ExecutionResult:
    """Result of an execution."""
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class TokenUsage:
    """Token usage tracking."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: str = ""
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "provider": self.provider,
            "cost_usd": self.cost_usd,
        }


@dataclass(frozen=True)
class ExecutionMetrics:
    """Execution metrics."""
    llm_call_count: int = 0
    llm_total_tokens: int = 0
    tool_call_count: int = 0
    tool_total_duration_ms: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    nodes_executed: int = 0
    retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm_call_count": self.llm_call_count,
            "llm_total_tokens": self.llm_total_tokens,
            "tool_call_count": self.tool_call_count,
            "tool_total_duration_ms": self.tool_total_duration_ms,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "nodes_executed": self.nodes_executed,
            "retries": self.retries,
        }
