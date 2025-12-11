"""
Request ID middleware for request tracing.
"""

import uuid
from fastapi import Request
from backend.core.structured_logging import set_request_context


def add_request_id_middleware(app):
    """Add unique request ID to each request and set logging context."""
    
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Set request context for structured logging
        set_request_context(request_id=request_id)

        # Try to extract user_id from request if authenticated
        try:
            if hasattr(request.state, "user") and request.state.user:
                user_id = str(request.state.user.id)
                set_request_context(user_id=user_id)
        except:
            pass

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
