# FastAPI application entry point

# Suppress ALL warnings globally before any imports
import warnings
import os
import sys

# Set environment variable BEFORE any imports
os.environ["PYTHONWARNINGS"] = "ignore"

# Comprehensive warning suppression - catch everything
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

# Specific suppressions for known warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*Pydantic.*")
warnings.filterwarnings("ignore", message=".*pydantic.*")
warnings.filterwarnings("ignore", message=".*model_fields.*")
warnings.filterwarnings("ignore", message=".*PydanticSerializationUnexpectedValue.*")
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince.*")
warnings.filterwarnings("ignore", message=".*dict.*method is deprecated.*")
warnings.filterwarnings("ignore", message=".*model_dump.*")
warnings.filterwarnings("ignore", message=".*StreamingChoices.*")
warnings.filterwarnings("ignore", message=".*Message.*serialized value.*")

# Suppress specific pydantic warnings by category
try:
    from pydantic import PydanticDeprecatedSince20, PydanticDeprecatedSince211
    warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
    warnings.filterwarnings("ignore", category=PydanticDeprecatedSince211)
except ImportError:
    pass

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings
from backend.core.dependencies import initialize_container, cleanup_container

# Note: rate_limit_middleware not implemented yet - using SecurityManager for rate limiting in endpoints

# Configure structured logging
from backend.core.structured_logging import (
    setup_structured_logging,
    get_logger,
    set_request_context,
)

# Setup structured logging (JSON format in production, plain text in debug)
log_file = (
    "logs/app.log"
    if os.path.exists("logs") or os.makedirs("logs", exist_ok=True)
    else None
)
setup_structured_logging(
    log_level=settings.LOG_LEVEL,
    log_file=log_file,
    json_format=not settings.DEBUG,  # JSON in production, plain text in debug
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up Agentic RAG System...")

    try:
        # Initialize service container
        await initialize_container()

        # Initialize connection pools
        from backend.core.connection_pool import get_redis_pool

        redis_pool = get_redis_pool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )
        logger.info("Redis connection pool initialized")

        # Initialize Milvus connection pool
        from backend.core.milvus_pool import get_milvus_pool

        milvus_pool = get_milvus_pool(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            pool_size=settings.MILVUS_POOL_SIZE,
        )
        await milvus_pool.initialize()
        logger.info("Milvus connection pool initialized")

        # Initialize cache manager
        from backend.core.cache_manager import get_cache_manager

        redis_client = redis_pool.get_client()
        cache_manager = get_cache_manager(redis_client)
        await cache_manager.start_cleanup_task()
        logger.info("Cache manager initialized")

        # Initialize background task manager
        from backend.core.background_tasks import get_task_manager

        task_manager = get_task_manager()
        logger.info("Background task manager initialized")

        # Initialize health checks
        from backend.core.health_check import (
            initialize_health_checks,
            get_health_checker,
        )
        from backend.core.dependencies import get_container

        container = get_container()
        await initialize_health_checks(container)
        logger.info("Health checks initialized")

        # Initialize ColPali processor (warm up model)
        try:
            logger.info("Initializing ColPali processor...")
            from backend.services.colpali_processor import get_colpali_processor
            
            colpali = get_colpali_processor()
            if colpali:
                logger.info(f"✅ ColPali initialized: model={colpali.model_name}, device={colpali.device}")
            else:
                logger.warning("⚠️  ColPali not available")
        except Exception as e:
            logger.warning(f"ColPali initialization failed: {e}")

        # Initialize cache warmer and warm cache on startup
        try:
            from backend.services.cache_warmer import get_cache_warmer
            from backend.services.speculative_processor import SpeculativeProcessor
            from backend.services.embedding import EmbeddingService
            from backend.services.milvus import MilvusManager
            from backend.services.llm_manager import LLMManager
            
            # Get services
            embedding_service = EmbeddingService()
            milvus_manager = MilvusManager(
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                collection_name=settings.MILVUS_COLLECTION_NAME,
                embedding_dim=embedding_service.dimension,
            )
            llm_manager = LLMManager()
            
            # Create speculative processor
            speculative_processor = SpeculativeProcessor(
                embedding_service=embedding_service,
                milvus_manager=milvus_manager,
                llm_manager=llm_manager,
                redis_client=redis_client
            )
            
            # Initialize cache warmer
            cache_warmer = get_cache_warmer(
                speculative_processor=speculative_processor,
                redis_client=redis_client
            )
            
            # Warm cache on startup (non-blocking)
            import asyncio
            asyncio.create_task(cache_warmer.warm_cache_on_startup())
            logger.info("Cache warming scheduled")
            
        except Exception as e:
            logger.warning(f"Failed to initialize cache warmer: {e}")

        logger.info(
            "Startup complete!", system_version="1.0.0", debug_mode=settings.DEBUG
        )

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Cleanup connection pools
    from backend.core.connection_pool import cleanup_redis_pool

    await cleanup_redis_pool()
    logger.info("Redis connection pool closed")

    # Cleanup Milvus connection pool
    from backend.core.milvus_pool import cleanup_milvus_pool

    await cleanup_milvus_pool()
    logger.info("Milvus connection pool closed")

    # Cleanup cache manager
    from backend.core.cache_manager import cleanup_cache_manager

    await cleanup_cache_manager()
    logger.info("Cache manager cleaned up")

    # Cleanup task manager
    from backend.core.background_tasks import cleanup_task_manager

    cleanup_task_manager()
    logger.info("Background task manager cleaned up")

    await cleanup_container()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Agentic RAG System",
    version="1.0.0",
    description="Intelligent RAG system with multi-agent orchestration",
    lifespan=lifespan,
)

# Configure CORS
if settings.DEBUG:
    # Development mode: Allow all origins
    logger.warning(
        "⚠️  CORS configured for ALL origins (DEBUG mode - Development only!)"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],  # Expose all headers
        max_age=3600,
    )
else:
    # Production mode: Restrict origins
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Add your production frontend URL here
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=3600,
    )


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:* ws://localhost:*; "
        "frame-ancestors 'none';"
    )

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # HSTS (only in production with HTTPS)
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


# ============================================================================
# MIDDLEWARE REGISTRATION (Order matters! First registered = Last executed)
# Execution order: error_handling -> logging -> request_id -> rate_limit
# ============================================================================


# Error handling middleware (최외곽 - 모든 에러를 캐치)
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware - catches all unhandled exceptions."""
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


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and responses with timing."""
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


# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add unique request ID to each request and set logging context."""
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


# Rate limiting middleware (최내곽 - 실제 endpoint 직전)
# Note: Rate limiting is currently handled per-endpoint using SecurityManager
# TODO: Implement global rate_limit_middleware for centralized rate limiting
# app.middleware("http")(rate_limit_middleware)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        f"[{request_id}] HTTP {exc.status_code}: {exc.detail} - "
        f"Path: {request.url.path}"
    )

    from backend.models.error import ErrorResponse

    error_response = ErrorResponse(
        error=exc.detail or "HTTP error",
        error_type="HTTPException",
        detail=str(exc.detail),
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


# Custom API Exception Handler
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


# Import dependency injection functions
from backend.core.dependencies import (
    get_redis_client,
    get_embedding_service,
    get_milvus_manager,
    get_llm_manager,
    get_document_processor,
    get_memory_manager,
    get_aggregator_agent,
    get_hybrid_query_router,
    get_intelligent_mode_router,
)


# Include API routers
from backend.api import (
    auth,
    conversations,
    documents,
    query,
    tasks,
    feedback,
    analytics,
    health,
    confidence,
    permissions,
    metrics,
    config,
    database_metrics,
    export,
    share,
    bookmarks,
    dashboard,
    notifications,
    usage,
    models,
    react_stats,
    advanced_rag,
    enterprise,
    monitoring_stats,
    web_search,
)

# Import new monitoring API
from backend.api import monitoring as monitoring_api

# Import PaddleOCR Advanced API
from backend.api import paddleocr_advanced

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(tasks.router)
app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(confidence.router)
app.include_router(permissions.router)
app.include_router(metrics.router)
app.include_router(config.router)
app.include_router(database_metrics.router)
app.include_router(models.router)
# New routers for Priority 2 & 3 features
app.include_router(export.router)
app.include_router(share.router)
app.include_router(bookmarks.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(usage.router)
# ReAct Statistics API
app.include_router(react_stats.router)
# Monitoring API (Priority 1)
app.include_router(monitoring_stats.router)

# New Monitoring Statistics API (PostgreSQL-based)
app.include_router(monitoring_api.router)
# Advanced RAG API (Priority 3)
app.include_router(advanced_rag.router)
# Enterprise API (Priority 4)
app.include_router(enterprise.router)
# Web Search API
app.include_router(web_search.router)

# PaddleOCR Advanced API (Phase 1: PP-ChatOCRv4)
app.include_router(paddleocr_advanced.router)


@app.get("/api/health")
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns detailed health status of all system components.
    """
    from backend.core.health_check import get_health_checker

    try:
        checker = get_health_checker()
        health_status = await checker.check_all(timeout_per_check=5.0)

        # Determine HTTP status code based on health
        if health_status["status"] == "healthy":
            status_code = 200
        elif health_status["status"] == "degraded":
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable

        return JSONResponse(status_code=status_code, content=health_status)

    except Exception as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e),
            },
        )


@app.get("/api/health/simple")
async def simple_health_check():
    """
    Simple health check for load balancers.

    Returns 200 OK if service is running.
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}


@app.get("/api/health/{component}")
async def component_health_check(component: str):
    """
    Check health of a specific component.

    Args:
        component: Component name (database, redis, milvus, etc.)
    """
    from backend.core.health_check import get_health_checker

    try:
        checker = get_health_checker()
        result = await checker.check_component(component, timeout=5.0)

        status_code = 200 if result.status.value in ["healthy", "degraded"] else 503

        return JSONResponse(status_code=status_code, content=result.to_dict())

    except Exception as e:
        logger.error(f"Component health check failed: {component}", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "name": component,
                "status": "unknown",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
