"""
Audit Logs API

Provides endpoints for viewing and managing audit logs.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user, require_admin
from backend.db.models.user import User
from backend.core.audit_logger import AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/audit-logs",
    tags=["Audit Logs"],
)


# ============================================================================
# Models
# ============================================================================

class AuditLogEntry(BaseModel):
    """Audit log entry response model."""
    id: str
    event_type: str
    severity: str
    action: str
    user_id: Optional[str]
    user_email: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: dict
    success: bool
    error_message: Optional[str]
    timestamp: str


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response."""
    logs: List[AuditLogEntry]
    total: int
    page: int
    page_size: int
    has_more: bool


class AuditLogStats(BaseModel):
    """Audit log statistics."""
    total_events: int
    events_by_type: dict
    events_by_severity: dict
    events_by_user: dict
    success_rate: float
    time_range: dict


# In-memory storage for demo (production uses database)
_audit_logs: List[dict] = []


def _add_sample_logs():
    """Add sample audit logs for demo."""
    if _audit_logs:
        return
    
    sample_events = [
        {
            "id": "log_001",
            "event_type": "auth.login.success",
            "severity": "info",
            "action": "User logged in successfully",
            "user_id": "user_123",
            "user_email": "user@example.com",
            "ip_address": "192.168.1.1",
            "resource_type": None,
            "resource_id": None,
            "details": {"method": "password"},
            "success": True,
            "error_message": None,
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
        },
        {
            "id": "log_002",
            "event_type": "workflow.executed",
            "severity": "info",
            "action": "Workflow executed successfully",
            "user_id": "user_123",
            "user_email": "user@example.com",
            "ip_address": "192.168.1.1",
            "resource_type": "workflow",
            "resource_id": "wf_456",
            "details": {"execution_id": "exec_789", "duration_ms": 1234},
            "success": True,
            "error_message": None,
            "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
        },
        {
            "id": "log_003",
            "event_type": "auth.login.failed",
            "severity": "warning",
            "action": "Login attempt failed",
            "user_id": None,
            "user_email": "attacker@example.com",
            "ip_address": "10.0.0.1",
            "resource_type": None,
            "resource_id": None,
            "details": {"reason": "Invalid credentials"},
            "success": False,
            "error_message": "Invalid credentials",
            "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z",
        },
    ]
    _audit_logs.extend(sample_events)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List audit logs with filtering and pagination.
    
    Regular users can only see their own logs.
    Admins can see all logs.
    """
    _add_sample_logs()
    
    # Filter logs
    filtered_logs = _audit_logs.copy()
    
    # Non-admin users can only see their own logs
    if not getattr(current_user, 'is_admin', False):
        filtered_logs = [
            log for log in filtered_logs 
            if log.get("user_id") == str(current_user.id)
        ]
    
    # Apply filters
    if event_type:
        filtered_logs = [log for log in filtered_logs if log.get("event_type") == event_type]
    
    if severity:
        filtered_logs = [log for log in filtered_logs if log.get("severity") == severity]
    
    if user_id:
        filtered_logs = [log for log in filtered_logs if log.get("user_id") == user_id]
    
    if resource_type:
        filtered_logs = [log for log in filtered_logs if log.get("resource_type") == resource_type]
    
    if resource_id:
        filtered_logs = [log for log in filtered_logs if log.get("resource_id") == resource_id]
    
    if success is not None:
        filtered_logs = [log for log in filtered_logs if log.get("success") == success]
    
    # Sort by timestamp descending
    filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Paginate
    total = len(filtered_logs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_logs = filtered_logs[start_idx:end_idx]
    
    return AuditLogListResponse(
        logs=[AuditLogEntry(**log) for log in page_logs],
        total=total,
        page=page,
        page_size=page_size,
        has_more=end_idx < total
    )


@router.get("/stats", response_model=AuditLogStats)
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get audit log statistics.
    
    Provides aggregated statistics for the specified time period.
    """
    _add_sample_logs()
    
    # Filter by time range
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_str = cutoff.isoformat() + "Z"
    
    filtered_logs = [
        log for log in _audit_logs
        if log.get("timestamp", "") >= cutoff_str
    ]
    
    # Non-admin users can only see their own stats
    if not getattr(current_user, 'is_admin', False):
        filtered_logs = [
            log for log in filtered_logs 
            if log.get("user_id") == str(current_user.id)
        ]
    
    # Calculate stats
    total = len(filtered_logs)
    
    events_by_type = {}
    events_by_severity = {}
    events_by_user = {}
    success_count = 0
    
    for log in filtered_logs:
        # By type
        event_type = log.get("event_type", "unknown")
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        # By severity
        severity = log.get("severity", "info")
        events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
        
        # By user
        user_id = log.get("user_id") or "anonymous"
        events_by_user[user_id] = events_by_user.get(user_id, 0) + 1
        
        # Success count
        if log.get("success"):
            success_count += 1
    
    return AuditLogStats(
        total_events=total,
        events_by_type=events_by_type,
        events_by_severity=events_by_severity,
        events_by_user=events_by_user,
        success_rate=success_count / total if total > 0 else 0,
        time_range={
            "start": cutoff.isoformat() + "Z",
            "end": datetime.utcnow().isoformat() + "Z",
            "days": days
        }
    )


@router.get("/event-types")
async def list_event_types(
    current_user: User = Depends(get_current_user),
):
    """
    List all available audit event types.
    """
    return {
        "event_types": [
            {"value": e.value, "name": e.name}
            for e in AuditEventType
        ]
    }


@router.get("/severities")
async def list_severities(
    current_user: User = Depends(get_current_user),
):
    """
    List all available severity levels.
    """
    return {
        "severities": [
            {"value": s.value, "name": s.name}
            for s in AuditSeverity
        ]
    }


@router.get("/{log_id}", response_model=AuditLogEntry)
async def get_audit_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific audit log entry by ID.
    """
    _add_sample_logs()
    
    for log in _audit_logs:
        if log.get("id") == log_id:
            # Check permission
            if not getattr(current_user, 'is_admin', False):
                if log.get("user_id") != str(current_user.id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied"
                    )
            
            return AuditLogEntry(**log)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audit log {log_id} not found"
    )


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: int = Query(90, ge=30, le=365, description="Delete logs older than this many days"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete old audit logs (admin only).
    
    Removes logs older than the specified number of days.
    """
    global _audit_logs
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_str = cutoff.isoformat() + "Z"
    
    original_count = len(_audit_logs)
    _audit_logs = [
        log for log in _audit_logs
        if log.get("timestamp", "") >= cutoff_str
    ]
    deleted_count = original_count - len(_audit_logs)
    
    logger.info(f"Admin {current_user.id} deleted {deleted_count} old audit logs")
    
    return {
        "message": f"Deleted {deleted_count} audit logs older than {days} days",
        "deleted_count": deleted_count,
        "remaining_count": len(_audit_logs)
    }


@router.post("/export")
async def export_audit_logs(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Export audit logs (admin only).
    
    Returns logs in the specified format for compliance/archival.
    """
    _add_sample_logs()
    
    filtered_logs = _audit_logs.copy()
    
    # Apply date filters
    if start_date:
        filtered_logs = [log for log in filtered_logs if log.get("timestamp", "") >= start_date]
    
    if end_date:
        filtered_logs = [log for log in filtered_logs if log.get("timestamp", "") <= end_date]
    
    if format == "csv":
        # Generate CSV
        import csv
        import io
        
        output = io.StringIO()
        if filtered_logs:
            writer = csv.DictWriter(output, fieldnames=filtered_logs[0].keys())
            writer.writeheader()
            writer.writerows(filtered_logs)
        
        return {
            "format": "csv",
            "count": len(filtered_logs),
            "data": output.getvalue()
        }
    
    return {
        "format": "json",
        "count": len(filtered_logs),
        "data": filtered_logs
    }
