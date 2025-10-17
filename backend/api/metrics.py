"""
Metrics API Endpoints

Provides access to system metrics including adaptive routing metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
from datetime import timedelta

from backend.core.metrics_collector import get_metrics_collector
from backend.services.adaptive_metrics import get_adaptive_metrics_service

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/prometheus")
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus format.

    Returns:
        Prometheus-formatted metrics
    """
    metrics_collector = get_metrics_collector()

    if not metrics_collector.enabled:
        raise HTTPException(status_code=503, detail="Metrics collection is not enabled")

    metrics_data = metrics_collector.get_metrics()

    return Response(content=metrics_data, media_type="text/plain; version=0.0.4")


@router.get("/adaptive")
async def get_adaptive_metrics():
    """
    Get adaptive routing metrics for dashboard.

    Returns comprehensive metrics including:
    - Mode distribution
    - Complexity distribution
    - Latency by mode
    - Cache performance
    - Escalation rates
    - User satisfaction
    - Active alerts

    Returns:
        Dictionary with dashboard-ready metrics
    """
    adaptive_metrics = get_adaptive_metrics_service()

    try:
        dashboard_data = await adaptive_metrics.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve adaptive metrics: {str(e)}"
        )


@router.get("/adaptive/timeseries")
async def get_adaptive_timeseries(
    metric: str = Query(
        ..., description="Metric name (latency, mode_distribution, cache_hit_rate)"
    ),
    hours: Optional[int] = Query(None, description="Time range in hours"),
):
    """
    Get time-series data for a specific metric.

    Args:
        metric: Metric name (latency, mode_distribution, cache_hit_rate)
        hours: Time range in hours (optional)

    Returns:
        List of time-series data points
    """
    adaptive_metrics = get_adaptive_metrics_service()

    time_range = timedelta(hours=hours) if hours else None

    try:
        timeseries_data = await adaptive_metrics.get_time_series_data(
            metric=metric, time_range=time_range
        )
        return {"metric": metric, "time_range_hours": hours, "data": timeseries_data}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve time-series data: {str(e)}"
        )


@router.get("/adaptive/alerts")
async def get_adaptive_alerts():
    """
    Get active performance alerts.

    Returns:
        List of active alerts with recommendations
    """
    adaptive_metrics = get_adaptive_metrics_service()

    try:
        dashboard_data = await adaptive_metrics.get_dashboard_data()
        return {
            "alerts": dashboard_data.get("alerts", []),
            "total": len(dashboard_data.get("alerts", [])),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alerts: {str(e)}"
        )


@router.post("/adaptive/snapshot")
async def create_metrics_snapshot():
    """
    Create a snapshot of current metrics for time-series analysis.

    This endpoint should be called periodically (e.g., every minute)
    to build time-series data.

    Returns:
        Success message
    """
    adaptive_metrics = get_adaptive_metrics_service()

    try:
        await adaptive_metrics.create_snapshot()
        return {"status": "success", "message": "Metrics snapshot created"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create snapshot: {str(e)}"
        )


@router.get("/stats")
async def get_stats():
    """
    Get general system statistics.

    Returns:
        Dictionary of system stats
    """
    metrics_collector = get_metrics_collector()

    return metrics_collector.get_stats()
