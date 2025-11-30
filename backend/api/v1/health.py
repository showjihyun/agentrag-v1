"""
Health Check API v1 - Kubernetes-ready health endpoints.

Provides separate endpoints for:
- Liveness: Is the process alive?
- Readiness: Can the service handle traffic?
- Startup: Has the service finished initializing?
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from datetime import datetime
import asyncio
import logging

from backend.db.database import get_db
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["health"])


# ============================================================================
# Health Check Models
# ============================================================================

class ComponentHealth:
    """Health status for a single component."""
    
    def __init__(
        self,
        name: str,
        status: str = "unknown",
        message: str = "",
        latency_ms: float = 0,
        details: Dict = None
    ):
        self.name = name
        self.status = status  # healthy, unhealthy, degraded, unknown
        self.message = message
        self.latency_ms = latency_ms
        self.details = details or {}
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "details": self.details,
        }


# ============================================================================
# Health Check Functions
# ============================================================================

async def check_database_health(db: Session) -> ComponentHealth:
    """Check PostgreSQL database health."""
    start = datetime.now()
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        latency = (datetime.now() - start).total_seconds() * 1000
        
        # Get pool status
        from backend.db.database import get_pool_status
        pool_status = get_pool_status()
        
        return ComponentHealth(
            name="postgresql",
            status="healthy",
            message="Connected",
            latency_ms=latency,
            details=pool_status
        )
    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"Database health check failed: {e}")
        return ComponentHealth(
            name="postgresql",
            status="unhealthy",
            message=str(e),
            latency_ms=latency
        )


async def check_redis_health() -> ComponentHealth:
    """Check Redis health."""
    start = datetime.now()
    try:
        from backend.core.connection_pool import get_redis_pool
        
        pool = get_redis_pool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD
        )
        redis = pool.get_connection()
        redis.ping()
        
        # Get Redis info
        info = redis.info("memory")
        pool.release(redis)
        
        latency = (datetime.now() - start).total_seconds() * 1000
        
        return ComponentHealth(
            name="redis",
            status="healthy",
            message="Connected",
            latency_ms=latency,
            details={
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
            }
        )
    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"Redis health check failed: {e}")
        return ComponentHealth(
            name="redis",
            status="unhealthy",
            message=str(e),
            latency_ms=latency
        )


async def check_milvus_health() -> ComponentHealth:
    """Check Milvus vector database health."""
    start = datetime.now()
    try:
        from pymilvus import connections, utility
        
        # Check if already connected
        if not connections.has_connection("default"):
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                timeout=5
            )
        
        # List collections as health check
        collections = utility.list_collections()
        latency = (datetime.now() - start).total_seconds() * 1000
        
        return ComponentHealth(
            name="milvus",
            status="healthy",
            message="Connected",
            latency_ms=latency,
            details={
                "collections_count": len(collections),
            }
        )
    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"Milvus health check failed: {e}")
        return ComponentHealth(
            name="milvus",
            status="unhealthy",
            message=str(e),
            latency_ms=latency
        )


async def check_llm_health() -> ComponentHealth:
    """Check LLM service health."""
    start = datetime.now()
    try:
        if settings.LLM_PROVIDER == "ollama":
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                latency = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return ComponentHealth(
                        name="llm_ollama",
                        status="healthy",
                        message="Connected",
                        latency_ms=latency,
                        details={
                            "provider": "ollama",
                            "models_available": len(models),
                        }
                    )
        
        # For cloud providers, just check if API key is configured
        if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            return ComponentHealth(
                name="llm_openai",
                status="healthy",
                message="API key configured",
                latency_ms=0,
                details={"provider": "openai"}
            )
        
        if settings.LLM_PROVIDER == "claude" and settings.ANTHROPIC_API_KEY:
            return ComponentHealth(
                name="llm_claude",
                status="healthy",
                message="API key configured",
                latency_ms=0,
                details={"provider": "claude"}
            )
        
        return ComponentHealth(
            name="llm",
            status="degraded",
            message="LLM provider not fully configured",
            latency_ms=0
        )
        
    except Exception as e:
        latency = (datetime.now() - start).total_seconds() * 1000
        logger.error(f"LLM health check failed: {e}")
        return ComponentHealth(
            name="llm",
            status="unhealthy",
            message=str(e),
            latency_ms=latency
        )


# ============================================================================
# Kubernetes Health Endpoints
# ============================================================================

@router.get("/live")
async def liveness_probe() -> Dict:
    """
    Kubernetes Liveness Probe.
    
    Checks if the process is alive and should not be restarted.
    This is a lightweight check that always returns 200 if the process is running.
    
    Returns:
        200 OK if process is alive
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/ready")
async def readiness_probe(
    response: Response,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Kubernetes Readiness Probe.
    
    Checks if the service is ready to accept traffic.
    Verifies critical dependencies (DB, Redis, Milvus).
    
    Returns:
        200 OK if ready to accept traffic
        503 Service Unavailable if not ready
    """
    # Check critical components in parallel
    db_health, redis_health, milvus_health = await asyncio.gather(
        check_database_health(db),
        check_redis_health(),
        check_milvus_health(),
        return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(db_health, Exception):
        db_health = ComponentHealth("postgresql", "unhealthy", str(db_health))
    if isinstance(redis_health, Exception):
        redis_health = ComponentHealth("redis", "unhealthy", str(redis_health))
    if isinstance(milvus_health, Exception):
        milvus_health = ComponentHealth("milvus", "unhealthy", str(milvus_health))
    
    components = [db_health, redis_health, milvus_health]
    
    # Determine overall readiness
    # Service is ready if DB is healthy (Redis/Milvus can be degraded)
    is_ready = db_health.status == "healthy"
    
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {c.name: c.to_dict() for c in components},
    }


@router.get("/startup")
async def startup_probe(
    response: Response,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Kubernetes Startup Probe.
    
    Checks if the application has finished starting up.
    Used for slow-starting containers to avoid premature restarts.
    
    Returns:
        200 OK if startup is complete
        503 Service Unavailable if still starting
    """
    try:
        # Check if service container is initialized
        from backend.core.dependencies import get_container
        container = get_container()
        
        # Verify critical services are initialized
        checks = {
            "embedding_service": container._embedding_service is not None,
            "milvus_manager": container._milvus_manager is not None,
            "llm_manager": container._llm_manager is not None,
            "redis_client": container._redis_client is not None,
        }
        
        all_initialized = all(checks.values())
        
        if not all_initialized:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        return {
            "status": "started" if all_initialized else "starting",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "services": checks,
        }
        
    except RuntimeError:
        # Container not initialized yet
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "starting",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": "Service container not yet initialized",
        }


# ============================================================================
# Detailed Health Check
# ============================================================================

@router.get("/detailed")
async def detailed_health_check(
    response: Response,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Detailed health check with all component statuses.
    
    Checks all system components including:
    - PostgreSQL database
    - Redis cache
    - Milvus vector database
    - LLM service
    - Circuit breakers
    
    Returns comprehensive health information for monitoring dashboards.
    """
    # Check all components in parallel
    results = await asyncio.gather(
        check_database_health(db),
        check_redis_health(),
        check_milvus_health(),
        check_llm_health(),
        return_exceptions=True
    )
    
    components: List[ComponentHealth] = []
    for result in results:
        if isinstance(result, Exception):
            components.append(ComponentHealth("unknown", "unhealthy", str(result)))
        else:
            components.append(result)
    
    # Check circuit breakers
    try:
        from backend.core.circuit_breaker import get_circuit_breaker_registry
        registry = get_circuit_breaker_registry()
        cb_summary = registry.get_summary()
    except Exception as e:
        cb_summary = {"error": str(e)}
    
    # Determine overall status
    unhealthy_count = sum(1 for c in components if c.status == "unhealthy")
    degraded_count = sum(1 for c in components if c.status == "degraded")
    
    if unhealthy_count > 0:
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
        "components": {c.name: c.to_dict() for c in components},
        "circuit_breakers": cb_summary,
        "summary": {
            "total_components": len(components),
            "healthy": sum(1 for c in components if c.status == "healthy"),
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
        }
    }
