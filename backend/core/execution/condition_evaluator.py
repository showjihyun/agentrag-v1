"""Condition evaluation for workflow branching.

This module provides functionality for evaluating conditions and
determining which path to follow in conditional branches.
"""

import logging
from typing import Dict, Any, Optional

from backend.core.execution.context import ExecutionContext
from backend.core.execution.errors import ConditionEvaluationError

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """
    Evaluates conditions for workflow branching.
    
    Handles condition evaluation and path selection based on
    condition block outputs.
    """
    
    @staticmethod
    async def evaluate_and_select_path(
        condition_block_id: str,
        context: ExecutionContext,
        edges: list
    ) -> Optional[str]:
        """
        Evaluate condition and select next block to execute.
        
        Args:
            condition_block_id: ID of condition block
            context: Execution context
            edges: List of edges from condition block
            
        Returns:
            ID of next block to execute, or None if no path matches
            
        Raises:
            ConditionEvaluationError: If condition evaluation fails
        """
        try:
            # Get condition block output
            block_output = context.get_block_output(condition_block_id)
            
            if not block_output:
                raise ConditionEvaluationError(
                    f"Condition block {condition_block_id} has no output",
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id
                )
            
            # Get selected path
            selected_path = block_output.get("path")
            
            if not selected_path:
                logger.warning(
                    f"Condition block {condition_block_id} did not return a path"
                )
                return None
            
            # Store routing decision in context
            context.decisions[condition_block_id] = selected_path
            
            logger.info(
                f"Condition block {condition_block_id} selected path: {selected_path}"
            )
            
            # Find edge matching the selected path
            # Edges from condition blocks should have source_handle matching the path
            for edge in edges:
                if str(edge.source_block_id) == condition_block_id:
                    # Check if edge's source_handle matches the selected path
                    if edge.source_handle == selected_path:
                        next_block_id = str(edge.target_block_id)
                        logger.info(
                            f"Following path '{selected_path}' to block {next_block_id}"
                        )
                        return next_block_id
            
            # No matching edge found
            logger.warning(
                f"No edge found for path '{selected_path}' "
                f"from condition block {condition_block_id}"
            )
            return None
            
        except Exception as e:
            logger.error(
                f"Failed to evaluate condition: {str(e)}",
                exc_info=True
            )
            raise ConditionEvaluationError(
                f"Condition evaluation failed: {str(e)}",
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                original_error=e
            )
    
    @staticmethod
    def get_condition_paths(edges: list, condition_block_id: str) -> list:
        """
        Get all possible paths from a condition block.
        
        Args:
            edges: List of edges
            condition_block_id: ID of condition block
            
        Returns:
            List of path names
        """
        paths = []
        
        for edge in edges:
            if str(edge.source_block_id) == condition_block_id:
                if edge.source_handle:
                    paths.append(edge.source_handle)
        
        return paths
    
    @staticmethod
    def log_condition_result(
        context: ExecutionContext,
        condition_block_id: str,
        selected_path: str,
        matched_condition: Optional[Dict[str, Any]] = None
    ):
        """
        Log condition evaluation result.
        
        Args:
            context: Execution context
            condition_block_id: ID of condition block
            selected_path: Selected path
            matched_condition: Condition that matched (if any)
        """
        logger.info(
            f"Condition evaluation result: "
            f"block={condition_block_id}, "
            f"path={selected_path}, "
            f"condition={matched_condition}"
        )
        
        # Store in context for debugging
        if "condition_results" not in context.decisions:
            context.decisions["condition_results"] = {}
        
        context.decisions["condition_results"][condition_block_id] = {
            "path": selected_path,
            "matched_condition": matched_condition,
        }
