"""
Execution monitoring and streaming API endpoints.

Provides real-time execution monitoring through Server-Sent Events (SSE)
and execution history management.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, AsyncGenerator
import asyncio
import json
from datetime import datetime

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.flows import FlowExecution, NodeExecution, ExecutionLog
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agent-builder/executions", tags=["Executions"])


@router.get("/stats/summary")
async def get_execution_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to include in stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution statistics summary for the user.
    """
    try:
        from datetime import timedelta
        from sqlalchemy import func
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get executions in date range
        executions = db.query(FlowExecution).filter(
            FlowExecution.user_id == current_user.id,
            FlowExecution.started_at >= start_date,
            FlowExecution.started_at <= end_date
        ).all()
        
        # Calculate statistics
        total_executions = len(executions)
        completed_executions = len([e for e in executions if e.status == "completed"])
        failed_executions = len([e for e in executions if e.status == "failed"])
        cancelled_executions = len([e for e in executions if e.status == "cancelled"])
        
        success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0
        
        # Calculate average duration for completed executions
        completed_durations = [e.duration_ms for e in executions if e.status == "completed" and e.duration_ms]
        avg_duration_ms = sum(completed_durations) / len(completed_durations) if completed_durations else 0
        
        # Calculate total costs
        total_cost = 0
        total_tokens = 0
        for execution in executions:
            if execution.metrics:
                total_cost += execution.metrics.get("estimated_cost", 0)
                total_tokens += execution.metrics.get("total_tokens", 0)
        
        # Group by flow type
        agentflow_count = len([e for e in executions if e.flow_type == "agentflow"])
        chatflow_count = len([e for e in executions if e.flow_type == "chatflow"])
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "totals": {
                "total_executions": total_executions,
                "completed_executions": completed_executions,
                "failed_executions": failed_executions,
                "cancelled_executions": cancelled_executions,
                "success_rate": round(success_rate, 2)
            },
            "performance": {
                "avg_duration_ms": round(avg_duration_ms, 2),
                "total_tokens": total_tokens,
                "estimated_cost": round(total_cost, 4)
            },
            "by_flow_type": {
                "agentflow_executions": agentflow_count,
                "chatflow_executions": chatflow_count
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_execution_stats_short(
    days: int = Query(7, ge=1, le=90, description="Number of days to include in stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution statistics summary for the user (short URL).
    """
    return await get_execution_stats(days, db, current_user)


@router.get("/{execution_id}")
async def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution details by ID.
    """
    try:
        execution = db.query(FlowExecution).filter(
            FlowExecution.id == execution_id,
            FlowExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # Get node executions
        node_executions = db.query(NodeExecution).filter(
            NodeExecution.flow_execution_id == execution_id
        ).order_by(NodeExecution.started_at).all()
        
        # Get execution logs
        logs = db.query(ExecutionLog).filter(
            ExecutionLog.flow_execution_id == execution_id
        ).order_by(ExecutionLog.timestamp.desc()).limit(100).all()
        
        return {
            "id": str(execution.id),
            "flow_id": str(execution.agentflow_id) if execution.agentflow_id else str(execution.chatflow_id),
            "flow_type": execution.flow_type,
            "flow_name": execution.flow_name,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_ms": execution.duration_ms,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "error_message": execution.error_message,
            "metrics": execution.metrics,
            "node_executions": [
                {
                    "id": str(node.id),
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "node_label": node.node_label,
                    "status": node.status,
                    "started_at": node.started_at.isoformat() if node.started_at else None,
                    "completed_at": node.completed_at.isoformat() if node.completed_at else None,
                    "duration_ms": node.duration_ms,
                    "input_data": node.input_data,
                    "output_data": node.output_data,
                    "error_message": node.error_message,
                    "retry_count": node.retry_count
                }
                for node in node_executions
            ],
            "logs": [
                {
                    "id": str(log.id),
                    "level": log.level,
                    "message": log.message,
                    "metadata": log.log_metadata,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ]
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/stream")
async def stream_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream real-time execution updates via Server-Sent Events (SSE).
    """
    try:
        # Verify execution exists and user has access
        execution = db.query(FlowExecution).filter(
            FlowExecution.id == execution_id,
            FlowExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        async def event_stream() -> AsyncGenerator[str, None]:
            """Generate SSE events for execution updates."""
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'execution_start', 'execution_id': execution_id})}\n\n"
            
            last_update = datetime.utcnow()
            
            while True:
                try:
                    # Get current execution status
                    current_execution = db.query(FlowExecution).filter(
                        FlowExecution.id == execution_id
                    ).first()
                    
                    if not current_execution:
                        break
                    
                    # Get node executions that have been updated
                    node_executions = db.query(NodeExecution).filter(
                        NodeExecution.flow_execution_id == execution_id
                    ).all()
                    
                    # Calculate progress
                    total_nodes = len(node_executions) if node_executions else 1
                    completed_nodes = len([n for n in node_executions if n.status == "completed"])
                    failed_nodes = len([n for n in node_executions if n.status == "failed"])
                    running_nodes = len([n for n in node_executions if n.status == "running"])
                    
                    progress = (completed_nodes / total_nodes) * 100 if total_nodes > 0 else 0
                    
                    # Create update event
                    update_data = {
                        "type": "execution_update",
                        "execution_id": execution_id,
                        "status": current_execution.status,
                        "progress": round(progress, 2),
                        "metrics": {
                            "total_nodes": total_nodes,
                            "completed_nodes": completed_nodes,
                            "failed_nodes": failed_nodes,
                            "running_nodes": running_nodes,
                            **(current_execution.metrics or {})
                        },
                        "node_updates": [
                            {
                                "node_id": node.node_id,
                                "status": node.status,
                                "duration_ms": node.duration_ms,
                                "error_message": node.error_message
                            }
                            for node in node_executions
                        ],
                        "error_message": current_execution.error_message,
                        "error_details": current_execution.metrics.get("error_details", []) if current_execution.metrics else [],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    yield f"data: {json.dumps(update_data)}\n\n"
                    
                    # Check if execution is complete
                    if current_execution.status in ["completed", "failed", "cancelled"]:
                        # Send final event
                        final_data = {
                            "type": "execution_complete",
                            "execution_id": execution_id,
                            "status": current_execution.status,
                            "duration_ms": current_execution.duration_ms,
                            "output_data": current_execution.output_data,
                            "error_message": current_execution.error_message,
                            "error_details": current_execution.metrics.get("error_details", []) if current_execution.metrics else [],
                            "final_metrics": current_execution.metrics,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                    
                    # Wait before next update
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error in execution stream: {str(e)}")
                    error_data = {
                        "type": "execution_error",
                        "execution_id": execution_id,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_executions(
    flow_id: Optional[str] = Query(None, description="Filter by flow ID"),
    flow_type: Optional[str] = Query(None, description="Filter by flow type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of executions to return"),
    offset: int = Query(0, ge=0, description="Number of executions to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List executions with optional filtering.
    """
    try:
        query = db.query(FlowExecution).filter(
            FlowExecution.user_id == current_user.id
        )
        
        # Apply filters
        if flow_id:
            query = query.filter(
                (FlowExecution.agentflow_id == flow_id) |
                (FlowExecution.chatflow_id == flow_id)
            )
        
        if flow_type:
            query = query.filter(FlowExecution.flow_type == flow_type)
        
        if status:
            query = query.filter(FlowExecution.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        executions = query.order_by(
            FlowExecution.started_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "executions": [
                {
                    "id": str(execution.id),
                    "flow_id": str(execution.agentflow_id) if execution.agentflow_id else str(execution.chatflow_id),
                    "flow_type": execution.flow_type,
                    "flow_name": execution.flow_name,
                    "status": execution.status,
                    "started_at": execution.started_at.isoformat(),
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                    "duration_ms": execution.duration_ms,
                    "error_message": execution.error_message,
                    "metrics": execution.metrics
                }
                for execution in executions
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list executions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a running execution.
    """
    try:
        execution = db.query(FlowExecution).filter(
            FlowExecution.id == execution_id,
            FlowExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        if execution.status not in ["running", "pending"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel execution with status: {execution.status}"
            )
        
        # Update execution status
        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        
        if execution.started_at:
            execution.duration_ms = int(
                (execution.completed_at - execution.started_at).total_seconds() * 1000
            )
        
        # Cancel any running node executions
        db.query(NodeExecution).filter(
            NodeExecution.flow_execution_id == execution_id,
            NodeExecution.status == "running"
        ).update({"status": "cancelled"})
        
        db.commit()
        
        logger.info(f"Execution {execution_id} cancelled by user {current_user.id}")
        
        return {"message": "Execution cancelled successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution logs with optional filtering.
    """
    try:
        # Verify execution exists and user has access
        execution = db.query(FlowExecution).filter(
            FlowExecution.id == execution_id,
            FlowExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        query = db.query(ExecutionLog).filter(
            ExecutionLog.flow_execution_id == execution_id
        )
        
        # Apply level filter
        if level:
            query = query.filter(ExecutionLog.level == level)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering (newest first)
        logs = query.order_by(
            ExecutionLog.timestamp.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": str(log.id),
                    "level": log.level,
                    "message": log.message,
                    "metadata": log.log_metadata,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution logs {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))