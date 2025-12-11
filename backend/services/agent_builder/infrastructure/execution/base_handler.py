"""
Base Node Handler

Abstract base class for all node type handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from backend.services.agent_builder.domain.workflow.value_objects import ExecutionContext
from backend.services.agent_builder.domain.workflow.entities import NodeEntity


@dataclass
class NodeExecutionResult:
    """Result of node execution."""
    success: bool
    output: Dict[str, Any]
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: int = 0
    next_node_id: Optional[str] = None  # For conditional routing
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseNodeHandler(ABC):
    """
    Abstract base class for node handlers.
    
    Each node type (agent, tool, condition, etc.) has its own handler
    that implements the execution logic.
    """
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """Return the node type this handler supports."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """
        Execute the node.
        
        Args:
            node: The node entity to execute
            context: Execution context with variables and previous results
            input_data: Input data for this node
            
        Returns:
            NodeExecutionResult with output and status
        """
        pass
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """
        Validate node configuration before execution.
        
        Args:
            node: The node to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return True, []
    
    async def pre_execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
    ) -> None:
        """Hook called before execution."""
        pass
    
    async def post_execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        result: NodeExecutionResult,
    ) -> None:
        """Hook called after execution."""
        pass
    
    def resolve_variables(
        self,
        template: str,
        context: ExecutionContext,
    ) -> str:
        """
        Resolve variables in a template string.
        
        Supports:
        - {{input.field}} - Input data
        - {{vars.name}} - Context variables
        - {{nodes.nodeId.output}} - Previous node outputs
        """
        import re
        
        def replace_var(match):
            var_path = match.group(1)
            parts = var_path.split(".")
            
            if parts[0] == "input":
                value = context.input_data
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part, "")
                    else:
                        value = ""
                return str(value)
            
            elif parts[0] == "vars":
                return str(context.get_variable(parts[1], ""))
            
            elif parts[0] == "nodes" and len(parts) >= 2:
                node_result = context.get_node_result(parts[1])
                if node_result and len(parts) > 2:
                    for part in parts[2:]:
                        if isinstance(node_result, dict):
                            node_result = node_result.get(part, "")
                        else:
                            node_result = ""
                return str(node_result or "")
            
            return match.group(0)
        
        return re.sub(r"\{\{([^}]+)\}\}", replace_var, template)
