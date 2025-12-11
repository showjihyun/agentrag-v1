"""
Condition Node Handler

Handles conditional branching in workflows.
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
class ConditionNodeHandler(BaseNodeHandler):
    """Handler for Condition nodes."""
    
    @property
    def node_type(self) -> str:
        return "condition"
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Evaluate condition and determine next node."""
        start_time = time.time()
        
        try:
            config = node.config
            condition = config.condition or config.extra.get("condition", "")
            
            # Resolve variables in condition
            if "{{" in condition:
                condition = self.resolve_variables(condition, context)
            
            # Evaluate condition
            result = self._evaluate_condition(condition, input_data, context)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Determine next node based on result
            # The executor will use edge conditions to route
            output = {
                "condition": condition,
                "result": result,
                "branch": "true" if result else "false",
            }
            
            return NodeExecutionResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
                metadata={"evaluated_condition": condition, "result": result},
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Condition evaluation failed: {e}", exc_info=True)
            
            return NodeExecutionResult(
                success=False,
                output={"result": False},
                error_message=str(e),
                error_code="CONDITION_EVAL_ERROR",
                duration_ms=duration_ms,
            )
    
    def _evaluate_condition(
        self,
        condition: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> bool:
        """
        Safely evaluate a condition expression.
        
        Supports:
        - Comparison operators: ==, !=, <, >, <=, >=
        - Logical operators: and, or, not
        - String operations: contains, startswith, endswith
        - Type checks: is_empty, is_not_empty
        """
        if not condition.strip():
            return True
        
        # Build evaluation context
        eval_context = {
            "input": input_data,
            "vars": context.variables,
            "nodes": context.node_results,
            "True": True,
            "False": False,
            "None": None,
            "true": True,
            "false": False,
            "null": None,
        }
        
        # Add helper functions
        eval_context["contains"] = lambda s, sub: sub in str(s) if s else False
        eval_context["startswith"] = lambda s, pre: str(s).startswith(pre) if s else False
        eval_context["endswith"] = lambda s, suf: str(s).endswith(suf) if s else False
        eval_context["is_empty"] = lambda x: x is None or x == "" or x == [] or x == {}
        eval_context["is_not_empty"] = lambda x: not (x is None or x == "" or x == [] or x == {})
        eval_context["len"] = len
        eval_context["str"] = str
        eval_context["int"] = int
        eval_context["float"] = float
        eval_context["bool"] = bool
        
        try:
            # Use restricted eval for safety
            result = eval(condition, {"__builtins__": {}}, eval_context)
            return bool(result)
        except Exception as e:
            logger.warning(f"Condition evaluation error: {e}, condition: {condition}")
            return False
