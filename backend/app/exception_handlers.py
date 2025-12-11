"""
Exception handlers for the FastAPI application.
"""

from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app):
    """Register all exception handlers."""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            f"[{request_id}] HTTP {exc.status_code}: {exc.detail} - "
            f"Path: {request.url.path}"
        )

        from backend.models.error import ErrorResponse

        # Handle detail being a dict or string
        detail_str = exc.detail
        if isinstance(exc.detail, dict):
            error_msg = exc.detail.get('error', 'HTTP error')
            detail_str = str(exc.detail)
        else:
            error_msg = str(exc.detail) if exc.detail else "HTTP error"
            detail_str = str(exc.detail)

        error_response = ErrorResponse(
            error=error_msg,
            error_type="HTTPException",
            detail=detail_str,
            status_code=exc.status_code,
            timestamp=datetime.now().isoformat(),
            path=str(request.url.path),
            request_id=request_id,
        )

        return JSONResponse(
            status_code=exc.status_code, content=error_response.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            f"[{request_id}] Validation error: {exc.errors()} - "
            f"Path: {request.url.path}"
        )

        from backend.models.error import ValidationErrorResponse

        validation_errors = [
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]

        error_response = ValidationErrorResponse(
            timestamp=datetime.now().isoformat(), validation_errors=validation_errors
        )

        return JSONResponse(status_code=422, content=error_response.model_dump())

    @app.exception_handler(Exception)
    async def api_exception_handler(request: Request, exc: Exception):
        """Handle custom API exceptions."""
        from backend.exceptions import APIException

        request_id = getattr(request.state, "request_id", "unknown")

        # Check if it's our custom APIException
        if isinstance(exc, APIException):
            logger.warning(
                f"[{request_id}] API Exception: {exc.error_code} - {exc.message}",
                extra={"details": exc.details},
            )

            response_data = exc.to_response_dict()
            response_data["request_id"] = request_id
            response_data["path"] = str(request.url.path)

            return JSONResponse(status_code=exc.status_code, content=response_data)

        # For other exceptions, use existing error handling
        logger.error(f"[{request_id}] Unhandled exception: {exc}", exc_info=True)

        from backend.models.error import ErrorResponse

        error_response = ErrorResponse(
            error="Internal server error",
            error_type=type(exc).__name__,
            detail=str(exc),
            status_code=500,
            timestamp=datetime.now().isoformat(),
            path=str(request.url.path),
            request_id=request_id,
        )

        return JSONResponse(status_code=500, content=error_response.model_dump())
