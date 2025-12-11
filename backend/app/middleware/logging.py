"""
Request logging middleware.
"""

from datetime import datetime
from fastapi import Request
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


def add_logging_middleware(app):
    """Log all requests and responses with timing."""
    
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = datetime.now()

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration:.2f}ms"
            )

            return response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration:.2f}ms",
                exc_info=True,
            )
            raise
