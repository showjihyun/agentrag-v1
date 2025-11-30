"""
Workflow Metrics API

Prometheus-compatible metrics endpoint and monitoring APIs.
"""

import logging
from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse

from backend.core.auth_dependencies import get_current_user, require_admin
from backend.db.models.user import User
from backend.services.agent_builder.workflow_metrics import get_metrics_collector
from backend.services.agent_builder.workflow_cache import get_cache_manager
from backend.services.agent_builder.workflow_security import get_security_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/metrics",
    tags=["agent-builder-metrics"],
)


@router.get("/prometheus", response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format.
    """
    collector = get_metrics_collector()
    return collector.to_prometheus_format()


@router.get("/summary")
async def metrics_summary(
    current_user: User = Depends(require_admin),
):
    """Get metrics summary for dashboard."""
    collector = get_metrics_collector()
    cache = get_cache_manager()
    
    return {
        "workflow_metrics": collector.get_summary(),
        "cache_metrics": cache.get_metrics(),
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers.
    
    Returns 200 if healthy, 503 if unhealthy.
    """
    # Check critical services
    checks = {
        "status": "healthy",
        "checks": {},
    }
    
    # Check database
    try:
        from backend.db.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        checks["checks"]["database"] = "ok"
    except Exception as e:
        checks["checks"]["database"] = f"error: {str(e)}"
        checks["status"] = "unhealthy"
    
    # Check Redis
    try:
        cache = get_cache_manager()
        if cache.redis:
            await cache.redis.ping()
            checks["checks"]["redis"] = "ok"
        else:
            checks["checks"]["redis"] = "not configured"
    except Exception as e:
        checks["checks"]["redis"] = f"error: {str(e)}"
    
    status_code = 200 if checks["status"] == "healthy" else 503
    return Response(
        content=str(checks),
        status_code=status_code,
        media_type="application/json",
    )


@router.get("/cache/stats")
async def cache_stats(
    current_user: User = Depends(require_admin),
):
    """Get detailed cache statistics."""
    cache = get_cache_manager()
    return cache.get_metrics()


@router.post("/cache/clear")
async def clear_cache(
    current_user: User = Depends(require_admin),
):
    """Clear all caches."""
    cache = get_cache_manager()
    await cache.local.clear()
    
    return {"message": "Cache cleared"}


@router.post("/cache/warm")
async def warm_cache(
    workflow_ids: list,
    current_user: User = Depends(require_admin),
):
    """Pre-warm cache with specified workflows."""
    cache = get_cache_manager()
    await cache.warm_cache(workflow_ids)
    
    return {
        "message": f"Warmed cache for {len(workflow_ids)} workflows",
        "workflow_ids": workflow_ids,
    }
