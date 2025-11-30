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
from backend.db.models.user import User
from backend.core.auth_dependencies import get_current_user
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


@router.put("/layout")
async def save_dashboard_layout(
    layout: DashboardLayout,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user's dashboard layout to database."""
    try:
        from backend.services.dashboard_service import get_dashboard_service, DashboardLayout as ServiceLayout, DashboardWidget as ServiceWidget
        
        # Validate layout
        if not layout.widgets:
            raise HTTPException(status_code=400, detail="Layout must contain at least one widget")
        
        service = get_dashboard_service()
        user_id = str(current_user.id)
        
        # Convert to service model
        widgets = [
            ServiceWidget(
                id=w.id,
                type=w.type,
                title=w.title,
                x=w.position.get("x", 0),
                y=w.position.get("y", 0),
                width=w.size == "large" and 12 or (w.size == "medium" and 6 or 4),
                height=2,
                config=w.config,
            )
            for w in layout.widgets
        ]
        
        service_layout = ServiceLayout(user_id=user_id, widgets=widgets)
        success = service.save_layout(user_id, service_layout)
        
        logger.info(f"Dashboard layout saved with {len(layout.widgets)} widgets")

        return {
            "success": success,
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


@router.post("/layout")
async def save_dashboard_layout_post(
    layout: DashboardLayout,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user's dashboard layout (POST method for compatibility)."""
    return await save_dashboard_layout(layout, current_user, db)


@router.delete("/layout")
async def reset_dashboard_layout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset dashboard to default layout."""
    try:
        from backend.services.dashboard_service import get_dashboard_service
        
        logger.info(f"Resetting dashboard to default layout for user {current_user.id}")
        
        service = get_dashboard_service()
        user_id = str(current_user.id)
        service.reset_layout(user_id)
        
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


# ============================================================================
# Widget Management Endpoints
# ============================================================================

class AddWidgetRequest(BaseModel):
    type: str
    title: str
    config: Optional[dict] = None


class UpdateWidgetRequest(BaseModel):
    title: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    config: Optional[dict] = None


@router.post("/layout/reset")
async def reset_layout_post(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset dashboard to default layout (POST method)."""
    return await reset_dashboard_layout(current_user, db)


@router.post("/widgets")
async def add_widget(
    request: AddWidgetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new widget to the dashboard."""
    try:
        from backend.services.dashboard_service import get_dashboard_service
        
        service = get_dashboard_service()
        user_id = str(current_user.id)
        
        widget = service.add_widget(
            user_id=user_id,
            widget_type=request.type,
            title=request.title,
            config=request.config,
        )
        
        return widget.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to add widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/widgets/{widget_id}")
async def update_widget(
    widget_id: str,
    request: UpdateWidgetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a widget's configuration."""
    try:
        from backend.services.dashboard_service import get_dashboard_service
        
        service = get_dashboard_service()
        user_id = str(current_user.id)
        
        updates = request.model_dump(exclude_none=True)
        widget = service.update_widget(user_id, widget_id, updates)
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return widget.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/widgets/{widget_id}")
async def remove_widget(
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a widget from the dashboard."""
    try:
        from backend.services.dashboard_service import get_dashboard_service
        
        service = get_dashboard_service()
        user_id = str(current_user.id)
        
        success = service.remove_widget(user_id, widget_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))
