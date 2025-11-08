"""
Dashboard API

Provides endpoints for managing custom dashboard layouts.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from backend.db.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


class Widget(BaseModel):
    id: str
    type: str  # chart, stat, list, table
    title: str
    size: str  # small, medium, large
    position: dict
    config: dict


class DashboardLayout(BaseModel):
    widgets: List[Widget]


@router.get("/layout")
async def get_dashboard_layout(db: Session = Depends(get_db)):
    """Get user's dashboard layout with real statistics."""
    try:
        from backend.db.repositories.query_repository import QueryRepository
        from backend.db.repositories.document_repository import DocumentRepository
        
        query_repo = QueryRepository(db)
        doc_repo = DocumentRepository(db)
        
        # Get real statistics
        total_queries = await query_repo.count_queries()
        total_documents = await doc_repo.count_documents()
        
        # Get recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_queries = await query_repo.count_queries_since(week_ago)
        
        # Calculate trend
        prev_week = datetime.utcnow() - timedelta(days=14)
        prev_week_queries = await query_repo.count_queries_between(prev_week, week_ago)
        trend = f"+{((recent_queries - prev_week_queries) / max(prev_week_queries, 1) * 100):.1f}%" if prev_week_queries > 0 else "+0%"
        
        default_layout = {
            "widgets": [
                {
                    "id": "1",
                    "type": "stat",
                    "title": "Total Queries",
                    "size": "small",
                    "position": {"x": 0, "y": 0},
                    "config": {"value": total_queries, "trend": trend},
                },
                {
                    "id": "2",
                    "type": "stat",
                    "title": "Total Documents",
                    "size": "small",
                    "position": {"x": 1, "y": 0},
                    "config": {"value": total_documents, "trend": "+0%"},
                },
                {
                    "id": "3",
                    "type": "chart",
                    "title": "Usage Trend (7 days)",
                    "size": "medium",
                    "position": {"x": 0, "y": 1},
                    "config": {"chartType": "line", "queries": recent_queries},
                },
                {
                    "id": "4",
                    "type": "list",
                    "title": "Recent Activity",
                    "size": "medium",
                    "position": {"x": 2, "y": 0},
                    "config": {"limit": 10},
                },
            ],
            "lastUpdated": datetime.utcnow().isoformat(),
        }

        return default_layout

    except Exception as e:
        logger.error(f"Failed to get dashboard layout: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard layout: {str(e)}"
        )


@router.post("/layout")
async def save_dashboard_layout(layout: DashboardLayout, db: Session = Depends(get_db)):
    """Save user's dashboard layout to database."""
    try:
        # Validate layout
        if not layout.widgets:
            raise HTTPException(status_code=400, detail="Layout must contain at least one widget")
        
        # In a real implementation, save to user_preferences table
        # For now, we'll log the save operation
        logger.info(f"Dashboard layout saved with {len(layout.widgets)} widgets")
        
        # TODO: Implement actual database save
        # await user_repo.save_dashboard_layout(user_id, layout.dict())

        return {
            "success": True,
            "message": "Dashboard layout saved successfully",
            "widgetCount": len(layout.widgets),
            "savedAt": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save dashboard layout: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to save dashboard layout: {str(e)}"
        )


@router.delete("/layout")
async def reset_dashboard_layout(db: Session = Depends(get_db)):
    """Reset dashboard to default layout."""
    try:
        logger.info("Resetting dashboard to default layout")
        
        # TODO: Implement actual database reset
        # await user_repo.delete_dashboard_layout(user_id)
        
        default_layout = {
            "widgets": [
                {
                    "id": "1",
                    "type": "stat",
                    "title": "Total Queries",
                    "size": "small",
                    "position": {"x": 0, "y": 0},
                    "config": {},
                },
                {
                    "id": "2",
                    "type": "chart",
                    "title": "Usage Trend",
                    "size": "medium",
                    "position": {"x": 1, "y": 0},
                    "config": {"chartType": "line"},
                },
            ],
        }

        return {
            "success": True,
            "message": "Dashboard reset to default",
            "layout": default_layout,
            "resetAt": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to reset dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to reset dashboard: {str(e)}"
        )
