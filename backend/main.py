# FastAPI application entry point

import warnings
import os
import sys

# =============================================================================
# Warning Filter Configuration
# Only suppress specific known warnings, not all warnings
# =============================================================================

def configure_warnings():
    """Configure warning filters for known third-party library warnings."""
    
    # Pydantic v2 migration warnings (safe to ignore if using v2 correctly)
    warnings.filterwarnings(
        "ignore",
        message=".*Pydantic.*deprecated.*",
        category=DeprecationWarning
    )
    warnings.filterwarnings(
        "ignore", 
        message=".*model_fields.*",
        category=DeprecationWarning
    )
    
    # LiteLLM streaming warnings (known issue with response serialization)
    warnings.filterwarnings(
        "ignore",
        message=".*StreamingChoices.*",
        category=UserWarning
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Message.*serialized value.*",
        category=UserWarning
    )
    
    # SQLAlchemy 2.0 migration warnings
    warnings.filterwarnings(
        "ignore",
        message=".*SQLAlchemy.*deprecated.*",
        category=DeprecationWarning
    )
    
    # Suppress Pydantic deprecation categories if available
    try:
        from pydantic import PydanticDeprecatedSince20, PydanticDeprecatedSince211
        warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
        warnings.filterwarnings("ignore", category=PydanticDeprecatedSince211)
    except ImportError:
        pass

# Apply warning configuration
configure_warnings()

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import settings

# Prometheus metrics
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Only log prometheus warning in debug mode or if explicitly requested
    if os.getenv("DEBUG", "false").lower() == "true" or os.getenv("SHOW_PROMETHEUS_WARNING", "false").lower() == "true":
        logging.warning("prometheus_client not installed, metrics endpoint disabled")
from backend.core.dependencies import initialize_container, cleanup_container

# Note: rate_limit_middleware not implemented yet - using SecurityManager for rate limiting in endpoints

# Configure structured logging
from backend.core.structured_logging import (
    setup_logging,
    get_logger,
    LogContext,
)

# Setup structured logging (JSON format in production, plain text in debug)
log_file = (
    "logs/app.log"
    if os.path.exists("logs") or os.makedirs("logs", exist_ok=True)
    else None
)

# Optimize logging level based on environment
effective_log_level = settings.LOG_LEVEL if settings.DEBUG else "INFO"
setup_logging(
    log_level=effective_log_level,
    json_logs=not settings.DEBUG,  # JSON in production, plain text in debug
    enable_colors=settings.DEBUG,  # Colors in debug mode
)

logger = get_logger(__name__)

# Suppress verbose third-party loggers in production
if not settings.DEBUG:
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up Agentic RAG System...")

    try:
        # Initialize Sentry error tracking
        from backend.services.sentry_service import initialize_sentry
        sentry_initialized = initialize_sentry(
            environment="production" if not settings.DEBUG else "development",
            enable_tracing=not settings.DEBUG,
        )
        if sentry_initialized:
            logger.info("Sentry error tracking initialized")
        
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

        # Initialize embedding configuration
        from backend.services.system_config_service import SystemConfigService
        try:
            await SystemConfigService.initialize_embedding_config()
            logger.info("Embedding configuration initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding config: {e}")

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

        # ColPali removed - not used in this system

        # Initialize distributed tracing (OpenTelemetry)
        try:
            from backend.core.tracing import setup_tracing
            
            if not settings.DEBUG:  # Enable in production
                setup_tracing(
                    service_name="agentic-rag",
                    jaeger_host=os.getenv("JAEGER_HOST", "localhost"),
                    jaeger_port=int(os.getenv("JAEGER_PORT", "6831"))
                )
                logger.info("Distributed tracing initialized (Jaeger)")
        except Exception as e:
            logger.warning(f"Failed to initialize tracing: {e}")

        # Initialize cache warmer (Phase 3)
        try:
            from backend.core.cache_warming import get_cache_warmer
            from backend.db.database import SessionLocal
            
            def db_factory():
                return SessionLocal()
            
            # Initialize cache warmer
            cache_warmer = get_cache_warmer(
                redis=redis_client,
                db_factory=db_factory
            )
            
            # Start cache warming scheduler
            cache_warmer.start()
            logger.info("Cache warming scheduler started")
            
        except Exception as e:
            logger.warning(f"Failed to initialize cache warmer: {e}")
        
        # Initialize API key manager
        try:
            from backend.core.security.api_key_manager import get_api_key_manager
            
            # Initialize with encryption key from environment
            api_key_manager = get_api_key_manager()
            logger.info("API key manager initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize API key manager: {e}")

        # Initialize tool integrations
        try:
            from backend.core.tools.init_tools import initialize_tools, get_tool_summary
            
            tool_count = initialize_tools()
            tool_summary = get_tool_summary()
            
            logger.info(
                f"Tool integrations initialized: {tool_count} tools across "
                f"{len(tool_summary['categories'])} categories"
            )
            
            for category, count in tool_summary['by_category'].items():
                logger.info(f"  - {category}: {count} tools")
            
            # Sync tools to database
            try:
                from backend.core.tools.sync_tools_to_db import sync_tools_to_database
                from backend.db.database import SessionLocal
                
                db = SessionLocal()
                try:
                    synced_count = sync_tools_to_database(db)
                    logger.info(f"✅ Synced {synced_count} tools to database")
                finally:
                    db.close()
            except Exception as sync_error:
                logger.warning(f"Failed to sync tools to database: {sync_error}")
                
        except Exception as e:
            logger.warning(f"Failed to initialize tool integrations: {e}")

        # Start background scheduler for periodic tasks
        try:
            from backend.core.scheduler import start_scheduler
            start_scheduler()
            logger.info("Background scheduler started (memory cleanup at 3 AM daily)")
        except Exception as e:
            logger.warning(f"Failed to start background scheduler: {e}")

        logger.info(
            "Startup complete!", system_version="1.0.0", debug_mode=settings.DEBUG
        )

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")
    
    # Stop cache warmer
    try:
        from backend.core.cache_warming import get_cache_warmer
        cache_warmer = get_cache_warmer()
        cache_warmer.stop()
        logger.info("Cache warmer stopped")
    except Exception as e:
        logger.warning(f"Failed to stop cache warmer: {e}")
    
    # Stop background scheduler
    try:
        from backend.core.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop scheduler: {e}")

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

# Add GZip compression middleware for better performance
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
logger.info("GZip compression middleware enabled (minimum size: 1000 bytes)")

# Add performance optimization middleware
from backend.middleware.performance_middleware import add_performance_middleware
add_performance_middleware(app)

# Configure CORS
print(f"DEBUG MODE: {settings.DEBUG}")
if settings.DEBUG:
    # Development mode: Allow all origins
    print("⚠️  CORS configured for ALL origins (DEBUG mode - Development only!)")
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
    print("✓ CORS middleware added successfully")
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

    # Content Security Policy - Allow Swagger UI CDN resources
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self' http://localhost:* ws://localhost:* https://cdn.jsdelivr.net; "
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
    from backend.core.structured_logging import request_id_var, user_id_var
    
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Set request context for structured logging
    request_id_var.set(request_id)

    # Try to extract user_id from request if authenticated
    try:
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)
            user_id_var.set(user_id)
    except:
        pass

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Rate limiting middleware (최내곽 - 실제 endpoint 직전)
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting middleware with Redis-based distributed limiting."""
    from backend.core.rate_limiter import RateLimiter
    from backend.core.dependencies import get_redis_client
    
    # Skip rate limiting for health checks and static files
    skip_paths = ["/api/health", "/docs", "/redoc", "/openapi.json"]
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
# Import directly from .py files to avoid conflicts with domain folders
from backend.api.auth import router as auth_router
# RAG-related routers - commented out for workflow-focused platform
# from backend.api.conversations import router as conversations_router
# from backend.api.documents import router as documents_router
# from backend.api.query import router as query_router
# from backend.api.advanced_rag import router as advanced_rag_router
# from backend.api.web_search import router as web_search_router
from backend.api.tasks import router as tasks_router
from backend.api.feedback import router as feedback_router
from backend.api.analytics import router as analytics_router
from backend.api.health import router as health_router
from backend.api.confidence import router as confidence_router
from backend.api.permissions import router as permissions_router
from backend.api.metrics import router as metrics_router
from backend.api.config import router as config_router
from backend.api.database_metrics import router as database_metrics_router
from backend.api.export import router as export_router
from backend.api.share import router as share_router
from backend.api.bookmarks import router as bookmarks_router
from backend.api.dashboard import router as dashboard_router
from backend.api.notifications import router as notifications_router
from backend.api.usage import router as usage_router
from backend.api.models import router as models_router
from backend.api.react_stats import router as react_stats_router
from backend.api.enterprise import router as enterprise_router
from backend.api.monitoring_stats import router as monitoring_stats_router

# Import new monitoring API
from backend.api import monitoring as monitoring_api

# Import PaddleOCR Advanced API
from backend.api import paddleocr_advanced

# Import v1 API routers (versioned APIs)
from backend.api.v1 import health as health_v1

# Legacy health router (backward compatibility)
app.include_router(health_router)

# v1 API routers (Kubernetes-ready health checks)
app.include_router(health_v1.router)
app.include_router(auth_router)
# RAG-related routers - commented out for workflow-focused platform
# app.include_router(conversations_router)
# app.include_router(documents_router)
# app.include_router(query_router)
# app.include_router(advanced_rag_router)
# app.include_router(web_search_router)
app.include_router(tasks_router)
app.include_router(feedback_router)
app.include_router(analytics_router)
app.include_router(confidence_router)
app.include_router(permissions_router)
app.include_router(metrics_router)
app.include_router(config_router)
app.include_router(database_metrics_router)
app.include_router(models_router)
# New routers for Priority 2 & 3 features
app.include_router(export_router)
app.include_router(share_router)
app.include_router(bookmarks_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)
app.include_router(usage_router)
# ReAct Statistics API
app.include_router(react_stats_router)
# Monitoring API (Priority 1)
app.include_router(monitoring_stats_router)

# New Monitoring Statistics API (PostgreSQL-based)
app.include_router(monitoring_api.router)
# Enterprise API (Priority 4)
app.include_router(enterprise_router)

# PaddleOCR Advanced API (Phase 1: PP-ChatOCRv4)
app.include_router(paddleocr_advanced.router)

# Document Preview API (with PaddleOCR)
from backend.api import document_preview
app.include_router(document_preview.router)

# Connection Pool Metrics API
from backend.api import pool_metrics
app.include_router(pool_metrics.router)

# Cache Metrics API
from backend.api import cache_metrics
app.include_router(cache_metrics.router)

# Admin API
from backend.api import admin
app.include_router(admin.router)

# Event Store API
from backend.api import event_store
app.include_router(event_store.router)

# Agent Builder API
from backend.api.agent_builder import (
    agents as agent_builder_agents,
    blocks as agent_builder_blocks,
    workflows as agent_builder_workflows,
    knowledgebases as agent_builder_knowledgebases,
    variables as agent_builder_variables,
    executions as agent_builder_executions,
    permissions as agent_builder_permissions,
    audit_logs as agent_builder_audit_logs,
    dashboard as agent_builder_dashboard,
    oauth as agent_builder_oauth,
    webhooks as agent_builder_webhooks,
    chat as agent_builder_chat,
    memory as agent_builder_memory,
    cost as agent_builder_cost,
    branches as agent_builder_branches,
    collaboration as agent_builder_collaboration,
    prompt_optimization as agent_builder_prompt_optimization,
    insights as agent_builder_insights,
    marketplace as agent_builder_marketplace,
    advanced_export as agent_builder_advanced_export,
    tools as agent_builder_tools,
    analytics as agent_builder_analytics,
    custom_tools as agent_builder_custom_tools,
    api_keys as agent_builder_api_keys,
    workflow_generator as agent_builder_workflow_generator,
    agent_chat as agent_builder_agent_chat,  # KB-aware agent chat
    kb_monitoring as agent_builder_kb_monitoring,  # KB monitoring
    embedding_models as agent_builder_embedding_models,  # Embedding models management
    milvus_admin as agent_builder_milvus_admin,  # Milvus administration
    triggers as agent_builder_triggers,  # Triggers management
    approvals as agent_builder_approvals,  # Human-in-the-Loop approvals
    templates as agent_builder_templates,  # Workflow templates
    versions as agent_builder_versions,  # Workflow versions
    tool_execution as agent_builder_tool_execution,  # Tool execution
    tool_metrics as agent_builder_tool_metrics,  # Tool metrics
    tool_marketplace as agent_builder_tool_marketplace,  # Tool marketplace
    tool_config as agent_builder_tool_config,  # Tool configuration
    workflow_debug as agent_builder_workflow_debug,  # Workflow debugging
    workflow_monitoring as agent_builder_workflow_monitoring,  # Workflow monitoring
    ai_assistant as agent_builder_ai_assistant,  # AI Assistant
    ai_agent_chat as agent_builder_ai_agent_chat,  # AI Agent Chat WebSocket
    cost_tracking as agent_builder_cost_tracking,  # Cost and token tracking
    agent_team as agent_builder_agent_team,  # Multi-agent team orchestration
    workflow_templates as agent_builder_workflow_templates,  # Workflow templates
    workflow_nlp_generator as agent_builder_workflow_nlp,  # NLP workflow generation
    code_execution as agent_builder_code_execution,  # Enhanced code block execution
    ai_copilot as agent_builder_ai_copilot,  # AI Copilot for code
    code_debugger as agent_builder_code_debugger,  # Interactive debugger
    code_analyzer as agent_builder_code_analyzer,  # Code analysis/linting
    code_profiler as agent_builder_code_profiler,  # Performance profiling & test generation
    code_secrets as agent_builder_code_secrets,  # Secrets management
    flows as agent_builder_flows,  # Agentflow & Chatflow management
    agentflows as agent_builder_agentflows,  # Agentflow-specific API
    chatflows as agent_builder_chatflows,  # Chatflow-specific API
    embed as agent_builder_embed,  # Embed widget for Chatflows
    flow_templates as agent_builder_flow_templates,  # Flow templates management
    chatflow_chat as agent_builder_chatflow_chat,  # Chatflow chat API
    prometheus_metrics as agent_builder_prometheus_metrics,  # Prometheus metrics export
    agentflow_execution as agent_builder_agentflow_execution,  # Agentflow execution API
    workflows_ddd as agent_builder_workflows_ddd,  # DDD Reference Implementation
    nlp_generator as agent_builder_nlp_generator,  # NLP Workflow Generator
    gemini_multimodal as agent_builder_gemini_multimodal,  # Gemini 3.0 MultiModal API
    gemini_templates as agent_builder_gemini_templates,  # Gemini MultiModal Templates
    gemini_realtime as agent_builder_gemini_realtime,  # Gemini Real-time Execution
    gemini_fusion as agent_builder_gemini_fusion,  # Gemini Advanced Fusion
    gemini_video as agent_builder_gemini_video,  # Gemini Video Processing
    gemini_batch as agent_builder_gemini_batch,  # Gemini Batch Processing
    gemini_auto_optimizer as agent_builder_gemini_auto_optimizer,  # Gemini Auto-optimization
    predictive_routing as agent_builder_predictive_routing,  # Predictive Routing
    nl_workflow_generator as agent_builder_nl_workflow_generator,  # 🌟 Natural Language Workflow Generator
    multi_agent_orchestration as agent_builder_multi_agent_orchestration,  # Multi-Agent Orchestration
    advanced_orchestration as agent_builder_advanced_orchestration,  # 🚀 Advanced Multi-Agent Orchestration
    workflow_optimization as agent_builder_workflow_optimization,  # 🎯 Intelligent Workflow Optimization
    predictive_maintenance as agent_builder_predictive_maintenance,  # 🛡️ Predictive Maintenance & Self-Healing
    agent_olympics as agent_builder_agent_olympics,  # 🏆 AI Agent Olympics
    emotional_ai as agent_builder_emotional_ai,  # 💝 Emotional AI Integration
    workflow_dna as agent_builder_workflow_dna,  # 🧬 Workflow DNA Evolution
    realtime_updates as agent_builder_realtime_updates,  # 🔄 Real-time Updates WebSocket
    performance_monitoring as agent_builder_performance_monitoring,  # 📊 Performance Monitoring
    knowledge_graphs as agent_builder_knowledge_graphs,  # 🕸️ Knowledge Graph API
    hybrid_search as agent_builder_hybrid_search,  # 🔍 Hybrid Search API
    kg_analytics as agent_builder_kg_analytics,  # 📈 Knowledge Graph Analytics API
    team_templates as agent_builder_team_templates,  # 👥 Team Templates API
)

# Circuit Breaker Status API (Phase 1 Architecture)
from backend.api import circuit_breaker_status

# Knowledge Base API
from backend.api import knowledge_base

# LLM Settings API
from backend.api import llm_settings

# Users Search API
from backend.api import users_search

app.include_router(agent_builder_dashboard.router)
app.include_router(agent_builder_agents.router)
app.include_router(agent_builder_blocks.router)
app.include_router(agent_builder_workflows.router)
app.include_router(agent_builder_knowledgebases.router)
app.include_router(agent_builder_knowledge_graphs.router)
app.include_router(agent_builder_hybrid_search.router)
app.include_router(agent_builder_kg_analytics.router)
app.include_router(agent_builder_team_templates.router)  # Team Templates API
app.include_router(users_search.router)  # Users Search API
app.include_router(agent_builder_variables.router)
app.include_router(agent_builder_executions.router)
app.include_router(agent_builder_permissions.router)
app.include_router(agent_builder_audit_logs.router)
app.include_router(agent_builder_oauth.router)
app.include_router(agent_builder_webhooks.router)
app.include_router(agent_builder_chat.router)
# New Agent Builder APIs (Frontend-Backend Gap)
app.include_router(agent_builder_memory.router)
app.include_router(agent_builder_cost.router)
app.include_router(agent_builder_branches.router)
app.include_router(agent_builder_collaboration.router)
app.include_router(agent_builder_prompt_optimization.router)
app.include_router(agent_builder_insights.router)
app.include_router(agent_builder_marketplace.router)
app.include_router(agent_builder_advanced_export.router)
app.include_router(agent_builder_api_keys.router)
app.include_router(agent_builder_tools.router)
app.include_router(agent_builder_analytics.router)
app.include_router(agent_builder_custom_tools.router)
app.include_router(agent_builder_workflow_generator.router)
app.include_router(agent_builder_agent_chat.router)  # KB-aware agent chat
app.include_router(agent_builder_kb_monitoring.router)  # KB monitoring
app.include_router(agent_builder_embedding_models.router)  # Embedding models management
app.include_router(agent_builder_milvus_admin.router)  # Milvus administration
app.include_router(agent_builder_triggers.router)  # Triggers management
app.include_router(agent_builder_approvals.router)  # Human-in-the-Loop approvals
app.include_router(agent_builder_templates.router)  # Workflow templates
app.include_router(agent_builder_versions.router)  # Workflow versions
app.include_router(agent_builder_tool_execution.router)  # Tool execution
app.include_router(agent_builder_tool_metrics.router)  # Tool metrics
app.include_router(agent_builder_tool_marketplace.router)  # Tool marketplace
app.include_router(agent_builder_tool_config.router)  # Tool configuration
app.include_router(agent_builder_workflow_debug.router)  # Workflow debugging
app.include_router(agent_builder_workflow_monitoring.router)  # Workflow monitoring
app.include_router(agent_builder_ai_assistant.router)  # AI Assistant
app.include_router(agent_builder_ai_agent_chat.router)  # AI Agent Chat WebSocket
app.include_router(agent_builder_cost_tracking.router)  # Cost and token tracking
app.include_router(agent_builder_agent_team.router)  # Multi-agent team orchestration
app.include_router(agent_builder_workflow_templates.router)  # Workflow templates
app.include_router(agent_builder_workflow_nlp.router)  # NLP workflow generation
app.include_router(agent_builder_code_execution.router)  # Enhanced code block execution
app.include_router(agent_builder_ai_copilot.router)  # AI Copilot for code
app.include_router(agent_builder_code_debugger.router)  # Interactive debugger
app.include_router(agent_builder_code_analyzer.router)  # Code analysis/linting
app.include_router(agent_builder_code_profiler.router)  # Performance profiling & test generation
app.include_router(agent_builder_code_secrets.router)  # Secrets management
app.include_router(agent_builder_flows.router)  # Agentflow & Chatflow management
app.include_router(agent_builder_agentflows.router)  # Agentflow-specific API
app.include_router(agent_builder_chatflows.router)  # Chatflow-specific API
app.include_router(agent_builder_embed.router)  # Embed widget for Chatflows
app.include_router(agent_builder_flow_templates.router)  # Flow templates management
app.include_router(agent_builder_nlp_generator.router)  # NLP Workflow Generator
app.include_router(agent_builder_gemini_multimodal.router)  # Gemini 3.0 MultiModal API
app.include_router(agent_builder_gemini_templates.router)  # Gemini MultiModal Templates
app.include_router(agent_builder_gemini_realtime.router)  # Gemini Real-time Execution
app.include_router(agent_builder_gemini_fusion.router)  # Gemini Advanced Fusion
app.include_router(agent_builder_gemini_video.router)  # Gemini Video Processing
app.include_router(agent_builder_gemini_batch.router)  # Gemini Batch Processing
app.include_router(agent_builder_gemini_auto_optimizer.router)  # Gemini Auto-optimization
app.include_router(agent_builder_predictive_routing.router)  # Predictive Routing
app.include_router(agent_builder_nl_workflow_generator.router)  # 🌟 Natural Language Workflow Generator
app.include_router(agent_builder_multi_agent_orchestration.router)  # Multi-Agent Orchestration
app.include_router(agent_builder_advanced_orchestration.router)  # 🚀 Advanced Multi-Agent Orchestration
app.include_router(agent_builder_workflow_optimization.router)  # 🎯 Intelligent Workflow Optimization
app.include_router(agent_builder_predictive_maintenance.router)  # 🛡️ Predictive Maintenance & Self-Healing
app.include_router(agent_builder_agent_olympics.router)  # 🏆 AI Agent Olympics
app.include_router(agent_builder_emotional_ai.router)  # 💝 Emotional AI Integration
app.include_router(agent_builder_workflow_dna.router)  # 🧬 Workflow DNA Evolution
app.include_router(agent_builder_realtime_updates.router)  # 🔄 Real-time Updates WebSocket
app.include_router(agent_builder_performance_monitoring.router)  # 📊 Performance Monitoring
app.include_router(agent_builder_chatflow_chat.router)  # Chatflow chat API
app.include_router(agent_builder_prometheus_metrics.router)  # Prometheus metrics export
app.include_router(agent_builder_agentflow_execution.router)  # Agentflow execution API
app.include_router(agent_builder_workflows_ddd.router)  # DDD Reference Implementation
app.include_router(llm_settings.router)

# Environment Variables API
from backend.api.agent_builder import environment_variables as agent_builder_env_vars
app.include_router(agent_builder_env_vars.router, prefix="/api/agent-builder", tags=["environment-variables"])

# User Settings API
from backend.api.agent_builder import user_settings as agent_builder_user_settings
app.include_router(agent_builder_user_settings.router)

# Workflow Execution Streaming API (SSE)
from backend.api.agent_builder import workflow_execution_stream
app.include_router(workflow_execution_stream.router, prefix="/api/agent-builder", tags=["workflow-execution-stream"])

# AI Agent Streaming API (SSE)
from backend.api.agent_builder import ai_agent_stream
app.include_router(ai_agent_stream.router)

# Memory Management API (Priority 4)
from backend.api.agent_builder import memory_management
app.include_router(memory_management.router)

# A2A Protocol API (Google Agent-to-Agent)
try:
    from backend.api.agent_builder.a2a_simple import router as a2a_router
    app.include_router(a2a_router, prefix="/api/agent-builder", tags=["a2a-protocol"])
    print("✅ A2A router registered successfully in main.py")
except Exception as e:
    print(f"❌ Failed to register A2A router in main.py: {e}")

# Cache Management API (Priority 9)
from backend.api import cache_management
app.include_router(cache_management.router)

# Knowledge Base API (for workflow integration)
app.include_router(knowledge_base.router)

# Circuit Breaker Status API (Phase 1 Architecture)
app.include_router(circuit_breaker_status.router)

# API v2 - Enhanced endpoints with standardized responses
from backend.api.v2 import workflows as v2_workflows
from backend.api.v2 import auth as v2_auth
app.include_router(v2_workflows.router)
app.include_router(v2_auth.router)

# Enhanced Audit Logs API (replaces basic audit_logs)
from backend.api.agent_builder import audit_logs as enhanced_audit_logs
app.include_router(enhanced_audit_logs.router)

# Session Management API
from backend.api import auth_sessions
app.include_router(auth_sessions.router)

# Enhanced Notifications API
from backend.api import notifications as notifications_api
app.include_router(notifications_api.router)

# PDF Export API
from backend.api import exports as exports_api
app.include_router(exports_api.router)

# Chat History API
from backend.api import chat_history as chat_history_api
app.include_router(chat_history_api.router)


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format for scraping.
    """
    if not PROMETHEUS_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Prometheus client not installed"}
        )
    
    try:
        metrics_output = generate_latest()
        return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate metrics"}
        )


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


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Agentic RAG application...")
    
    # Start KB cache scheduler
    try:
        from backend.core.kb_scheduler import start_kb_scheduler
        start_kb_scheduler()
        logger.info("KB cache scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start KB cache scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Agentic RAG application...")
    
    # Stop KB cache scheduler
    try:
        from backend.core.kb_scheduler import stop_kb_scheduler
        stop_kb_scheduler()
        logger.info("KB cache scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop KB cache scheduler: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
