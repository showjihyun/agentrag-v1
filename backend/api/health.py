"""Health check and monitoring endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Optional

from backend.db.database import get_db
from backend.core.monitoring import metrics_collector, HealthChecker

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> Dict:
    """
    Basic health check endpoint.

    Returns system health status.
    """
    return {"status": "healthy", "service": "Agentic RAG System", "version": "1.0.0"}


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict:
    """
    Detailed health check with component status.

    Checks:
    - Database connectivity
    - System resources
    - Service health
    """
    # Check database
    db_health = HealthChecker.check_database(db)

    # Get system health
    system_health = metrics_collector.get_system_health()

    # Determine overall status
    overall_status = "healthy"
    if db_health["status"] != "healthy":
        overall_status = "unhealthy"
    elif system_health["status"] in ["warning", "critical"]:
        overall_status = system_health["status"]

    return {
        "status": overall_status,
        "timestamp": system_health["timestamp"],
        "components": {"database": db_health, "system": system_health},
    }


@router.get("/metrics")
async def get_metrics() -> Dict:
    """
    Get system metrics.

    Returns performance and usage metrics.
    """
    # Collect current system metrics
    system_metrics = metrics_collector.collect_system_metrics()

    # Get performance trends
    trends = metrics_collector.get_performance_trends(minutes=60)

    # Get endpoint statistics
    endpoint_stats = metrics_collector.get_endpoint_stats()

    return {
        "system": {
            "cpu_percent": system_metrics.cpu_percent,
            "memory_percent": system_metrics.memory_percent,
            "memory_used_mb": round(system_metrics.memory_used_mb, 2),
            "disk_usage_percent": system_metrics.disk_usage_percent,
        },
        "performance": trends,
        "endpoints": endpoint_stats,
    }


@router.get("/errors")
async def get_error_summary(limit: int = 10) -> Dict:
    """
    Get error summary.

    Returns most common errors.
    """
    errors = metrics_collector.get_error_summary(limit=limit)

    return {
        "errors": errors,
        "total_unique_errors": len(metrics_collector.error_counts),
    }


@router.get("/requests/recent")
async def get_recent_requests(
    limit: int = 100, status_code: Optional[int] = None
) -> Dict:
    """
    Get recent requests.

    Args:
        limit: Maximum number of requests to return
        status_code: Filter by status code (optional)
    """
    requests = metrics_collector.get_recent_requests(
        limit=limit, status_code=status_code
    )

    return {"requests": requests, "count": len(requests)}


@router.post("/metrics/reset")
async def reset_metrics() -> Dict:
    """
    Reset collected metrics.
    """
    metrics_collector.reset_metrics()

    return {"message": "Metrics reset successfully"}
