"""
Custom exceptions for the RAG system.

This module defines all custom exceptions used throughout the application,
organized by functional area with enhanced error context support.

Exception Hierarchy:
    RAGException (base)
    ├── HybridRAGException
    │   ├── StaticRAGException
    │   ├── RoutingException
    │   └── EscalationException
    ├── ServiceException
    │   ├── EmbeddingException
    │   ├── VectorSearchException
    │   ├── LLMException
    │   └── CacheException
    ├── DocumentException
    │   ├── DocumentUploadException
    │   └── DocumentProcessingException
    └── DatabaseException
        ├── ConnectionException
        └── QueryException
"""


# Base Exceptions
class RAGException(Exception):
    """
    Base exception for all RAG system errors.

    Provides enhanced error context with details dictionary
    and structured error responses for API.
    """

    def __init__(self, message: str, details: dict = None, cause: Exception = None):
        """
        Initialize exception with message and optional context.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
            cause: Optional original exception that caused this error
        """
        self.message = message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """
        Convert exception to dictionary for API responses.

        Returns:
            Dictionary with error_type, message, and details
        """
        result = {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def __str__(self) -> str:
        """String representation with details."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


# Hybrid RAG Exceptions
class HybridRAGException(RAGException):
    """Base exception for Hybrid RAG system errors."""

    pass


class StaticRAGException(HybridRAGException):
    """Exception raised when Static RAG pipeline encounters an error."""

    pass


class RoutingException(HybridRAGException):
    """Exception raised when query routing fails."""

    pass


class EscalationException(HybridRAGException):
    """Exception raised when escalation from Static to Agentic fails."""

    pass


# Service Exceptions
class ServiceException(RAGException):
    """Base exception for service-level errors."""

    pass


class EmbeddingException(ServiceException):
    """Exception raised when embedding generation fails."""

    pass


class VectorSearchException(ServiceException):
    """Exception raised when vector search fails."""

    pass


class LLMException(ServiceException):
    """Exception raised when LLM generation fails."""

    pass


class CacheException(ServiceException):
    """Exception raised when cache operations fail."""

    pass


# Document Processing Exceptions
class DocumentException(RAGException):
    """Base exception for document processing errors."""

    pass


class DocumentUploadException(DocumentException):
    """Exception raised when document upload fails."""

    pass


class DocumentProcessingException(DocumentException):
    """Exception raised when document processing fails."""

    pass


# Database Exceptions
class DatabaseException(RAGException):
    """Base exception for database errors."""

    pass


class ConnectionException(DatabaseException):
    """Exception raised when database connection fails."""

    pass


class QueryException(DatabaseException):
    """Exception raised when database query fails."""

    pass


# ============================================================================
# API Exception Hierarchy (HTTP Status Code Based)
# ============================================================================

from typing import Optional, Dict, Any
from datetime import datetime


class APIException(RAGException):
    """
    Base exception for all API errors with HTTP status codes.

    Provides standardized error structure for FastAPI responses.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.timestamp = datetime.now().isoformat()

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert exception to API response dictionary."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code,
            "timestamp": self.timestamp,
        }


class ValidationException(APIException):
    """Validation error (422)."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message, status_code=422, details={"field": field} if field else {}
        )


class ResourceNotFoundException(APIException):
    """Resource not found error (404)."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=404,
            details={"resource": resource, "id": identifier},
        )


class QuotaExceededException(APIException):
    """Quota exceeded error (413)."""

    def __init__(self, quota_type: str, limit: int, current: int):
        super().__init__(
            message=f"{quota_type} quota exceeded: {current}/{limit}",
            status_code=413,
            details={"quota_type": quota_type, "limit": limit, "current": current},
        )


class AuthenticationException(APIException):
    """Authentication error (401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class AuthorizationException(APIException):
    """Authorization error (403)."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, status_code=403)


class RateLimitException(APIException):
    """Rate limit exceeded error (429)."""

    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            status_code=429,
            details={"limit": limit, "window": window},
        )


class ProcessingException(APIException):
    """Processing error (422)."""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=422,
            details={"operation": operation} if operation else {},
        )


class ExternalServiceException(APIException):
    """External service error (502)."""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=502,
            details={"service": service},
        )
