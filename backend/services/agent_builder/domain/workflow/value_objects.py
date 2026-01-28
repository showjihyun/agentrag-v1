"""
Workflow Value Objects

Immutable objects that describe characteristics of workflow entities.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class NodeType(str, Enum):
    """Workflow node types."""
    # Entry/Exit
    START = "start"
    END = "end"
    
    # AI/Agent
    AGENT = "agent"
    AI_AGENT = "ai_agent"
    LLM = "llm"
    
    # Agentic Blocks
    AGENTIC_REFLECTION = "agentic_reflection"
    AGENTIC_PLANNING = "agentic_planning"
    AGENTIC_TOOL_SELECTOR = "agentic_tool_selector"
    AGENTIC_RAG = "agentic_rag"
    
    # Control Flow
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    MERGE = "merge"
    DELAY = "delay"
    
    # Data Processing
    TRANSFORM = "transform"
    FILTER = "filter"
    CODE = "code"
    
    # Integration
    TOOL = "tool"
    HTTP_REQUEST = "http_request"
    DATABASE = "database"
    
    # Human
    HUMAN_APPROVAL = "human_approval"
    
    # Block
    BLOCK = "block"
    
    # Trigger
    TRIGGER = "trigger"
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"


class EdgeType(str, Enum):
    """Workflow edge types."""
    NORMAL = "normal"
    CONDITIONAL = "conditional"
    ERROR = "error"
    TIMEOUT = "timeout"
    LOOP_BACK = "loop_back"


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass(frozen=True)
class Position:
    """Node position on canvas."""
    x: float = 0.0
    y: float = 0.0


@dataclass
class NodeConfig:
    """Node configuration value object."""
    node_type: NodeType
    label: Optional[str] = None
    description: Optional[str] = None
    
    # Type-specific config
    agent_id: Optional[str] = None
    tool_id: Optional[str] = None
    block_id: Optional[str] = None
    
    # LLM config
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    prompt_template: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Control flow config
    condition: Optional[str] = None
    max_iterations: int = 10
    timeout_seconds: int = 60
    
    # HTTP config
    url: Optional[str] = None
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Code config
    code: Optional[str] = None
    language: str = "python"
    
    # Additional config (mutable for runtime modifications)
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "node_type": self.node_type.value,
            "label": self.label,
            "description": self.description,
        }
        
        # Add non-None values
        if self.agent_id:
            result["agentId"] = self.agent_id
        if self.tool_id:
            result["toolId"] = self.tool_id
        if self.block_id:
            result["blockId"] = self.block_id
        if self.llm_provider:
            result["llm_provider"] = self.llm_provider
        if self.llm_model:
            result["llm_model"] = self.llm_model
        if self.prompt_template:
            result["prompt_template"] = self.prompt_template
        if self.condition:
            result["condition"] = self.condition
        if self.url:
            result["url"] = self.url
        if self.code:
            result["code"] = self.code
        
        result["temperature"] = self.temperature
        result["max_tokens"] = self.max_tokens
        result["max_iterations"] = self.max_iterations
        result["timeout_seconds"] = self.timeout_seconds
        result["method"] = self.method
        result["language"] = self.language
        
        if self.headers:
            result["headers"] = self.headers
        if self.extra:
            result.update(self.extra)
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeConfig":
        node_type_str = data.get("node_type", data.get("nodeType", "block"))
        try:
            node_type = NodeType(node_type_str)
        except ValueError:
            node_type = NodeType.BLOCK
        
        return cls(
            node_type=node_type,
            label=data.get("label"),
            description=data.get("description"),
            agent_id=data.get("agentId") or data.get("agent_id"),
            tool_id=data.get("toolId") or data.get("tool_id"),
            block_id=data.get("blockId") or data.get("block_id"),
            llm_provider=data.get("llm_provider"),
            llm_model=data.get("llm_model"),
            prompt_template=data.get("prompt_template"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            condition=data.get("condition"),
            max_iterations=data.get("max_iterations", data.get("maxIterations", 10)),
            timeout_seconds=data.get("timeout_seconds", 60),
            url=data.get("url"),
            method=data.get("method", "GET"),
            headers=data.get("headers", {}),
            code=data.get("code"),
            language=data.get("language", "python"),
            extra={k: v for k, v in data.items() if k not in [
                "node_type", "nodeType", "label", "description",
                "agentId", "agent_id", "toolId", "tool_id", "blockId", "block_id",
                "llm_provider", "llm_model", "prompt_template", "temperature", "max_tokens",
                "condition", "max_iterations", "maxIterations", "timeout_seconds",
                "url", "method", "headers", "code", "language"
            ]},
        )


@dataclass(frozen=True)
class EdgeCondition:
    """Edge condition for conditional routing."""
    expression: str
    label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "expression": self.expression,
            "label": self.label,
        }


@dataclass
class ExecutionContext:
    """Execution context passed through workflow."""
    execution_id: str
    workflow_id: str
    user_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, Any] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    parent_execution_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from context."""
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in context."""
        self.variables[name] = value
    
    def get_node_result(self, node_id: str) -> Optional[Any]:
        """Get result from a previous node."""
        return self.node_results.get(node_id)
    
    def set_node_result(self, node_id: str, result: Any) -> None:
        """Set result for a node."""
        self.node_results[node_id] = result
