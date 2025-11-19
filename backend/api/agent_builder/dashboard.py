"""
Agent Builder Dashboard API

Provides statistics and overview for Agent Builder home page.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case, text

from backend.db.database import get_db
from backend.db.query_helpers import get_dashboard_executions_optimized
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.agent_builder import (
    Agent,
    AgentExecution,
    Block,
    Workflow,
    Knowledgebase,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/dashboard",
    tags=["agent-builder-dashboard"],
)


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Agent Builder dashboard statistics."""
    try:
        user_id = str(current_user.id)

        # Count resources
        total_agents = db.query(Agent).filter(
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        ).count()

        total_blocks = db.query(Block).filter(
            Block.user_id == user_id
        ).count()

        total_workflows = db.query(Workflow).filter(
            Workflow.user_id == user_id
        ).count()

        total_knowledgebases = db.query(Knowledgebase).filter(
            Knowledgebase.user_id == user_id
        ).count()

        # Execution statistics
        total_executions = db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id
        ).count()

        # Last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        executions_24h = db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= last_24h
        ).count()

        # Success rate
        successful_executions = db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.status == "completed"
        ).count()

        success_rate = (
            (successful_executions / total_executions * 100)
            if total_executions > 0
            else 0
        )

        # Running executions
        running_executions = db.query(AgentExecution).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.status == "running"
        ).count()

        # Average execution time (in seconds)
        avg_duration_result = db.query(
            func.avg(
                func.extract('epoch', AgentExecution.completed_at - AgentExecution.started_at)
            )
        ).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.status == "completed",
            AgentExecution.completed_at.isnot(None)
        ).scalar()

        avg_duration = round(avg_duration_result, 2) if avg_duration_result else 0

        return {
            "resources": {
                "agents": total_agents,
                "blocks": total_blocks,
                "workflows": total_workflows,
                "knowledgebases": total_knowledgebases,
            },
            "executions": {
                "total": total_executions,
                "last_24h": executions_24h,
                "running": running_executions,
                "success_rate": round(success_rate, 1),
                "avg_duration_seconds": avg_duration,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent activity timeline."""
    try:
        user_id = str(current_user.id)

        # Get recent executions with agent info preloaded (prevents N+1 queries)
        recent_executions = get_dashboard_executions_optimized(db, user_id, limit)

        activities = []
        for execution in recent_executions:
            # Agent is already loaded via joinedload
            activities.append({
                "id": execution.id,
                "type": "execution",
                "agent_name": execution.agent.name if execution.agent else "Unknown",
                "agent_id": execution.agent_id,
                "status": execution.status,
                "started_at": execution.started_at.isoformat(),
                "duration": (
                    (execution.completed_at - execution.started_at).total_seconds()
                    if execution.completed_at
                    else None
                ),
            })

        return {
            "activities": activities,
            "total": len(activities),
        }

    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent activity: {str(e)}"
        )


@router.get("/favorite-agents")
async def get_favorite_agents(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get most frequently used agents."""
    try:
        user_id = str(current_user.id)

        # Get agents with execution count
        agent_stats = db.query(
            Agent.id,
            Agent.name,
            Agent.description,
            Agent.agent_type,
            Agent.updated_at,
            func.count(AgentExecution.id).label("execution_count")
        ).outerjoin(
            AgentExecution,
            Agent.id == AgentExecution.agent_id
        ).filter(
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        ).group_by(
            Agent.id
        ).order_by(
            desc("execution_count")
        ).limit(limit).all()

        favorite_agents = []
        for stat in agent_stats:
            # Get last execution
            last_execution = db.query(AgentExecution).filter(
                AgentExecution.agent_id == stat.id
            ).order_by(desc(AgentExecution.started_at)).first()

            favorite_agents.append({
                "id": stat.id,
                "name": stat.name,
                "description": stat.description,
                "agent_type": stat.agent_type,
                "execution_count": stat.execution_count,
                "last_execution": (
                    last_execution.started_at.isoformat()
                    if last_execution
                    else None
                ),
                "last_status": (
                    last_execution.status
                    if last_execution
                    else None
                ),
            })

        return {
            "agents": favorite_agents,
            "total": len(favorite_agents),
        }

    except Exception as e:
        logger.error(f"Failed to get favorite agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get favorite agents: {str(e)}"
        )


@router.get("/execution-trend")
async def get_execution_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution trend for the last N days."""
    try:
        user_id = str(current_user.id)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get daily execution counts
        daily_stats = db.query(
            func.date(AgentExecution.started_at).label("date"),
            func.count(AgentExecution.id).label("total"),
            func.sum(
                case(
                    (AgentExecution.status == "completed", 1),
                    else_=0
                )
            ).label("successful"),
            func.sum(
                case(
                    (AgentExecution.status == "failed", 1),
                    else_=0
                )
            ).label("failed"),
        ).filter(
            AgentExecution.user_id == user_id,
            AgentExecution.started_at >= start_date
        ).group_by(
            func.date(AgentExecution.started_at)
        ).order_by(
            func.date(AgentExecution.started_at)
        ).all()

        trend_data = []
        for stat in daily_stats:
            trend_data.append({
                "date": stat.date.isoformat(),
                "total": stat.total,
                "successful": stat.successful or 0,
                "failed": stat.failed or 0,
            })

        return {
            "trend": trend_data,
            "period_days": days,
        }

    except Exception as e:
        logger.error(f"Failed to get execution trend: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution trend: {str(e)}"
        )


@router.get("/system-status")
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get system health status."""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"

        # Check for stuck executions (running for more than 1 hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        stuck_executions = db.query(AgentExecution).filter(
            AgentExecution.status == "running",
            AgentExecution.started_at < one_hour_ago
        ).count()

        return {
            "database": db_status,
            "stuck_executions": stuck_executions,
            "status": "healthy" if stuck_executions == 0 else "warning",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get system status: {e}", exc_info=True)
        return {
            "database": "unhealthy",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
