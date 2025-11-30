"""
Global Exception Handlers

Provides centralized exception handling for FastAPI application.
All exceptions are converted to standardized API response format.
"""

from typing import Any, Dict, Optional
from datetime import datetime
import logging
import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from backend.core.api_response import ErrorCode, ErrorDetail, ResponseMeta
from backend.exceptions import (
    APIException,
    AuthenticationException,
    AuthorizationException,
    ValidationException,
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    ResourceConflictException,
    BusinessRuleException,
    QuotaExceededException,
    RateLimitExceededException,
    ExternalServiceException,
    DatabaseException,
    WorkflowPausedException,
    WorkflowValidationException,
)


logger = logging.getLogger(__name__)


def _build_error_response(
    error_code: str,
    message: str,
    status_code: int,
    request: Request,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build standardized error response."""
    request_id = getattr(request.state, "request_id", None)
    
    return {
        "success": False,
        "data": None,
        "error": {
            "code": error_code,
            "message": message,
            "field": field,
            "details": details,
        },
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "path": str(request.url.path),
        },
    }


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log based on severity
    if exc.status_code >= 500:
        logger.error(
            f"[{request_id}] API Exception: {exc.error_code} - {exc.message}",
            extra={"details": exc.details, "status_code": exc.status_code},
        )
    else:
        logger.warning(
            f"[{request_id}] API Exception: {exc.error_code} - {exc.message}",
            extra={"details": exc.details, "status_code": exc.status_code},
        )
    
    response_data = _build_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        request=request,
        field=exc.field,
        details=exc.details,
    )
    
    return JSONResponse(status_code=exc.status_code, content=response_data)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"[{request_id}] HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}"
    )
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: ErrorCode.VALIDATION_FAILED,
        401: ErrorCode.AUTH_INVALID_CREDENTIALS,
        403: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        405: ErrorCode.OPERATION_NOT_ALLOWED,
        409: ErrorCode.RESOURCE_CONFLICT,
        422: ErrorCode.VALIDATION_FAILED,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        504: ErrorCode.EXTERNAL_SERVICE_TIMEOUT,
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    # Handle detail being a dict or string
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", exc.detail.get("error", str(exc.detail)))
        details = exc.detail
    else:
        message = str(exc.detail) if exc.detail else "An error occurred"
        details = None
    
    response_data = _build_error_response(
        error_code=error_code.value,
        message=message,
        status_code=exc.status_code,
        request=request,
        details=details,
    )
    
    return JSONResponse(status_code=exc.status_code, content=response_data)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"[{request_id}] Validation error: {exc.errors()} - Path: {request.url.path}"
    )
    
    # Format validation errors
    validation_errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input"),
        })
    
    # Get first error for main message
    first_error = validation_errors[0] if validation_errors else {}
    main_message = first_error.get("message", "Validation failed")
    main_field = first_error.get("field")
    
    response_data = _build_error_response(
        error_code=ErrorCode.VALIDATION_FAILED.value,
        message=main_message,
        status_code=422,
        request=request,
        field=main_field,
        details={"validation_errors": validation_errors},
    )
    
    return JSONResponse(status_code=422, content=response_data)


async def pydantic_validation_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic ValidationError (from model validation)."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"[{request_id}] Pydantic validation error: {exc.errors()} - Path: {request.url.path}"
    )
    
    validation_errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
        })
    
    first_error = validation_errors[0] if validation_errors else {}
    
    response_data = _build_error_response(
        error_code=ErrorCode.VALIDATION_FAILED.value,
        message=first_error.get("message", "Validation failed"),
        status_code=422,
        request=request,
        field=first_error.get("field"),
        details={"validation_errors": validation_errors},
    )
    
    return JSONResponse(status_code=422, content=response_data)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log full traceback for debugging
    logger.error(
        f"[{request_id}] Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
    )
    
    # In production, don't expose internal error details
    from backend.config import settings
    
    if settings.DEBUG:
        message = f"{type(exc).__name__}: {str(exc)}"
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n"),
        }
    else:
        message = "An unexpected error occurred"
        details = None
    
    response_data = _build_error_response(
        error_code=ErrorCode.UNEXPECTED_ERROR.value,
        message=message,
        status_code=500,
        request=request,
        details=details,
    )
    
    return JSONResponse(status_code=500, content=response_data)


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.
    
    Usage:
        from backend.core.exception_handlers import register_exception_handlers
        
        app = FastAPI()
        register_exception_handlers(app)
    """
    # Custom API exceptions
    app.add_exception_handler(APIException, api_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
