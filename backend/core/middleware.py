"""
Centralized Middleware Module.

Provides all middleware components in a single, organized module
for better maintainability and consistent request processing.
"""

import asyncio
import time
import uuid
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.core.structured_logging import (
    set_request_context,
    clear_request_context,
    get_logger,
)
from backend.config import settings

logger = get_logger(__name__)


# ============================================================================
# Request Timeout Middleware
# ============================================================================

class RequestTimeoutMiddleware:
    """
    ASGI Middleware for request timeout handling.
    
    Cancels requests that exceed the configured timeout.
    Uses pure ASGI for better performance than BaseHTTPMiddleware.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        timeout_seconds: float = 30.0,
        exclude_paths: list = None
    ):
        self.app = app
        self.timeout_seconds = timeout_seconds
        self.exclude_paths = exclude_paths or [
            "/api/query",  # Streaming endpoints
            "/api/agent-builder/chat",
            "/ws",
            "/health",
        ]
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check if path should be excluded
        path = scope.get("path", "")
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            await self.app(scope, receive, send)
            return
        
        # Apply timeout
        try:
            await asyncio.wait_for(
                self.app(scope, receive, send),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout after {self.timeout_seconds}s",
                path=path,
                timeout_seconds=self.timeout_seconds
            )
            
            # Send timeout response
            response = Response(
                content='{"error": "Request timeout", "status_code": 504}',
                status_code=504,
                media_type="application/json"
            )
            await response(scope, receive, send)


# ============================================================================
# Request Context Middleware (ASGI)
# ============================================================================

class RequestContextMiddleware:
    """
    ASGI Middleware for request context management.
    
    Sets up request ID, timing, and logging context for each request.
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Store in scope for access by other middleware/handlers
        scope["request_id"] = request_id
        scope["start_time"] = start_time
        
        # Set logging context
        set_request_context(request_id=request_id)
        
        # Wrap send to add headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                
                # Add timing header
                duration_ms = (time.time() - start_time) * 1000
                headers.append((b"x-response-time", f"{duration_ms:.2f}ms".encode()))
                
                message["headers"] = headers
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Clear logging context
            clear_request_context()
            
            # Log request completion
            duration_ms = (time.time() - start_time) * 1000
            path = scope.get("path", "")
            method = scope.get("method", "")
            
            if duration_ms > 1000:
                logger.warning(
                    f"Slow request: {method} {path}",
                    method=method,
                    path=path,
                    duration_ms=duration_ms
                )


# ============================================================================
# Prometheus Metrics Middleware
# ============================================================================

class PrometheusMetricsMiddleware:
    """
    ASGI Middleware for Prometheus metrics collection.
    
    Collects:
    - Request count by endpoint, method, status
    - Request duration histogram
    - Active requests gauge
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Setup Prometheus metrics."""
        try:
            from prometheus_client import Counter, Histogram, Gauge
            
            self.request_count = Counter(
                'http_requests_total',
                'Total HTTP requests',
                ['method', 'endpoint', 'status']
            )
            
            self.request_duration = Histogram(
                'http_request_duration_seconds',
                'HTTP request duration',
                ['method', 'endpoint'],
                buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            )
            
            self.active_requests = Gauge(
                'http_active_requests',
                'Active HTTP requests',
                ['method']
            )
            
            self.metrics_enabled = True
            
        except ImportError:
            # Only log prometheus warning in debug mode or if explicitly requested
            import os
            if os.getenv("DEBUG", "false").lower() == "true" or os.getenv("SHOW_PROMETHEUS_WARNING", "false").lower() == "true":
                logger.warning("prometheus_client not installed, metrics disabled")
            self.metrics_enabled = False
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or not self.metrics_enabled:
            await self.app(scope, receive, send)
            return
        
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        
        # Normalize path for metrics (remove IDs)
        endpoint = self._normalize_path(path)
        
        # Track active requests
        self.active_requests.labels(method=method).inc()
        
        start_time = time.time()
        status_code = 500  # Default if error
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            self.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            self.active_requests.labels(method=method).dec()
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders."""
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{id}',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+(?=/|$)', '/{id}', path)
        
        return path


# ============================================================================
# Security Headers Middleware
# ============================================================================

class SecurityHeadersMiddleware:
    """
    ASGI Middleware for security headers.
    
    Adds security headers to all responses:
    - Content-Security-Policy
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (production only)
    """
    
    def __init__(self, app: ASGIApp, debug: bool = False):
        self.app = app
        self.debug = debug
        
        # Build security headers
        self.security_headers = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"x-xss-protection", b"1; mode=block"),
            (b"referrer-policy", b"strict-origin-when-cross-origin"),
            (b"permissions-policy", b"geolocation=(), microphone=(), camera=()"),
        ]
        
        # CSP header
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:* ws://localhost:*; "
            "frame-ancestors 'none';"
        )
        self.security_headers.append((b"content-security-policy", csp.encode()))
        
        # HSTS for production
        if not debug:
            self.security_headers.append(
                (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
            )
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(self.security_headers)
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# ============================================================================
# Graceful Shutdown Handler
# ============================================================================

class GracefulShutdownManager:
    """
    Manages graceful shutdown of the application.
    
    Tracks active requests and waits for them to complete
    before shutting down.
    """
    
    def __init__(self, shutdown_timeout: float = 30.0):
        self.shutdown_timeout = shutdown_timeout
        self.active_requests = 0
        self.is_shutting_down = False
        self._lock = asyncio.Lock()
    
    async def increment(self):
        """Increment active request count."""
        async with self._lock:
            self.active_requests += 1
    
    async def decrement(self):
        """Decrement active request count."""
        async with self._lock:
            self.active_requests -= 1
    
    async def wait_for_requests(self):
        """Wait for all active requests to complete."""
        self.is_shutting_down = True
        
        logger.info(
            f"Graceful shutdown initiated, waiting for {self.active_requests} requests"
        )
        
        start_time = time.time()
        
        while self.active_requests > 0:
            if time.time() - start_time > self.shutdown_timeout:
                logger.warning(
                    f"Shutdown timeout reached with {self.active_requests} active requests"
                )
                break
            
            await asyncio.sleep(0.1)
        
        logger.info("All requests completed, proceeding with shutdown")


# Global shutdown manager
shutdown_manager = GracefulShutdownManager()


class GracefulShutdownMiddleware:
    """
    ASGI Middleware for graceful shutdown support.
    
    Tracks active requests and rejects new requests during shutdown.
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Reject requests during shutdown
        if shutdown_manager.is_shutting_down:
            response = Response(
                content='{"error": "Service is shutting down", "status_code": 503}',
                status_code=503,
                media_type="application/json",
                headers={"Retry-After": "30"}
            )
            await response(scope, receive, send)
            return
        
        # Track request
        await shutdown_manager.increment()
        
        try:
            await self.app(scope, receive, send)
        finally:
            await shutdown_manager.decrement()


# ============================================================================
# Middleware Stack Builder
# ============================================================================

def build_middleware_stack(app: ASGIApp, debug: bool = False) -> ASGIApp:
    """
    Build the complete middleware stack.
    
    Order matters! Middleware is applied in reverse order:
    Last added = First executed
    
    Execution order:
    1. GracefulShutdown (reject during shutdown)
    2. RequestContext (set request ID, timing)
    3. SecurityHeaders (add security headers)
    4. Prometheus (collect metrics)
    5. RequestTimeout (cancel slow requests)
    6. Application
    
    Args:
        app: FastAPI application
        debug: Debug mode flag
    
    Returns:
        Wrapped application with middleware
    """
    # Apply in reverse order
    app = RequestTimeoutMiddleware(app, timeout_seconds=30.0)
    app = PrometheusMetricsMiddleware(app)
    app = SecurityHeadersMiddleware(app, debug=debug)
    app = RequestContextMiddleware(app)
    app = GracefulShutdownMiddleware(app)
    
    return app
