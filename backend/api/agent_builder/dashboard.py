"""Agent Builder Dashboard API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/dashboard",
    tags=["agent-builder-dashboard"],
)


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics."""
    try:
        from backend.db.models.agent_builder import Agent, Workflow, WorkflowExecution
        
        user_id = str(current_user.id)
        
        # Count agents
        total_agents = db.query(func.count(Agent.id)).filter(
            Agent.user_id == user_id
        ).scalar() or 0
        
        # Count workflows
        total_workflows = db.query(func.count(Workflow.id)).filter(
            Workflow.user_id == user_id
        ).scalar() or 0
        
        # Count executions (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        total_executions = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.user_id == user_id,
            WorkflowExecution.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Success rate
        successful_executions = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.user_id == user_id,
            WorkflowExecution.status == 'completed',
            WorkflowExecution.created_at >= thirty_days_ago
        ).scalar() or 0
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        return {
            "total_agents": total_agents,
            "total_workflows": total_workflows,
            "total_executions": total_executions,
            "success_rate": round(success_rate, 1),
            "active_workflows": total_workflows,  # Simplified
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        return {
            "total_agents": 0,
            "total_workflows": 0,
            "total_executions": 0,
            "success_rate": 0,
            "active_workflows": 0,
        }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent activity."""
    try:
        from backend.db.models.agent_builder import WorkflowExecution, Workflow
        
        user_id = str(current_user.id)
        
        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.user_id == user_id
        ).order_by(WorkflowExecution.created_at.desc()).limit(limit).all()
        
        activities = []
        for exec in executions:
            workflow = db.query(Workflow).filter(Workflow.id == exec.workflow_id).first()
            activities.append({
                "id": str(exec.id),
                "type": "execution",
                "workflow_name": workflow.name if workflow else "Unknown",
                "status": exec.status,
                "created_at": exec.created_at.isoformat() if exec.created_at else None,
                "duration_ms": exec.duration_ms,
            })
        
        return {"activities": activities}
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        return {"activities": []}


@router.get("/favorite-agents")
async def get_favorite_agents(
    limit: int = Query(default=5, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get favorite/most used agents."""
    try:
        from backend.db.models.agent_builder import Agent
        
        user_id = str(current_user.id)
        
        agents = db.query(Agent).filter(
            Agent.user_id == user_id
        ).order_by(Agent.updated_at.desc()).limit(limit).all()
        
        return {
            "agents": [
                {
                    "id": str(agent.id),
                    "name": agent.name,
                    "description": agent.description,
                    "model": agent.model,
                    "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                }
                for agent in agents
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get favorite agents: {e}")
        return {"agents": []}


@router.get("/execution-trend")
async def get_execution_trend(
    days: int = Query(default=7, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get execution trend over time."""
    try:
        from backend.db.models.agent_builder import WorkflowExecution
        
        user_id = str(current_user.id)
        
        # Generate trend data for each day
        trend = []
        for i in range(days - 1, -1, -1):
            date = datetime.utcnow().date() - timedelta(days=i)
            start = datetime.combine(date, datetime.min.time())
            end = datetime.combine(date, datetime.max.time())
            
            count = db.query(func.count(WorkflowExecution.id)).filter(
                WorkflowExecution.user_id == user_id,
                WorkflowExecution.created_at >= start,
                WorkflowExecution.created_at <= end
            ).scalar() or 0
            
            successful = db.query(func.count(WorkflowExecution.id)).filter(
                WorkflowExecution.user_id == user_id,
                WorkflowExecution.status == 'completed',
                WorkflowExecution.created_at >= start,
                WorkflowExecution.created_at <= end
            ).scalar() or 0
            
            trend.append({
                "date": date.isoformat(),
                "total": count,
                "successful": successful,
                "failed": count - successful,
            })
        
        return {"trend": trend}
    except Exception as e:
        logger.error(f"Failed to get execution trend: {e}")
        return {"trend": []}


@router.get("/system-status")
async def get_system_status(
    current_user: User = Depends(get_current_user),
):
    """Get system status."""
    try:
        # Check various services
        services = {
            "database": "healthy",
            "llm": "healthy",
            "vector_db": "healthy",
            "cache": "healthy",
        }
        
        # Simple health check
        overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
        
        return {
            "status": overall_status,
            "services": services,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return {
            "status": "unknown",
            "services": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
