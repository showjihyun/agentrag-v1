"""
Export API Endpoints

Provides PDF and other export functionality.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO

from backend.services.pdf_export_service import get_pdf_export_service
from backend.services.chat_history_service import get_chat_history_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exports", tags=["exports"])


class ChatExportRequest(BaseModel):
    """Request model for chat export."""
    session_id: str
    title: Optional[str] = "Chat Export"
    include_metadata: bool = True


class WorkflowExportRequest(BaseModel):
    """Request model for workflow export."""
    workflow_id: str
    include_details: bool = True
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@router.post("/chat/pdf")
async def export_chat_to_pdf(request: ChatExportRequest):
    """Export chat history to PDF."""
    try:
        pdf_service = get_pdf_export_service()
        chat_service = get_chat_history_service()
        
        # Get messages
        messages = chat_service.get_messages(request.session_id)
        if not messages:
            raise HTTPException(status_code=404, detail="No messages found")
        
        # Get session metadata
        session = chat_service.get_session(request.session_id)
        metadata = {"session_id": request.session_id}
        if session:
            metadata.update(session)
        
        # Generate PDF
        pdf_bytes = pdf_service.export_chat_history(
            messages=[m.to_dict() for m in messages],
            title=request.title or session.get("title", "Chat Export"),
            metadata=metadata if request.include_metadata else None,
        )
        
        filename = f"chat_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow/pdf")
async def export_workflow_to_pdf(request: WorkflowExportRequest):
    """Export workflow report to PDF."""
    from backend.db.database import SessionLocal
    from backend.db.models.agent_builder import Workflow, WorkflowExecution
    from sqlalchemy import desc
    from datetime import datetime as dt
    
    try:
        pdf_service = get_pdf_export_service()
        
        # Get workflow and executions from database
        db = SessionLocal()
        try:
            workflow_record = db.query(Workflow).filter(
                Workflow.id == request.workflow_id
            ).first()
            
            if not workflow_record:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # Build query for executions
            exec_query = db.query(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == request.workflow_id
            )
            
            # Apply date filters if provided
            if request.date_from:
                try:
                    date_from = dt.fromisoformat(request.date_from.replace('Z', '+00:00'))
                    exec_query = exec_query.filter(WorkflowExecution.started_at >= date_from)
                except ValueError:
                    pass
            
            if request.date_to:
                try:
                    date_to = dt.fromisoformat(request.date_to.replace('Z', '+00:00'))
                    exec_query = exec_query.filter(WorkflowExecution.started_at <= date_to)
                except ValueError:
                    pass
            
            executions = exec_query.order_by(desc(WorkflowExecution.started_at)).limit(100).all()
            
            # Convert to dict format
            workflow = {
                "id": str(workflow_record.id),
                "name": workflow_record.name,
                "description": workflow_record.description,
                "status": workflow_record.status,
                "created_at": workflow_record.created_at.isoformat() if workflow_record.created_at else None,
            }
            
            execution_list = []
            for exec in executions:
                duration_ms = None
                if exec.started_at and exec.completed_at:
                    duration_ms = int((exec.completed_at - exec.started_at).total_seconds() * 1000)
                
                execution_list.append({
                    "id": str(exec.id),
                    "status": exec.status,
                    "duration_ms": duration_ms,
                    "started_at": exec.started_at.isoformat() if exec.started_at else None,
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                    "error": exec.error,
                })
            
        finally:
            db.close()
        
        pdf_bytes = pdf_service.export_workflow_report(
            workflow=workflow,
            executions=execution_list,
            include_details=request.include_details,
        )
        
        safe_name = workflow["name"].replace(" ", "_")[:30]
        filename = f"workflow_{safe_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/pdf")
async def export_dashboard_to_pdf(
    user_id: str = Query(..., description="User ID"),
):
    """Export dashboard to PDF with real statistics."""
    from backend.db.database import SessionLocal
    from backend.db.models.agent_builder import Workflow, WorkflowExecution, Agent
    from sqlalchemy import func
    from datetime import timedelta
    
    try:
        pdf_service = get_pdf_export_service()
        
        db = SessionLocal()
        try:
            # Get real statistics
            total_workflows = db.query(func.count(Workflow.id)).filter(
                Workflow.user_id == user_id
            ).scalar() or 0
            
            total_agents = db.query(func.count(Agent.id)).filter(
                Agent.user_id == user_id
            ).scalar() or 0
            
            # Today's executions
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            executions_today = db.query(func.count(WorkflowExecution.id)).join(
                Workflow, WorkflowExecution.workflow_id == Workflow.id
            ).filter(
                Workflow.user_id == user_id,
                WorkflowExecution.started_at >= today_start
            ).scalar() or 0
            
            # Yesterday's executions for comparison
            yesterday_start = today_start - timedelta(days=1)
            executions_yesterday = db.query(func.count(WorkflowExecution.id)).join(
                Workflow, WorkflowExecution.workflow_id == Workflow.id
            ).filter(
                Workflow.user_id == user_id,
                WorkflowExecution.started_at >= yesterday_start,
                WorkflowExecution.started_at < today_start
            ).scalar() or 0
            
            # Calculate change
            if executions_yesterday > 0:
                exec_change = ((executions_today - executions_yesterday) / executions_yesterday) * 100
                exec_change_str = f"{'+' if exec_change >= 0 else ''}{exec_change:.1f}%"
            else:
                exec_change_str = "+0%" if executions_today == 0 else f"+{executions_today}"
            
            # Success rate (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            total_recent = db.query(func.count(WorkflowExecution.id)).join(
                Workflow, WorkflowExecution.workflow_id == Workflow.id
            ).filter(
                Workflow.user_id == user_id,
                WorkflowExecution.started_at >= week_ago
            ).scalar() or 0
            
            successful_recent = db.query(func.count(WorkflowExecution.id)).join(
                Workflow, WorkflowExecution.workflow_id == Workflow.id
            ).filter(
                Workflow.user_id == user_id,
                WorkflowExecution.started_at >= week_ago,
                WorkflowExecution.status == "completed"
            ).scalar() or 0
            
            success_rate = (successful_recent / total_recent * 100) if total_recent > 0 else 0
            
        finally:
            db.close()
        
        dashboard_data = {
            "metrics": [
                {"name": "Total Workflows", "value": str(total_workflows), "change": ""},
                {"name": "Total Agents", "value": str(total_agents), "change": ""},
                {"name": "Executions Today", "value": str(executions_today), "change": exec_change_str},
                {"name": "Success Rate (7d)", "value": f"{success_rate:.1f}%", "change": ""},
                {"name": "Total Executions (7d)", "value": str(total_recent), "change": ""},
            ]
        }
        
        pdf_bytes = pdf_service.export_dashboard(dashboard_data)
        
        filename = f"dashboard_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Dashboard PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
