"""
Workflow Admin API

Administrative endpoints for workflow management, monitoring,
and system operations.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user, require_admin
from backend.db.database import get_db
from backend.db.models.user import User

from backend.services.agent_builder.dead_letter_queue import (
    get_dead_letter_queue,
    DLQEntryStatus,
)
from backend.services.agent_builder.workflow_state_manager import (
    get_state_manager,
    WorkflowState,
)
from backend.services.agent_builder.distributed_lock import get_lock_manager
from backend.services.agent_builder.idempotency_manager import get_idempotency_manager
from backend.services.agent_builder.workflow_event_bus import (
    get_event_bus,
    WorkflowEventType,
)
from backend.services.agent_builder.workflow_versioning import (
    get_version_manager,
    VersionChangeType,
)
from backend.services.agent_builder.circuit_breaker import get_all_circuit_breaker_states

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/admin",
    tags=["agent-builder-admin"],
)


# ============================================================================
# Dead Letter Queue Management
# ============================================================================

@router.get("/dlq/stats")
async def get_dlq_stats(
    current_user: User = Depends(require_admin),
):
    """Get Dead Letter Queue statistics."""
    dlq = get_dead_letter_queue()
    stats = await dlq.get_stats()
    return stats


@router.get("/dlq/entries")
async def list_dlq_entries(
    status: Optional[str] = Query(None, description="Filter by status"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
):
    """List Dead Letter Queue entries."""
    dlq = get_dead_letter_queue()
    
    status_filter = DLQEntryStatus(status) if status else None
    entries = await dlq.list_entries(
        status=status_filter,
        workflow_id=workflow_id,
        limit=limit,
        offset=offset,
    )
    
    return {
        "entries": [e.to_dict() for e in entries],
        "total": len(entries),
    }


@router.post("/dlq/entries/{entry_id}/retry")
async def retry_dlq_entry(
    entry_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retry a failed execution from DLQ."""
    dlq = get_dead_letter_queue()
    
    entry = await dlq.mark_retrying(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ entry not found or max retries exceeded",
        )
    
    # Re-execute workflow
    from backend.services.agent_builder.workflow_service import WorkflowService
    from backend.services.agent_builder.workflow_executor_v2 import execute_workflow_v2
    
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(entry.workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    try:
        result = await execute_workflow_v2(
            workflow=workflow,
            db=db,
            input_data=entry.input_data,
        )
        
        if result.get("success"):
            await dlq.resolve(entry_id, notes=f"Retry successful by {current_user.email}")
        
        return {
            "entry_id": entry_id,
            "retry_count": entry.retry_count,
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"DLQ retry failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retry failed: {str(e)}",
        )


@router.post("/dlq/entries/{entry_id}/resolve")
async def resolve_dlq_entry(
    entry_id: str,
    notes: Optional[str] = None,
    discard: bool = False,
    current_user: User = Depends(require_admin),
):
    """Manually resolve or discard a DLQ entry."""
    dlq = get_dead_letter_queue()
    
    entry = await dlq.resolve(
        entry_id,
        notes=notes or f"Resolved by {current_user.email}",
        discard=discard,
    )
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DLQ entry not found",
        )
    
    return entry.to_dict()


@router.post("/dlq/cleanup")
async def cleanup_dlq(
    older_than_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_admin),
):
    """Clean up old resolved DLQ entries."""
    dlq = get_dead_letter_queue()
    removed = await dlq.cleanup_resolved(older_than_days)
    
    return {
        "removed": removed,
        "message": f"Removed {removed} entries older than {older_than_days} days",
    }


# ============================================================================
# Execution State Management
# ============================================================================

@router.get("/executions/{execution_id}/state")
async def get_execution_state(
    execution_id: str,
    current_user: User = Depends(require_admin),
):
    """Get detailed execution state."""
    state_manager = get_state_manager()
    state = await state_manager.get_state(execution_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    
    return state


@router.get("/executions/{execution_id}/history")
async def get_execution_history(
    execution_id: str,
    current_user: User = Depends(require_admin),
):
    """Get execution state transition history."""
    state_manager = get_state_manager()
    history = await state_manager.get_history(execution_id)
    
    return {
        "execution_id": execution_id,
        "history": history,
    }


@router.get("/executions/{execution_id}/checkpoints")
async def list_execution_checkpoints(
    execution_id: str,
    current_user: User = Depends(require_admin),
):
    """List checkpoints for an execution."""
    state_manager = get_state_manager()
    state = await state_manager.get_state(execution_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    
    return {
        "execution_id": execution_id,
        "checkpoints": state.get("checkpoints", []),
    }


@router.post("/executions/{execution_id}/restore/{checkpoint_id}")
async def restore_checkpoint(
    execution_id: str,
    checkpoint_id: str,
    current_user: User = Depends(require_admin),
):
    """Restore execution to a checkpoint."""
    state_manager = get_state_manager()
    
    try:
        state = await state_manager.restore_checkpoint(execution_id, checkpoint_id)
        return state
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Version Management
# ============================================================================

@router.get("/workflows/{workflow_id}/versions")
async def list_workflow_versions(
    workflow_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
):
    """List all versions of a workflow."""
    version_manager = get_version_manager()
    versions = await version_manager.list_versions(workflow_id, limit, offset)
    
    return {
        "workflow_id": workflow_id,
        "versions": [v.to_dict() for v in versions],
        "total": len(versions),
    }


@router.get("/workflows/{workflow_id}/versions/{version_id}")
async def get_workflow_version(
    workflow_id: str,
    version_id: str,
    current_user: User = Depends(require_admin),
):
    """Get a specific workflow version."""
    version_manager = get_version_manager()
    version = await version_manager.get_version(workflow_id, version_id=version_id)
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )
    
    return version.to_dict()


@router.post("/workflows/{workflow_id}/versions/{version_id}/publish")
async def publish_workflow_version(
    workflow_id: str,
    version_id: str,
    current_user: User = Depends(require_admin),
):
    """Publish a workflow version."""
    version_manager = get_version_manager()
    
    try:
        version = await version_manager.publish_version(workflow_id, version_id)
        return version.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/workflows/{workflow_id}/rollback")
async def rollback_workflow(
    workflow_id: str,
    target_version_id: str,
    reason: str,
    current_user: User = Depends(require_admin),
):
    """Rollback workflow to a previous version."""
    version_manager = get_version_manager()
    
    try:
        version = await version_manager.rollback(
            workflow_id=workflow_id,
            target_version_id=target_version_id,
            reason=reason,
            created_by=str(current_user.id),
        )
        return version.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/workflows/{workflow_id}/versions/compare")
async def compare_workflow_versions(
    workflow_id: str,
    from_version_id: str,
    to_version_id: str,
    current_user: User = Depends(require_admin),
):
    """Compare two workflow versions."""
    version_manager = get_version_manager()
    
    try:
        diff = await version_manager.compare_versions(
            workflow_id,
            from_version_id,
            to_version_id,
        )
        return diff.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Event History
# ============================================================================

@router.get("/events")
async def list_events(
    workflow_id: Optional[str] = None,
    event_type: Optional[str] = None,
    execution_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin),
):
    """List workflow events."""
    event_bus = get_event_bus()
    
    event_type_filter = WorkflowEventType(event_type) if event_type else None
    events = await event_bus.get_events(
        workflow_id=workflow_id,
        event_type=event_type_filter,
        execution_id=execution_id,
        limit=limit,
    )
    
    return {
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }


# ============================================================================
# System Health & Monitoring
# ============================================================================

@router.get("/health/circuit-breakers")
async def get_circuit_breaker_status(
    current_user: User = Depends(require_admin),
):
    """Get status of all circuit breakers."""
    states = get_all_circuit_breaker_states()
    return {
        "circuit_breakers": states,
        "total": len(states),
    }


@router.get("/health/locks")
async def get_active_locks(
    current_user: User = Depends(require_admin),
):
    """Get information about active distributed locks."""
    lock_manager = get_lock_manager()
    
    # This would need Redis SCAN to list all locks
    # For now, return basic info
    return {
        "message": "Lock information available via Redis directly",
        "pattern": "lock:*",
    }


@router.post("/maintenance/cleanup")
async def run_maintenance_cleanup(
    current_user: User = Depends(require_admin),
):
    """Run maintenance cleanup tasks."""
    results = {}
    
    # Cleanup state manager
    state_manager = get_state_manager()
    results["expired_states"] = await state_manager.cleanup_expired(max_age_days=7)
    
    # Cleanup idempotency records
    idempotency_manager = get_idempotency_manager()
    results["expired_idempotency"] = await idempotency_manager.cleanup_expired()
    
    # Cleanup DLQ
    dlq = get_dead_letter_queue()
    results["resolved_dlq_entries"] = await dlq.cleanup_resolved(older_than_days=30)
    
    return {
        "status": "completed",
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats/overview")
async def get_system_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get system overview statistics."""
    from backend.db.models.agent_builder import Workflow, WorkflowExecution
    from sqlalchemy import func
    
    # Get workflow counts
    total_workflows = db.query(func.count(Workflow.id)).scalar()
    
    # Get execution stats
    total_executions = db.query(func.count(WorkflowExecution.id)).scalar()
    
    recent_executions = db.query(WorkflowExecution).filter(
        WorkflowExecution.started_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    failed_executions = db.query(WorkflowExecution).filter(
        WorkflowExecution.status == "failed",
        WorkflowExecution.started_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # Get DLQ stats
    dlq = get_dead_letter_queue()
    dlq_stats = await dlq.get_stats()
    
    # Get circuit breaker states
    cb_states = get_all_circuit_breaker_states()
    open_circuits = sum(1 for s in cb_states.values() if s.get("state") == "open")
    
    return {
        "workflows": {
            "total": total_workflows,
        },
        "executions": {
            "total": total_executions,
            "last_24h": recent_executions,
            "failed_24h": failed_executions,
            "success_rate": (
                round((recent_executions - failed_executions) / recent_executions * 100, 2)
                if recent_executions > 0 else 100
            ),
        },
        "dlq": {
            "pending": dlq_stats.get("by_status", {}).get("pending", 0),
            "total": dlq_stats.get("total", 0),
        },
        "circuit_breakers": {
            "total": len(cb_states),
            "open": open_circuits,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
