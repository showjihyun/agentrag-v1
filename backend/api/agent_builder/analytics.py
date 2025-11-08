"""Agent Builder Analytics API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.agent_builder import (
    Agent,
    AgentExecution,
    Workflow,
    WorkflowExecution,
    Block,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/analytics",
    tags=["agent-builder-analytics"],
)


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get analytics overview for the specified period.
    
    Returns:
    - Total executions
    - Success rate
    - Average duration
    - Most used agents
    - Execution trends
    """
    try:
        user_id = current_user.id
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total executions
        total_executions = db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= start_date
        ).count()
        
        # Success rate
        successful = db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= start_date,
            AgentExecution.status == "completed"
        ).count()
        
        success_rate = (successful / total_executions * 100) if total_executions > 0 else 0
        
        # Average duration
        avg_duration = db.query(
            func.avg(
                func.extract('epoch', AgentExecution.completed_at - AgentExecution.started_at)
            )
        ).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= start_date,
            AgentExecution.status == "completed",
            AgentExecution.completed_at.isnot(None)
        ).scalar() or 0
        
        # Most used agents
        most_used = db.query(
            Agent.id,
            Agent.name,
            func.count(AgentExecution.id).label("execution_count")
        ).join(
            AgentExecution,
            Agent.id == AgentExecution.agent_id
        ).filter(
            Agent.user_id == user_id,
            AgentExecution.started_at >= start_date
        ).group_by(
            Agent.id, Agent.name
        ).order_by(
            desc("execution_count")
        ).limit(5).all()
        
        return {
            "period_days": days,
            "total_executions": total_executions,
            "success_rate": round(success_rate, 1),
            "avg_duration_seconds": round(avg_duration, 2),
            "most_used_agents": [
                {
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "execution_count": agent.execution_count
                }
                for agent in most_used
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics overview"
        )


@router.get("/performance")
async def get_performance_analytics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get performance analytics including response times and error rates."""
    try:
        user_id = current_user.id
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily performance metrics
        daily_metrics = db.query(
            func.date(AgentExecution.started_at).label("date"),
            func.count(AgentExecution.id).label("total"),
            func.avg(
                func.extract('epoch', AgentExecution.completed_at - AgentExecution.started_at)
            ).label("avg_duration"),
            func.min(
                func.extract('epoch', AgentExecution.completed_at - AgentExecution.started_at)
            ).label("min_duration"),
            func.max(
                func.extract('epoch', AgentExecution.completed_at - AgentExecution.started_at)
            ).label("max_duration")
        ).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= start_date,
            AgentExecution.status == "completed",
            AgentExecution.completed_at.isnot(None)
        ).group_by(
            func.date(AgentExecution.started_at)
        ).order_by(
            func.date(AgentExecution.started_at)
        ).all()
        
        return {
            "period_days": days,
            "daily_metrics": [
                {
                    "date": metric.date.isoformat(),
                    "total_executions": metric.total,
                    "avg_duration": round(metric.avg_duration or 0, 2),
                    "min_duration": round(metric.min_duration or 0, 2),
                    "max_duration": round(metric.max_duration or 0, 2)
                }
                for metric in daily_metrics
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance analytics"
        )


@router.get("/usage")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get usage analytics including resource utilization."""
    try:
        user_id = current_user.id
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Agent usage
        agent_count = db.query(Agent).filter(
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        ).count()
        
        # Block usage
        block_count = db.query(Block).filter(
            Block.user_id == user_id
        ).count()
        
        # Workflow usage
        workflow_count = db.query(Workflow).filter(
            Workflow.user_id == user_id
        ).count()
        
        # Execution by agent type
        by_type = db.query(
            Agent.agent_type,
            func.count(AgentExecution.id).label("count")
        ).join(
            AgentExecution,
            Agent.id == AgentExecution.agent_id
        ).filter(
            Agent.user_id == user_id,
            AgentExecution.started_at >= start_date
        ).group_by(
            Agent.agent_type
        ).all()
        
        return {
            "period_days": days,
            "resources": {
                "agents": agent_count,
                "blocks": block_count,
                "workflows": workflow_count
            },
            "executions_by_type": [
                {
                    "type": item.agent_type,
                    "count": item.count
                }
                for item in by_type
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage analytics"
        )


@router.get("/errors")
async def get_error_analytics(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get error analytics including most common errors."""
    try:
        user_id = current_user.id
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Failed executions
        failed_executions = db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= start_date,
            AgentExecution.status == "failed"
        ).order_by(
            desc(AgentExecution.started_at)
        ).limit(limit).all()
        
        # Error rate by day
        error_rate_daily = db.query(
            func.date(AgentExecution.started_at).label("date"),
            func.count(AgentExecution.id).label("total"),
            func.sum(
                func.case(
                    (AgentExecution.status == "failed", 1),
                    else_=0
                )
            ).label("failed")
        ).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= start_date
        ).group_by(
            func.date(AgentExecution.started_at)
        ).order_by(
            func.date(AgentExecution.started_at)
        ).all()
        
        return {
            "period_days": days,
            "recent_errors": [
                {
                    "execution_id": str(execution.id),
                    "agent_id": str(execution.agent_id),
                    "started_at": execution.started_at.isoformat(),
                    "error": execution.error_message
                }
                for execution in failed_executions
            ],
            "error_rate_daily": [
                {
                    "date": item.date.isoformat(),
                    "total": item.total,
                    "failed": item.failed or 0,
                    "error_rate": round((item.failed or 0) / item.total * 100, 1) if item.total > 0 else 0
                }
                for item in error_rate_daily
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get error analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get error analytics"
        )
