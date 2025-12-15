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


@router.get("/test")
async def test_endpoint():
    """Test endpoint without authentication."""
    return {"status": "ok", "message": "Dashboard API is working"}


@router.get("/stats")
async def get_dashboard_stats(
    # current_user: User = Depends(get_current_user),  # Temporarily disabled for testing
    # db: Session = Depends(get_db),  # Temporarily disabled for testing
):
    """Get dashboard statistics."""
    # Temporarily return mock data for testing
    return {
        "total_agents": 5,
        "total_workflows": 12,
        "total_executions": 48,
        "success_rate": 92.5,
        "active_workflows": 8,
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(default=10, le=50),
    # current_user: User = Depends(get_current_user),  # Temporarily disabled
    # db: Session = Depends(get_db),  # Temporarily disabled
):
    """Get recent activity."""
    # Return mock data for now
    return {
        "activities": [
            {
                "id": "exec_001",
                "type": "execution",
                "agent_name": "Customer Support Bot",
                "status": "completed",
                "started_at": "2025-12-13T10:30:00Z",
                "duration": 45.2
            },
            {
                "id": "exec_002", 
                "type": "execution",
                "agent_name": "Data Analysis Agent",
                "status": "running",
                "started_at": "2025-12-13T10:25:00Z",
                "duration": None
            },
            {
                "id": "exec_003",
                "type": "execution", 
                "agent_name": "Content Generator",
                "status": "failed",
                "started_at": "2025-12-13T10:20:00Z",
                "duration": 12.8
            }
        ]
    }


@router.get("/favorite-agents")
async def get_favorite_agents(
    limit: int = Query(default=5, le=20),
    # current_user: User = Depends(get_current_user),  # Temporarily disabled
    # db: Session = Depends(get_db),  # Temporarily disabled
):
    """Get favorite/most used agents."""
    # Return mock data for now
    return {
        "agents": [
            {
                "id": "agent_001",
                "name": "Customer Support Assistant",
                "description": "Handles customer inquiries and support tickets",
                "execution_count": 156,
                "last_execution": "2025-12-13T10:30:00Z",
                "last_status": "completed"
            },
            {
                "id": "agent_002",
                "name": "Data Analysis Bot",
                "description": "Analyzes sales data and generates reports",
                "execution_count": 89,
                "last_execution": "2025-12-13T09:45:00Z", 
                "last_status": "completed"
            },
            {
                "id": "agent_003",
                "name": "Content Generator",
                "description": "Creates marketing content and blog posts",
                "execution_count": 67,
                "last_execution": "2025-12-13T08:20:00Z",
                "last_status": "failed"
            }
        ]
    }


@router.get("/execution-trend")
async def get_execution_trend(
    days: int = Query(default=7, le=30),
    # current_user: User = Depends(get_current_user),  # Temporarily disabled
    # db: Session = Depends(get_db),  # Temporarily disabled
):
    """Get execution trend over time."""
    # Generate mock trend data for the last 7 days
    trend = []
    for i in range(days - 1, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        # Generate realistic mock data
        total = max(0, 20 + (i * 3) + (i % 3) * 5)  # Varying daily totals
        successful = int(total * 0.85)  # 85% success rate
        failed = total - successful
        
        trend.append({
            "date": date.isoformat(),
            "total": total,
            "successful": successful,
            "failed": failed,
        })
    
    return {"trend": trend}


@router.get("/system-status")
async def get_system_status(
    # current_user: User = Depends(get_current_user),  # Temporarily disabled
):
    """Get system status."""
    # Return mock system status
    return {
        "status": "healthy",
        "services": {
            "database": "healthy",
            "llm": "healthy", 
            "vector_db": "healthy",
            "cache": "healthy",
            "redis": "healthy",
            "milvus": "healthy"
        },
        "stuck_executions": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
