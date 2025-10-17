"""
Adaptive Metrics Service

Collects and analyzes metrics for the adaptive routing system.
Tracks query complexity distribution, mode selection, latency, cache performance,
and user satisfaction.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
from collections import defaultdict, deque
import statistics

from backend.models.hybrid import QueryMode
from backend.services.adaptive_rag_service import QueryComplexity


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""

    timestamp: datetime
    mode_distribution: Dict[str, float]
    complexity_distribution: Dict[str, float]
    avg_latency_by_mode: Dict[str, float]
    cache_hit_rate_by_mode: Dict[str, float]
    escalation_rate: float
    user_satisfaction_by_mode: Dict[str, float]
    total_queries: int


@dataclass
class PerformanceAlert:
    """Performance degradation alert."""

    level: AlertLevel
    metric: str
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AdaptiveMetrics:
    """Comprehensive adaptive routing metrics."""

    # Distribution metrics
    mode_distribution: Dict[str, int]
    complexity_distribution: Dict[str, int]

    # Performance metrics
    latency_by_mode: Dict[str, List[float]]
    latency_by_complexity: Dict[str, List[float]]

    # Cache metrics
    cache_hits_by_mode: Dict[str, int]
    cache_misses_by_mode: Dict[str, int]

    # Escalation metrics
    escalations: Dict[str, int]  # from_mode -> to_mode

    # User satisfaction
    satisfaction_by_mode: Dict[str, List[float]]

    # Routing metrics
    routing_confidence: List[float]
    routing_time: List[float]

    # Threshold history
    threshold_history: List[Dict[str, Any]]

    # Time range
    start_time: datetime
    end_time: datetime

    # Total counts
    total_queries: int = 0


class AdaptiveMetricsService:
    """
    Service for collecting and analyzing adaptive routing metrics.

    Provides real-time metrics, performance analysis, and alerting.
    """

    def __init__(self, max_history_size: int = 10000):
        """
        Initialize metrics service.

        Args:
            max_history_size: Maximum number of metric entries to keep in memory
        """
        self.max_history_size = max_history_size

        # Current metrics
        self.mode_counts = defaultdict(int)
        self.complexity_counts = defaultdict(int)
        self.latency_by_mode = defaultdict(list)
        self.latency_by_complexity = defaultdict(list)
        self.cache_hits_by_mode = defaultdict(int)
        self.cache_misses_by_mode = defaultdict(int)
        self.escalations = defaultdict(int)
        self.satisfaction_by_mode = defaultdict(list)
        self.routing_confidence = deque(maxlen=max_history_size)
        self.routing_time = deque(maxlen=max_history_size)
        self.threshold_history = []

        # Time-series data for trends
        self.snapshots = deque(maxlen=1000)  # Keep last 1000 snapshots

        # Alerts
        self.active_alerts = []

        # Start time
        self.start_time = datetime.now()

        # Total queries
        self.total_queries = 0

        # Performance thresholds
        self.thresholds = {
            "fast_mode_latency_p95": 1.0,
            "balanced_mode_latency_p95": 3.0,
            "deep_mode_latency_p95": 15.0,
            "cache_hit_rate_min": 0.3,
            "escalation_rate_max": 0.15,
            "user_satisfaction_min": 4.0,
        }

    async def record_query(
        self,
        query_id: str,
        mode: QueryMode,
        complexity: QueryComplexity,
        latency: float,
        cache_hit: bool,
        routing_confidence: float,
        routing_time: float,
        escalated: bool = False,
        escalated_from: Optional[QueryMode] = None,
        user_satisfaction: Optional[float] = None,
    ):
        """
        Record metrics for a single query.

        Args:
            query_id: Unique query identifier
            mode: Processing mode used
            complexity: Query complexity
            latency: Processing time in seconds
            cache_hit: Whether result was cached
            routing_confidence: Confidence in routing decision
            routing_time: Time spent on routing
            escalated: Whether mode was escalated
            escalated_from: Original mode if escalated
            user_satisfaction: User rating (1-5)
        """
        self.total_queries += 1

        # Record mode distribution
        self.mode_counts[mode.value] += 1

        # Record complexity distribution
        self.complexity_counts[complexity.value] += 1

        # Record latency
        self.latency_by_mode[mode.value].append(latency)
        self.latency_by_complexity[complexity.value].append(latency)

        # Trim latency lists if too large
        if len(self.latency_by_mode[mode.value]) > self.max_history_size:
            self.latency_by_mode[mode.value] = self.latency_by_mode[mode.value][
                -self.max_history_size :
            ]
        if len(self.latency_by_complexity[complexity.value]) > self.max_history_size:
            self.latency_by_complexity[complexity.value] = self.latency_by_complexity[
                complexity.value
            ][-self.max_history_size :]

        # Record cache performance
        if cache_hit:
            self.cache_hits_by_mode[mode.value] += 1
        else:
            self.cache_misses_by_mode[mode.value] += 1

        # Record escalation
        if escalated and escalated_from:
            escalation_key = f"{escalated_from.value}_to_{mode.value}"
            self.escalations[escalation_key] += 1

        # Record user satisfaction
        if user_satisfaction is not None:
            self.satisfaction_by_mode[mode.value].append(user_satisfaction)
            if len(self.satisfaction_by_mode[mode.value]) > self.max_history_size:
                self.satisfaction_by_mode[mode.value] = self.satisfaction_by_mode[
                    mode.value
                ][-self.max_history_size :]

        # Record routing metrics
        self.routing_confidence.append(routing_confidence)
        self.routing_time.append(routing_time)

        # Check for performance degradation
        await self._check_performance_alerts()

    async def record_threshold_change(
        self, simple_threshold: float, complex_threshold: float, reason: str
    ):
        """
        Record threshold adjustment.

        Args:
            simple_threshold: New simple/medium threshold
            complex_threshold: New medium/complex threshold
            reason: Reason for adjustment
        """
        self.threshold_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "simple_threshold": simple_threshold,
                "complex_threshold": complex_threshold,
                "reason": reason,
            }
        )

    async def get_current_metrics(self) -> AdaptiveMetrics:
        """
        Get current metrics snapshot.

        Returns:
            AdaptiveMetrics object with current data
        """
        return AdaptiveMetrics(
            mode_distribution=dict(self.mode_counts),
            complexity_distribution=dict(self.complexity_counts),
            latency_by_mode={k: list(v) for k, v in self.latency_by_mode.items()},
            latency_by_complexity={
                k: list(v) for k, v in self.latency_by_complexity.items()
            },
            cache_hits_by_mode=dict(self.cache_hits_by_mode),
            cache_misses_by_mode=dict(self.cache_misses_by_mode),
            escalations=dict(self.escalations),
            satisfaction_by_mode={
                k: list(v) for k, v in self.satisfaction_by_mode.items()
            },
            routing_confidence=list(self.routing_confidence),
            routing_time=list(self.routing_time),
            threshold_history=list(self.threshold_history),
            start_time=self.start_time,
            end_time=datetime.now(),
            total_queries=self.total_queries,
        )

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get formatted data for dashboard visualization.

        Returns:
            Dictionary with dashboard-ready metrics
        """
        metrics = await self.get_current_metrics()

        # Calculate percentages for mode distribution
        total = sum(metrics.mode_distribution.values()) or 1
        mode_percentages = {
            mode: (count / total) * 100
            for mode, count in metrics.mode_distribution.items()
        }

        # Calculate average latencies
        avg_latency_by_mode = {}
        p95_latency_by_mode = {}
        for mode, latencies in metrics.latency_by_mode.items():
            if latencies:
                avg_latency_by_mode[mode] = statistics.mean(latencies)
                p95_latency_by_mode[mode] = self._calculate_percentile(latencies, 95)

        # Calculate cache hit rates
        cache_hit_rates = {}
        for mode in set(
            list(metrics.cache_hits_by_mode.keys())
            + list(metrics.cache_misses_by_mode.keys())
        ):
            hits = metrics.cache_hits_by_mode.get(mode, 0)
            misses = metrics.cache_misses_by_mode.get(mode, 0)
            total_requests = hits + misses
            if total_requests > 0:
                cache_hit_rates[mode] = (hits / total_requests) * 100
            else:
                cache_hit_rates[mode] = 0.0

        # Calculate escalation rate
        total_escalations = sum(metrics.escalations.values())
        escalation_rate = (total_escalations / total) * 100 if total > 0 else 0.0

        # Calculate average user satisfaction
        avg_satisfaction_by_mode = {}
        for mode, ratings in metrics.satisfaction_by_mode.items():
            if ratings:
                avg_satisfaction_by_mode[mode] = statistics.mean(ratings)

        # Calculate routing metrics
        avg_routing_confidence = (
            statistics.mean(metrics.routing_confidence)
            if metrics.routing_confidence
            else 0.0
        )
        avg_routing_time = (
            statistics.mean(metrics.routing_time) if metrics.routing_time else 0.0
        )

        return {
            "overview": {
                "total_queries": metrics.total_queries,
                "time_range": {
                    "start": metrics.start_time.isoformat(),
                    "end": metrics.end_time.isoformat(),
                },
                "avg_routing_confidence": round(avg_routing_confidence, 3),
                "avg_routing_time_ms": round(avg_routing_time * 1000, 2),
            },
            "mode_distribution": {
                "counts": metrics.mode_distribution,
                "percentages": {k: round(v, 1) for k, v in mode_percentages.items()},
            },
            "complexity_distribution": metrics.complexity_distribution,
            "latency": {
                "average_by_mode": {
                    k: round(v, 3) for k, v in avg_latency_by_mode.items()
                },
                "p95_by_mode": {k: round(v, 3) for k, v in p95_latency_by_mode.items()},
            },
            "cache_performance": {
                "hit_rates": {k: round(v, 1) for k, v in cache_hit_rates.items()},
                "hits_by_mode": metrics.cache_hits_by_mode,
                "misses_by_mode": metrics.cache_misses_by_mode,
            },
            "escalations": {
                "total": total_escalations,
                "rate_percent": round(escalation_rate, 1),
                "by_transition": metrics.escalations,
            },
            "user_satisfaction": {
                "average_by_mode": {
                    k: round(v, 2) for k, v in avg_satisfaction_by_mode.items()
                }
            },
            "thresholds": {
                "current": (
                    self.threshold_history[-1] if self.threshold_history else None
                ),
                "history": self.threshold_history[-10:],  # Last 10 changes
            },
            "alerts": [
                {
                    "level": alert.level.value,
                    "metric": alert.metric,
                    "message": alert.message,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "timestamp": alert.timestamp.isoformat(),
                    "recommendations": alert.recommendations,
                }
                for alert in self.active_alerts
            ],
        }

    async def get_time_series_data(
        self, metric: str, time_range: Optional[timedelta] = None
    ) -> List[Dict[str, Any]]:
        """
        Get time-series data for a specific metric.

        Args:
            metric: Metric name (e.g., 'latency', 'mode_distribution')
            time_range: Time range to include (default: all)

        Returns:
            List of time-series data points
        """
        if time_range:
            cutoff = datetime.now() - time_range
            snapshots = [s for s in self.snapshots if s.timestamp >= cutoff]
        else:
            snapshots = list(self.snapshots)

        if metric == "latency":
            return [
                {"timestamp": s.timestamp.isoformat(), "values": s.avg_latency_by_mode}
                for s in snapshots
            ]
        elif metric == "mode_distribution":
            return [
                {"timestamp": s.timestamp.isoformat(), "values": s.mode_distribution}
                for s in snapshots
            ]
        elif metric == "cache_hit_rate":
            return [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "values": s.cache_hit_rate_by_mode,
                }
                for s in snapshots
            ]
        else:
            return []

    async def create_snapshot(self):
        """Create a snapshot of current metrics for time-series analysis."""
        metrics = await self.get_current_metrics()

        # Calculate current values
        total = sum(metrics.mode_distribution.values()) or 1
        mode_percentages = {
            mode: (count / total) * 100
            for mode, count in metrics.mode_distribution.items()
        }

        complexity_total = sum(metrics.complexity_distribution.values()) or 1
        complexity_percentages = {
            comp: (count / complexity_total) * 100
            for comp, count in metrics.complexity_distribution.items()
        }

        avg_latency_by_mode = {}
        for mode, latencies in metrics.latency_by_mode.items():
            if latencies:
                avg_latency_by_mode[mode] = statistics.mean(
                    latencies[-100:]
                )  # Last 100

        cache_hit_rates = {}
        for mode in set(
            list(metrics.cache_hits_by_mode.keys())
            + list(metrics.cache_misses_by_mode.keys())
        ):
            hits = metrics.cache_hits_by_mode.get(mode, 0)
            misses = metrics.cache_misses_by_mode.get(mode, 0)
            total_requests = hits + misses
            if total_requests > 0:
                cache_hit_rates[mode] = (hits / total_requests) * 100

        total_escalations = sum(metrics.escalations.values())
        escalation_rate = (total_escalations / total) * 100 if total > 0 else 0.0

        avg_satisfaction_by_mode = {}
        for mode, ratings in metrics.satisfaction_by_mode.items():
            if ratings:
                avg_satisfaction_by_mode[mode] = statistics.mean(
                    ratings[-100:]
                )  # Last 100

        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            mode_distribution=mode_percentages,
            complexity_distribution=complexity_percentages,
            avg_latency_by_mode=avg_latency_by_mode,
            cache_hit_rate_by_mode=cache_hit_rates,
            escalation_rate=escalation_rate,
            user_satisfaction_by_mode=avg_satisfaction_by_mode,
            total_queries=metrics.total_queries,
        )

        self.snapshots.append(snapshot)

    async def _check_performance_alerts(self):
        """Check for performance degradation and generate alerts."""
        self.active_alerts = []  # Clear old alerts

        metrics = await self.get_current_metrics()

        # Check latency thresholds
        for mode in ["fast", "balanced", "deep"]:
            latencies = metrics.latency_by_mode.get(mode, [])
            if len(latencies) >= 10:  # Need minimum samples
                p95 = self._calculate_percentile(
                    latencies[-100:], 95
                )  # Last 100 queries
                threshold_key = f"{mode}_mode_latency_p95"
                threshold = self.thresholds.get(threshold_key, float("inf"))

                if p95 > threshold * 1.2:  # 20% over threshold
                    self.active_alerts.append(
                        PerformanceAlert(
                            level=AlertLevel.CRITICAL,
                            metric=f"{mode}_mode_latency",
                            message=f"{mode.upper()} mode latency (p95) exceeds threshold",
                            current_value=p95,
                            threshold_value=threshold,
                            timestamp=datetime.now(),
                            recommendations=[
                                f"Review {mode} mode query patterns",
                                "Check system resources",
                                "Consider threshold adjustment",
                            ],
                        )
                    )
                elif p95 > threshold:
                    self.active_alerts.append(
                        PerformanceAlert(
                            level=AlertLevel.WARNING,
                            metric=f"{mode}_mode_latency",
                            message=f"{mode.upper()} mode latency (p95) approaching threshold",
                            current_value=p95,
                            threshold_value=threshold,
                            timestamp=datetime.now(),
                            recommendations=[
                                f"Monitor {mode} mode performance",
                                "Review recent queries",
                            ],
                        )
                    )

        # Check cache hit rates
        for mode in ["fast", "balanced", "deep"]:
            hits = metrics.cache_hits_by_mode.get(mode, 0)
            misses = metrics.cache_misses_by_mode.get(mode, 0)
            total_requests = hits + misses

            if total_requests >= 10:
                hit_rate = hits / total_requests
                min_rate = self.thresholds.get("cache_hit_rate_min", 0.3)

                if hit_rate < min_rate * 0.5:  # 50% below minimum
                    self.active_alerts.append(
                        PerformanceAlert(
                            level=AlertLevel.CRITICAL,
                            metric=f"{mode}_cache_hit_rate",
                            message=f"{mode.upper()} mode cache hit rate critically low",
                            current_value=hit_rate,
                            threshold_value=min_rate,
                            timestamp=datetime.now(),
                            recommendations=[
                                "Review cache configuration",
                                "Check cache TTL settings",
                                "Analyze query patterns",
                            ],
                        )
                    )

        # Check escalation rate
        total = sum(metrics.mode_distribution.values())
        if total >= 10:
            total_escalations = sum(metrics.escalations.values())
            escalation_rate = total_escalations / total
            max_rate = self.thresholds.get("escalation_rate_max", 0.15)

            if escalation_rate > max_rate * 1.5:
                self.active_alerts.append(
                    PerformanceAlert(
                        level=AlertLevel.WARNING,
                        metric="escalation_rate",
                        message="High escalation rate detected",
                        current_value=escalation_rate,
                        threshold_value=max_rate,
                        timestamp=datetime.now(),
                        recommendations=[
                            "Review complexity thresholds",
                            "Analyze escalated queries",
                            "Consider threshold tuning",
                        ],
                    )
                )

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]

    async def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        self.mode_counts.clear()
        self.complexity_counts.clear()
        self.latency_by_mode.clear()
        self.latency_by_complexity.clear()
        self.cache_hits_by_mode.clear()
        self.cache_misses_by_mode.clear()
        self.escalations.clear()
        self.satisfaction_by_mode.clear()
        self.routing_confidence.clear()
        self.routing_time.clear()
        self.threshold_history.clear()
        self.snapshots.clear()
        self.active_alerts.clear()
        self.start_time = datetime.now()
        self.total_queries = 0


# Global instance
_adaptive_metrics_service: Optional[AdaptiveMetricsService] = None


def get_adaptive_metrics_service() -> AdaptiveMetricsService:
    """Get or create the global adaptive metrics service instance."""
    global _adaptive_metrics_service
    if _adaptive_metrics_service is None:
        _adaptive_metrics_service = AdaptiveMetricsService()
    return _adaptive_metrics_service
