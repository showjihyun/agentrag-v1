"""Loop Block for iteration in workflows."""

import logging
from typing import Dict, Any, List

from backend.core.blocks.base import BaseBlock, BlockExecutionError
from backend.core.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


@BlockRegistry.register(
    block_type="loop",
    name="Loop",
    description="Iterate over a collection or count",
    category="blocks",
    sub_blocks=[
        {
            "id": "loop_type",
            "type": "dropdown",
            "title": "Loop Type",
            "required": True,
            "default_value": "forEach",
            "options": ["for", "forEach"],
        },
        {
            "id": "iterations",
            "type": "number-input",
            "title": "Iterations",
            "default_value": 5,
            "required": False,
            "condition": {
                "field": "loop_type",
                "operator": "==",
                "value": "for"
            },
        },
        {
            "id": "collection_path",
            "type": "short-input",
            "title": "Collection Path",
            "placeholder": "items",
            "required": False,
            "condition": {
                "field": "loop_type",
                "operator": "==",
                "value": "forEach"
            },
        },
        {
            "id": "item_variable",
            "type": "short-input",
            "title": "Item Variable Name",
            "placeholder": "item",
            "default_value": "item",
            "required": False,
        },
        {
            "id": "index_variable",
            "type": "short-input",
            "title": "Index Variable Name",
            "placeholder": "index",
            "default_value": "index",
            "required": False,
        },
    ],
    inputs={
        "collection": {
            "type": "array",
            "description": "Collection to iterate over (for forEach)",
        },
        "variables": {
            "type": "object",
            "description": "Variables available in loop",
        },
    },
    outputs={
        "iterations": {"type": "array", "description": "Array of iteration results"},
        "count": {"type": "integer", "description": "Number of iterations"},
    },
    bg_color="#8B5CF6",
    icon="repeat",
)
class LoopBlock(BaseBlock):
    """
    Block for iterating in workflows.
    
    This block supports two types of loops:
    - for: Fixed number of iterations
    - forEach: Iterate over a collection
    
    The loop block manages iteration state and provides current item
    and index to nested blocks.
    """
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute loop iteration setup.
        
        Note: This block doesn't execute the loop body itself. It prepares
        the iteration state that will be used by the workflow executor.
        
        Args:
            inputs: Input data containing:
                - collection: Collection to iterate over (for forEach)
                - variables: Variables available in loop
            context: Execution context
            
        Returns:
            Dict containing:
                - iterations: Array of iteration contexts
                - count: Number of iterations
                
        Raises:
            BlockExecutionError: If loop setup fails
        """
        try:
            # Get configuration from SubBlocks
            loop_type = self.sub_blocks.get("loop_type", "forEach")
            iterations_count = int(self.sub_blocks.get("iterations", 5))
            collection_path = self.sub_blocks.get("collection_path", "")
            item_variable = self.sub_blocks.get("item_variable", "item")
            index_variable = self.sub_blocks.get("index_variable", "index")
            
            # Get variables
            variables = inputs.get("variables", {})
            
            # Prepare iterations
            iterations = []
            
            if loop_type == "for":
                # Fixed count loop
                logger.info(f"Preparing 'for' loop with {iterations_count} iterations")
                
                for i in range(iterations_count):
                    iteration_vars = {
                        **variables,
                        index_variable: i,
                    }
                    iterations.append({
                        "index": i,
                        "variables": iteration_vars,
                    })
            
            elif loop_type == "forEach":
                # Collection loop
                collection = inputs.get("collection")
                
                # If collection not in inputs, try to get from variables using path
                if collection is None and collection_path:
                    collection = self._get_nested_value(
                        variables,
                        collection_path
                    )
                
                if collection is None:
                    raise BlockExecutionError(
                        "Collection is required for forEach loop",
                        block_type="loop",
                        block_id=self.block_id
                    )
                
                if not isinstance(collection, (list, tuple)):
                    raise BlockExecutionError(
                        f"Collection must be an array, got {type(collection).__name__}",
                        block_type="loop",
                        block_id=self.block_id
                    )
                
                logger.info(f"Preparing 'forEach' loop with {len(collection)} items")
                
                for i, item in enumerate(collection):
                    iteration_vars = {
                        **variables,
                        item_variable: item,
                        index_variable: i,
                    }
                    iterations.append({
                        "index": i,
                        "item": item,
                        "variables": iteration_vars,
                    })
            
            else:
                raise BlockExecutionError(
                    f"Unknown loop type: {loop_type}",
                    block_type="loop",
                    block_id=self.block_id
                )
            
            logger.info(f"Loop prepared with {len(iterations)} iterations")
            
            return {
                "iterations": iterations,
                "count": len(iterations),
            }
            
        except BlockExecutionError:
            raise
        except Exception as e:
            logger.error(f"Loop block execution failed: {str(e)}", exc_info=True)
            raise BlockExecutionError(
                f"Failed to execute loop block: {str(e)}",
                block_type="loop",
                block_id=self.block_id,
                original_error=e
            )
    
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
