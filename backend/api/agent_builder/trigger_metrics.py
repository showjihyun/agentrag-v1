"""
Trigger Metrics and Monitoring API.

Provides endpoints for monitoring trigger performance and health.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.agent_builder import (
    Workflow,
    WorkflowWebhook,
    WorkflowSchedule,
    TriggerExecution,
)
from backend.core.triggers.enhanced_manager import (
    EnhancedTriggerManager,
    TriggerType,
    RetryConfig,
    RateLimitConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/triggers/metrics", tags=["trigger-metrics"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TriggerMetricsResponse(BaseModel):
    """Trigger metrics response."""
    trigger_id: str
    trigger_type: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_duration_ms: float
    last_execution_at: Optional[datetime]
    last_error: Optional[str]


class RateLimitStatusResponse(BaseModel):
    """Rate limit status response."""
    trigger_id: str
    remaining_requests: Dict[str, int]
    limits: Dict[str, int]


class TriggerHealthResponse(BaseModel):
    """Trigger health status."""
    trigger_id: str
    trigger_type: str
    workflow_id: str
    is_active: bool
    health_status: str  # healthy, degraded, unhealthy
    issues: List[str]
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    failure_rate_24h: float


class TriggerPerformanceReport(BaseModel):
    """Performance report for triggers."""
    period_start: datetime
    period_end: datetime
    total_triggers: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    by_type: Dict[str, Dict[str, Any]]
    slowest_triggers: List[Dict[str, Any]]
    most_failed_triggers: List[Dict[str, Any]]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/{trigger_id}", response_model=TriggerMetricsResponse)
async def get_trigger_metrics(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics for a specific trigger.
    
    Returns execution statistics including success rate and duration.
    """
    logger.info(f"Getting metrics for trigger {trigger_id}")
    
    try:
        # Verify access
        await _verify_trigger_access(db, trigger_id, trigger_type, current_user)
        
        # Get metrics from enhanced manager
        manager = EnhancedTriggerManager(db)
        metrics = manager.get_metrics(trigger_id)
        
        if not metrics:
            # Calculate from database if not in memory
            metrics = await _calculate_metrics_from_db(db, trigger_id, trigger_type)
        
        return TriggerMetricsResponse(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trigger metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trigger_id}/rate-limit", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get rate limit status for a trigger.
    
    Shows remaining requests and current limits.
    """
    logger.info(f"Getting rate limit status for trigger {trigger_id}")
    
    try:
        # Verify access
        await _verify_trigger_access(db, trigger_id, trigger_type, current_user)
        
        # Get rate limit status
        manager = EnhancedTriggerManager(db)
        status = manager.get_rate_limit_status(trigger_id)
        
        return RateLimitStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trigger_id}/health", response_model=TriggerHealthResponse)
async def get_trigger_health(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get health status for a trigger.
    
    Analyzes recent executions to determine health.
    """
    logger.info(f"Getting health status for trigger {trigger_id}")
    
    try:
        # Verify access
        workflow_id = await _verify_trigger_access(db, trigger_id, trigger_type, current_user)
        
        # Get trigger info
        is_active = await _get_trigger_active_status(db, trigger_id, trigger_type)
        
        # Get recent executions (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        executions = db.query(TriggerExecution).filter(
            TriggerExecution.trigger_id == trigger_id,
            TriggerExecution.triggered_at >= cutoff
        ).all()
        
        # Calculate health metrics
        total = len(executions)
        failed = sum(1 for e in executions if e.status == "failed")
        failure_rate = (failed / total * 100) if total > 0 else 0
        
        # Determine health status
        issues = []
        if not is_active:
            health_status = "unhealthy"
            issues.append("Trigger is inactive")
        elif failure_rate > 50:
            health_status = "unhealthy"
            issues.append(f"High failure rate: {failure_rate:.1f}%")
        elif failure_rate > 20:
            health_status = "degraded"
            issues.append(f"Elevated failure rate: {failure_rate:.1f}%")
        elif total == 0:
            health_status = "unknown"
            issues.append("No executions in last 24 hours")
        else:
            health_status = "healthy"
        
        # Get last success/failure times
        last_success = None
        last_failure = None
        
        for e in sorted(executions, key=lambda x: x.triggered_at, reverse=True):
            if e.status == "success" and not last_success:
                last_success = e.triggered_at
            elif e.status == "failed" and not last_failure:
                last_failure = e.triggered_at
            
            if last_success and last_failure:
                break
        
        return TriggerHealthResponse(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            workflow_id=workflow_id,
            is_active=is_active,
            health_status=health_status,
            issues=issues,
            last_success_at=last_success,
            last_failure_at=last_failure,
            failure_rate_24h=failure_rate,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trigger health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/performance", response_model=TriggerPerformanceReport)
async def get_performance_report(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance report for all triggers.
    
    Provides comprehensive analysis of trigger performance.
    """
    logger.info(f"Generating trigger performance report for user {current_user.id}")
    
    try:
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)
        
        # Get user's workflows
        workflow_query = db.query(Workflow).filter(Workflow.user_id == current_user.id)
        if workflow_id:
            workflow_query = workflow_query.filter(Workflow.id == workflow_id)
        
        workflows = workflow_query.all()
        workflow_ids = [w.id for w in workflows]
        
        # Get executions in period
        executions = db.query(TriggerExecution).filter(
            TriggerExecution.workflow_id.in_(workflow_ids),
            TriggerExecution.triggered_at >= period_start,
            TriggerExecution.triggered_at <= period_end,
        ).all()
        
        # Calculate statistics
        total_executions = len(executions)
        successful = sum(1 for e in executions if e.status == "success")
        failed = sum(1 for e in executions if e.status == "failed")
        
        durations = [e.duration_ms for e in executions if e.duration_ms]
        durations.sort()
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        def percentile(data, p):
            if not data:
                return 0
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]
        
        # Group by type
        by_type = {}
        for e in executions:
            if e.trigger_type not in by_type:
                by_type[e.trigger_type] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "avg_duration_ms": 0,
                    "durations": [],
                }
            
            by_type[e.trigger_type]["total"] += 1
            if e.status == "success":
                by_type[e.trigger_type]["successful"] += 1
            elif e.status == "failed":
                by_type[e.trigger_type]["failed"] += 1
            
            if e.duration_ms:
                by_type[e.trigger_type]["durations"].append(e.duration_ms)
        
        # Calculate averages per type
        for t in by_type:
            d = by_type[t]["durations"]
            by_type[t]["avg_duration_ms"] = sum(d) / len(d) if d else 0
            del by_type[t]["durations"]
        
        # Find slowest triggers
        trigger_durations = {}
        for e in executions:
            if e.duration_ms:
                key = e.trigger_id or "unknown"
                if key not in trigger_durations:
                    trigger_durations[key] = []
                trigger_durations[key].append(e.duration_ms)
        
        slowest = sorted(
            [
                {
                    "trigger_id": tid,
                    "avg_duration_ms": sum(d) / len(d),
                    "execution_count": len(d),
                }
                for tid, d in trigger_durations.items()
            ],
            key=lambda x: x["avg_duration_ms"],
            reverse=True
        )[:5]
        
        # Find most failed triggers
        trigger_failures = {}
        for e in executions:
            key = e.trigger_id or "unknown"
            if key not in trigger_failures:
                trigger_failures[key] = {"total": 0, "failed": 0}
            trigger_failures[key]["total"] += 1
            if e.status == "failed":
                trigger_failures[key]["failed"] += 1
        
        most_failed = sorted(
            [
                {
                    "trigger_id": tid,
                    "failure_rate": (d["failed"] / d["total"] * 100) if d["total"] > 0 else 0,
                    "failed_count": d["failed"],
                    "total_count": d["total"],
                }
                for tid, d in trigger_failures.items()
                if d["failed"] > 0
            ],
            key=lambda x: x["failure_rate"],
            reverse=True
        )[:5]
        
        # Count total triggers
        webhook_count = db.query(WorkflowWebhook).filter(
            WorkflowWebhook.workflow_id.in_(workflow_ids)
        ).count()
        schedule_count = db.query(WorkflowSchedule).filter(
            WorkflowSchedule.workflow_id.in_(workflow_ids)
        ).count()
        
        return TriggerPerformanceReport(
            period_start=period_start,
            period_end=period_end,
            total_triggers=webhook_count + schedule_count,
            total_executions=total_executions,
            successful_executions=successful,
            failed_executions=failed,
            avg_duration_ms=avg_duration,
            p50_duration_ms=percentile(durations, 50),
            p95_duration_ms=percentile(durations, 95),
            p99_duration_ms=percentile(durations, 99),
            by_type=by_type,
            slowest_triggers=slowest,
            most_failed_triggers=most_failed,
        )
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _verify_trigger_access(
    db: Session,
    trigger_id: str,
    trigger_type: str,
    user: User
) -> str:
    """Verify user has access to trigger. Returns workflow_id."""
    workflow_id = None
    
    if trigger_type == "webhook":
        trigger = db.query(WorkflowWebhook).filter(
            WorkflowWebhook.id == trigger_id
        ).first()
        if trigger:
            workflow_id = str(trigger.workflow_id)
    
    elif trigger_type == "schedule":
        trigger = db.query(WorkflowSchedule).filter(
            WorkflowSchedule.id == trigger_id
        ).first()
        if trigger:
            workflow_id = str(trigger.workflow_id)
    
    if not workflow_id:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    # Verify workflow ownership
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow or str(workflow.user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return workflow_id


async def _get_trigger_active_status(
    db: Session,
    trigger_id: str,
    trigger_type: str
) -> bool:
    """Get trigger active status."""
    if trigger_type == "webhook":
        trigger = db.query(WorkflowWebhook).filter(
            WorkflowWebhook.id == trigger_id
        ).first()
        return trigger.is_active if trigger else False
    
    elif trigger_type == "schedule":
        trigger = db.query(WorkflowSchedule).filter(
            WorkflowSchedule.id == trigger_id
        ).first()
        return trigger.is_active if trigger else False
    
    return False


async def _calculate_metrics_from_db(
    db: Session,
    trigger_id: str,
    trigger_type: str
) -> Dict[str, Any]:
    """Calculate metrics from database."""
    executions = db.query(TriggerExecution).filter(
        TriggerExecution.trigger_id == trigger_id
    ).all()
    
    total = len(executions)
    successful = sum(1 for e in executions if e.status == "success")
    failed = sum(1 for e in executions if e.status == "failed")
    
    durations = [e.duration_ms for e in executions if e.duration_ms]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    last_execution = max(
        (e.triggered_at for e in executions),
        default=None
    )
    
    last_error = None
    for e in sorted(executions, key=lambda x: x.triggered_at, reverse=True):
        if e.error_message:
            last_error = e.error_message
            break
    
    return {
        "trigger_id": trigger_id,
        "trigger_type": trigger_type,
        "total_executions": total,
        "successful_executions": successful,
        "failed_executions": failed,
        "success_rate": (successful / total * 100) if total > 0 else 100.0,
        "avg_duration_ms": avg_duration,
        "last_execution_at": last_execution,
        "last_error": last_error,
    }
