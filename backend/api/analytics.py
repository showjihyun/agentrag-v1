"""
Analytics API endpoints for performance monitoring.

Provides insights on path effectiveness, mode usage patterns,
and performance reports for the hybrid RAG system.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from backend.services.performance_monitor import PerformanceMonitor
from backend.core.dependencies import get_performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class TimingAnalytics(BaseModel):
    """Timing analytics response model."""

    total_queries: int = Field(..., description="Total number of queries processed")
    time_window_hours: int = Field(..., description="Time window for statistics")
    avg_speculative_time: Optional[float] = Field(
        None, description="Average speculative path time in seconds"
    )
    avg_agentic_time: Optional[float] = Field(
        None, description="Average agentic path time in seconds"
    )
    avg_total_time: Optional[float] = Field(
        None, description="Average total processing time in seconds"
    )
    speculative_first_percentage: Optional[float] = Field(
        None, description="Percentage of queries where speculative path completed first"
    )
    agentic_first_percentage: Optional[float] = Field(
        None, description="Percentage of queries where agentic path completed first"
    )
    fast_mode_count: int = Field(0, description="Number of FAST mode queries")
    balanced_mode_count: int = Field(0, description="Number of BALANCED mode queries")
    deep_mode_count: int = Field(0, description="Number of DEEP mode queries")


class ConfidenceAnalytics(BaseModel):
    """Confidence score analytics response model."""

    time_window_hours: int = Field(..., description="Time window for statistics")
    avg_speculative_confidence: Optional[float] = Field(
        None, description="Average confidence score from speculative path"
    )
    avg_agentic_confidence: Optional[float] = Field(
        None, description="Average confidence score from agentic path"
    )
    avg_confidence_improvement: Optional[float] = Field(
        None,
        description="Average improvement in confidence from speculative to agentic",
    )


class ErrorAnalytics(BaseModel):
    """Error rate analytics response model."""

    total_errors: int = Field(..., description="Total number of errors")
    total_queries: int = Field(..., description="Total number of queries")
    error_rate: float = Field(..., description="Overall error rate (0-1)")
    time_window_hours: int = Field(..., description="Time window for statistics")
    speculative_errors: int = Field(0, description="Errors in speculative path")
    speculative_error_rate: Optional[float] = Field(
        None, description="Error rate for speculative path"
    )
    agentic_errors: int = Field(0, description="Errors in agentic path")
    agentic_error_rate: Optional[float] = Field(
        None, description="Error rate for agentic path"
    )
    hybrid_errors: int = Field(0, description="Errors in hybrid coordination")
    hybrid_error_rate: Optional[float] = Field(
        None, description="Error rate for hybrid coordination"
    )
    error_types: dict = Field(
        default_factory=dict, description="Breakdown of errors by type"
    )


class ModeUsageAnalytics(BaseModel):
    """Mode usage analytics response model."""

    fast: int = Field(0, description="Number of FAST mode queries")
    balanced: int = Field(0, description="Number of BALANCED mode queries")
    deep: int = Field(0, description="Number of DEEP mode queries")
    total: int = Field(0, description="Total number of queries")


class PathEffectivenessReport(BaseModel):
    """Path effectiveness report combining multiple metrics."""

    timing: TimingAnalytics
    confidence: ConfidenceAnalytics
    errors: ErrorAnalytics
    mode_usage: ModeUsageAnalytics
    insights: list[str] = Field(
        default_factory=list, description="Key insights and recommendations"
    )


class AlertResponse(BaseModel):
    """Performance alert response model."""

    category: str = Field(..., description="Alert category (timing/error)")
    alert_type: str = Field(..., description="Type of alert")
    timestamp: str = Field(..., description="When the alert was triggered")
    details: dict = Field(default_factory=dict, description="Alert details")


@router.get(
    "/timing",
    response_model=TimingAnalytics,
    summary="Get timing analytics",
    description="Retrieve timing metrics for path performance analysis",
)
async def get_timing_analytics(
    time_window_hours: int = Query(
        24, ge=1, le=168, description="Time window in hours (1-168)"
    ),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
) -> TimingAnalytics:
    """
    Get timing analytics for the hybrid RAG system.

    Provides insights on:
    - Average processing times for each path
    - Which path typically completes first
    - Mode usage distribution

    Requirements: 11.1, 11.3, 11.6
    """
    try:
        stats = await monitor.get_timing_stats(time_window_hours=time_window_hours)

        if not stats:
            # Return empty stats if no data
            return TimingAnalytics(total_queries=0, time_window_hours=time_window_hours)

        return TimingAnalytics(**stats)

    except Exception as e:
        logger.error(f"Failed to get timing analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve timing analytics"
        )


@router.get(
    "/confidence",
    response_model=ConfidenceAnalytics,
    summary="Get confidence score analytics",
    description="Retrieve confidence score metrics and improvement tracking",
)
async def get_confidence_analytics(
    time_window_hours: int = Query(
        24, ge=1, le=168, description="Time window in hours (1-168)"
    ),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
) -> ConfidenceAnalytics:
    """
    Get confidence score analytics.

    Provides insights on:
    - Average confidence scores from each path
    - Confidence improvement from speculative to agentic

    Requirements: 11.2, 11.6
    """
    try:
        stats = await monitor.get_confidence_stats(time_window_hours=time_window_hours)

        if not stats:
            return ConfidenceAnalytics(time_window_hours=time_window_hours)

        return ConfidenceAnalytics(**stats)

    except Exception as e:
        logger.error(f"Failed to get confidence analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve confidence analytics"
        )


@router.get(
    "/errors",
    response_model=ErrorAnalytics,
    summary="Get error rate analytics",
    description="Retrieve error metrics and failure rate analysis",
)
async def get_error_analytics(
    time_window_hours: int = Query(
        24, ge=1, le=168, description="Time window in hours (1-168)"
    ),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
) -> ErrorAnalytics:
    """
    Get error rate analytics.

    Provides insights on:
    - Overall error rates
    - Per-path failure rates
    - Error type distribution

    Requirements: 11.4, 11.5, 11.6
    """
    try:
        stats = await monitor.get_error_stats(time_window_hours=time_window_hours)

        if not stats:
            return ErrorAnalytics(
                total_errors=0,
                total_queries=0,
                error_rate=0.0,
                time_window_hours=time_window_hours,
            )

        return ErrorAnalytics(**stats)

    except Exception as e:
        logger.error(f"Failed to get error analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve error analytics"
        )


@router.get(
    "/mode-usage",
    response_model=ModeUsageAnalytics,
    summary="Get mode usage analytics",
    description="Retrieve statistics on query mode usage patterns",
)
async def get_mode_usage_analytics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
) -> ModeUsageAnalytics:
    """
    Get mode usage analytics.

    Provides insights on:
    - How frequently each mode is used
    - Mode preference patterns

    Requirements: 11.6
    """
    try:
        stats = await monitor.get_mode_usage_stats()

        fast_count = stats.get("fast", 0)
        balanced_count = stats.get("balanced", 0)
        deep_count = stats.get("deep", 0)

        return ModeUsageAnalytics(
            fast=fast_count,
            balanced=balanced_count,
            deep=deep_count,
            total=fast_count + balanced_count + deep_count,
        )

    except Exception as e:
        logger.error(f"Failed to get mode usage analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve mode usage analytics"
        )


@router.get(
    "/path-effectiveness",
    response_model=PathEffectivenessReport,
    summary="Get comprehensive path effectiveness report",
    description="Retrieve a comprehensive report on path effectiveness with insights",
)
async def get_path_effectiveness_report(
    time_window_hours: int = Query(
        24, ge=1, le=168, description="Time window in hours (1-168)"
    ),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
) -> PathEffectivenessReport:
    """
    Get comprehensive path effectiveness report.

    Combines timing, confidence, error, and mode usage metrics
    with actionable insights and recommendations.

    Requirements: 11.6
    """
    try:
        # Gather all metrics
        timing_stats = await monitor.get_timing_stats(time_window_hours)
        confidence_stats = await monitor.get_confidence_stats(time_window_hours)
        error_stats = await monitor.get_error_stats(time_window_hours)
        mode_usage_stats = await monitor.get_mode_usage_stats()

        # Create response models
        timing = TimingAnalytics(
            **(
                timing_stats
                if timing_stats
                else {"total_queries": 0, "time_window_hours": time_window_hours}
            )
        )

        confidence = ConfidenceAnalytics(
            **(
                confidence_stats
                if confidence_stats
                else {"time_window_hours": time_window_hours}
            )
        )

        # Ensure error_stats has all required fields
        if error_stats:
            # Add missing required fields if not present
            if "total_queries" not in error_stats:
                error_stats["total_queries"] = 0
            if "time_window_hours" not in error_stats:
                error_stats["time_window_hours"] = time_window_hours
            errors = ErrorAnalytics(**error_stats)
        else:
            errors = ErrorAnalytics(
                total_errors=0,
                total_queries=0,
                error_rate=0.0,
                time_window_hours=time_window_hours,
            )

        fast_count = mode_usage_stats.get("fast", 0)
        balanced_count = mode_usage_stats.get("balanced", 0)
        deep_count = mode_usage_stats.get("deep", 0)

        mode_usage = ModeUsageAnalytics(
            fast=fast_count,
            balanced=balanced_count,
            deep=deep_count,
            total=fast_count + balanced_count + deep_count,
        )

        # Generate insights
        insights = _generate_insights(timing, confidence, errors, mode_usage)

        return PathEffectivenessReport(
            timing=timing,
            confidence=confidence,
            errors=errors,
            mode_usage=mode_usage,
            insights=insights,
        )

    except Exception as e:
        logger.error(f"Failed to generate path effectiveness report: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate path effectiveness report"
        )


@router.get(
    "/alerts",
    response_model=list[AlertResponse],
    summary="Get recent performance alerts",
    description="Retrieve recent performance degradation alerts",
)
async def get_recent_alerts(
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of alerts to return"
    ),
    monitor: PerformanceMonitor = Depends(get_performance_monitor),
) -> list[AlertResponse]:
    """
    Get recent performance alerts.

    Returns alerts for:
    - Slow response times
    - High error rates
    - Performance degradation

    Requirements: 11.5
    """
    try:
        alerts = await monitor.get_recent_alerts(limit=limit)

        # Convert to response model
        response_alerts = []
        for alert in alerts:
            category = alert.pop("category", "unknown")
            alert_type = alert.pop("alert_type", "unknown")
            timestamp = alert.pop("timestamp", "")

            response_alerts.append(
                AlertResponse(
                    category=category,
                    alert_type=alert_type,
                    timestamp=timestamp,
                    details=alert,
                )
            )

        return response_alerts

    except Exception as e:
        logger.error(f"Failed to get recent alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent alerts")


def _generate_insights(
    timing: TimingAnalytics,
    confidence: ConfidenceAnalytics,
    errors: ErrorAnalytics,
    mode_usage: ModeUsageAnalytics,
) -> list[str]:
    """
    Generate actionable insights from analytics data.

    Args:
        timing: Timing analytics
        confidence: Confidence analytics
        errors: Error analytics
        mode_usage: Mode usage analytics

    Returns:
        List of insight strings
    """
    insights = []

    # Timing insights
    if timing.avg_speculative_time and timing.avg_agentic_time:
        speedup = timing.avg_agentic_time / timing.avg_speculative_time
        insights.append(
            f"Speculative path is {speedup:.1f}x faster than agentic path on average"
        )

    if timing.speculative_first_percentage:
        if timing.speculative_first_percentage > 90:
            insights.append(
                "Speculative path completes first in >90% of queries, "
                "providing excellent user experience"
            )
        elif timing.speculative_first_percentage < 50:
            insights.append(
                "Speculative path is slower than expected in many queries, "
                "consider optimizing vector search or caching"
            )

    # Confidence insights
    if confidence.avg_confidence_improvement:
        if confidence.avg_confidence_improvement > 0.1:
            insights.append(
                f"Agentic path provides significant confidence improvement "
                f"(+{confidence.avg_confidence_improvement:.2f} on average)"
            )
        elif confidence.avg_confidence_improvement < 0.05:
            insights.append(
                "Agentic path provides minimal confidence improvement, "
                "consider if FAST mode would be sufficient for most queries"
            )

    # Error insights
    if errors.error_rate > 0.05:
        insights.append(
            f"Error rate is elevated at {errors.error_rate:.1%}, "
            f"investigate common failure patterns"
        )

    if errors.speculative_error_rate and errors.speculative_error_rate > 0.1:
        insights.append(
            "Speculative path has high error rate, "
            "check vector search and LLM availability"
        )

    if errors.agentic_error_rate and errors.agentic_error_rate > 0.1:
        insights.append(
            "Agentic path has high error rate, "
            "check agent orchestration and timeout settings"
        )

    # Mode usage insights
    if mode_usage.total > 0:
        fast_pct = (mode_usage.fast / mode_usage.total) * 100
        balanced_pct = (mode_usage.balanced / mode_usage.total) * 100
        deep_pct = (mode_usage.deep / mode_usage.total) * 100

        if fast_pct > 60:
            insights.append(
                f"FAST mode is heavily used ({fast_pct:.0f}%), "
                f"users prioritize speed over depth"
            )
        elif deep_pct > 60:
            insights.append(
                f"DEEP mode is heavily used ({deep_pct:.0f}%), "
                f"users prioritize comprehensive analysis"
            )
        elif balanced_pct > 60:
            insights.append(
                f"BALANCED mode is most popular ({balanced_pct:.0f}%), "
                f"users value progressive refinement"
            )

    # Performance recommendations
    if timing.avg_total_time and timing.avg_total_time > 10:
        insights.append(
            "Average response time exceeds 10 seconds, "
            "consider optimizing agentic path or reducing timeout"
        )

    if not insights:
        insights.append("System is performing within normal parameters")

    return insights
