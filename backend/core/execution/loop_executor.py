"""Loop execution for workflows.

This module provides functionality for executing loop blocks and
managing iteration state.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.core.execution.context import ExecutionContext
from backend.core.execution.errors import LoopExecutionError

logger = logging.getLogger(__name__)


class LoopExecutor:
    """
    Executes loop blocks and manages iteration state.
    
    Handles both 'for' loops (fixed count) and 'forEach' loops
    (iterate over collection).
    """
    
    @staticmethod
    async def execute_loop(
        loop_block_id: str,
        loop_body_blocks: List[Any],
        context: ExecutionContext,
        block_executor_func: Any
    ) -> Dict[str, Any]:
        """
        Execute a loop block.
        
        Args:
            loop_block_id: ID of loop block
            loop_body_blocks: List of blocks in loop body
            context: Execution context
            block_executor_func: Function to execute individual blocks
            
        Returns:
            Dict containing:
                - results: Array of results from each iteration
                - count: Number of iterations executed
                
        Raises:
            LoopExecutionError: If loop execution fails
        """
        try:
            # Get loop block output (contains iteration setup)
            loop_output = context.get_block_output(loop_block_id)
            
            if not loop_output:
                raise LoopExecutionError(
                    f"Loop block {loop_block_id} has no output",
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id
                )
            
            iterations = loop_output.get("iterations", [])
            
            if not iterations:
                logger.warning(f"Loop block {loop_block_id} has no iterations")
                return {
                    "results": [],
                    "count": 0,
                }
            
            logger.info(
                f"Executing loop {loop_block_id} with {len(iterations)} iterations"
            )
            
            # Execute each iteration
            results = []
            
            for iteration_data in iterations:
                iteration_index = iteration_data.get("index", 0)
                iteration_vars = iteration_data.get("variables", {})
                
                logger.info(
                    f"Loop {loop_block_id} iteration {iteration_index}"
                )
                
                # Update context with iteration variables
                original_vars = context.workflow_variables.copy()
                context.workflow_variables.update(iteration_vars)
                
                # Track iteration count
                context.loop_iterations[loop_block_id] = iteration_index
                
                try:
                    # Execute loop body blocks
                    iteration_result = {}
                    
                    for block in loop_body_blocks:
                        await block_executor_func(block, context)
                        
                        # Collect block output
                        block_id = str(block.id)
                        block_output = context.get_block_output(block_id)
                        if block_output:
                            iteration_result[block_id] = block_output
                    
                    results.append({
                        "index": iteration_index,
                        "success": True,
                        "outputs": iteration_result,
                    })
                    
                except Exception as e:
                    logger.error(
                        f"Loop iteration {iteration_index} failed: {str(e)}",
                        exc_info=True
                    )
                    
                    results.append({
                        "index": iteration_index,
                        "success": False,
                        "error": str(e),
                    })
                    
                    # Optionally stop on first error
                    # For now, continue with remaining iterations
                
                finally:
                    # Restore original variables
                    context.workflow_variables = original_vars
            
            logger.info(
                f"Loop {loop_block_id} completed: "
                f"{len(results)} iterations, "
                f"{sum(1 for r in results if r.get('success'))} successful"
            )
            
            return {
                "results": results,
                "count": len(results),
            }
            
        except Exception as e:
            logger.error(
                f"Loop execution failed: {str(e)}",
                exc_info=True
            )
            raise LoopExecutionError(
                f"Loop execution failed: {str(e)}",
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                original_error=e
            )
    
    @staticmethod
    def get_loop_body_blocks(
        edges: list,
        loop_block_id: str,
        all_blocks: List[Any]
    ) -> List[Any]:
        """
        Get blocks that are part of the loop body.
        
        Loop body blocks are those that are reachable from the loop block
        and are not the loop block itself.
        
        Args:
            edges: List of edges
            loop_block_id: ID of loop block
            all_blocks: List of all blocks
            
        Returns:
            List of blocks in loop body
        """
        # Find blocks directly connected to loop block
        body_block_ids = set()
        
        for edge in edges:
            if str(edge.source_block_id) == loop_block_id:
                body_block_ids.add(str(edge.target_block_id))
        
        # Get block objects
        block_map = {str(block.id): block for block in all_blocks}
        body_blocks = [
            block_map[block_id]
            for block_id in body_block_ids
            if block_id in block_map
        ]
        
        return body_blocks
    
    @staticmethod
    def aggregate_loop_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from loop iterations.
        
        Args:
            results: List of iteration results
            
        Returns:
            Aggregated results
        """
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        return {
            "total_iterations": len(results),
            "successful_iterations": len(successful),
            "failed_iterations": len(failed),
            "all_results": results,
            "successful_results": successful,
            "failed_results": failed,
        }
    
    @staticmethod
    def log_loop_execution(
        context: ExecutionContext,
        loop_block_id: str,
        iteration_count: int,
        successful_count: int,
        failed_count: int
    ):
        """
        Log loop execution summary.
        
        Args:
            context: Execution context
            loop_block_id: ID of loop block
            iteration_count: Total iterations
            successful_count: Successful iterations
            failed_count: Failed iterations
        """
        logger.info(
            f"Loop execution summary: "
            f"block={loop_block_id}, "
            f"iterations={iteration_count}, "
            f"successful={successful_count}, "
            f"failed={failed_count}"
        )
        
        # Store in context for debugging
        if "loop_results" not in context.decisions:
            context.decisions["loop_results"] = {}
        
        context.decisions["loop_results"][loop_block_id] = {
            "iteration_count": iteration_count,
            "successful_count": successful_count,
            "failed_count": failed_count,
        }
