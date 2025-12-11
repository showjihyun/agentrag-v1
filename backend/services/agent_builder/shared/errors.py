"""
Domain Errors

Custom exception classes for the agent builder domain.
"""

from typing import Optional, Dict, Any


class DomainError(Exception):
    """Base class for domain errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(DomainError):
    """Raised when validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(DomainError):
    """Raised when an entity is not found."""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
    ):
        super().__init__(
            f"{entity_type} not found: {entity_id}",
            "NOT_FOUND",
            {"entity_type": entity_type, "entity_id": entity_id},
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class ConflictError(DomainError):
    """Raised when there's a conflict (e.g., duplicate)."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "CONFLICT", details)


class AuthorizationError(DomainError):
    """Raised when user is not authorized."""
    
    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "UNAUTHORIZED", details)


class ExecutionError(DomainError):
    """Raised when execution fails."""
    
    def __init__(
        self,
        message: str,
        node_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "EXECUTION_ERROR", details)
        self.node_id = node_id


class TimeoutError(DomainError):
    """Raised when operation times out."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[int] = None,
    ):
        super().__init__(
            message,
            "TIMEOUT",
            {"timeout_seconds": timeout_seconds} if timeout_seconds else {},
        )
        self.timeout_seconds = timeout_seconds
