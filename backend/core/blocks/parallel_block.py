"""Parallel Block for concurrent execution in workflows."""

import logging
from typing import Dict, Any, List

from backend.core.blocks.base import BaseBlock, BlockExecutionError
from backend.core.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


@BlockRegistry.register(
    block_type="parallel",
    name="Parallel",
    description="Execute multiple branches concurrently",
    category="blocks",
    sub_blocks=[
        {
            "id": "parallel_type",
            "type": "dropdown",
            "title": "Parallel Type",
            "required": True,
            "default_value": "fixed",
            "options": ["fixed", "collection"],
        },
        {
            "id": "branch_count",
            "type": "number-input",
            "title": "Number of Branches",
            "default_value": 2,
            "required": False,
            "condition": {
                "field": "parallel_type",
                "operator": "==",
                "value": "fixed"
            },
        },
        {
            "id": "collection_path",
            "type": "short-input",
            "title": "Collection Path",
            "placeholder": "items",
            "required": False,
            "condition": {
                "field": "parallel_type",
                "operator": "==",
                "value": "collection"
            },
        },
        {
            "id": "item_variable",
            "type": "short-input",
            "title": "Item Variable Name",
            "placeholder": "item",
            "default_value": "item",
            "required": False,
            "condition": {
                "field": "parallel_type",
                "operator": "==",
                "value": "collection"
            },
        },
        {
            "id": "aggregation_strategy",
            "type": "dropdown",
            "title": "Result Aggregation",
            "required": True,
            "default_value": "array",
            "options": ["array", "merge", "first"],
        },
    ],
    inputs={
        "collection": {
            "type": "array",
            "description": "Collection to process in parallel (for collection type)",
        },
        "variables": {
            "type": "object",
            "description": "Variables available to parallel branches",
        },
    },
    outputs={
        "results": {"type": "array", "description": "Array of branch results"},
        "count": {"type": "integer", "description": "Number of parallel branches"},
        "aggregated": {"type": "any", "description": "Aggregated result based on strategy"},
    },
    bg_color="#EC4899",
    icon="layers",
)
class ParallelBlock(BaseBlock):
    """
    Block for parallel execution in workflows.
    
    This block supports two types of parallel execution:
    - fixed: Fixed number of parallel branches
    - collection: Process each item in a collection in parallel
    
    Results can be aggregated using different strategies:
    - array: Return array of all results
    - merge: Merge all results into single object
    - first: Return first completed result
    """
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute parallel execution setup.
        
        Note: This block doesn't execute the parallel branches itself. It prepares
        the parallel execution state that will be used by the workflow executor.
        
        Args:
            inputs: Input data containing:
                - collection: Collection to process in parallel (for collection type)
                - variables: Variables available to parallel branches
            context: Execution context
            
        Returns:
            Dict containing:
                - branches: Array of branch contexts
                - count: Number of parallel branches
                - aggregation_strategy: Strategy for aggregating results
                
        Raises:
            BlockExecutionError: If parallel setup fails
        """
        try:
            # Get configuration from SubBlocks
            parallel_type = self.sub_blocks.get("parallel_type", "fixed")
            branch_count = int(self.sub_blocks.get("branch_count", 2))
            collection_path = self.sub_blocks.get("collection_path", "")
            item_variable = self.sub_blocks.get("item_variable", "item")
            aggregation_strategy = self.sub_blocks.get("aggregation_strategy", "array")
            
            # Get variables
            variables = inputs.get("variables", {})
            
            # Prepare branches
            branches = []
            
            if parallel_type == "fixed":
                # Fixed number of branches
                logger.info(f"Preparing parallel execution with {branch_count} branches")
                
                for i in range(branch_count):
                    branch_vars = {
                        **variables,
                        "branch_index": i,
                    }
                    branches.append({
                        "index": i,
                        "variables": branch_vars,
                    })
            
            elif parallel_type == "collection":
                # Collection-based parallel execution
                collection = inputs.get("collection")
                
                # If collection not in inputs, try to get from variables using path
                if collection is None and collection_path:
                    collection = self._get_nested_value(
                        variables,
                        collection_path
                    )
                
                if collection is None:
                    raise BlockExecutionError(
                        "Collection is required for collection-based parallel execution",
                        block_type="parallel",
                        block_id=self.block_id
                    )
                
                if not isinstance(collection, (list, tuple)):
                    raise BlockExecutionError(
                        f"Collection must be an array, got {type(collection).__name__}",
                        block_type="parallel",
                        block_id=self.block_id
                    )
                
                logger.info(
                    f"Preparing parallel execution for {len(collection)} items"
                )
                
                for i, item in enumerate(collection):
                    branch_vars = {
                        **variables,
                        item_variable: item,
                        "branch_index": i,
                    }
                    branches.append({
                        "index": i,
                        "item": item,
                        "variables": branch_vars,
                    })
            
            else:
                raise BlockExecutionError(
                    f"Unknown parallel type: {parallel_type}",
                    block_type="parallel",
                    block_id=self.block_id
                )
            
            logger.info(
                f"Parallel execution prepared with {len(branches)} branches "
                f"(aggregation: {aggregation_strategy})"
            )
            
            return {
                "branches": branches,
                "count": len(branches),
                "aggregation_strategy": aggregation_strategy,
            }
            
        except BlockExecutionError:
            raise
        except Exception as e:
            logger.error(f"Parallel block execution failed: {str(e)}", exc_info=True)
            raise BlockExecutionError(
                f"Failed to execute parallel block: {str(e)}",
                block_type="parallel",
                block_id=self.block_id,
                original_error=e
            )
    
    @staticmethod
    def aggregate_results(
        results: List[Any],
        strategy: str
    ) -> Any:
        """
        Aggregate parallel execution results.
        
        This is a utility method that can be called by the workflow executor
        after all parallel branches complete.
        
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
            path: Dot-separated path (e.g., "user.items")
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        if not path:
            return default
        
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
