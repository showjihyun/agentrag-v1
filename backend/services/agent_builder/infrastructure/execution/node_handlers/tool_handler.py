"""
Tool Node Handler

Handles tool execution in workflows.
"""

import logging
import time
from typing import Dict, Any

from backend.services.agent_builder.domain.workflow.value_objects import ExecutionContext
from backend.services.agent_builder.domain.workflow.entities import NodeEntity
from backend.services.agent_builder.infrastructure.execution.base_handler import (
    BaseNodeHandler, NodeExecutionResult
)
from backend.services.agent_builder.infrastructure.execution.node_handler_registry import register_handler

logger = logging.getLogger(__name__)


@register_handler
class ToolNodeHandler(BaseNodeHandler):
    """Handler for Tool nodes."""
    
    @property
    def node_type(self) -> str:
        return "tool"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate tool node configuration."""
        errors = []
        config = node.config
        
        tool_id = config.tool_id or config.extra.get("toolId")
        if not tool_id:
            errors.append(f"Tool node '{node.id}' missing toolId")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute tool."""
        start_time = time.time()
        
        try:
            config = node.config
            tool_id = config.tool_id or config.extra.get("toolId")
            
            # Resolve variables in input
            resolved_input = {}
            for key, value in input_data.items():
                if isinstance(value, str) and "{{" in value:
                    resolved_input[key] = self.resolve_variables(value, context)
                else:
                    resolved_input[key] = value
            
            logger.info(f"Executing tool: {tool_id}")
            
            # Execute tool
            from backend.services.agent_builder.tool_registry import ToolRegistry
            
            registry = ToolRegistry()
            result = await registry.execute_tool(
                tool_id=tool_id,
                input_data=resolved_input,
                context={"user_id": context.user_id},
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            output = result if isinstance(result, dict) else {"output": result}
            
            return NodeExecutionResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
                metadata={"tool_id": tool_id},
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="TOOL_EXECUTION_ERROR",
                duration_ms=duration_ms,
            )
