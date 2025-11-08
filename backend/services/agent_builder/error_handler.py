"""
Error Handler for Agent Builder.

Provides user-friendly error messages, recovery suggestions,
and error reporting to administrators.
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    TIMEOUT = "timeout"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    EXECUTION = "execution"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentBuilderError(Exception):
    """Base exception for Agent Builder errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.recovery_suggestions = recovery_suggestions or []


class ErrorHandler:
    """Handles errors and provides user-friendly messages."""
    
    # Error message templates
    ERROR_MESSAGES = {
        # Validation errors
        "invalid_input": "The provided input is invalid. Please check your data and try again.",
        "missing_required_field": "Required field '{field}' is missing.",
        "invalid_field_type": "Field '{field}' has an invalid type. Expected {expected}, got {actual}.",
        "invalid_field_value": "Field '{field}' has an invalid value: {value}.",
        
        # Authentication errors
        "authentication_failed": "Authentication failed. Please check your credentials.",
        "token_expired": "Your session has expired. Please log in again.",
        "invalid_token": "Invalid authentication token.",
        
        # Authorization errors
        "permission_denied": "You don't have permission to perform this action.",
        "resource_access_denied": "You don't have access to this resource.",
        
        # Not found errors
        "agent_not_found": "Agent not found. It may have been deleted.",
        "workflow_not_found": "Workflow not found. It may have been deleted.",
        "block_not_found": "Block not found. It may have been deleted.",
        "knowledgebase_not_found": "Knowledgebase not found. It may have been deleted.",
        "execution_not_found": "Execution not found.",
        
        # Conflict errors
        "agent_name_exists": "An agent with this name already exists.",
        "workflow_name_exists": "A workflow with this name already exists.",
        "block_name_exists": "A block with this name already exists.",
        
        # Rate limit errors
        "rate_limit_exceeded": "Rate limit exceeded. Please try again in {retry_after} seconds.",
        
        # Quota errors
        "execution_quota_exceeded": "Execution quota exceeded. Please upgrade your plan or wait for quota reset.",
        "token_quota_exceeded": "Token quota exceeded. Please upgrade your plan or wait for quota reset.",
        
        # Timeout errors
        "execution_timeout": "Execution timed out after {timeout} seconds.",
        "request_timeout": "Request timed out. Please try again.",
        
        # External service errors
        "llm_service_unavailable": "LLM service is temporarily unavailable. Please try again later.",
        "vector_db_unavailable": "Vector database is temporarily unavailable. Please try again later.",
        "web_search_failed": "Web search service failed. Please try again later.",
        
        # Database errors
        "database_error": "Database error occurred. Please try again.",
        "connection_error": "Failed to connect to the database. Please try again later.",
        
        # Execution errors
        "workflow_execution_failed": "Workflow execution failed: {error}",
        "agent_execution_failed": "Agent execution failed: {error}",
        "block_execution_failed": "Block execution failed: {error}",
        "tool_execution_failed": "Tool '{tool}' execution failed: {error}",
        
        # Unknown errors
        "unknown_error": "An unexpected error occurred. Please try again or contact support.",
    }
    
    # Recovery suggestions
    RECOVERY_SUGGESTIONS = {
        ErrorCategory.VALIDATION: [
            "Check that all required fields are filled in",
            "Verify that field values match the expected format",
            "Review the API documentation for correct input format"
        ],
        ErrorCategory.AUTHENTICATION: [
            "Log out and log in again",
            "Clear your browser cache and cookies",
            "Contact support if the problem persists"
        ],
        ErrorCategory.AUTHORIZATION: [
            "Request access from the resource owner",
            "Check that you have the correct permissions",
            "Contact an administrator for help"
        ],
        ErrorCategory.NOT_FOUND: [
            "Verify the resource ID is correct",
            "Check if the resource was recently deleted",
            "Try refreshing the page"
        ],
        ErrorCategory.CONFLICT: [
            "Choose a different name",
            "Check for existing resources with the same name",
            "Delete the conflicting resource if appropriate"
        ],
        ErrorCategory.RATE_LIMIT: [
            "Wait a few moments before trying again",
            "Reduce the frequency of your requests",
            "Consider upgrading your plan for higher limits"
        ],
        ErrorCategory.QUOTA_EXCEEDED: [
            "Wait for your quota to reset",
            "Upgrade your plan for higher quotas",
            "Optimize your usage to reduce quota consumption"
        ],
        ErrorCategory.TIMEOUT: [
            "Try again with a simpler query",
            "Break down complex workflows into smaller steps",
            "Contact support if timeouts persist"
        ],
        ErrorCategory.EXTERNAL_SERVICE: [
            "Wait a few moments and try again",
            "Check the service status page",
            "Contact support if the problem persists"
        ],
        ErrorCategory.DATABASE: [
            "Try again in a few moments",
            "Contact support if the problem persists"
        ],
        ErrorCategory.EXECUTION: [
            "Review the execution logs for details",
            "Check that all required tools are configured",
            "Verify that input data is valid",
            "Try executing with simpler inputs first"
        ],
        ErrorCategory.UNKNOWN: [
            "Try again",
            "Contact support with error details",
            "Check the system status page"
        ]
    }
    
    @classmethod
    def get_user_friendly_message(
        cls,
        error_code: str,
        **kwargs
    ) -> str:
        """
        Get user-friendly error message.
        
        Args:
            error_code: Error code
            **kwargs: Template variables
            
        Returns:
            User-friendly error message
        """
        template = cls.ERROR_MESSAGES.get(error_code, cls.ERROR_MESSAGES["unknown_error"])
        
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    
    @classmethod
    def get_recovery_suggestions(
        cls,
        category: ErrorCategory
    ) -> List[str]:
        """
        Get recovery suggestions for error category.
        
        Args:
            category: Error category
            
        Returns:
            List of recovery suggestions
        """
        return cls.RECOVERY_SUGGESTIONS.get(category, cls.RECOVERY_SUGGESTIONS[ErrorCategory.UNKNOWN])
    
    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle exception and return error response.
        
        Args:
            exception: Exception to handle
            context: Additional context
            
        Returns:
            Error response dict
        """
        # Check if it's an AgentBuilderError
        if isinstance(exception, AgentBuilderError):
            return {
                "error": exception.message,
                "category": exception.category.value,
                "severity": exception.severity.value,
                "details": exception.details,
                "recovery_suggestions": exception.recovery_suggestions or cls.get_recovery_suggestions(exception.category)
            }
        
        # Handle common exception types
        error_code = "unknown_error"
        category = ErrorCategory.UNKNOWN
        severity = ErrorSeverity.MEDIUM
        details = {}
        
        if isinstance(exception, ValueError):
            error_code = "invalid_input"
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.LOW
        elif isinstance(exception, KeyError):
            error_code = "missing_required_field"
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.LOW
            details = {"field": str(exception)}
        elif isinstance(exception, PermissionError):
            error_code = "permission_denied"
            category = ErrorCategory.AUTHORIZATION
            severity = ErrorSeverity.MEDIUM
        elif isinstance(exception, TimeoutError):
            error_code = "request_timeout"
            category = ErrorCategory.TIMEOUT
            severity = ErrorSeverity.MEDIUM
        elif isinstance(exception, ConnectionError):
            error_code = "connection_error"
            category = ErrorCategory.DATABASE
            severity = ErrorSeverity.HIGH
        
        # Log error
        logger.error(
            f"Error handled: {error_code} - {str(exception)}",
            exc_info=True,
            extra={"context": context}
        )
        
        # Build response
        message = cls.get_user_friendly_message(error_code)
        suggestions = cls.get_recovery_suggestions(category)
        
        return {
            "error": message,
            "category": category.value,
            "severity": severity.value,
            "details": {
                **details,
                "original_error": str(exception),
                **(context or {})
            },
            "recovery_suggestions": suggestions
        }
    
    @classmethod
    def report_to_admin(
        cls,
        error: Exception,
        user_id: str,
        context: Dict[str, Any]
    ):
        """
        Report error to administrators.
        
        This would typically send an email or notification.
        For now, we just log it with high severity.
        
        Args:
            error: Exception that occurred
            user_id: User who encountered the error
            context: Error context
        """
        logger.critical(
            f"Critical error reported for user {user_id}: {str(error)}",
            exc_info=True,
            extra={
                "user_id": user_id,
                "context": context,
                "error_type": type(error).__name__
            }
        )
        
        # TODO: Implement email notification to admins
        # TODO: Implement Slack/Discord webhook notification
        # TODO: Implement error tracking service integration (e.g., Sentry)


# Convenience functions
def handle_error(exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle error and return response."""
    return ErrorHandler.handle_exception(exception, context)


def report_critical_error(error: Exception, user_id: str, context: Dict[str, Any]):
    """Report critical error to administrators."""
    ErrorHandler.report_to_admin(error, user_id, context)
