"""
Request Logging Middleware

Provides comprehensive request/response logging with:
- Request/response timing
- Performance metrics collection
- Structured logging
- Sensitive data masking
- Request body logging (optional)
"""

import time
import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque
import asyncio

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.structured_logging import get_logger, set_request_context


logger = get_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# Paths to skip logging
SKIP_PATHS: Set[str] = {
    "/health",
    "/health/live",
    "/health/ready",
    "/api/v1/health/live",
    "/api/v1/health/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

# Sensitive headers to mask
SENSITIVE_HEADERS: Set[str] = {
    "authorization",
    "x-api-key",
    "cookie",
    "set-cookie",
}

# Sensitive fields in request/response body
SENSITIVE_FIELDS: Set[str] = {
    "password",
    "password_hash",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "credit_card",
    "ssn",
}


# ============================================================================
# Metrics Storage
# ============================================================================

@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    request_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: str
    client_ip: Optional[str] = None
    user_id: Optional[str] = None
    user_agent: Optional[str] = None
    request_size: int = 0
    response_size: int = 0
    error: Optional[str] = None


@dataclass
class EndpointStats:
    """Statistics for an endpoint."""
    path: str
    method: str
    total_requests: int = 0
    total_errors: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    
    @property
    def avg_duration_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests
    
    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests


class MetricsCollector:
    """Collects and stores request metrics."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.request_history: deque = deque(maxlen=max_history)
        self.endpoint_stats: Dict[str, EndpointStats] = {}
        self._lock = asyncio.Lock()
    
    async def record(self, metrics: RequestMetrics) -> None:
        """Record request metrics."""
        async with self._lock:
            # Add to history
            self.request_history.append(metrics)
            
            # Update endpoint stats
            key = f"{metrics.method}:{metrics.path}"
            
            if key not in self.endpoint_stats:
                self.endpoint_stats[key] = EndpointStats(
                    path=metrics.path,
                    method=metrics.method,
                )
            
            stats = self.endpoint_stats[key]
            stats.total_requests += 1
            stats.total_duration_ms += metrics.duration_ms
            stats.min_duration_ms = min(stats.min_duration_ms, metrics.duration_ms)
            stats.max_duration_ms = max(stats.max_duration_ms, metrics.duration_ms)
            
            # Track status codes
            status_code = metrics.status_code
            stats.status_codes[status_code] = stats.status_codes.get(status_code, 0) + 1
            
            # Track errors
            if status_code >= 400:
                stats.total_errors += 1
    
    def get_recent_requests(
        self,
        limit: int = 100,
        status_code: Optional[int] = None,
        path_prefix: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent requests with optional filtering."""
        results = []
        
        for metrics in reversed(self.request_history):
            if status_code and metrics.status_code != status_code:
                continue
            if path_prefix and not metrics.path.startswith(path_prefix):
                continue
            
            results.append({
                "request_id": metrics.request_id,
                "method": metrics.method,
                "path": metrics.path,
                "status_code": metrics.status_code,
                "duration_ms": round(metrics.duration_ms, 2),
                "timestamp": metrics.timestamp,
                "client_ip": metrics.client_ip,
                "user_id": metrics.user_id,
            })
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_endpoint_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all endpoints."""
        results = []
        
        for key, stats in self.endpoint_stats.items():
            results.append({
                "method": stats.method,
                "path": stats.path,
                "total_requests": stats.total_requests,
                "total_errors": stats.total_errors,
                "error_rate": round(stats.error_rate * 100, 2),
                "avg_duration_ms": round(stats.avg_duration_ms, 2),
                "min_duration_ms": round(stats.min_duration_ms, 2) if stats.min_duration_ms != float('inf') else 0,
                "max_duration_ms": round(stats.max_duration_ms, 2),
                "status_codes": stats.status_codes,
            })
        
        # Sort by total requests descending
        results.sort(key=lambda x: x["total_requests"], reverse=True)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall metrics summary."""
        total_requests = sum(s.total_requests for s in self.endpoint_stats.values())
        total_errors = sum(s.total_errors for s in self.endpoint_stats.values())
        
        # Calculate percentiles from recent requests
        durations = [m.duration_ms for m in self.request_history]
        
        if durations:
            durations.sort()
            p50 = durations[len(durations) // 2]
            p95 = durations[int(len(durations) * 0.95)]
            p99 = durations[int(len(durations) * 0.99)]
        else:
            p50 = p95 = p99 = 0.0
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_requests * 100, 2) if total_requests > 0 else 0,
            "unique_endpoints": len(self.endpoint_stats),
            "latency_percentiles": {
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
            },
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.request_history.clear()
        self.endpoint_stats.clear()


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# ============================================================================
# Utility Functions
# ============================================================================

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive fields in a dictionary."""
    if not isinstance(data, dict):
        return data
    
    masked = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value)
        elif isinstance(value, list):
            masked[key] = [
                mask_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            masked[key] = value
    
    return masked


def mask_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Mask sensitive headers."""
    masked = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            masked[key] = "***MASKED***"
        else:
            masked[key] = value
    return masked


def should_skip_logging(path: str) -> bool:
    """Check if path should skip logging."""
    return path in SKIP_PATHS or path.startswith("/static/")


# ============================================================================
# Request Logging Middleware
# ============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.
    
    Features:
    - Request/response timing
    - Structured logging with request context
    - Metrics collection
    - Sensitive data masking
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        slow_request_threshold_ms: float = 1000.0,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Skip logging for certain paths
        if should_skip_logging(request.url.path):
            return await call_next(request)
        
        # Generate request ID if not present
        request_id = getattr(request.state, "request_id", None)
        if not request_id:
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
        
        # Set logging context
        set_request_context(request_id=request_id)
        
        # Extract request info
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Start timing
        start_time = time.perf_counter()
        
        # Log request
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent[:100] if user_agent else None,
        }
        
        # Optionally log request body
        if self.log_request_body and request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    body_json = json.loads(body)
                    log_data["request_body"] = mask_sensitive_data(body_json)
            except:
                pass
        
        logger.info(f"Request started: {request.method} {request.url.path}", extra=log_data)
        
        # Process request
        error_message = None
        try:
            response = await call_next(request)
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Get user ID if available
            user_id = None
            try:
                if hasattr(request.state, "user") and request.state.user:
                    user_id = str(request.state.user.id)
            except:
                pass
            
            # Create metrics
            metrics = RequestMetrics(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code if 'response' in locals() else 500,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat() + "Z",
                client_ip=client_ip,
                user_id=user_id,
                user_agent=user_agent[:100] if user_agent else None,
                error=error_message,
            )
            
            # Record metrics
            await self.metrics_collector.record(metrics)
            
            # Log response
            status_code = response.status_code if 'response' in locals() else 500
            log_level = logging.WARNING if status_code >= 400 else logging.INFO
            
            response_log = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            }
            
            # Warn for slow requests
            if duration_ms > self.slow_request_threshold_ms:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {duration_ms:.2f}ms",
                    extra=response_log,
                )
            else:
                logger.log(
                    log_level,
                    f"Request completed: {request.method} {request.url.path} "
                    f"- {status_code} in {duration_ms:.2f}ms",
                    extra=response_log,
                )
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response


def setup_request_logging(
    app,
    log_request_body: bool = False,
    log_response_body: bool = False,
    slow_request_threshold_ms: float = 1000.0,
) -> None:
    """
    Setup request logging middleware.
    
    Usage:
        from backend.core.request_logging import setup_request_logging
        
        app = FastAPI()
        setup_request_logging(app)
    """
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        slow_request_threshold_ms=slow_request_threshold_ms,
    )
    logger.info("Request logging middleware configured")
