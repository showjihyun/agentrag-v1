"""
Application factory for creating the FastAPI application.

This module provides a clean separation of concerns by:
- Creating the FastAPI app instance
- Configuring middleware
- Registering routers
- Setting up exception handlers
- Managing application lifecycle
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from datetime import datetime

from backend.config import settings
from backend.core.structured_logging import setup_structured_logging, get_logger

# Setup logging
log_file = (
    "logs/app.log"
    if os.path.exists("logs") or os.makedirs("logs", exist_ok=True)
    else None
)

effective_log_level = settings.LOG_LEVEL if settings.DEBUG else "INFO"
setup_structured_logging(
    log_level=effective_log_level,
    log_file=log_file,
    json_format=not settings.DEBUG,
)

logger = get_logger(__name__)

# Suppress verbose third-party loggers in production
if not settings.DEBUG:
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager for startup and shutdown events."""
        from backend.app.lifecycle import startup_handler, shutdown_handler
        
        # Startup
        await startup_handler()
        
        yield
        
        # Shutdown
        await shutdown_handler()

    # Create FastAPI app
    app = FastAPI(
        title="Agentic RAG System",
        version="1.0.0",
        description="Intelligent RAG system with multi-agent orchestration",
        lifespan=lifespan,
    )

    # Configure app
    _configure_cors(app)
    _configure_middleware(app)
    _configure_exception_handlers(app)
    _configure_routers(app)
    _configure_health_endpoints(app)
    _configure_metrics_endpoint(app)

    return app


def _configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware."""
    print(f"DEBUG MODE: {settings.DEBUG}")
    
    if settings.DEBUG:
        print("⚠️  CORS configured for ALL origins (DEBUG mode - Development only!)")
        logger.warning(
            "⚠️  CORS configured for ALL origins (DEBUG mode - Development only!)"
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=3600,
        )
        print("✓ CORS middleware added successfully")
    else:
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            max_age=3600,
        )


def _configure_middleware(app: FastAPI) -> None:
    """Configure all middleware."""
    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    logger.info("GZip compression middleware enabled (minimum size: 1000 bytes)")
    
    # Register custom middleware
    from backend.app.middleware import register_all_middleware
    register_all_middleware(app)


def _configure_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers."""
    from backend.app.exception_handlers import register_exception_handlers
    register_exception_handlers(app)


def _configure_routers(app: FastAPI) -> None:
    """Configure API routers."""
    from backend.app.routers import register_all_routers
    register_all_routers(app)


def _configure_health_endpoints(app: FastAPI) -> None:
    """Configure health check endpoints."""
    
    @app.get("/api/health")
    async def health_check():
        """Comprehensive health check endpoint."""
        from backend.core.health_check import get_health_checker

        try:
            checker = get_health_checker()
            health_status = await checker.check_all(timeout_per_check=5.0)

            if health_status["status"] == "healthy":
                status_code = 200
            elif health_status["status"] == "degraded":
                status_code = 200
            else:
                status_code = 503

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
        """Simple health check for load balancers."""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}

    @app.get("/api/health/{component}")
    async def component_health_check(component: str):
        """Check health of a specific component."""
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


def _configure_metrics_endpoint(app: FastAPI) -> None:
    """Configure Prometheus metrics endpoint."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        PROMETHEUS_AVAILABLE = True
    except ImportError:
        PROMETHEUS_AVAILABLE = False
        logger.warning("prometheus_client not installed, metrics endpoint disabled")
        return

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
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
