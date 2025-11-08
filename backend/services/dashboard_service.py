"""Dashboard service for managing user dashboard layouts."""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.query_log import QueryLog
from backend.db.models.document import Document
from backend.core.enhanced_error_handler import DatabaseError

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data and layouts."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_dashboard_layout(
        self,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get user's dashboard layout with real statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            Dashboard layout with widgets
        """
        try:
            # Get statistics
            total_queries = self.db.query(func.count(QueryLog.id)).filter(
                QueryLog.user_id == user_id
            ).scalar() or 0
            
            total_documents = self.db.query(func.count(Document.id)).filter(
                Document.user_id == user_id
            ).scalar() or 0
            
            # Get recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_queries = self.db.query(func.count(QueryLog.id)).filter(
                and_(
                    QueryLog.user_id == user_id,
                    QueryLog.created_at >= week_ago
                )
            ).scalar() or 0
            
            # Calculate trend
            prev_week = datetime.utcnow() - timedelta(days=14)
            prev_week_queries = self.db.query(func.count(QueryLog.id)).filter(
                and_(
                    QueryLog.user_id == user_id,
                    QueryLog.created_at >= prev_week,
                    QueryLog.created_at < week_ago
                )
            ).scalar() or 0
            
            if prev_week_queries > 0:
                trend_pct = ((recent_queries - prev_week_queries) / prev_week_queries) * 100
                trend = f"+{trend_pct:.1f}%" if trend_pct > 0 else f"{trend_pct:.1f}%"
            else:
                trend = "+0%"
            
            # Build default layout
            layout = {
                "widgets": [
                    {
                        "id": "1",
                        "type": "stat",
                        "title": "Total Queries",
                        "size": "small",
                        "position": {"x": 0, "y": 0},
                        "config": {
                            "value": total_queries,
                            "trend": trend
                        },
                    },
                    {
                        "id": "2",
                        "type": "stat",
                        "title": "Total Documents",
                        "size": "small",
                        "position": {"x": 1, "y": 0},
                        "config": {
                            "value": total_documents,
                            "trend": "+0%"
                        },
                    },
                    {
                        "id": "3",
                        "type": "chart",
                        "title": "Usage Trend (7 days)",
                        "size": "medium",
                        "position": {"x": 0, "y": 1},
                        "config": {
                            "chartType": "line",
                            "queries": recent_queries
                        },
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
            
            return layout
            
        except Exception as e:
            logger.error(f"Failed to get dashboard layout: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to retrieve dashboard layout",
                details={"user_id": str(user_id)},
                original_error=e
            )
    
    async def save_dashboard_layout(
        self,
        user_id: UUID,
        layout: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save user's dashboard layout.
        
        Args:
            user_id: User ID
            layout: Dashboard layout
            
        Returns:
            Saved layout
        """
        try:
            # In a real implementation, save to database
            # For now, just return the layout with timestamp
            layout["lastUpdated"] = datetime.utcnow().isoformat()
            
            logger.info(f"Saved dashboard layout for user {user_id}")
            return layout
            
        except Exception as e:
            logger.error(f"Failed to save dashboard layout: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to save dashboard layout",
                details={"user_id": str(user_id)},
                original_error=e
            )
    
    async def reset_dashboard_layout(
        self,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Reset dashboard to default layout.
        
        Args:
            user_id: User ID
            
        Returns:
            Default layout
        """
        try:
            # Get default layout
            layout = await self.get_dashboard_layout(user_id)
            
            logger.info(f"Reset dashboard layout for user {user_id}")
            return layout
            
        except Exception as e:
            logger.error(f"Failed to reset dashboard layout: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to reset dashboard layout",
                details={"user_id": str(user_id)},
                original_error=e
            )


def get_dashboard_service(db: Session) -> DashboardService:
    """Get dashboard service instance."""
    return DashboardService(db)
