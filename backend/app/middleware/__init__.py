"""
Middleware components for the FastAPI application.
"""

from backend.app.middleware.security import add_security_headers_middleware
from backend.app.middleware.logging import add_logging_middleware
from backend.app.middleware.request_id import add_request_id_middleware
from backend.app.middleware.rate_limit import add_rate_limit_middleware
from backend.app.middleware.error_handling import add_error_handling_middleware

__all__ = [
    "add_security_headers_middleware",
    "add_logging_middleware", 
    "add_request_id_middleware",
    "add_rate_limit_middleware",
    "add_error_handling_middleware",
]


def register_all_middleware(app):
    """
    Register all middleware in the correct order.
    
    Order matters! First registered = Last executed.
    Execution order: error_handling -> logging -> request_id -> rate_limit
    """
    # Error handling (outermost - catches all errors)
    add_error_handling_middleware(app)
    
    # Logging middleware
    add_logging_middleware(app)
    
    # Request ID middleware
    add_request_id_middleware(app)
    
    # Rate limiting (innermost - right before endpoint)
    add_rate_limit_middleware(app)
    
    # Security headers
    add_security_headers_middleware(app)
