"""
Workflow Monitoring System

Real-time monitoring and alerting for workflow executions:
- Real-time metrics dashboard
- Performance analysis
- Anomaly detection
- Alert management
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

from backend.services.agent_builder.workflow_metrics import (
    WorkflowMetricsCollector,
    get_metrics_collector,
)

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_EXECUTION = "slow_execution"
    HIGH_DLQ_SIZE = "high_dlq_size"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    NODE_FAILURE_SPIKE = "node_failure_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    ANOMALY_DETECTED = "anomaly_detected"


@dataclass
class Alert:
    """Represents a monitoring alert."""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class AlertThreshold:
    """Threshold configuration for alerts."""
    alert_type: AlertType
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    window_minutes: int = 5
    min_samples: int = 10


class PerformanceAnalyzer:
    """
    Analyzes workflow performance metrics.
    
    Features:
    - Execution time analysis
    - Node-level performance breakdown
    - Trend detection
    - Bottleneck identification
    """
    
    def __init__(self, metrics_collector: WorkflowMetricsCollector):
        self.metrics = metrics_collector
        self._execution_times: Dict[str, List[float]] = defaultdict(list)
        self._node_times: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self._max_samples = 1000
    
    def record_execution(
        self,
        workflow_id: str,
        duration: float,
        node_durations: Dict[str, float],
    ):
        """Record execution for analysis."""
        # Store execution time
        times = self._execution_times[workflow_id]
        times.append(duration)
        if len(times) > self._max_samples:
            times.pop(0)
        
        # Store node times
        for node_id, node_duration in node_durations.items():
            node_times = self._node_times[workflow_id][node_id]
            node_times.append(node_duration)
            if len(node_times) > self._max_samples:
                node_times.pop(0)
    
    def get_workflow_stats(self, workflow_id: str) -> Dict[str, Any]:
        """Get performance statistics for a workflow."""
        times = self._execution_times.get(workflow_id, [])
        
        if not times:
            return {"error": "No data available"}
        
        return {
            "workflow_id": workflow_id,
            "sample_count": len(times),
            "avg_duration": statistics.mean(times),
            "median_duration": statistics.median(times),
            "min_duration": min(times),
            "max_duration": max(times),
            "std_deviation": statistics.stdev(times) if len(times) > 1 else 0,
            "p95_duration": self._percentile(times, 95),
            "p99_duration": self._percentile(times, 99),
        }
    
    def get_node_stats(self, workflow_id: str) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for each node."""
        node_data = self._node_times.get(workflow_id, {})
        
        result = {}
        for node_id, times in node_data.items():
            if times:
                result[node_id] = {
                    "sample_count": len(times),
                    "avg_duration": statistics.mean(times),
                    "median_duration": statistics.median(times),
                    "max_duration": max(times),
                    "p95_duration": self._percentile(times, 95),
                }
        
        return result
    
    def identify_bottlenecks(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        node_stats = self.get_node_stats(workflow_id)
        workflow_stats = self.get_workflow_stats(workflow_id)
        
        if "error" in workflow_stats:
            return []
        
        bottlenecks = []
        total_avg = workflow_stats["avg_duration"]
        
        for node_id, stats in node_stats.items():
            # Node takes more than 30% of total time
            if stats["avg_duration"] > total_avg * 0.3:
                bottlenecks.append({
                    "node_id": node_id,
                    "avg_duration": stats["avg_duration"],
                    "percentage_of_total": (stats["avg_duration"] / total_avg) * 100,
                    "recommendation": self._get_optimization_recommendation(node_id, stats),
                })
        
        return sorted(bottlenecks, key=lambda x: x["avg_duration"], reverse=True)
    
    def detect_performance_regression(
        self,
        workflow_id: str,
        window_size: int = 50,
    ) -> Optional[Dict[str, Any]]:
        """Detect performance regression."""
        times = self._execution_times.get(workflow_id, [])
        
        if len(times) < window_size * 2:
            return None
        
        # Compare recent window to previous window
        recent = times[-window_size:]
        previous = times[-window_size * 2:-window_size]
        
        recent_avg = statistics.mean(recent)
        previous_avg = statistics.mean(previous)
        
        # Check for significant increase (>20%)
        if recent_avg > previous_avg * 1.2:
            return {
                "detected": True,
                "previous_avg": previous_avg,
                "recent_avg": recent_avg,
                "increase_percentage": ((recent_avg - previous_avg) / previous_avg) * 100,
            }
        
        return {"detected": False}
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_optimization_recommendation(
        self,
        node_id: str,
        stats: Dict[str, Any],
    ) -> str:
        """Get optimization recommendation for a node."""
        if stats["p95_duration"] > stats["avg_duration"] * 2:
            return "High variance - consider adding timeout or retry logic"
        if stats["avg_duration"] > 5:
            return "Consider caching results or optimizing external calls"
        return "Monitor for further optimization opportunities"


class AnomalyDetector:
    """
    Detects anomalies in workflow metrics.
    
    Features:
    - Statistical anomaly detection
    - Pattern-based detection
    - Adaptive thresholds
    """
    
    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Standard deviations for anomaly
        self._baselines: Dict[str, Dict[str, float]] = {}
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._max_history = 500
    
    def update_baseline(self, metric_name: str, value: float):
        """Update baseline with new value."""
        history = self._history[metric_name]
        history.append(value)
        
        if len(history) > self._max_history:
            history.pop(0)
        
        if len(history) >= 30:
            self._baselines[metric_name] = {
                "mean": statistics.mean(history),
                "std": statistics.stdev(history) if len(history) > 1 else 0,
                "min": min(history),
                "max": max(history),
            }
    
    def check_anomaly(self, metric_name: str, value: float) -> Optional[Dict[str, Any]]:
        """Check if value is anomalous."""
        baseline = self._baselines.get(metric_name)
        
        if not baseline or baseline["std"] == 0:
            return None
        
        z_score = abs(value - baseline["mean"]) / baseline["std"]
        
        if z_score > self.sensitivity:
            return {
                "metric": metric_name,
                "value": value,
                "baseline_mean": baseline["mean"],
                "baseline_std": baseline["std"],
                "z_score": z_score,
                "severity": self._get_severity(z_score),
            }
        
        return None
    
    def _get_severity(self, z_score: float) -> AlertSeverity:
        """Get severity based on z-score."""
        if z_score > 4:
            return AlertSeverity.CRITICAL
        if z_score > 3:
            return AlertSeverity.ERROR
        if z_score > 2:
            return AlertSeverity.WARNING
        return AlertSeverity.INFO


class AlertManager:
    """
    Manages monitoring alerts.
    
    Features:
    - Alert creation and lifecycle
    - Alert deduplication
    - Alert routing
    - Alert history
    """
    
    def __init__(
        self,
        alert_callback: Optional[Callable[[Alert], Awaitable[None]]] = None,
        dedup_window_minutes: int = 15,
    ):
        self.alert_callback = alert_callback
        self.dedup_window = timedelta(minutes=dedup_window_minutes)
        
        self._alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._last_alerts: Dict[str, datetime] = {}
        self._max_history = 1000
        
        # Default thresholds
        self.thresholds: Dict[AlertType, AlertThreshold] = {
            AlertType.HIGH_ERROR_RATE: AlertThreshold(
                AlertType.HIGH_ERROR_RATE, 5.0, 10.0, 25.0, 5, 10
            ),
            AlertType.SLOW_EXECUTION: AlertThreshold(
                AlertType.SLOW_EXECUTION, 30.0, 60.0, 120.0, 5, 5
            ),
            AlertType.HIGH_DLQ_SIZE: AlertThreshold(
                AlertType.HIGH_DLQ_SIZE, 10, 50, 100, 5, 1
            ),
            AlertType.NODE_FAILURE_SPIKE: AlertThreshold(
                AlertType.NODE_FAILURE_SPIKE, 3, 5, 10, 5, 5
            ),
        }
    
    async def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        workflow_id: Optional[str] = None,
        node_id: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Alert]:
        """Create a new alert."""
        import uuid
        
        # Check deduplication
        dedup_key = f"{alert_type.value}:{workflow_id}:{node_id}"
        last_alert = self._last_alerts.get(dedup_key)
        
        if last_alert and datetime.utcnow() - last_alert < self.dedup_window:
            logger.debug(f"Alert deduplicated: {dedup_key}")
            return None
        
        alert = Alert(
            id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            workflow_id=workflow_id,
            node_id=node_id,
            metric_value=metric_value,
            threshold=threshold,
        )
        
        self._alerts[alert.id] = alert
        self._alert_history.append(alert)
        self._last_alerts[dedup_key] = datetime.utcnow()
        
        # Trim history
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]
        
        logger.warning(f"Alert created: {title} ({severity.value})")
        
        # Send callback
        if self.alert_callback:
            try:
                await self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        return alert
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
    ) -> Optional[Alert]:
        """Acknowledge an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        
        return alert
    
    async def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        
        return alert
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        workflow_id: Optional[str] = None,
    ) -> List[Alert]:
        """Get active (unresolved) alerts."""
        alerts = [a for a in self._alerts.values() if not a.resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if workflow_id:
            alerts = [a for a in alerts if a.workflow_id == workflow_id]
        
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def get_alert_history(
        self,
        limit: int = 100,
        alert_type: Optional[AlertType] = None,
    ) -> List[Alert]:
        """Get alert history."""
        alerts = self._alert_history
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        return alerts[-limit:]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        active = [a for a in self._alerts.values() if not a.resolved]
        
        return {
            "total_alerts": len(self._alert_history),
            "active_alerts": len(active),
            "by_severity": {
                s.value: len([a for a in active if a.severity == s])
                for s in AlertSeverity
            },
            "by_type": {
                t.value: len([a for a in active if a.alert_type == t])
                for t in AlertType
            },
        }


class WorkflowMonitor:
    """
    Main monitoring orchestrator.
    
    Combines metrics, analysis, anomaly detection, and alerting.
    """
    
    def __init__(
        self,
        metrics_collector: Optional[WorkflowMetricsCollector] = None,
        alert_callback: Optional[Callable[[Alert], Awaitable[None]]] = None,
    ):
        self.metrics = metrics_collector or get_metrics_collector()
        self.analyzer = PerformanceAnalyzer(self.metrics)
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager(alert_callback)
        
        self._monitoring = False
    
    async def record_execution_complete(
        self,
        workflow_id: str,
        execution_id: str,
        success: bool,
        duration: float,
        node_durations: Dict[str, float],
        error_type: Optional[str] = None,
    ):
        """Record completed execution and check for alerts."""
        # Record metrics
        status = "success" if success else "failed"
        self.metrics.record_execution_end(workflow_id, status, duration)
        
        # Record for analysis
        self.analyzer.record_execution(workflow_id, duration, node_durations)
        
        # Update anomaly baselines
        self.anomaly_detector.update_baseline(f"duration:{workflow_id}", duration)
        
        # Check for anomalies
        anomaly = self.anomaly_detector.check_anomaly(f"duration:{workflow_id}", duration)
        if anomaly:
            await self.alert_manager.create_alert(
                AlertType.ANOMALY_DETECTED,
                anomaly["severity"],
                f"Anomalous execution time for {workflow_id}",
                f"Duration {duration:.2f}s is {anomaly['z_score']:.1f} std devs from mean",
                workflow_id=workflow_id,
                metric_value=duration,
                threshold=anomaly["baseline_mean"],
            )
        
        # Check for slow execution
        threshold = self.alert_manager.thresholds.get(AlertType.SLOW_EXECUTION)
        if threshold and duration > threshold.error_threshold:
            await self.alert_manager.create_alert(
                AlertType.SLOW_EXECUTION,
                AlertSeverity.ERROR if duration > threshold.critical_threshold else AlertSeverity.WARNING,
                f"Slow execution: {workflow_id}",
                f"Execution took {duration:.2f}s (threshold: {threshold.error_threshold}s)",
                workflow_id=workflow_id,
                metric_value=duration,
                threshold=threshold.error_threshold,
            )
        
        # Record error
        if not success and error_type:
            self.metrics.record_error(workflow_id, error_type)
    
    async def check_error_rate(self, workflow_id: str):
        """Check error rate and create alerts if needed."""
        # This would typically query recent executions
        # Simplified implementation
        pass
    
    def get_dashboard_data(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        data = {
            "metrics_summary": self.metrics.get_summary(),
            "active_alerts": [a.to_dict() for a in self.alert_manager.get_active_alerts()],
            "alert_stats": self.alert_manager.get_alert_stats(),
        }
        
        if workflow_id:
            data["workflow_stats"] = self.analyzer.get_workflow_stats(workflow_id)
            data["node_stats"] = self.analyzer.get_node_stats(workflow_id)
            data["bottlenecks"] = self.analyzer.identify_bottlenecks(workflow_id)
            data["regression"] = self.analyzer.detect_performance_regression(workflow_id)
        
        return data
    
    async def start_monitoring_loop(self, interval_seconds: int = 60):
        """Start background monitoring loop."""
        self._monitoring = True
        logger.info("Starting workflow monitoring loop")
        
        while self._monitoring:
            try:
                # Periodic checks
                await self._run_periodic_checks()
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop monitoring loop."""
        self._monitoring = False
    
    async def _run_periodic_checks(self):
        """Run periodic monitoring checks."""
        # Check DLQ size
        # Check resource usage
        # Check for stale executions
        pass


# Global monitor instance
_workflow_monitor: Optional[WorkflowMonitor] = None


def get_workflow_monitor(
    metrics_collector: Optional[WorkflowMetricsCollector] = None,
    alert_callback: Optional[Callable[[Alert], Awaitable[None]]] = None,
) -> WorkflowMonitor:
    """Get or create workflow monitor."""
    global _workflow_monitor
    if _workflow_monitor is None:
        _workflow_monitor = WorkflowMonitor(metrics_collector, alert_callback)
    return _workflow_monitor
