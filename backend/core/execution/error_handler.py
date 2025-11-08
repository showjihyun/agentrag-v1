"""Error handling for workflow execution.

This module provides comprehensive error handling for workflow execution,
including error recovery strategies, timeout handling, and error formatting.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import traceback

from backend.core.execution.context import ExecutionContext
from backend.core.execution.errors import (
    ExecutionError,
    BlockExecutionError,
    ExecutionTimeoutError,
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Handles errors during workflow execution.
    
    Provides:
    - Error recovery strategies
    - Timeout handling
    - Error response formatting
    - Error logging
    """
    
    # Default timeout for block execution (seconds)
    DEFAULT_BLOCK_TIMEOUT = 300  # 5 minutes
    
    # Default timeout for workflow execution (seconds)
    DEFAULT_WORKFLOW_TIMEOUT = 1800  # 30 minutes
    
    @staticmethod
    async def execute_with_timeout(
        coro: Callable,
        timeout_seconds: Optional[int] = None,
        error_message: str = "Operation timed out"
    ) -> Any:
        """
        Execute a coroutine with timeout.
        
        Args:
            coro: Coroutine to execute
            timeout_seconds: Timeout in seconds (default: DEFAULT_BLOCK_TIMEOUT)
            error_message: Error message if timeout occurs
            
        Returns:
            Result of coroutine
            
        Raises:
            ExecutionTimeoutError: If timeout occurs
        """
        timeout = timeout_seconds or ErrorHandler.DEFAULT_BLOCK_TIMEOUT
        
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Timeout after {timeout} seconds: {error_message}")
            raise ExecutionTimeoutError(
                f"{error_message} (timeout: {timeout}s)"
            )
    
    @staticmethod
    async def execute_block_with_recovery(
        block: Any,
        context: ExecutionContext,
        executor_func: Callable,
        max_retries: int = 0,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Execute a block with error recovery.
        
        Args:
            block: Block to execute
            context: Execution context
            executor_func: Function to execute block
            max_retries: Maximum number of retries (default: 0)
            retry_delay: Delay between retries in seconds
            
        Returns:
            Execution result
            
        Raises:
            BlockExecutionError: If all retries fail
        """
        block_id = str(block.id)
        attempt = 0
        last_error = None
        
        while attempt <= max_retries:
            try:
                if attempt > 0:
                    logger.info(
                        f"Retrying block {block_id} (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(retry_delay)
                
                # Execute block
                await executor_func(block, context)
                
                # Check if execution was successful
                block_state = context.block_states.get(block_id)
                if block_state and block_state.success:
                    if attempt > 0:
                        logger.info(
                            f"Block {block_id} succeeded after {attempt} retries"
                        )
                    return {"success": True}
                
                # Execution failed
                error_msg = block_state.error if block_state else "Unknown error"
                last_error = BlockExecutionError(
                    error_msg,
                    block_id=block_id,
                    block_type=block.type
                )
                
                attempt += 1
                
            except Exception as e:
                logger.error(
                    f"Block {block_id} execution error (attempt {attempt + 1}): {str(e)}",
                    exc_info=True
                )
                last_error = e
                attempt += 1
        
        # All retries failed
        logger.error(
            f"Block {block_id} failed after {max_retries + 1} attempts"
        )
        raise last_error
    
    @staticmethod
    def format_error_response(
        error: Exception,
        context: Optional[ExecutionContext] = None,
        include_stack_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Format error as response dictionary.
        
        Args:
            error: Exception that occurred
            context: Execution context (optional)
            include_stack_trace: Whether to include stack trace
            
        Returns:
            Formatted error response
        """
        error_response = {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add context information if available
        if context:
            error_response["execution_id"] = context.execution_id
            error_response["workflow_id"] = context.workflow_id
        
        # Add specific error details
        if isinstance(error, BlockExecutionError):
            error_response["block_id"] = error.block_id
            error_response["block_type"] = error.block_type
        
        elif isinstance(error, ExecutionTimeoutError):
            error_response["timeout"] = True
        
        # Add stack trace if requested
        if include_stack_trace:
            error_response["stack_trace"] = traceback.format_exc()
        
        return error_response
    
    @staticmethod
    def log_error(
        error: Exception,
        context: Optional[ExecutionContext] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """
        Log error with context information.
        
        Args:
            error: Exception that occurred
            context: Execution context (optional)
            additional_info: Additional information to log
        """
        error_info = {
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if context:
            error_info["execution_id"] = context.execution_id
            error_info["workflow_id"] = context.workflow_id
            error_info["user_id"] = context.user_id
        
        if additional_info:
            error_info.update(additional_info)
        
        logger.error(
            f"Execution error: {error_info}",
            exc_info=True
        )
    
    @staticmethod
    def handle_block_error(
        block_id: str,
        block_type: str,
        error: Exception,
        context: ExecutionContext,
        stop_on_error: bool = True
    ):
        """
        Handle block execution error.
        
        Args:
            block_id: Block identifier
            block_type: Block type
            error: Exception that occurred
            context: Execution context
            stop_on_error: Whether to stop workflow execution on error
        """
        # Log error
        ErrorHandler.log_error(
            error,
            context=context,
            additional_info={
                "block_id": block_id,
                "block_type": block_type,
            }
        )
        
        # Update context
        if stop_on_error:
            context.status = "failed"
            context.error_message = f"Block {block_id} failed: {str(error)}"
        
        # Add error to block state
        if block_id in context.block_states:
            block_state = context.block_states[block_id]
            block_state.executed = True
            block_state.success = False
            block_state.error = str(error)
    
    @staticmethod
    def handle_workflow_error(
        error: Exception,
        context: ExecutionContext
    ):
        """
        Handle workflow-level error.
        
        Args:
            error: Exception that occurred
            context: Execution context
        """
        # Log error
        ErrorHandler.log_error(error, context=context)
        
        # Update context
        context.status = "failed"
        context.error_message = str(error)
        context.completed_at = datetime.utcnow()
    
    @staticmethod
    def is_recoverable_error(error: Exception) -> bool:
        """
        Check if error is recoverable (can be retried).
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is recoverable
        """
        # Network errors, timeouts, and temporary failures are recoverable
        recoverable_types = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        
        if isinstance(error, recoverable_types):
            return True
        
        # Check error message for recoverable patterns
        error_msg = str(error).lower()
        recoverable_patterns = [
            "timeout",
            "connection",
            "temporary",
            "rate limit",
            "too many requests",
        ]
        
        return any(pattern in error_msg for pattern in recoverable_patterns)
    
    @staticmethod
    def get_retry_strategy(error: Exception) -> Dict[str, Any]:
        """
        Get retry strategy for error.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Dict with retry configuration:
                - should_retry: Whether to retry
                - max_retries: Maximum number of retries
                - retry_delay: Delay between retries
        """
        if not ErrorHandler.is_recoverable_error(error):
            return {
                "should_retry": False,
                "max_retries": 0,
                "retry_delay": 0,
            }
        
        # Default retry strategy for recoverable errors
        return {
            "should_retry": True,
            "max_retries": 3,
            "retry_delay": 2.0,  # seconds
        }
    
    @staticmethod
    def create_error_summary(context: ExecutionContext) -> Dict[str, Any]:
        """
        Create error summary from execution context.
        
        Args:
            context: Execution context
            
        Returns:
            Dict containing error summary
        """
        # Collect all errors from block states
        block_errors = []
        for block_id, block_state in context.block_states.items():
            if block_state.executed and not block_state.success:
                block_errors.append({
                    "block_id": block_id,
                    "block_type": block_state.block_type,
                    "error": block_state.error,
                })
        
        return {
            "workflow_error": context.error_message,
            "block_errors": block_errors,
            "total_errors": len(block_errors),
            "status": context.status,
        }
