"""Parallel execution for workflows.

This module provides functionality for executing parallel blocks and
managing concurrent execution.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional

from backend.core.execution.context import ExecutionContext, ParallelExecution
from backend.core.execution.errors import ParallelExecutionError

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """
    Executes parallel blocks and manages concurrent execution.
    
    Handles both fixed-count parallel execution and collection-based
    parallel processing.
    """
    
    # Maximum number of concurrent executions
    MAX_CONCURRENT = 10
    
    @staticmethod
    async def execute_parallel(
        parallel_block_id: str,
        parallel_body_blocks: List[Any],
        context: ExecutionContext,
        block_executor_func: Any,
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a parallel block.
        
        Args:
            parallel_block_id: ID of parallel block
            parallel_body_blocks: List of blocks in parallel body
            context: Execution context
            block_executor_func: Function to execute individual blocks
            max_concurrent: Maximum concurrent executions (default: MAX_CONCURRENT)
            
        Returns:
            Dict containing:
                - results: Array of results from each branch
                - count: Number of branches executed
                - aggregated: Aggregated result based on strategy
                
        Raises:
            ParallelExecutionError: If parallel execution fails
        """
        try:
            # Get parallel block output (contains branch setup)
            parallel_output = context.get_block_output(parallel_block_id)
            
            if not parallel_output:
                raise ParallelExecutionError(
                    f"Parallel block {parallel_block_id} has no output",
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id
                )
            
            branches = parallel_output.get("branches", [])
            aggregation_strategy = parallel_output.get("aggregation_strategy", "array")
            
            if not branches:
                logger.warning(f"Parallel block {parallel_block_id} has no branches")
                return {
                    "results": [],
                    "count": 0,
                    "aggregated": None,
                }
            
            logger.info(
                f"Executing parallel block {parallel_block_id} "
                f"with {len(branches)} branches"
            )
            
            # Initialize parallel execution state
            parallel_state = ParallelExecution(
                block_id=parallel_block_id,
                parallel_count=len(branches),
            )
            context.parallel_executions[parallel_block_id] = parallel_state
            
            # Limit concurrent executions
            max_concurrent = max_concurrent or ParallelExecutor.MAX_CONCURRENT
            semaphore = asyncio.Semaphore(max_concurrent)
            
            # Execute branches concurrently
            tasks = []
            for branch_data in branches:
                task = ParallelExecutor._execute_branch(
                    parallel_block_id=parallel_block_id,
                    branch_data=branch_data,
                    parallel_body_blocks=parallel_body_blocks,
                    context=context,
                    block_executor_func=block_executor_func,
                    semaphore=semaphore,
                )
                tasks.append(task)
            
            # Wait for all branches to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_results = []
            failed_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Parallel branch {i} failed: {str(result)}",
                        exc_info=result
                    )
                    failed_results.append({
                        "index": i,
                        "success": False,
                        "error": str(result),
                    })
                    parallel_state.errors.append(str(result))
                else:
                    successful_results.append(result)
                    parallel_state.results.append(result)
                
                parallel_state.completed_count += 1
            
            # Aggregate results
            aggregated = ParallelExecutor.aggregate_results(
                successful_results,
                aggregation_strategy
            )
            
            logger.info(
                f"Parallel block {parallel_block_id} completed: "
                f"{len(successful_results)} successful, "
                f"{len(failed_results)} failed"
            )
            
            return {
                "results": results,
                "count": len(results),
                "aggregated": aggregated,
                "successful_count": len(successful_results),
                "failed_count": len(failed_results),
            }
            
        except Exception as e:
            logger.error(
                f"Parallel execution failed: {str(e)}",
                exc_info=True
            )
            raise ParallelExecutionError(
                f"Parallel execution failed: {str(e)}",
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                original_error=e
            )
    
    @staticmethod
    async def _execute_branch(
        parallel_block_id: str,
        branch_data: Dict[str, Any],
        parallel_body_blocks: List[Any],
        context: ExecutionContext,
        block_executor_func: Any,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        Execute a single parallel branch.
        
        Args:
            parallel_block_id: ID of parallel block
            branch_data: Branch data including index and variables
            parallel_body_blocks: List of blocks in parallel body
            context: Execution context
            block_executor_func: Function to execute individual blocks
            semaphore: Semaphore for limiting concurrency
            
        Returns:
            Dict containing branch results
        """
        async with semaphore:
            branch_index = branch_data.get("index", 0)
            branch_vars = branch_data.get("variables", {})
            
            logger.info(
                f"Parallel block {parallel_block_id} branch {branch_index} starting"
            )
            
            # Update context with branch variables
            original_vars = context.workflow_variables.copy()
            context.workflow_variables.update(branch_vars)
            
            try:
                # Execute branch blocks
                branch_result = {}
                
                for block in parallel_body_blocks:
                    await block_executor_func(block, context)
                    
                    # Collect block output
                    block_id = str(block.id)
                    block_output = context.get_block_output(block_id)
                    if block_output:
                        branch_result[block_id] = block_output
                
                logger.info(
                    f"Parallel block {parallel_block_id} branch {branch_index} completed"
                )
                
                return {
                    "index": branch_index,
                    "success": True,
                    "outputs": branch_result,
                }
                
            except Exception as e:
                logger.error(
                    f"Parallel branch {branch_index} failed: {str(e)}",
                    exc_info=True
                )
                
                return {
                    "index": branch_index,
                    "success": False,
                    "error": str(e),
                }
                
            finally:
                # Restore original variables
                context.workflow_variables = original_vars
    
    @staticmethod
    def get_parallel_body_blocks(
        edges: list,
        parallel_block_id: str,
        all_blocks: List[Any]
    ) -> List[Any]:
        """
        Get blocks that are part of the parallel body.
        
        Parallel body blocks are those that are reachable from the parallel block
        and are not the parallel block itself.
        
        Args:
            edges: List of edges
            parallel_block_id: ID of parallel block
            all_blocks: List of all blocks
            
        Returns:
            List of blocks in parallel body
        """
        # Find blocks directly connected to parallel block
        body_block_ids = set()
        
        for edge in edges:
            if str(edge.source_block_id) == parallel_block_id:
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
    def aggregate_results(
        results: List[Any],
        strategy: str
    ) -> Any:
        """
        Aggregate parallel execution results.
        
        Args:
            results: List of results from parallel branches
            strategy: Aggregation strategy ("array", "merge", "first")
            
        Returns:
            Aggregated result
        """
        if strategy == "array":
            # Return array of all results
            return results
        
        elif strategy == "merge":
            # Merge all results into single object
            merged = {}
            for result in results:
                if isinstance(result, dict):
                    merged.update(result)
            return merged
        
        elif strategy == "first":
            # Return first result
            return results[0] if results else None
        
        else:
            logger.warning(f"Unknown aggregation strategy: {strategy}, using array")
            return results
    
    @staticmethod
    def log_parallel_execution(
        context: ExecutionContext,
        parallel_block_id: str,
        branch_count: int,
        successful_count: int,
        failed_count: int
    ):
        """
        Log parallel execution summary.
        
        Args:
            context: Execution context
            parallel_block_id: ID of parallel block
            branch_count: Total branches
            successful_count: Successful branches
            failed_count: Failed branches
        """
        logger.info(
            f"Parallel execution summary: "
            f"block={parallel_block_id}, "
            f"branches={branch_count}, "
            f"successful={successful_count}, "
            f"failed={failed_count}"
        )
        
        # Store in context for debugging
        if "parallel_results" not in context.decisions:
            context.decisions["parallel_results"] = {}
        
        context.decisions["parallel_results"][parallel_block_id] = {
            "branch_count": branch_count,
            "successful_count": successful_count,
            "failed_count": failed_count,
        }
