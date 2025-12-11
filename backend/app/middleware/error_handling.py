"""
Global error handling middleware.
"""

from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


def add_error_handling_middleware(app):
    """Global error handling middleware - catches all unhandled exceptions."""
    
    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(f"[{request_id}] Unhandled error: {e}", exc_info=True)

            from backend.models.error import ErrorResponse

            error_response = ErrorResponse(
                error="Internal server error",
                error_type=type(e).__name__,
                detail=str(e),
                status_code=500,
                timestamp=datetime.now().isoformat(),
                path=str(request.url.path),
                request_id=request_id,
            )

            return JSONResponse(status_code=500, content=error_response.model_dump())
