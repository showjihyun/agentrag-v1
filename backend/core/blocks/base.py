"""Base Block class for workflow blocks.

This module provides the abstract base class that all workflow blocks must inherit from.
It defines the interface for block execution and configuration.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class BlockExecutionError(Exception):
    """Exception raised when block execution fails."""
    
    def __init__(
        self,
        message: str,
        block_type: str,
        block_id: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize BlockExecutionError.
        
        Args:
            message: Error message
            block_type: Type of block that failed
            block_id: ID of block instance that failed
            original_error: Original exception that caused the failure
        """
        self.message = message
        self.block_type = block_type
        self.block_id = block_id
        self.original_error = original_error
        super().__init__(self.message)


class BlockValidationError(Exception):
    """Exception raised when block validation fails."""
    
    def __init__(
        self,
        message: str,
        block_type: str,
        validation_errors: Optional[List[str]] = None
    ):
        """
        Initialize BlockValidationError.
        
        Args:
            message: Error message
            block_type: Type of block that failed validation
            validation_errors: List of specific validation errors
        """
        self.message = message
        self.block_type = block_type
        self.validation_errors = validation_errors or []
        super().__init__(self.message)


class BaseBlock(ABC):
    """
    Abstract base class for all workflow blocks.
    
    All blocks must inherit from this class and implement the execute() method.
    Blocks can optionally override validation and configuration methods.
    """
    
    def __init__(
        self,
        block_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        sub_blocks: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize BaseBlock.
        
        Args:
            block_id: Unique identifier for this block instance
            config: Block configuration
            sub_blocks: SubBlock values (UI inputs)
        """
        self.block_id = block_id
        self.config = config or {}
        self.sub_blocks = sub_blocks or {}
        self.execution_history: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the block with given inputs.
        
        This is the main method that must be implemented by all blocks.
        
        Args:
            inputs: Input data for the block
            context: Execution context containing:
                - execution_id: Unique execution identifier
                - workflow_id: Workflow identifier
                - user_id: User identifier
                - variables: Workflow variables
                - previous_outputs: Outputs from previous blocks
                
        Returns:
            Dict containing block outputs
            
        Raises:
            BlockExecutionError: If execution fails
        """
        pass
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        Get block configuration.
        
        This method returns the block's metadata including name, description,
        SubBlocks, and input/output schemas. It's typically set via the
        @BlockRegistry.register decorator.
        
        Returns:
            Block configuration dict
        """
        # This will be populated by the registry decorator
        return {}
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate block inputs against schema.
        
        Args:
            inputs: Input data to validate
            
        Returns:
            True if valid
            
        Raises:
            BlockValidationError: If validation fails
        """
        config = self.get_config()
        input_schema = config.get("inputs", {})
        
        # Check required inputs
        required_inputs = input_schema.get("required", [])
        missing_inputs = [
            field for field in required_inputs
            if field not in inputs
        ]
        
        if missing_inputs:
            raise BlockValidationError(
                f"Missing required inputs: {', '.join(missing_inputs)}",
                block_type=config.get("type", "unknown"),
                validation_errors=missing_inputs
            )
        
        return True
    
    def validate_sub_blocks(self) -> bool:
        """
        Validate SubBlock values against configuration.
        
        Returns:
            True if valid
            
        Raises:
            BlockValidationError: If validation fails
        """
        config = self.get_config()
        sub_blocks_config = config.get("sub_blocks", [])
        
        # Check required SubBlocks
        missing_sub_blocks = []
        for sub_block in sub_blocks_config:
            if sub_block.get("required", False):
                sub_block_id = sub_block["id"]
                if sub_block_id not in self.sub_blocks:
                    missing_sub_blocks.append(sub_block_id)
        
        if missing_sub_blocks:
            raise BlockValidationError(
                f"Missing required SubBlocks: {', '.join(missing_sub_blocks)}",
                block_type=config.get("type", "unknown"),
                validation_errors=missing_sub_blocks
            )
        
        return True
    
    async def execute_with_error_handling(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute block with error handling and logging.
        
        This method wraps the execute() method with error handling,
        validation, and execution tracking.
        
        Args:
            inputs: Input data for the block
            context: Execution context
            
        Returns:
            Dict containing:
                - success: Boolean indicating success
                - outputs: Block outputs (if successful)
                - error: Error message (if failed)
                - duration_ms: Execution duration in milliseconds
                - metadata: Additional execution metadata
                
        Raises:
            BlockExecutionError: If execution fails critically
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate inputs
            self.validate_inputs(inputs)
            
            # Validate SubBlocks
            self.validate_sub_blocks()
            
            # Execute block
            logger.info(
                f"Executing block {self.block_id} "
                f"(type: {self.get_config().get('type', 'unknown')})"
            )
            
            outputs = await self.execute(inputs, context)
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Record execution
            execution_record = {
                "timestamp": start_time.isoformat(),
                "success": True,
                "duration_ms": duration_ms,
                "inputs": inputs,
                "outputs": outputs,
            }
            self.execution_history.append(execution_record)
            
            logger.info(
                f"Block {self.block_id} executed successfully "
                f"in {duration_ms}ms"
            )
            
            return {
                "success": True,
                "outputs": outputs,
                "duration_ms": duration_ms,
                "metadata": {
                    "block_id": self.block_id,
                    "block_type": self.get_config().get("type", "unknown"),
                    "timestamp": start_time.isoformat(),
                }
            }
            
        except BlockValidationError as e:
            # Validation error - don't retry
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(
                f"Block {self.block_id} validation failed: {e.message}"
            )
            
            # Record failure
            execution_record = {
                "timestamp": start_time.isoformat(),
                "success": False,
                "duration_ms": duration_ms,
                "error": e.message,
                "error_type": "validation",
            }
            self.execution_history.append(execution_record)
            
            return {
                "success": False,
                "error": e.message,
                "error_type": "validation",
                "validation_errors": e.validation_errors,
                "duration_ms": duration_ms,
                "metadata": {
                    "block_id": self.block_id,
                    "block_type": self.get_config().get("type", "unknown"),
                    "timestamp": start_time.isoformat(),
                }
            }
            
        except BlockExecutionError as e:
            # Execution error
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(
                f"Block {self.block_id} execution failed: {e.message}",
                exc_info=e.original_error
            )
            
            # Record failure
            execution_record = {
                "timestamp": start_time.isoformat(),
                "success": False,
                "duration_ms": duration_ms,
                "error": e.message,
                "error_type": "execution",
            }
            self.execution_history.append(execution_record)
            
            return {
                "success": False,
                "error": e.message,
                "error_type": "execution",
                "duration_ms": duration_ms,
                "metadata": {
                    "block_id": self.block_id,
                    "block_type": self.get_config().get("type", "unknown"),
                    "timestamp": start_time.isoformat(),
                }
            }
            
        except Exception as e:
            # Unexpected error
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(
                f"Block {self.block_id} unexpected error: {str(e)}",
                exc_info=True
            )
            
            # Record failure
            execution_record = {
                "timestamp": start_time.isoformat(),
                "success": False,
                "duration_ms": duration_ms,
                "error": str(e),
                "error_type": "unexpected",
            }
            self.execution_history.append(execution_record)
            
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected",
                "duration_ms": duration_ms,
                "metadata": {
                    "block_id": self.block_id,
                    "block_type": self.get_config().get("type", "unknown"),
                    "timestamp": start_time.isoformat(),
                }
            }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get execution history for this block instance.
        
        Returns:
            List of execution records
        """
        return self.execution_history
    
    def clear_execution_history(self):
        """Clear execution history."""
        self.execution_history.clear()
    
    def __repr__(self) -> str:
        """String representation of block."""
        config = self.get_config()
        return (
            f"<{self.__class__.__name__} "
            f"id={self.block_id} "
            f"type={config.get('type', 'unknown')}>"
        )
