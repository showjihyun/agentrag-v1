"""
Workflow Monitoring API Endpoints

Real-time monitoring and alerting endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.services.agent_builder.workflow_monitor import (
    WorkflowMonitor,
    Alert,
    AlertSeverity,
    Metric,
    MetricType,
    WorkflowStatus,
)

# Import enhanced monitoring components
from backend.services.agent_builder.workflow_monitoring import (
    get_workflow_monitor as get_enhanced_monitor,
    AlertType as EnhancedAlertType,
    AlertSeverity as EnhancedAlertSeverity,
)
from backend.services.agent_builder.workflow_metrics import get_metrics_collector
from backend.services.agent_builder.dead_letter_queue import get_dead_letter_queue, DLQEntryStatus
from backend.services.agent_builder.dlq_processor import get_dlq_processor
from backend.services.agent_builder.checkpoint_recovery import get_checkpoint_manager, CheckpointType

router = APIRouter(prefix="/monitoring", tags=["workflow-monitoring"])

# Global monitor instance (in production, use dependency injection)
monitor = WorkflowMonitor()


# Pydantic Models
class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    current_node_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    total_nodes: int
    completed_nodes: int
    failed_nodes: int
    progress_percent: float
    estimated_completion: Optional[datetime]


class AlertResponse(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    workflow_id: str
    node_id: Optional[str]
    timestamp: datetime
    acknowledged: bool
    metadata: Dict[str, Any]


class MetricResponse(BaseModel):
    name: str
    type: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]


class AlertRuleCreate(BaseModel):
    metric: str = Field(..., description="Metric name to monitor")
    condition: str = Field(..., description="Condition: gt, lt, eq, gte, lte")
    threshold: float = Field(..., description="Threshold value")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    workflow_id: Optional[str] = Field(None, description="Specific workflow ID")


class SystemHealthResponse(BaseModel):
    status: str
    active_workflows: int
    total_executions: int
    success_count: int
    error_count: int
    error_rate: float
    avg_execution_time: float
    cpu_percent: float
    memory_mb: float
    unacknowledged_alerts: int
    timestamp: datetime


@router.on_event("startup")
async def startup_monitoring():
    """Start monitoring on startup"""
    await monitor.start_monitoring()
    
    # Add default alert rules
    monitor.add_alert_rule(
        metric="system_cpu_percent",
        condition="gt",
        threshold=80.0,
        severity=AlertSeverity.WARNING,
        title="High CPU Usage",
        message="CPU usage exceeded 80%"
    )
    
    monitor.add_alert_rule(
        metric="system_memory_mb",
        condition="gt",
        threshold=1000.0,
        severity=AlertSeverity.WARNING,
        title="High Memory Usage",
        message="Memory usage exceeded 1GB"
    )


@router.on_event("shutdown")
async def shutdown_monitoring():
    """Stop monitoring on shutdown"""
    await monitor.stop_monitoring()


@router.get("/health")
async def get_system_health(
    
) -> SystemHealthResponse:
    """Get overall system health"""
    health = monitor.get_system_health()
    return SystemHealthResponse(**health)


@router.get("/workflows/active")
async def get_active_workflows(
    
) -> List[WorkflowStatusResponse]:
    """Get all active workflows"""
    workflows = monitor.get_all_active_workflows()
    
    return [
        WorkflowStatusResponse(
            workflow_id=w.workflow_id,
            status=w.status,
            current_node_id=w.current_node_id,
            start_time=w.start_time,
            end_time=w.end_time,
            total_nodes=w.total_nodes,
            completed_nodes=w.completed_nodes,
            failed_nodes=w.failed_nodes,
            progress_percent=w.progress_percent,
            estimated_completion=w.estimated_completion
        )
        for w in workflows
    ]


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    
) -> WorkflowStatusResponse:
    """Get specific workflow status"""
    status = monitor.get_workflow_status(workflow_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found or not active")
    
    return WorkflowStatusResponse(
        workflow_id=status.workflow_id,
        status=status.status,
        current_node_id=status.current_node_id,
        start_time=status.start_time,
        end_time=status.end_time,
        total_nodes=status.total_nodes,
        completed_nodes=status.completed_nodes,
        failed_nodes=status.failed_nodes,
        progress_percent=status.progress_percent,
        estimated_completion=status.estimated_completion
    )


@router.get("/metrics/{metric_name}")
async def get_metrics(
    metric_name: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    
) -> List[MetricResponse]:
    """Get metrics within time range"""
    metrics = monitor.get_metrics(metric_name, start_time, end_time)
    
    return [
        MetricResponse(
            name=m.name,
            type=m.type.value,
            value=m.value,
            timestamp=m.timestamp,
            labels=m.labels
        )
        for m in metrics
    ]


@router.get("/metrics")
async def list_available_metrics(
    
) -> Dict[str, int]:
    """List all available metrics with count"""
    return {
        name: len(metrics)
        for name, metrics in monitor.metrics.items()
    }


@router.get("/alerts")
async def get_alerts(
    severity: Optional[AlertSeverity] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    
) -> List[AlertResponse]:
    """Get alerts with optional filtering"""
    alerts = monitor.get_alerts(severity, acknowledged)
    
    return [
        AlertResponse(
            id=a.id,
            severity=a.severity.value,
            title=a.title,
            message=a.message,
            workflow_id=a.workflow_id,
            node_id=a.node_id,
            timestamp=a.timestamp,
            acknowledged=a.acknowledged,
            metadata=a.metadata
        )
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    
):
    """Acknowledge an alert"""
    success = monitor.acknowledge_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert acknowledged", "alert_id": alert_id}


@router.post("/alert-rules")
async def add_alert_rule(
    rule: AlertRuleCreate,
    
):
    """Add a new alert rule"""
    monitor.add_alert_rule(
        metric=rule.metric,
        condition=rule.condition,
        threshold=rule.threshold,
        severity=rule.severity,
        title=rule.title,
        message=rule.message,
        workflow_id=rule.workflow_id
    )
    
    return {"message": "Alert rule added successfully"}


@router.get("/export")
async def export_monitoring_data(
    
) -> Dict[str, Any]:
    """Export all monitoring data"""
    return monitor.export_monitoring_data()


@router.get("/resource-history")
async def get_resource_history(
    limit: int = Query(100, ge=1, le=1000),
    
) -> List[Dict[str, Any]]:
    """Get resource usage history"""
    history = list(monitor.resource_history)[-limit:]
    
    return [
        {
            "timestamp": r["timestamp"].isoformat(),
            "cpu_percent": r["cpu_percent"],
            "memory_mb": r["memory_mb"],
            "active_workflows": r["active_workflows"]
        }
        for r in history
    ]


@router.get("/statistics")
async def get_statistics(
    
) -> Dict[str, Any]:
    """Get comprehensive statistics"""
    health = monitor.get_system_health()
    
    # Calculate additional statistics
    total_workflows = len(monitor.success_counts) + len(monitor.error_counts)
    
    return {
        "system_health": health,
        "workflow_statistics": {
            "total_workflows": total_workflows,
            "success_by_workflow": dict(monitor.success_counts),
            "errors_by_workflow": dict(monitor.error_counts),
        },
        "execution_times": {
            "recent": list(monitor.execution_times)[-10:],
            "average": sum(monitor.execution_times) / len(monitor.execution_times) if monitor.execution_times else 0,
            "min": min(monitor.execution_times) if monitor.execution_times else 0,
            "max": max(monitor.execution_times) if monitor.execution_times else 0,
        },
        "alerts_summary": {
            "total": len(monitor.alerts),
            "unacknowledged": len([a for a in monitor.alerts if not a.acknowledged]),
            "by_severity": {
                severity.value: len([a for a in monitor.alerts if a.severity == severity])
                for severity in AlertSeverity
            }
        }
    }


# ============================================================================
# Enhanced Monitoring Endpoints (V2)
# ============================================================================

# Request/Response Models for V2
class DLQRetryRequest(BaseModel):
    force: bool = False


class DLQResolveRequest(BaseModel):
    notes: Optional[str] = None
    discard: bool = False


class AlertThresholdUpdate(BaseModel):
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    window_minutes: int = 5


# Dashboard V2
@router.get("/v2/dashboard")
async def get_monitoring_dashboard_v2(
    workflow_id: Optional[str] = None,
):
    """Get enhanced monitoring dashboard data."""
    enhanced_monitor = get_enhanced_monitor()
    return enhanced_monitor.get_dashboard_data(workflow_id)


@router.get("/v2/metrics")
async def get_metrics_v2(
    format: str = Query("json", regex="^(json|prometheus)$"),
):
    """Get workflow metrics in JSON or Prometheus format."""
    metrics = get_metrics_collector()
    
    if format == "prometheus":
        return metrics.to_prometheus_format()
    
    return {
        "summary": metrics.get_summary(),
        "metrics": [m.__dict__ for m in metrics.collect_all()],
    }


# Performance Analysis
@router.get("/v2/performance/{workflow_id}")
async def get_workflow_performance(
    workflow_id: str,
):
    """Get performance analysis for a workflow."""
    enhanced_monitor = get_enhanced_monitor()
    
    return {
        "workflow_stats": enhanced_monitor.analyzer.get_workflow_stats(workflow_id),
        "node_stats": enhanced_monitor.analyzer.get_node_stats(workflow_id),
        "bottlenecks": enhanced_monitor.analyzer.identify_bottlenecks(workflow_id),
        "regression": enhanced_monitor.analyzer.detect_performance_regression(workflow_id),
    }


@router.get("/v2/performance/{workflow_id}/bottlenecks")
async def get_bottlenecks(
    workflow_id: str,
):
    """Identify performance bottlenecks."""
    enhanced_monitor = get_enhanced_monitor()
    return enhanced_monitor.analyzer.identify_bottlenecks(workflow_id)


# Enhanced Alerts
@router.get("/v2/alerts")
async def get_alerts_v2(
    severity: Optional[str] = None,
    workflow_id: Optional[str] = None,
    include_resolved: bool = False,
    limit: int = 100,
):
    """Get alerts with enhanced filtering."""
    enhanced_monitor = get_enhanced_monitor()
    
    severity_enum = EnhancedAlertSeverity(severity) if severity else None
    
    if include_resolved:
        alerts = enhanced_monitor.alert_manager.get_alert_history(limit)
    else:
        alerts = enhanced_monitor.alert_manager.get_active_alerts(severity_enum, workflow_id)
    
    return {
        "alerts": [a.to_dict() for a in alerts],
        "total": len(alerts),
    }


@router.post("/v2/alerts/{alert_id}/resolve")
async def resolve_alert_v2(
    alert_id: str,
):
    """Resolve an alert."""
    enhanced_monitor = get_enhanced_monitor()
    alert = await enhanced_monitor.alert_manager.resolve_alert(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert.to_dict()


# DLQ Management
@router.get("/v2/dlq")
async def get_dlq_entries(
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get DLQ entries."""
    dlq = get_dead_letter_queue()
    
    status_enum = DLQEntryStatus(status) if status else None
    entries = await dlq.list_entries(status_enum, workflow_id, limit, offset)
    
    return {
        "entries": [e.to_dict() for e in entries],
        "total": len(entries),
    }


@router.get("/v2/dlq/stats")
async def get_dlq_stats():
    """Get DLQ statistics."""
    dlq = get_dead_letter_queue()
    return await dlq.get_stats()


@router.get("/v2/dlq/{entry_id}")
async def get_dlq_entry(
    entry_id: str,
):
    """Get a specific DLQ entry."""
    dlq = get_dead_letter_queue()
    entry = await dlq.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    
    return entry.to_dict()


@router.post("/v2/dlq/{entry_id}/retry")
async def retry_dlq_entry(
    entry_id: str,
    request: DLQRetryRequest,
):
    """Retry a DLQ entry."""
    dlq = get_dead_letter_queue()
    processor = get_dlq_processor(dlq)
    
    entry = await dlq.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    
    result = await processor.process_entry(entry, force_retry=request.force)
    
    return {
        "entry_id": result.entry_id,
        "decision": result.decision.value,
        "success": result.success,
        "message": result.message,
        "retry_scheduled_at": result.retry_scheduled_at.isoformat() if result.retry_scheduled_at else None,
    }


@router.post("/v2/dlq/{entry_id}/resolve")
async def resolve_dlq_entry(
    entry_id: str,
    request: DLQResolveRequest,
):
    """Resolve a DLQ entry."""
    dlq = get_dead_letter_queue()
    entry = await dlq.resolve(entry_id, request.notes, request.discard)
    
    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    
    return entry.to_dict()


@router.post("/v2/dlq/process-pending")
async def process_pending_dlq(
    limit: int = 10,
    workflow_id: Optional[str] = None,
):
    """Process pending DLQ entries."""
    dlq = get_dead_letter_queue()
    processor = get_dlq_processor(dlq)
    
    results = await processor.process_pending(limit, workflow_id)
    
    return {
        "processed": len(results),
        "results": [
            {
                "entry_id": r.entry_id,
                "decision": r.decision.value,
                "success": r.success,
                "message": r.message,
            }
            for r in results
        ],
    }


# Checkpoint Management
@router.get("/v2/checkpoints/{execution_id}")
async def get_checkpoints(
    execution_id: str,
):
    """Get checkpoints for an execution."""
    manager = get_checkpoint_manager()
    checkpoints = await manager.list_checkpoints(execution_id)
    
    return {
        "execution_id": execution_id,
        "checkpoints": [cp.to_dict() for cp in checkpoints],
        "total": len(checkpoints),
    }


@router.get("/v2/checkpoints/{execution_id}/latest")
async def get_latest_checkpoint(
    execution_id: str,
    checkpoint_type: Optional[str] = None,
):
    """Get latest checkpoint for an execution."""
    manager = get_checkpoint_manager()
    type_enum = CheckpointType(checkpoint_type) if checkpoint_type else None
    checkpoint = await manager.get_latest_checkpoint(execution_id, type_enum)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="No checkpoint found")
    
    return checkpoint.to_dict()


@router.delete("/v2/checkpoints/{checkpoint_id}")
async def delete_checkpoint(
    checkpoint_id: str,
):
    """Delete a checkpoint."""
    manager = get_checkpoint_manager()
    success = await manager.delete_checkpoint(checkpoint_id)
    
    return {"deleted": success}


# Health Check V2
@router.get("/v2/health")
async def monitoring_health_v2():
    """Check enhanced monitoring system health."""
    enhanced_monitor = get_enhanced_monitor()
    metrics = get_metrics_collector()
    dlq = get_dead_letter_queue()
    
    dlq_stats = await dlq.get_stats()
    
    return {
        "status": "healthy",
        "components": {
            "metrics": "ok",
            "alerts": "ok",
            "dlq": "ok",
            "checkpoints": "ok",
        },
        "summary": {
            "active_alerts": len(enhanced_monitor.alert_manager.get_active_alerts()),
            "dlq_pending": dlq_stats.get("by_status", {}).get("pending", 0),
            "total_executions": metrics.get_summary().get("total_executions", 0),
        },
    }
