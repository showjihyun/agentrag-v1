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
