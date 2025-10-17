# Monitoring Dashboard API
from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from backend.services.metrics_collector import get_metrics_collector, MetricStats
from backend.core.auth_dependencies import get_optional_user
from backend.db.models.user import User

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class MetricStatsResponse(BaseModel):
    """Metric statistics response"""

    metric_name: str
    time_window_minutes: int
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float


class CacheMetricsResponse(BaseModel):
    """Cache metrics response"""

    cache_type: str
    hit_rate: float
    time_window_minutes: int


class AgentMetricsResponse(BaseModel):
    """Agent metrics response"""

    agent_name: str
    success_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    time_window_minutes: int


class SystemMetricsResponse(BaseModel):
    """Overall system metrics"""

    timestamp: datetime
    query_metrics: Optional[MetricStatsResponse]
    cache_metrics: List[CacheMetricsResponse]
    agent_metrics: List[AgentMetricsResponse]
    llm_metrics: Optional[Dict[str, Any]]


@router.get("/metrics/query", response_model=MetricStatsResponse)
async def get_query_metrics(
    time_window: int = Query(60, description="Time window in minutes"),
    mode: Optional[str] = Query(None, description="Query mode filter"),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get query performance metrics.

    Returns latency statistics for queries.
    """
    collector = get_metrics_collector()

    labels = {"mode": mode} if mode else None
    stats = await collector.get_stats(
        "query_latency_ms", time_window_minutes=time_window, labels=labels
    )

    if not stats:
        return MetricStatsResponse(
            metric_name="query_latency_ms",
            time_window_minutes=time_window,
            count=0,
            sum=0.0,
            min=0.0,
            max=0.0,
            avg=0.0,
            p50=0.0,
            p95=0.0,
            p99=0.0,
        )

    return MetricStatsResponse(
        metric_name="query_latency_ms",
        time_window_minutes=time_window,
        count=stats.count,
        sum=stats.sum,
        min=stats.min,
        max=stats.max,
        avg=stats.avg,
        p50=stats.p50,
        p95=stats.p95,
        p99=stats.p99,
    )


@router.get("/metrics/cache", response_model=List[CacheMetricsResponse])
async def get_cache_metrics(
    time_window: int = Query(60, description="Time window in minutes"),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get cache performance metrics.

    Returns hit rates for different cache types.
    """
    collector = get_metrics_collector()

    cache_types = ["semantic", "l1", "l2", "llm"]
    results = []

    for cache_type in cache_types:
        hit_rate = await collector.get_cache_hit_rate(
            cache_type, time_window_minutes=time_window
        )

        results.append(
            CacheMetricsResponse(
                cache_type=cache_type,
                hit_rate=hit_rate,
                time_window_minutes=time_window,
            )
        )

    return results


@router.get("/metrics/agents", response_model=List[AgentMetricsResponse])
async def get_agent_metrics(
    time_window: int = Query(60, description="Time window in minutes"),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get agent performance metrics.

    Returns success rates and latency for each agent.
    """
    collector = get_metrics_collector()

    agent_names = ["vector_search", "web_search", "local_data", "aggregator"]
    results = []

    for agent_name in agent_names:
        success_rate = await collector.get_agent_success_rate(
            agent_name, time_window_minutes=time_window
        )

        stats = await collector.get_stats(
            "agent_latency_ms",
            time_window_minutes=time_window,
            labels={"agent": agent_name},
        )

        results.append(
            AgentMetricsResponse(
                agent_name=agent_name,
                success_rate=success_rate,
                avg_latency_ms=stats.avg if stats else 0.0,
                p95_latency_ms=stats.p95 if stats else 0.0,
                time_window_minutes=time_window,
            )
        )

    return results


@router.get("/metrics/system", response_model=SystemMetricsResponse)
async def get_system_metrics(
    time_window: int = Query(60, description="Time window in minutes"),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get comprehensive system metrics.

    Returns all key metrics in a single response.
    """
    collector = get_metrics_collector()

    # Query metrics
    query_stats = await collector.get_stats(
        "query_latency_ms", time_window_minutes=time_window
    )

    query_metrics = None
    if query_stats:
        query_metrics = MetricStatsResponse(
            metric_name="query_latency_ms",
            time_window_minutes=time_window,
            count=query_stats.count,
            sum=query_stats.sum,
            min=query_stats.min,
            max=query_stats.max,
            avg=query_stats.avg,
            p50=query_stats.p50,
            p95=query_stats.p95,
            p99=query_stats.p99,
        )

    # Cache metrics
    cache_types = ["semantic", "l1", "l2", "llm"]
    cache_metrics = []

    for cache_type in cache_types:
        hit_rate = await collector.get_cache_hit_rate(
            cache_type, time_window_minutes=time_window
        )

        cache_metrics.append(
            CacheMetricsResponse(
                cache_type=cache_type,
                hit_rate=hit_rate,
                time_window_minutes=time_window,
            )
        )

    # Agent metrics
    agent_names = ["vector_search", "web_search", "local_data", "aggregator"]
    agent_metrics = []

    for agent_name in agent_names:
        success_rate = await collector.get_agent_success_rate(
            agent_name, time_window_minutes=time_window
        )

        stats = await collector.get_stats(
            "agent_latency_ms",
            time_window_minutes=time_window,
            labels={"agent": agent_name},
        )

        agent_metrics.append(
            AgentMetricsResponse(
                agent_name=agent_name,
                success_rate=success_rate,
                avg_latency_ms=stats.avg if stats else 0.0,
                p95_latency_ms=stats.p95 if stats else 0.0,
                time_window_minutes=time_window,
            )
        )

    # LLM metrics
    llm_stats = await collector.get_stats(
        "llm_latency_ms", time_window_minutes=time_window
    )

    llm_metrics = None
    if llm_stats:
        llm_metrics = {
            "avg_latency_ms": llm_stats.avg,
            "p95_latency_ms": llm_stats.p95,
            "total_requests": llm_stats.count,
        }

    return SystemMetricsResponse(
        timestamp=datetime.utcnow(),
        query_metrics=query_metrics,
        cache_metrics=cache_metrics,
        agent_metrics=agent_metrics,
        llm_metrics=llm_metrics,
    )
