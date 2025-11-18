"""
Tool Performance Metrics API endpoints.
Track and analyze tool execution performance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import random

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

router = APIRouter()


class ToolMetrics(BaseModel):
    """Tool performance metrics model."""
    tool_id: str
    tool_name: str
    
    # Execution metrics
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    
    # Performance metrics
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    p50_execution_time_ms: float
    p95_execution_time_ms: float
    p99_execution_time_ms: float
    
    # Cost metrics
    total_cost: float
    avg_cost_per_execution: float
    
    # Cache metrics
    cache_hit_rate: float
    cache_hits: int
    cache_misses: int
    
    # Time range
    time_range: str
    last_updated: datetime


class ToolPerformanceData(BaseModel):
    """Time-series performance data."""
    timestamp: datetime
    executions: int
    success_rate: float
    avg_execution_time_ms: float
    cost: float


class ToolAlert(BaseModel):
    """Tool performance alert."""
    id: str
    tool_id: str
    alert_type: str  # "high_error_rate", "slow_execution", "high_cost"
    severity: str  # "info", "warning", "critical"
    message: str
    threshold: float
    current_value: float
    created_at: datetime
    resolved: bool


class OptimizationSuggestion(BaseModel):
    """AI-generated optimization suggestion."""
    id: str
    tool_id: str
    suggestion_type: str
    title: str
    description: str
    impact: str  # "low", "medium", "high"
    effort: str  # "low", "medium", "high"
    estimated_improvement: str
    created_at: datetime


def generate_mock_metrics(tool_id: str, time_range: str) -> ToolMetrics:
    """Generate mock metrics for demonstration."""
    
    # Calculate time range
    if time_range == "1h":
        total_executions = random.randint(50, 200)
    elif time_range == "24h":
        total_executions = random.randint(500, 2000)
    elif time_range == "7d":
        total_executions = random.randint(3000, 10000)
    elif time_range == "30d":
        total_executions = random.randint(10000, 50000)
    else:
        total_executions = random.randint(100, 1000)
    
    success_rate = random.uniform(0.92, 0.99)
    successful_executions = int(total_executions * success_rate)
    failed_executions = total_executions - successful_executions
    
    avg_time = random.uniform(100, 2000)
    
    return ToolMetrics(
        tool_id=tool_id,
        tool_name=tool_id.replace("_", " ").title(),
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        success_rate=round(success_rate * 100, 2),
        avg_execution_time_ms=round(avg_time, 2),
        min_execution_time_ms=round(avg_time * 0.3, 2),
        max_execution_time_ms=round(avg_time * 3.5, 2),
        p50_execution_time_ms=round(avg_time * 0.9, 2),
        p95_execution_time_ms=round(avg_time * 2.1, 2),
        p99_execution_time_ms=round(avg_time * 2.8, 2),
        total_cost=round(total_executions * 0.001, 2),
        avg_cost_per_execution=0.001,
        cache_hit_rate=round(random.uniform(0.4, 0.8) * 100, 2),
        cache_hits=int(total_executions * random.uniform(0.4, 0.8)),
        cache_misses=int(total_executions * random.uniform(0.2, 0.6)),
        time_range=time_range,
        last_updated=datetime.utcnow()
    )


def generate_mock_performance_data(tool_id: str, time_range: str) -> List[ToolPerformanceData]:
    """Generate mock time-series performance data."""
    
    data = []
    
    # Determine number of data points
    if time_range == "1h":
        points = 12  # Every 5 minutes
        delta = timedelta(minutes=5)
    elif time_range == "24h":
        points = 24  # Every hour
        delta = timedelta(hours=1)
    elif time_range == "7d":
        points = 7  # Every day
        delta = timedelta(days=1)
    elif time_range == "30d":
        points = 30  # Every day
        delta = timedelta(days=1)
    else:
        points = 10
        delta = timedelta(hours=1)
    
    now = datetime.utcnow()
    
    for i in range(points):
        timestamp = now - (delta * (points - i - 1))
        data.append(ToolPerformanceData(
            timestamp=timestamp,
            executions=random.randint(10, 100),
            success_rate=round(random.uniform(92, 99), 2),
            avg_execution_time_ms=round(random.uniform(100, 2000), 2),
            cost=round(random.uniform(0.01, 0.5), 2)
        ))
    
    return data


@router.get("/tools/{tool_id}/metrics", response_model=ToolMetrics)
async def get_tool_metrics(
    tool_id: str,
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for a specific tool."""
    
    return generate_mock_metrics(tool_id, time_range)


@router.get("/tools/{tool_id}/performance", response_model=List[ToolPerformanceData])
async def get_tool_performance(
    tool_id: str,
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(get_current_user)
):
    """Get time-series performance data for a tool."""
    
    return generate_mock_performance_data(tool_id, time_range)


@router.get("/tools/{tool_id}/alerts", response_model=List[ToolAlert])
async def get_tool_alerts(
    tool_id: str,
    resolved: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get performance alerts for a tool."""
    
    alerts = [
        ToolAlert(
            id="alert-1",
            tool_id=tool_id,
            alert_type="high_error_rate",
            severity="warning",
            message="Error rate exceeded 5% threshold",
            threshold=5.0,
            current_value=6.2,
            created_at=datetime.utcnow() - timedelta(hours=2),
            resolved=False
        ),
        ToolAlert(
            id="alert-2",
            tool_id=tool_id,
            alert_type="slow_execution",
            severity="info",
            message="Average execution time increased by 30%",
            threshold=1000.0,
            current_value=1350.0,
            created_at=datetime.utcnow() - timedelta(hours=5),
            resolved=True
        )
    ]
    
    if resolved is not None:
        alerts = [a for a in alerts if a.resolved == resolved]
    
    return alerts


@router.post("/tools/{tool_id}/alerts")
async def create_tool_alert(
    tool_id: str,
    alert_type: str = Query(...),
    threshold: float = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new performance alert for a tool."""
    
    return {
        "success": True,
        "message": "Alert created successfully",
        "alert_id": "alert-new"
    }


@router.patch("/tools/{tool_id}/alerts/{alert_id}/resolve")
async def resolve_alert(
    tool_id: str,
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an alert as resolved."""
    
    return {
        "success": True,
        "message": "Alert resolved successfully"
    }


@router.get("/tools/{tool_id}/optimization-suggestions", response_model=List[OptimizationSuggestion])
async def get_optimization_suggestions(
    tool_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI-generated optimization suggestions for a tool."""
    
    suggestions = [
        OptimizationSuggestion(
            id="opt-1",
            tool_id=tool_id,
            suggestion_type="caching",
            title="Enable Response Caching",
            description="This tool makes repeated calls with similar parameters. Enabling caching could reduce execution time by 40% and cost by 35%.",
            impact="high",
            effort="low",
            estimated_improvement="40% faster, 35% cheaper",
            created_at=datetime.utcnow()
        ),
        OptimizationSuggestion(
            id="opt-2",
            tool_id=tool_id,
            suggestion_type="batching",
            title="Batch Multiple Requests",
            description="Consider batching multiple requests together to reduce overhead. This could improve throughput by 25%.",
            impact="medium",
            effort="medium",
            estimated_improvement="25% higher throughput",
            created_at=datetime.utcnow()
        ),
        OptimizationSuggestion(
            id="opt-3",
            tool_id=tool_id,
            suggestion_type="timeout",
            title="Optimize Timeout Settings",
            description="Current timeout is set too high. Reducing it to 10s could prevent hanging requests and improve overall reliability.",
            impact="medium",
            effort="low",
            estimated_improvement="Better reliability",
            created_at=datetime.utcnow()
        )
    ]
    
    return suggestions


@router.get("/tools/compare")
async def compare_tools(
    tool_ids: List[str] = Query(...),
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    current_user: User = Depends(get_current_user)
):
    """Compare performance metrics across multiple tools."""
    
    comparison = []
    
    for tool_id in tool_ids:
        metrics = generate_mock_metrics(tool_id, time_range)
        comparison.append(metrics)
    
    return {
        "tools": comparison,
        "time_range": time_range,
        "comparison_date": datetime.utcnow()
    }


@router.get("/tools/leaderboard")
async def get_tools_leaderboard(
    metric: str = Query("success_rate", regex="^(success_rate|avg_execution_time_ms|total_executions)$"),
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get top performing tools leaderboard."""
    
    # Mock tool IDs
    tool_ids = [
        "http_request", "llm_call", "calculator", "vector_search",
        "python_executor", "csv_parser", "json_transformer", "web_search"
    ]
    
    leaderboard = []
    for tool_id in tool_ids[:limit]:
        metrics = generate_mock_metrics(tool_id, time_range)
        leaderboard.append({
            "tool_id": tool_id,
            "tool_name": metrics.tool_name,
            "metric_value": getattr(metrics, metric),
            "rank": len(leaderboard) + 1
        })
    
    # Sort by metric
    reverse = metric in ["success_rate", "total_executions"]
    leaderboard.sort(key=lambda x: x["metric_value"], reverse=reverse)
    
    # Update ranks
    for i, item in enumerate(leaderboard):
        item["rank"] = i + 1
    
    return {
        "leaderboard": leaderboard,
        "metric": metric,
        "time_range": time_range
    }
