"""
Start/End Node Handlers

Handles workflow entry and exit points.
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
class StartNodeHandler(BaseNodeHandler):
    """Handler for Start nodes."""
    
    @property
    def node_type(self) -> str:
        return "start"
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Pass through input data."""
        return NodeExecutionResult(
            success=True,
            output=input_data,
            duration_ms=0,
        )


@register_handler
class EndNodeHandler(BaseNodeHandler):
    """Handler for End nodes."""
    
    @property
    def node_type(self) -> str:
        return "end"
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Collect and return final output."""
        # Collect output from configuration or input
        config = node.config
        output_mapping = config.extra.get("outputMapping", {})
        
        if output_mapping:
            output = {}
            for key, source in output_mapping.items():
                if source.startswith("nodes."):
                    parts = source.split(".")
                    node_id = parts[1]
                    field = parts[2] if len(parts) > 2 else "output"
                    node_result = context.get_node_result(node_id)
                    if node_result:
                        output[key] = node_result.get(field, node_result)
                else:
                    output[key] = input_data.get(source, source)
        else:
            output = input_data
        
        return NodeExecutionResult(
            success=True,
            output=output,
            duration_ms=0,
        )


@register_handler
class TriggerNodeHandler(BaseNodeHandler):
    """Handler for Trigger nodes (webhook, schedule, etc.)."""
    
    @property
    def node_type(self) -> str:
        return "trigger"
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Pass through trigger data."""
        return NodeExecutionResult(
            success=True,
            output=input_data,
            duration_ms=0,
            metadata={"trigger_type": node.config.extra.get("triggerType", "manual")},
        )
