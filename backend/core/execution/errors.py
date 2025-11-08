"""Execution engine error classes."""

from typing import Optional


class ExecutionError(Exception):
    """Base exception for execution errors."""
    
    def __init__(
        self,
        message: str,
        execution_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize ExecutionError.
        
        Args:
            message: Error message
            execution_id: Execution identifier
            workflow_id: Workflow identifier
            original_error: Original exception that caused the error
        """
        self.message = message
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.original_error = original_error
        super().__init__(self.message)


class WorkflowNotFoundError(ExecutionError):
    """Exception raised when workflow is not found."""
    pass


class BlockExecutionError(ExecutionError):
    """Exception raised when block execution fails."""
    
    def __init__(
        self,
        message: str,
        block_id: Optional[str] = None,
        block_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize BlockExecutionError.
        
        Args:
            message: Error message
            block_id: Block identifier
            block_type: Block type
            **kwargs: Additional arguments for ExecutionError
        """
        self.block_id = block_id
        self.block_type = block_type
        super().__init__(message, **kwargs)


class CyclicDependencyError(ExecutionError):
    """Exception raised when workflow has cyclic dependencies."""
    pass


class ExecutionTimeoutError(ExecutionError):
    """Exception raised when execution times out."""
    pass


class ConditionEvaluationError(ExecutionError):
    """Exception raised when condition evaluation fails."""
    pass


class LoopExecutionError(ExecutionError):
    """Exception raised when loop execution fails."""
    pass


class ParallelExecutionError(ExecutionError):
    """Exception raised when parallel execution fails."""
    pass
