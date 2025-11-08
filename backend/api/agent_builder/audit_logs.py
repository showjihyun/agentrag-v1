"""
Audit Logs API endpoints for Agent Builder.

Provides endpoints for viewing and exporting audit logs.
"""

import logging
import csv
import io
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.database import get_db
from backend.db.models.agent_builder import AuditLog
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs with filtering and pagination.
    
    Requires admin privileges.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Build query
        query = db.query(AuditLog)
        
        # Apply filters
        filters = []
        
        if action:
            if action.endswith("_"):
                # Prefix match (e.g., "security_")
                filters.append(AuditLog.action.like(f"{action}%"))
            else:
                filters.append(AuditLog.action == action)
        
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filters.append(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filters.append(AuditLog.timestamp <= end_dt)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size).all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        # Format response
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "timestamp": log.timestamp.isoformat()
            })
        
        return {
            "logs": logs_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$"),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export audit logs in CSV or JSON format.
    
    Requires admin privileges.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Build query
        query = db.query(AuditLog)
        
        # Apply filters (same as get_audit_logs)
        filters = []
        
        if action:
            if action.endswith("_"):
                filters.append(AuditLog.action.like(f"{action}%"))
            else:
                filters.append(AuditLog.action == action)
        
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filters.append(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filters.append(AuditLog.timestamp <= end_dt)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get all logs (limit to 10000 for safety)
        logs = query.order_by(AuditLog.timestamp.desc()).limit(10000).all()
        
        if format == "csv":
            # Generate CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Timestamp",
                "User ID",
                "Action",
                "Resource Type",
                "Resource ID",
                "IP Address",
                "User Agent",
                "Success",
                "Error Message",
                "Details"
            ])
            
            # Write rows
            for log in logs:
                writer.writerow([
                    log.timestamp.isoformat(),
                    log.user_id,
                    log.action,
                    log.resource_type or "",
                    log.resource_id or "",
                    log.ip_address or "",
                    log.user_agent or "",
                    log.details.get("success", True),
                    log.details.get("error_message", ""),
                    json.dumps(log.details)
                ])
            
            # Return CSV response
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        
        else:  # JSON format
            # Generate JSON
            logs_data = []
            for log in logs:
                logs_data.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "timestamp": log.timestamp.isoformat()
                })
            
            # Return JSON response
            json_str = json.dumps(logs_data, indent=2)
            return StreamingResponse(
                iter([json_str]),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        
    except Exception as e:
        logger.error(f"Failed to export audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_audit_log_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit log statistics.
    
    Requires admin privileges.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Build base query
        query = db.query(AuditLog)
        
        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end_dt)
        
        # Get total count
        total_logs = query.count()
        
        # Count by action
        from sqlalchemy import func
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label("count")
        ).group_by(AuditLog.action).all()
        
        # Count by resource type
        resource_counts = db.query(
            AuditLog.resource_type,
            func.count(AuditLog.id).label("count")
        ).filter(AuditLog.resource_type.isnot(None)).group_by(AuditLog.resource_type).all()
        
        # Count successes and failures
        success_count = query.filter(
            AuditLog.details["success"].astext == "true"
        ).count()
        
        failure_count = query.filter(
            AuditLog.details["success"].astext == "false"
        ).count()
        
        return {
            "total_logs": total_logs,
            "success_count": success_count,
            "failure_count": failure_count,
            "action_counts": {action: count for action, count in action_counts},
            "resource_counts": {resource: count for resource, count in resource_counts}
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit log stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
