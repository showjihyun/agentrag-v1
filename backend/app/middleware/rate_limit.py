"""
Rate limiting middleware.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from backend.config import settings
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


def add_rate_limit_middleware(app):
    """Global rate limiting middleware with Redis-based distributed limiting."""
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        from backend.core.rate_limiter import RateLimiter
        from backend.core.dependencies import get_redis_client
        
        # Skip rate limiting for health checks and static files
        skip_paths = ["/api/health", "/docs", "/redoc", "/openapi.json", "/metrics"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        try:
            redis_client = await get_redis_client()
            
            # Get identifier (user_id or IP)
            identifier = request.client.host if request.client else "unknown"
            
            # Try to get user_id if authenticated
            try:
                if hasattr(request.state, "user") and request.state.user:
                    identifier = f"user:{request.state.user.id}"
            except:
                pass
            
            # Create rate limiter with default limits
            rate_limiter = RateLimiter(
                redis_client=redis_client,
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                enabled=not settings.DEBUG  # Disable in debug mode
            )
            
            # Check rate limit
            is_allowed, error_msg, remaining = await rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=request.url.path
            )
            
            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier}",
                    extra={
                        "identifier": identifier,
                        "endpoint": request.url.path,
                        "remaining": remaining,
                    }
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": error_msg,
                        "remaining": remaining,
                        "retry_after": 60
                    },
                    headers={
                        "X-RateLimit-Remaining-Minute": str(remaining.get("minute", 0)),
                        "X-RateLimit-Remaining-Hour": str(remaining.get("hour", 0)),
                        "X-RateLimit-Remaining-Day": str(remaining.get("day", 0)),
                        "Retry-After": "60",
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Remaining-Minute"] = str(remaining.get("minute", 0))
            response.headers["X-RateLimit-Remaining-Hour"] = str(remaining.get("hour", 0))
            response.headers["X-RateLimit-Remaining-Day"] = str(remaining.get("day", 0))
            
            return response
            
        except Exception as e:
            # Graceful degradation: allow request if rate limiting fails
            logger.error(f"Rate limiting failed: {e}", exc_info=True)
            return await call_next(request)
