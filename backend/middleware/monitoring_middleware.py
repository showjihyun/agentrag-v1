"""Monitoring middleware for FastAPI."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.monitoring import metrics_collector

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()

        # Extract user ID if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)

        # Process request
        try:
            response = await call_next(request)
            error = None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            error = str(e)
            response = Response(
                content={"error": "Internal server error"}, status_code=500
            )

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Record metrics
        metrics_collector.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            error=error,
        )

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log slow requests
        if duration_ms > 1000:  # > 1 second
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms"
            )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details."""
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code}"
        )

        return response
