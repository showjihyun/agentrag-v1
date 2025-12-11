"""Error handling module"""

from backend.core.errors.error_handler import (
    ErrorCode,
    AppError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
    TimeoutError,
    ErrorHandler,
    get_error_handler,
    handle_errors,
)

__all__ = [
    "ErrorCode",
    "AppError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "DatabaseError",
    "ExternalServiceError",
    "TimeoutError",
    "ErrorHandler",
    "get_error_handler",
    "handle_errors",
]
