"""
Standardized Error Handler

Provides consistent error handling across the application.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class ErrorCode(str, Enum):
    """Standard error codes"""
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class AppError(Exception):
    """Base application error"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or self._get_user_friendly_message()
        super().__init__(self.message)
    
    def _get_user_friendly_message(self) -> str:
        """Get user-friendly error message"""
        messages = {
            ErrorCode.VALIDATION_ERROR: "입력 데이터가 올바르지 않습니다.",
            ErrorCode.AUTHENTICATION_ERROR: "인증에 실패했습니다. 다시 로그인해주세요.",
            ErrorCode.AUTHORIZATION_ERROR: "이 작업을 수행할 권한이 없습니다.",
            ErrorCode.NOT_FOUND: "요청한 리소스를 찾을 수 없습니다.",
            ErrorCode.CONFLICT: "요청이 현재 상태와 충돌합니다.",
            ErrorCode.RATE_LIMIT_EXCEEDED: "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.INTERNAL_ERROR: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.DATABASE_ERROR: "데이터베이스 오류가 발생했습니다.",
            ErrorCode.EXTERNAL_SERVICE_ERROR: "외부 서비스 연결에 실패했습니다.",
            ErrorCode.TIMEOUT_ERROR: "요청 시간이 초과되었습니다.",
        }
        return messages.get(self.code, "알 수 없는 오류가 발생했습니다.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "error": {
                "code": self.code.value,
                "message": self.user_message,
                "details": self.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }


# Specific error classes
class ValidationError(AppError):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(AppError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code=ErrorCode.AUTHENTICATION_ERROR,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(AppError):
    """Authorization error"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            code=ErrorCode.AUTHORIZATION_ERROR,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(AppError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)}
        )


class ConflictError(AppError):
    """Conflict error"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class RateLimitError(AppError):
    """Rate limit exceeded error"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after}
        )


class DatabaseError(AppError):
    """Database error"""
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation} if operation else None
        )


class ExternalServiceError(AppError):
    """External service error"""
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class TimeoutError(AppError):
    """Timeout error"""
    def __init__(self, operation: str, timeout: float):
        super().__init__(
            message=f"Operation timed out: {operation}",
            code=ErrorCode.TIMEOUT_ERROR,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details={"operation": operation, "timeout": timeout}
        )


class ErrorHandler:
    """Centralized error handler"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def handle_error(
        self,
        request: Request,
        error: Exception
    ) -> JSONResponse:
        """
        Handle error and return appropriate response
        
        Args:
            request: FastAPI request
            error: Exception
            
        Returns:
            JSONResponse with error details
        """
        # Get request ID
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Handle AppError
        if isinstance(error, AppError):
            self._log_error(error, request_id, request)
            return JSONResponse(
                status_code=error.status_code,
                content=error.to_dict()
            )
        
        # Handle unexpected errors
        self._log_unexpected_error(error, request_id, request)
        
        # Don't expose internal error details in production
        from backend.config import settings
        if settings.DEBUG:
            error_details = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": self._get_traceback(error)
            }
        else:
            error_details = {}
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    "details": error_details,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "request_id": request_id
                }
            }
        )
    
    def _log_error(self, error: AppError, request_id: str, request: Request):
        """Log application error"""
        self.logger.warning(
            "application_error",
            request_id=request_id,
            error_code=error.code.value,
            message=error.message,
            status_code=error.status_code,
            path=request.url.path,
            method=request.method,
            details=error.details
        )
    
    def _log_unexpected_error(self, error: Exception, request_id: str, request: Request):
        """Log unexpected error"""
        self.logger.error(
            "unexpected_error",
            request_id=request_id,
            error_type=type(error).__name__,
            message=str(error),
            path=request.url.path,
            method=request.method,
            exc_info=True
        )
        
        # Send to Sentry if available
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(error)
        except:
            pass
    
    def _get_traceback(self, error: Exception) -> List[str]:
        """Get error traceback"""
        import traceback
        return traceback.format_exception(type(error), error, error.__traceback__)


# Global error handler
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler"""
    return _error_handler


# Decorator for error handling
def handle_errors(func):
    """Decorator to handle errors in async functions"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AppError:
            raise  # Re-raise AppError
        except Exception as e:
            # Convert to AppError
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise AppError(
                message=f"Error in {func.__name__}: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR
            )
    return wrapper


# Example usage:
"""
from backend.core.errors.error_handler import (
    NotFoundError,
    ValidationError,
    handle_errors
)

@router.get("/workflows/{id}")
@handle_errors
async def get_workflow(id: int, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == id).first()
    if not workflow:
        raise NotFoundError("Workflow", id)
    return workflow

@router.post("/workflows")
async def create_workflow(data: WorkflowCreate):
    if not data.name:
        raise ValidationError(
            "Name is required",
            details={"field": "name"}
        )
    ...
"""
