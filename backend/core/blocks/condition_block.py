"""Condition Block for branching logic in workflows."""

import logging
from typing import Dict, Any, List
import operator

from backend.core.blocks.base import BaseBlock, BlockExecutionError
from backend.core.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


@BlockRegistry.register(
    block_type="condition",
    name="Condition",
    description="Branch workflow based on conditions",
    category="blocks",
    sub_blocks=[
        {
            "id": "conditions",
            "type": "code",
            "title": "Conditions (JSON Array)",
            "language": "json",
            "placeholder": '[{"variable": "status", "operator": "==", "value": "success", "path": "true"}]',
            "required": True,
        },
        {
            "id": "default_path",
            "type": "short-input",
            "title": "Default Path",
            "placeholder": "false",
            "default_value": "false",
            "required": False,
        },
    ],
    inputs={
        "variables": {
            "type": "object",
            "description": "Variables to evaluate conditions against",
        },
    },
    outputs={
        "path": {"type": "string", "description": "Selected path (e.g., 'true', 'false', 'path1')"},
        "matched_condition": {"type": "object", "description": "The condition that matched"},
    },
    bg_color="#F59E0B",
    icon="git-branch",
)
class ConditionBlock(BaseBlock):
    """
    Block for conditional branching in workflows.
    
    This block evaluates conditions against input variables and returns
    the path to follow. It supports multiple conditions with different
    operators and can have a default path.
    """
    
    # Supported operators
    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "in": lambda a, b: a in b,
        "not_in": lambda a, b: a not in b,
        "contains": lambda a, b: b in a,
        "starts_with": lambda a, b: str(a).startswith(str(b)),
        "ends_with": lambda a, b: str(a).endswith(str(b)),
        "is_empty": lambda a, b: not a,
        "is_not_empty": lambda a, b: bool(a),
    }
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute condition evaluation.
        
        Args:
            inputs: Input data containing:
                - variables: Variables to evaluate conditions against
            context: Execution context
            
        Returns:
            Dict containing:
                - path: Selected path identifier
                - matched_condition: The condition that matched (if any)
                
        Raises:
            BlockExecutionError: If condition evaluation fails
        """
        try:
            # Get configuration from SubBlocks
            conditions_str = self.sub_blocks.get("conditions", "[]")
            default_path = self.sub_blocks.get("default_path", "false")
            
            # Parse conditions
            import json
            try:
                conditions = json.loads(conditions_str)
            except json.JSONDecodeError as e:
                raise BlockExecutionError(
                    f"Invalid JSON in conditions: {str(e)}",
                    block_type="condition",
                    block_id=self.block_id,
                    original_error=e
                )
            
            if not isinstance(conditions, list):
                raise BlockExecutionError(
                    "Conditions must be a JSON array",
                    block_type="condition",
                    block_id=self.block_id
                )
            
            # Get variables
            variables = inputs.get("variables", {})
            
            # Evaluate conditions
            logger.info(f"Evaluating {len(conditions)} conditions")
            
            for i, condition in enumerate(conditions):
                if self._evaluate_condition(condition, variables):
                    path = condition.get("path", f"path_{i}")
                    logger.info(f"Condition {i} matched, taking path: {path}")
                    return {
                        "path": path,
                        "matched_condition": condition,
                    }
            
            # No condition matched, use default path
            logger.info(f"No condition matched, taking default path: {default_path}")
            return {
                "path": default_path,
                "matched_condition": None,
            }
            
        except BlockExecutionError:
            raise
        except Exception as e:
            logger.error(f"Condition block execution failed: {str(e)}", exc_info=True)
            raise BlockExecutionError(
                f"Failed to execute condition block: {str(e)}",
                block_type="condition",
                block_id=self.block_id,
                original_error=e
            )
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            condition: Condition dict with keys:
                - variable: Variable name to check
                - operator: Comparison operator
                - value: Value to compare against
            variables: Available variables
            
        Returns:
            True if condition matches, False otherwise
        """
        try:
            variable_name = condition.get("variable")
            op_name = condition.get("operator", "==")
            expected_value = condition.get("value")
            
            if not variable_name:
                logger.warning("Condition missing 'variable' field")
                return False
            
            # Get variable value (support nested paths with dot notation)
            actual_value = self._get_nested_value(variables, variable_name)
            
            # Get operator function
            op_func = self.OPERATORS.get(op_name)
            if not op_func:
                logger.warning(f"Unknown operator: {op_name}")
                return False
            
            # Special handling for operators that don't need expected_value
            if op_name in ["is_empty", "is_not_empty"]:
                return op_func(actual_value, None)
            
            # Evaluate condition
            result = op_func(actual_value, expected_value)
            
            logger.debug(
                f"Condition: {variable_name} {op_name} {expected_value} "
                f"(actual: {actual_value}) = {result}"
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"Error evaluating condition: {e}")
            return False
    
    def _get_nested_value(
        self,
        data: Dict[str, Any],
        path: str,
        default: Any = None
    ) -> Any:
        """
        Get value from nested dict using dot notation.
        
        Args:
            data: Dict to get value from
            path: Dot-separated path (e.g., "user.name")
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
