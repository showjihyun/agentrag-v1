"""
Workflow Monitoring Service

Real-time monitoring and alerting for workflow execution:
- Live execution tracking
- Resource usage monitoring
- Error rate tracking
- Performance metrics
- Alert system
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
from collections import defaultdict, deque
import psutil


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    workflow_id: str
    node_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    """Metric data structure"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowStatus:
    """Current workflow status"""
    workflow_id: str
    status: str  # running, completed, failed, paused
    current_node_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    progress_percent: float = 0.0
    estimated_completion: Optional[datetime] = None


class WorkflowMonitor:
    """
    Real-time workflow monitoring service
    
    Features:
    - Live execution tracking
    - Resource usage monitoring
    - Error rate tracking
    - Performance metrics
    - Alert system
    - Health checks
    """
    
    def __init__(self, alert_callback: Optional[Callable] = None):
        self.alert_callback = alert_callback
        
        # Active workflows
        self.active_workflows: Dict[str, WorkflowStatus] = {}
        
        # Metrics storage (time-series data)
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Alerts
        self.alerts: List[Alert] = []
        self.alert_rules: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.execution_times: deque = deque(maxlen=100)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.success_counts: Dict[str, int] = defaultdict(int)
        
        # Resource monitoring
        self.process = psutil.Process()
        self.resource_history: deque = deque(maxlen=100)
        
        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        
    async def start_monitoring(self) -> None:
        """Start background monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
    async def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect resource metrics
                await self._collect_resource_metrics()
                
                # Check alert rules
                await self._check_alert_rules()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait before next iteration
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitoring loop error: {e}")
                
    async def _collect_resource_metrics(self) -> None:
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self.record_metric(Metric(
                name="system_cpu_percent",
                type=MetricType.GAUGE,
                value=cpu_percent
            ))
            
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.record_metric(Metric(
                name="system_memory_mb",
                type=MetricType.GAUGE,
                value=memory_mb
            ))
            
            # Active workflows
            self.record_metric(Metric(
                name="active_workflows",
                type=MetricType.GAUGE,
                value=len(self.active_workflows)
            ))
            
            # Store in history
            self.resource_history.append({
                "timestamp": datetime.now(),
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "active_workflows": len(self.active_workflows)
            })
            
        except Exception as e:
            print(f"Resource collection error: {e}")
            
    async def _check_alert_rules(self) -> None:
        """Check alert rules and trigger alerts"""
        for rule in self.alert_rules:
            try:
                if await self._evaluate_alert_rule(rule):
                    await self._trigger_alert(rule)
            except Exception as e:
                print(f"Alert rule check error: {e}")
                
    async def _evaluate_alert_rule(self, rule: Dict[str, Any]) -> bool:
        """Evaluate if alert rule condition is met"""
        metric_name = rule.get("metric")
        condition = rule.get("condition")
        threshold = rule.get("threshold")
        
        if not metric_name or not condition or threshold is None:
            return False
            
        # Get recent metrics
        recent_metrics = list(self.metrics.get(metric_name, []))
        if not recent_metrics:
            return False
            
        # Get latest value
        latest_value = recent_metrics[-1].value
        
        # Evaluate condition
        if condition == "gt":
            return latest_value > threshold
        elif condition == "lt":
            return latest_value < threshold
        elif condition == "eq":
            return latest_value == threshold
        elif condition == "gte":
            return latest_value >= threshold
        elif condition == "lte":
            return latest_value <= threshold
            
        return False
        
    async def _trigger_alert(self, rule: Dict[str, Any]) -> None:
        """Trigger an alert"""
        alert = Alert(
            id=f"alert-{len(self.alerts)}",
            severity=AlertSeverity(rule.get("severity", "warning")),
            title=rule.get("title", "Alert"),
            message=rule.get("message", "Alert condition met"),
            workflow_id=rule.get("workflow_id", "system"),
            metadata=rule.get("metadata", {})
        )
        
        self.alerts.append(alert)
        
        # Call callback if provided
        if self.alert_callback:
            try:
                await self.alert_callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")
                
    async def _cleanup_old_data(self) -> None:
        """Clean up old data to prevent memory leaks"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Clean up old alerts
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp > cutoff_time
        ]
        
    def start_workflow(
        self,
        workflow_id: str,
        total_nodes: int
    ) -> WorkflowStatus:
        """Start tracking a workflow"""
        status = WorkflowStatus(
            workflow_id=workflow_id,
            status="running",
            current_node_id=None,
            start_time=datetime.now(),
            total_nodes=total_nodes
        )
        
        self.active_workflows[workflow_id] = status
        
        # Record metric
        self.record_metric(Metric(
            name="workflow_started",
            type=MetricType.COUNTER,
            value=1,
            labels={"workflow_id": workflow_id}
        ))
        
        return status
        
    def update_workflow_progress(
        self,
        workflow_id: str,
        current_node_id: str,
        completed_nodes: int,
        failed_nodes: int = 0
    ) -> None:
        """Update workflow progress"""
        if workflow_id not in self.active_workflows:
            return
            
        status = self.active_workflows[workflow_id]
        status.current_node_id = current_node_id
        status.completed_nodes = completed_nodes
        status.failed_nodes = failed_nodes
        
        # Calculate progress
        if status.total_nodes > 0:
            status.progress_percent = (completed_nodes / status.total_nodes) * 100
            
        # Estimate completion time
        if completed_nodes > 0:
            elapsed = (datetime.now() - status.start_time).total_seconds()
            avg_time_per_node = elapsed / completed_nodes
            remaining_nodes = status.total_nodes - completed_nodes
            estimated_seconds = remaining_nodes * avg_time_per_node
            status.estimated_completion = datetime.now() + timedelta(seconds=estimated_seconds)
            
    def complete_workflow(
        self,
        workflow_id: str,
        success: bool = True
    ) -> None:
        """Mark workflow as completed"""
        if workflow_id not in self.active_workflows:
            return
            
        status = self.active_workflows[workflow_id]
        status.status = "completed" if success else "failed"
        status.end_time = datetime.now()
        status.progress_percent = 100.0
        
        # Calculate execution time
        execution_time = (status.end_time - status.start_time).total_seconds()
        self.execution_times.append(execution_time)
        
        # Update counters
        if success:
            self.success_counts[workflow_id] += 1
            self.record_metric(Metric(
                name="workflow_success",
                type=MetricType.COUNTER,
                value=1,
                labels={"workflow_id": workflow_id}
            ))
        else:
            self.error_counts[workflow_id] += 1
            self.record_metric(Metric(
                name="workflow_error",
                type=MetricType.COUNTER,
                value=1,
                labels={"workflow_id": workflow_id}
            ))
            
        # Record execution time
        self.record_metric(Metric(
            name="workflow_execution_time",
            type=MetricType.HISTOGRAM,
            value=execution_time,
            labels={"workflow_id": workflow_id}
        ))
        
        # Remove from active workflows
        del self.active_workflows[workflow_id]
        
    def record_metric(self, metric: Metric) -> None:
        """Record a metric"""
        self.metrics[metric.name].append(metric)
        
    def add_alert_rule(
        self,
        metric: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        title: str,
        message: str,
        workflow_id: Optional[str] = None
    ) -> None:
        """Add an alert rule"""
        rule = {
            "metric": metric,
            "condition": condition,
            "threshold": threshold,
            "severity": severity.value,
            "title": title,
            "message": message,
            "workflow_id": workflow_id or "system"
        }
        self.alert_rules.append(rule)
        
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """Get current workflow status"""
        return self.active_workflows.get(workflow_id)
        
    def get_all_active_workflows(self) -> List[WorkflowStatus]:
        """Get all active workflows"""
        return list(self.active_workflows.values())
        
    def get_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Metric]:
        """Get metrics within time range"""
        metrics = list(self.metrics.get(metric_name, []))
        
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
            
        return metrics
        
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None
    ) -> List[Alert]:
        """Get alerts with optional filtering"""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
            
        return alerts
        
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
        
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        # Calculate error rate
        total_executions = sum(self.success_counts.values()) + sum(self.error_counts.values())
        total_errors = sum(self.error_counts.values())
        error_rate = (total_errors / total_executions * 100) if total_executions > 0 else 0
        
        # Calculate average execution time
        avg_execution_time = (
            sum(self.execution_times) / len(self.execution_times)
            if self.execution_times else 0
        )
        
        # Get latest resource usage
        latest_resources = self.resource_history[-1] if self.resource_history else {}
        
        # Determine health status
        health_status = "healthy"
        if error_rate > 10:
            health_status = "degraded"
        if error_rate > 25 or len(self.active_workflows) > 100:
            health_status = "unhealthy"
            
        return {
            "status": health_status,
            "active_workflows": len(self.active_workflows),
            "total_executions": total_executions,
            "success_count": sum(self.success_counts.values()),
            "error_count": total_errors,
            "error_rate": error_rate,
            "avg_execution_time": avg_execution_time,
            "cpu_percent": latest_resources.get("cpu_percent", 0),
            "memory_mb": latest_resources.get("memory_mb", 0),
            "unacknowledged_alerts": len([a for a in self.alerts if not a.acknowledged]),
            "timestamp": datetime.now()
        }
        
    def export_monitoring_data(self) -> Dict[str, Any]:
        """Export all monitoring data"""
        return {
            "active_workflows": [
                {
                    "workflow_id": status.workflow_id,
                    "status": status.status,
                    "current_node_id": status.current_node_id,
                    "start_time": status.start_time.isoformat(),
                    "progress_percent": status.progress_percent,
                    "completed_nodes": status.completed_nodes,
                    "failed_nodes": status.failed_nodes,
                    "total_nodes": status.total_nodes,
                }
                for status in self.active_workflows.values()
            ],
            "metrics": {
                name: [
                    {
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "labels": m.labels
                    }
                    for m in metrics
                ]
                for name, metrics in self.metrics.items()
            },
            "alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "workflow_id": alert.workflow_id,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged
                }
                for alert in self.alerts
            ],
            "system_health": self.get_system_health(),
            "resource_history": [
                {
                    "timestamp": r["timestamp"].isoformat(),
                    "cpu_percent": r["cpu_percent"],
                    "memory_mb": r["memory_mb"],
                    "active_workflows": r["active_workflows"]
                }
                for r in self.resource_history
            ]
        }
