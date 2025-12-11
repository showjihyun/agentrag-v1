"""
Workflow Monitoring API

REST API endpoints for workflow monitoring and alerting.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from backend.core.auth_dependencies import get_current_user
from backend.services.agent_builder.workflow_monitoring import (
    get_workflow_monitor,
    AlertSeverity,
    AlertType,
)
from backend.services.agent_builder.workflow_metrics import get_metrics_collector
from backend.services.agent_builder.dead_letter_queue import get_dead_letter_queue, DLQEntryStatus
from backend.services.agent_builder.dlq_processor import get_dlq_processor

router = APIRouter(prefix="/monitoring", tags=["Workflow Monitoring"])


# Request/Response Models
class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: str


class AlertThresholdUpdate(BaseModel):
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    window_minutes: int = 5


class DLQRetryRequest(BaseModel):
    force: bool = False


class DLQResolveRequest(BaseModel):
    notes: Optional[str] = None
    discard: bool = False


# Dashboard Endpoints
@router.get("/dashboard")
async def get_monitoring_dashboard(
    workflow_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Get monitoring dashboard data."""
    monitor = get_workflow_monitor()
    return monitor.get_dashboard_data(workflow_id)


@router.get("/metrics")
async def get_metrics(
    format: str = Query("json", enum=["json", "prometheus"]),
    current_user=Depends(get_current_user),
):
    """Get workflow metrics."""
    metrics = get_metrics_collector()
    
    if format == "prometheus":
        return metrics.to_prometheus_format()
    
    return {
        "summary": metrics.get_summary(),
        "metrics": [m.__dict__ for m in metrics.collect_all()],
    }


@router.get("/metrics/summary")
async def get_metrics_summary(
    current_user=Depends(get_current_user),
):
    """Get metrics summary."""
    metrics = get_metrics_collector()
    return metrics.get_summary()


# Performance Analysis Endpoints
@router.get("/performance/{workflow_id}")
async def get_workflow_performance(
    workflow_id: str,
    current_user=Depends(get_current_user),
):
    """Get performance analysis for a workflow."""
    monitor = get_workflow_monitor()
    
    return {
        "workflow_stats": monitor.analyzer.get_workflow_stats(workflow_id),
        "node_stats": monitor.analyzer.get_node_stats(workflow_id),
        "bottlenecks": monitor.analyzer.identify_bottlenecks(workflow_id),
        "regression": monitor.analyzer.detect_performance_regression(workflow_id),
    }


@router.get("/performance/{workflow_id}/nodes")
async def get_node_performance(
    workflow_id: str,
    current_user=Depends(get_current_user),
):
    """Get node-level performance stats."""
    monitor = get_workflow_monitor()
    return monitor.analyzer.get_node_stats(workflow_id)


@router.get("/performance/{workflow_id}/bottlenecks")
async def get_bottlenecks(
    workflow_id: str,
    current_user=Depends(get_current_user),
):
    """Identify performance bottlenecks."""
    monitor = get_workflow_monitor()
    return monitor.analyzer.identify_bottlenecks(workflow_id)


# Alert Endpoints
@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    workflow_id: Optional[str] = None,
    include_resolved: bool = False,
    limit: int = 100,
    current_user=Depends(get_current_user),
):
    """Get alerts."""
    monitor = get_workflow_monitor()
    
    severity_enum = AlertSeverity(severity) if severity else None
    
    if include_resolved:
        alerts = monitor.alert_manager.get_alert_history(limit)
    else:
        alerts = monitor.alert_manager.get_active_alerts(severity_enum, workflow_id)
    
    return {
        "alerts": [a.to_dict() for a in alerts],
        "total": len(alerts),
    }


@router.get("/alerts/stats")
async def get_alert_stats(
    current_user=Depends(get_current_user),
):
    """Get alert statistics."""
    monitor = get_workflow_monitor()
    return monitor.alert_manager.get_alert_stats()


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    current_user=Depends(get_current_user),
):
    """Acknowledge an alert."""
    monitor = get_workflow_monitor()
    alert = await monitor.alert_manager.acknowledge_alert(alert_id, request.acknowledged_by)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert.to_dict()


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user=Depends(get_current_user),
):
    """Resolve an alert."""
    monitor = get_workflow_monitor()
    alert = await monitor.alert_manager.resolve_alert(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert.to_dict()


@router.put("/alerts/thresholds/{alert_type}")
async def update_alert_threshold(
    alert_type: str,
    request: AlertThresholdUpdate,
    current_user=Depends(get_current_user),
):
    """Update alert threshold."""
    monitor = get_workflow_monitor()
    
    try:
        alert_type_enum = AlertType(alert_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid alert type: {alert_type}")
    
    from backend.services.agent_builder.workflow_monitoring import AlertThreshold
    
    monitor.alert_manager.thresholds[alert_type_enum] = AlertThreshold(
        alert_type=alert_type_enum,
        warning_threshold=request.warning_threshold,
        error_threshold=request.error_threshold,
        critical_threshold=request.critical_threshold,
        window_minutes=request.window_minutes,
    )
    
    return {"status": "updated", "alert_type": alert_type}


# DLQ Endpoints
@router.get("/dlq")
async def get_dlq_entries(
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user=Depends(get_current_user),
):
    """Get DLQ entries."""
    dlq = get_dead_letter_queue()
    
    status_enum = DLQEntryStatus(status) if status else None
    entries = await dlq.list_entries(status_enum, workflow_id, limit, offset)
    
    return {
        "entries": [e.to_dict() for e in entries],
        "total": len(entries),
    }


@router.get("/dlq/stats")
async def get_dlq_stats(
    current_user=Depends(get_current_user),
):
    """Get DLQ statistics."""
    dlq = get_dead_letter_queue()
    return await dlq.get_stats()


@router.get("/dlq/{entry_id}")
async def get_dlq_entry(
    entry_id: str,
    current_user=Depends(get_current_user),
):
    """Get a specific DLQ entry."""
    dlq = get_dead_letter_queue()
    entry = await dlq.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    
    return entry.to_dict()


@router.post("/dlq/{entry_id}/retry")
async def retry_dlq_entry(
    entry_id: str,
    request: DLQRetryRequest,
    current_user=Depends(get_current_user),
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


@router.post("/dlq/{entry_id}/resolve")
async def resolve_dlq_entry(
    entry_id: str,
    request: DLQResolveRequest,
    current_user=Depends(get_current_user),
):
    """Resolve a DLQ entry."""
    dlq = get_dead_letter_queue()
    entry = await dlq.resolve(entry_id, request.notes, request.discard)
    
    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    
    return entry.to_dict()


@router.post("/dlq/process-pending")
async def process_pending_dlq(
    limit: int = 10,
    workflow_id: Optional[str] = None,
    current_user=Depends(get_current_user),
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


@router.get("/dlq/processor/stats")
async def get_dlq_processor_stats(
    current_user=Depends(get_current_user),
):
    """Get DLQ processor statistics."""
    processor = get_dlq_processor()
    return processor.get_stats()


@router.get("/dlq/processor/schedule")
async def get_retry_schedule(
    current_user=Depends(get_current_user),
):
    """Get scheduled retries."""
    processor = get_dlq_processor()
    return await processor.get_retry_schedule()


# Checkpoint Endpoints
@router.get("/checkpoints/{execution_id}")
async def get_checkpoints(
    execution_id: str,
    current_user=Depends(get_current_user),
):
    """Get checkpoints for an execution."""
    from backend.services.agent_builder.checkpoint_recovery import get_checkpoint_manager
    
    manager = get_checkpoint_manager()
    checkpoints = await manager.list_checkpoints(execution_id)
    
    return {
        "execution_id": execution_id,
        "checkpoints": [cp.to_dict() for cp in checkpoints],
        "total": len(checkpoints),
    }


@router.get("/checkpoints/{execution_id}/latest")
async def get_latest_checkpoint(
    execution_id: str,
    checkpoint_type: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Get latest checkpoint for an execution."""
    from backend.services.agent_builder.checkpoint_recovery import (
        get_checkpoint_manager,
        CheckpointType,
    )
    
    manager = get_checkpoint_manager()
    type_enum = CheckpointType(checkpoint_type) if checkpoint_type else None
    checkpoint = await manager.get_latest_checkpoint(execution_id, type_enum)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="No checkpoint found")
    
    return checkpoint.to_dict()


@router.delete("/checkpoints/{checkpoint_id}")
async def delete_checkpoint(
    checkpoint_id: str,
    current_user=Depends(get_current_user),
):
    """Delete a checkpoint."""
    from backend.services.agent_builder.checkpoint_recovery import get_checkpoint_manager
    
    manager = get_checkpoint_manager()
    success = await manager.delete_checkpoint(checkpoint_id)
    
    return {"deleted": success}


# Health Check
@router.get("/health")
async def monitoring_health():
    """Check monitoring system health."""
    monitor = get_workflow_monitor()
    metrics = get_metrics_collector()
    dlq = get_dead_letter_queue()
    
    dlq_stats = await dlq.get_stats()
    
    return {
        "status": "healthy",
        "components": {
            "metrics": "ok",
            "alerts": "ok",
            "dlq": "ok",
        },
        "summary": {
            "active_alerts": len(monitor.alert_manager.get_active_alerts()),
            "dlq_pending": dlq_stats.get("by_status", {}).get("pending", 0),
            "total_executions": metrics.get_summary().get("total_executions", 0),
        },
    }
