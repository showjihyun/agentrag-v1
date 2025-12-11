"""
Workflow Execution Error Classes

Standardized error handling for workflow execution.
"""

from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


class WorkflowErrorCode(str, Enum):
    """Standard error codes for workflow execution."""
    
    # Validation errors (1xxx)
    VALIDATION_ERROR = "WF1001"
    INVALID_NODE_TYPE = "WF1002"
    MISSING_REQUIRED_FIELD = "WF1003"
    INVALID_EXPRESSION = "WF1004"
    CYCLE_DETECTED = "WF1005"
    
    # Execution errors (2xxx)
    EXECUTION_FAILED = "WF2001"
    NODE_EXECUTION_FAILED = "WF2002"
    TIMEOUT = "WF2003"
    CANCELLED = "WF2004"
    CONCURRENCY_LIMIT = "WF2005"
    
    # Resource errors (3xxx)
    RESOURCE_NOT_FOUND = "WF3001"
    PERMISSION_DENIED = "WF3002"
    RATE_LIMITED = "WF3003"
    QUOTA_EXCEEDED = "WF3004"
    
    # External service errors (4xxx)
    EXTERNAL_SERVICE_ERROR = "WF4001"
    API_ERROR = "WF4002"
    DATABASE_ERROR = "WF4003"
    LLM_ERROR = "WF4004"
    
    # Internal errors (5xxx)
    INTERNAL_ERROR = "WF5001"
    CONFIGURATION_ERROR = "WF5002"


class WorkflowError(Exception):
    """Base exception for workflow errors."""
    
    def __init__(
        self,
        message: str,
        code: WorkflowErrorCode = WorkflowErrorCode.INTERNAL_ERROR,
        node_id: Optional[str] = None,
        node_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.node_id = node_id
        self.node_type = node_type
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API response."""
        return {
            "error": True,
            "code": self.code.value,
            "message": self.message,
            "node_id": self.node_id,
            "node_type": self.node_type,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        parts = [f"[{self.code.value}] {self.message}"]
        if self.node_id:
            parts.append(f"(node: {self.node_id})")
        if self.cause:
            parts.append(f"caused by: {str(self.cause)}")
        return " ".join(parts)


class ValidationError(WorkflowError):
    """Workflow validation error."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=WorkflowErrorCode.VALIDATION_ERROR,
            **kwargs
        )
        self.field = field
        if field:
            self.details["field"] = field


class NodeExecutionError(WorkflowError):
    """Node execution error."""
    
    def __init__(
        self,
        message: str,
        node_id: str,
        node_type: str,
        input_data: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=WorkflowErrorCode.NODE_EXECUTION_FAILED,
            node_id=node_id,
            node_type=node_type,
            **kwargs
        )
        if input_data is not None:
            # Truncate large input data
            input_str = str(input_data)
            self.details["input_preview"] = input_str[:500] if len(input_str) > 500 else input_str


class TimeoutError(WorkflowError):
    """Workflow or node timeout error."""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=WorkflowErrorCode.TIMEOUT,
            **kwargs
        )
        self.details["timeout_seconds"] = timeout_seconds


class ConcurrencyLimitError(WorkflowError):
    """Concurrency limit exceeded error."""
    
    def __init__(
        self,
        workflow_id: str,
        current_count: int,
        max_count: int,
    ):
        super().__init__(
            message=f"Maximum concurrent executions ({max_count}) reached for workflow",
            code=WorkflowErrorCode.CONCURRENCY_LIMIT,
            details={
                "workflow_id": workflow_id,
                "current_count": current_count,
                "max_count": max_count,
            }
        )


class ExternalServiceError(WorkflowError):
    """External service error (API, database, etc.)."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        status_code: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=WorkflowErrorCode.EXTERNAL_SERVICE_ERROR,
            **kwargs
        )
        self.details["service_name"] = service_name
        if status_code:
            self.details["status_code"] = status_code


class LLMError(WorkflowError):
    """LLM-specific error."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        model: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=WorkflowErrorCode.LLM_ERROR,
            **kwargs
        )
        self.details["provider"] = provider
        if model:
            self.details["model"] = model


class ExpressionError(WorkflowError):
    """Expression evaluation error."""
    
    def __init__(
        self,
        message: str,
        expression: str,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=WorkflowErrorCode.INVALID_EXPRESSION,
            **kwargs
        )
        self.details["expression"] = expression[:200]  # Truncate long expressions


def create_error_response(
    error: Exception,
    node_id: Optional[str] = None,
    node_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create standardized error response from any exception.
    
    Args:
        error: The exception
        node_id: Optional node ID where error occurred
        node_type: Optional node type
        
    Returns:
        Standardized error dictionary
    """
    if isinstance(error, WorkflowError):
        return error.to_dict()
    
    # Convert generic exception to WorkflowError format
    return {
        "error": True,
        "code": WorkflowErrorCode.INTERNAL_ERROR.value,
        "message": str(error),
        "error_type": type(error).__name__,
        "node_id": node_id,
        "node_type": node_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
