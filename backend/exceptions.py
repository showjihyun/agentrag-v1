"""Custom exceptions for the application."""

from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.core.api_response import ErrorCode


class APIException(Exception):
    """
    Base exception for API errors.
    
    Provides standardized error response format with:
    - HTTP status code
    - Error code for programmatic handling
    - Human-readable message
    - Optional details for debugging
    
    Usage:
        raise APIException(
            status_code=404,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Document not found",
            details={"document_id": "doc123"}
        )
    """
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code if isinstance(error_code, str) else error_code.value
        self.message = message
        self.details = details or {}
        self.field = field
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)
    
    def to_response_dict(self) -> Dict[str, Any]:
        """Convert exception to standardized response dictionary."""
        return {
            "success": False,
            "data": None,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "field": self.field,
                "details": self.details,
            },
            "meta": {
                "timestamp": self.timestamp,
                "version": "1.0",
            }
        }


# ============================================================================
# Authentication Exceptions
# ============================================================================

class AuthenticationException(APIException):
    """Base exception for authentication errors."""
    
    def __init__(
        self,
        error_code: str = ErrorCode.AUTH_INVALID_CREDENTIALS,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=401,
            error_code=error_code,
            message=message,
            details=details,
        )


class InvalidCredentialsException(AuthenticationException):
    """Invalid username or password."""
    
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(
            error_code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message=message,
        )


class TokenExpiredException(AuthenticationException):
    """JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message=message,
        )


class InvalidTokenException(AuthenticationException):
    """JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(
            error_code=ErrorCode.AUTH_TOKEN_INVALID,
            message=message,
        )


class InactiveAccountException(AuthenticationException):
    """User account is inactive."""
    
    def __init__(self, message: str = "Account is inactive"):
        super().__init__(
            error_code=ErrorCode.AUTH_ACCOUNT_INACTIVE,
            message=message,
        )


class AccountLockedException(AuthenticationException):
    """User account is locked."""
    
    def __init__(self, message: str = "Account is locked", unlock_time: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.AUTH_ACCOUNT_LOCKED,
            message=message,
            details={"unlock_time": unlock_time} if unlock_time else None,
        )


# ============================================================================
# Authorization Exceptions
# ============================================================================

class AuthorizationException(APIException):
    """Base exception for authorization errors."""
    
    def __init__(
        self,
        message: str = "Access denied",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        required_permission: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        if required_permission:
            details["required_permission"] = required_permission
        
        super().__init__(
            status_code=403,
            error_code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message=message,
            details=details if details else None,
        )


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationException(APIException):
    """Base exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: str = ErrorCode.VALIDATION_FAILED,
    ):
        super().__init__(
            status_code=422,
            error_code=error_code,
            message=message,
            details=details,
            field=field,
        )


class RequiredFieldException(ValidationException):
    """Required field is missing."""
    
    def __init__(self, field: str):
        super().__init__(
            message=f"Field '{field}' is required",
            field=field,
            error_code=ErrorCode.VALIDATION_REQUIRED_FIELD,
        )


class InvalidFormatException(ValidationException):
    """Field has invalid format."""
    
    def __init__(self, field: str, expected_format: str):
        super().__init__(
            message=f"Field '{field}' has invalid format. Expected: {expected_format}",
            field=field,
            error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
            details={"expected_format": expected_format},
        )


class DuplicateValueException(ValidationException):
    """Value already exists."""
    
    def __init__(self, field: str, value: Any):
        super().__init__(
            message=f"Value for '{field}' already exists",
            field=field,
            error_code=ErrorCode.VALIDATION_DUPLICATE_VALUE,
            details={"duplicate_value": str(value)},
        )


# ============================================================================
# Resource Exceptions
# ============================================================================

class ResourceNotFoundException(APIException):
    """Resource not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
    ):
        super().__init__(
            status_code=404,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message or f"{resource_type} not found: {resource_id}",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


class ResourceAlreadyExistsException(APIException):
    """Resource already exists."""
    
    def __init__(
        self,
        resource_type: str,
        identifier: str,
        message: Optional[str] = None,
    ):
        super().__init__(
            status_code=409,
            error_code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message=message or f"{resource_type} already exists: {identifier}",
            details={
                "resource_type": resource_type,
                "identifier": identifier,
            },
        )


class ResourceConflictException(APIException):
    """Resource conflict (e.g., concurrent modification)."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
    ):
        super().__init__(
            status_code=409,
            error_code=ErrorCode.RESOURCE_CONFLICT,
            message=message or f"Conflict updating {resource_type}: {resource_id}",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


# ============================================================================
# Workflow Exceptions
# ============================================================================

class WorkflowPausedException(APIException):
    """Exception raised when workflow needs to pause for human approval."""
    
    def __init__(
        self,
        approval_id: str,
        message: str = "Workflow paused for human approval",
        node_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.approval_id = approval_id
        self.node_id = node_id
        self.data = data
        super().__init__(
            status_code=202,
            error_code=ErrorCode.WORKFLOW_INVALID_STATE,
            message=message,
            details={
                "approval_id": approval_id,
                "node_id": node_id,
                "data": data,
            },
        )


class WorkflowValidationException(ValidationException):
    """Exception raised when workflow validation fails."""
    
    def __init__(self, errors: List[str], warnings: Optional[List[str]] = None):
        self.errors = errors
        self.warnings = warnings or []
        super().__init__(
            message=f"Workflow validation failed: {', '.join(errors)}",
            details={
                "errors": errors,
                "warnings": self.warnings,
            },
        )


class WorkflowNotFoundException(ResourceNotFoundException):
    """Exception raised when workflow is not found."""
    
    def __init__(self, workflow_id: str):
        super().__init__(
            resource_type="Workflow",
            resource_id=workflow_id,
        )


class AgentNotFoundException(ResourceNotFoundException):
    """Exception raised when agent is not found."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            resource_type="Agent",
            resource_id=agent_id,
        )


class KnowledgebaseNotFoundException(ResourceNotFoundException):
    """Exception raised when knowledgebase is not found."""
    
    def __init__(self, kb_id: str):
        super().__init__(
            resource_type="Knowledgebase",
            resource_id=kb_id,
        )


class InsufficientPermissionsException(AuthorizationException):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, resource_type: str, resource_id: str, action: str):
        super().__init__(
            message=f"Insufficient permissions to {action} {resource_type}: {resource_id}",
            resource_type=resource_type,
            resource_id=resource_id,
            required_permission=action,
        )



# ============================================================================
# Business Logic Exceptions
# ============================================================================

class BusinessRuleException(APIException):
    """Business rule violation."""
    
    def __init__(
        self,
        message: str,
        rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=400,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            message=message,
            details={
                "rule": rule,
                **(details or {}),
            } if rule else details,
        )


class QuotaExceededException(APIException):
    """Quota or limit exceeded."""
    
    def __init__(
        self,
        resource_type: str,
        limit: int,
        current: int,
        message: Optional[str] = None,
    ):
        super().__init__(
            status_code=429,
            error_code=ErrorCode.QUOTA_EXCEEDED,
            message=message or f"{resource_type} quota exceeded",
            details={
                "resource_type": resource_type,
                "limit": limit,
                "current": current,
            },
        )


class RateLimitExceededException(APIException):
    """Rate limit exceeded."""
    
    def __init__(
        self,
        limit: int,
        window: str,
        retry_after: int,
        message: Optional[str] = None,
    ):
        super().__init__(
            status_code=429,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message or f"Rate limit exceeded: {limit} requests per {window}",
            details={
                "limit": limit,
                "window": window,
                "retry_after": retry_after,
            },
        )


# ============================================================================
# External Service Exceptions
# ============================================================================

class ExternalServiceException(APIException):
    """External service error."""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        error_code: str = ErrorCode.EXTERNAL_SERVICE_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=502,
            error_code=error_code,
            message=f"{service_name} error: {message}",
            details={
                "service": service_name,
                **(details or {}),
            },
        )


class ServiceTimeoutException(ExternalServiceException):
    """External service timeout."""
    
    def __init__(self, service_name: str, timeout_seconds: float):
        super().__init__(
            service_name=service_name,
            message=f"Request timed out after {timeout_seconds}s",
            error_code=ErrorCode.EXTERNAL_SERVICE_TIMEOUT,
            details={"timeout_seconds": timeout_seconds},
        )


class ServiceUnavailableException(ExternalServiceException):
    """External service unavailable."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        super().__init__(
            service_name=service_name,
            message=message or "Service is currently unavailable",
            error_code=ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        )


class LLMServiceException(ExternalServiceException):
    """LLM service error."""
    
    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            service_name=f"LLM ({provider})",
            message=message,
            error_code=ErrorCode.LLM_SERVICE_ERROR,
            details=details,
        )


class DatabaseException(APIException):
    """Database error."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            error_code=ErrorCode.DATABASE_ERROR,
            message=f"Database error: {message}",
            details=details,
        )


# ============================================================================
# Tool Execution Exceptions
# ============================================================================

class ToolExecutionError(APIException):
    """Base exception for tool execution errors."""
    
    def __init__(
        self,
        tool_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.tool_name = tool_name
        super().__init__(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            message=f"Tool '{tool_name}' execution failed: {message}",
            details={
                "tool_name": tool_name,
                **(details or {}),
            },
        )


class ToolNotFoundError(ToolExecutionError):
    """Tool not found in registry."""
    
    def __init__(self, tool_name: str):
        super().__init__(
            tool_name=tool_name,
            message="not found in registry",
        )


class ToolConfigurationError(ToolExecutionError):
    """Tool configuration is invalid."""
    
    def __init__(self, tool_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            tool_name=tool_name,
            message=f"Configuration error: {message}",
            details=details,
        )


# ============================================================================
# Agent Execution Exceptions
# ============================================================================

class AgentExecutionError(APIException):
    """Base exception for agent execution errors."""
    
    def __init__(
        self,
        agent_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        super().__init__(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            message=f"Agent '{agent_id}' execution failed: {message}",
            details={
                "agent_id": agent_id,
                **(details or {}),
            },
        )


class AgentNotFoundError(AgentExecutionError):
    """Agent not found."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            message="not found",
        )


# ============================================================================
# Legacy Compatibility (Deprecated - use specific exceptions above)
# ============================================================================

class ResourceNotFoundError(ResourceNotFoundException):
    """
    Resource not found.
    
    Deprecated: Use ResourceNotFoundException instead.
    """
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            resource_type=resource_type,
            resource_id=resource_id,
        )
