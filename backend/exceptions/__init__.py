"""
Custom exceptions for the RAG system.

This module provides RAG-specific exceptions and re-exports API exceptions
from the main exceptions module for backward compatibility.

For API exceptions, use backend.exceptions directly:
    from backend.exceptions import APIException, ResourceNotFoundException

For RAG-specific exceptions, use this module:
    from backend.exceptions import RAGException, HybridRAGException
"""

from typing import Optional, Dict, Any
from datetime import datetime


# =============================================================================
# RAG-Specific Exceptions (Domain Exceptions)
# =============================================================================

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


# =============================================================================
# Agent Builder Exceptions
# =============================================================================

class AgentBuilderException(RAGException):
    """Base exception for Agent Builder errors."""
    pass


class WorkflowExecutionException(AgentBuilderException):
    """Exception raised when workflow execution fails."""
    pass


class BlockExecutionException(AgentBuilderException):
    """Exception raised when block execution fails."""
    pass


class ToolExecutionException(AgentBuilderException):
    """Exception raised when tool execution fails."""
    pass


# =============================================================================
# Re-export from main exceptions module (lazy import to avoid circular import)
# =============================================================================

def __getattr__(name):
    """Lazy import to avoid circular imports."""
    # Import from backend.exceptions (the file, not this package)
    import importlib.util
    import os
    
    # Get the path to backend/exceptions.py
    current_dir = os.path.dirname(os.path.dirname(__file__))
    exceptions_file = os.path.join(current_dir, "exceptions.py")
    
    if os.path.exists(exceptions_file):
        spec = importlib.util.spec_from_file_location("backend_exceptions", exceptions_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, name):
            return getattr(module, name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Define what's available for import
__all__ = [
    # RAG Exceptions
    "RAGException",
    "HybridRAGException",
    "StaticRAGException",
    "RoutingException",
    "EscalationException",
    "ServiceException",
    "EmbeddingException",
    "VectorSearchException",
    "LLMException",
    "CacheException",
    "DocumentException",
    "DocumentUploadException",
    "DocumentProcessingException",
    "DatabaseException",
    "ConnectionException",
    "QueryException",
    # Agent Builder Exceptions
    "AgentBuilderException",
    "WorkflowExecutionException",
    "BlockExecutionException",
    "ToolExecutionException",
    # Re-exported from backend.exceptions (via __getattr__)
    "APIException",
    "AuthenticationException",
    "AuthorizationException",
    "ValidationException",
    "ResourceNotFoundException",
    "ResourceAlreadyExistsException",
    "ResourceConflictException",
    "QuotaExceededException",
    "RateLimitExceededException",
    "ExternalServiceException",
    "ServiceTimeoutException",
    "ServiceUnavailableException",
    "LLMServiceException",
    "ToolExecutionError",
    "ToolNotFoundError",
    "WorkflowPausedException",
    "WorkflowValidationException",
    "WorkflowNotFoundException",
    "AgentNotFoundException",
]
