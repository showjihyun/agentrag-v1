"""
Dashboard Service

Provides persistent storage for user dashboard layouts and preferences.
Supports both Redis cache and PostgreSQL database storage.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
import json

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DashboardWidget:
    """Dashboard widget configuration."""
    
    def __init__(
        self,
        id: str,
        type: str,
        title: str,
        x: int,
        y: int,
        width: int,
        height: int,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.type = type
        self.title = title
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.config = config or {}
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "config": self.config,
        }


class DashboardLayout:
    """User dashboard layout."""
    
    def __init__(
        self,
        user_id: str,
        widgets: List[DashboardWidget],
        theme: str = "default",
        columns: int = 12,
        row_height: int = 100,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.widgets = widgets
        self.theme = theme
        self.columns = columns
        self.row_height = row_height
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "widgets": [w.to_dict() for w in self.widgets],
            "theme": self.theme,
            "columns": self.columns,
            "row_height": self.row_height,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }


# Default dashboard layout
DEFAULT_WIDGETS = [
    DashboardWidget(
        id="widget_1",
        type="workflow_stats",
        title="Workflow Statistics",
        x=0, y=0, width=6, height=2,
    ),
    DashboardWidget(
        id="widget_2",
        type="recent_executions",
        title="Recent Executions",
        x=6, y=0, width=6, height=2,
    ),
    DashboardWidget(
        id="widget_3",
        type="system_health",
        title="System Health",
        x=0, y=2, width=4, height=2,
    ),
    DashboardWidget(
        id="widget_4",
        type="quick_actions",
        title="Quick Actions",
        x=4, y=2, width=4, height=2,
    ),
    DashboardWidget(
        id="widget_5",
        type="notifications",
        title="Notifications",
        x=8, y=2, width=4, height=2,
    ),
]


class DashboardService:
    """
    Service for managing user dashboard layouts.
    Supports Redis caching with PostgreSQL persistence.
    """
    
    def __init__(self, db: Optional[Session] = None, redis_client=None):
        self.db = db
        self.redis = redis_client
        self._layouts: Dict[str, DashboardLayout] = {}
    
    def get_layout(self, user_id: str) -> DashboardLayout:
        """Get user's dashboard layout."""
        # Try memory cache first
        if user_id in self._layouts:
            return self._layouts[user_id]
        
        # Try Redis
        if self.redis:
            try:
                data = self.redis.get(f"dashboard:layout:{user_id}")
                if data:
                    layout_dict = json.loads(data)
                    layout = self._dict_to_layout(layout_dict)
                    self._layouts[user_id] = layout
                    return layout
            except Exception as e:
                logger.warning(f"Redis read failed: {e}")
        
        # Return default layout
        return DashboardLayout(
            user_id=user_id,
            widgets=DEFAULT_WIDGETS.copy(),
        )
    
    def save_layout(self, user_id: str, layout: DashboardLayout) -> bool:
        """Save user's dashboard layout to DB and cache."""
        layout.updated_at = datetime.utcnow()
        
        # Save to memory cache
        self._layouts[user_id] = layout
        
        # Save to Redis cache
        if self.redis:
            try:
                self.redis.set(
                    f"dashboard:layout:{user_id}",
                    json.dumps(layout.to_dict()),
                    ex=86400 * 365  # 1 year
                )
            except Exception as e:
                logger.warning(f"Redis cache save failed: {e}")
        
        # Dashboard models have been removed - skip database persistence
        logger.debug("Dashboard models removed - layout saved to memory/Redis only")
                    db_layout.row_height = layout.row_height
                    db_layout.updated_at = datetime.utcnow()
                    
                    # Delete old widgets and recreate
                    self.db.query(DBWidget).filter(DBWidget.layout_id == db_layout.id).delete()
                else:
                    # Create new layout
                    db_layout = DBLayout(
                        id=str(uuid4()),
                        user_id=user_id,
                        name="Default Dashboard",
                        theme=layout.theme,
                        columns=layout.columns,
                        row_height=layout.row_height,
                    )
                    self.db.add(db_layout)
                    self.db.flush()
                
                # Add widgets
                for widget in layout.widgets:
                    db_widget = DBWidget(
                        id=widget.id,
                        layout_id=db_layout.id,
                        widget_type=widget.type,
                        title=widget.title,
                        x=widget.x,
                        y=widget.y,
                        width=widget.width,
                        height=widget.height,
                        config=widget.config,
                    )
                    self.db.add(db_widget)
                
                self.db.commit()
                logger.info(f"Saved dashboard layout to DB for user {user_id}")
                
            except Exception as e:
                logger.error(f"Database save failed: {e}")
                self.db.rollback()
                return False
        
        logger.info(f"Saved dashboard layout for user {user_id}")
        return True
    
    def reset_layout(self, user_id: str) -> DashboardLayout:
        """Reset user's dashboard to default layout."""
        layout = DashboardLayout(
            user_id=user_id,
            widgets=DEFAULT_WIDGETS.copy(),
        )
        
        # Remove from memory
        if user_id in self._layouts:
            del self._layouts[user_id]
        
        # Remove from Redis
        if self.redis:
            try:
                self.redis.delete(f"dashboard:layout:{user_id}")
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        logger.info(f"Reset dashboard layout for user {user_id}")
        return layout
    
    def add_widget(
        self,
        user_id: str,
        widget_type: str,
        title: str,
        config: Optional[dict] = None,
    ) -> DashboardWidget:
        """Add a widget to user's dashboard."""
        layout = self.get_layout(user_id)
        
        # Find next available position
        max_y = max((w.y + w.height for w in layout.widgets), default=0)
        
        widget = DashboardWidget(
            id=f"widget_{datetime.utcnow().timestamp()}",
            type=widget_type,
            title=title,
            x=0,
            y=max_y,
            width=6,
            height=2,
            config=config,
        )
        
        layout.widgets.append(widget)
        self.save_layout(user_id, layout)
        
        return widget
    
    def remove_widget(self, user_id: str, widget_id: str) -> bool:
        """Remove a widget from user's dashboard."""
        layout = self.get_layout(user_id)
        
        original_count = len(layout.widgets)
        layout.widgets = [w for w in layout.widgets if w.id != widget_id]
        
        if len(layout.widgets) < original_count:
            self.save_layout(user_id, layout)
            return True
        
        return False
    
    def update_widget(
        self,
        user_id: str,
        widget_id: str,
        updates: dict,
    ) -> Optional[DashboardWidget]:
        """Update a widget's configuration."""
        layout = self.get_layout(user_id)
        
        for widget in layout.widgets:
            if widget.id == widget_id:
                if "title" in updates:
                    widget.title = updates["title"]
                if "x" in updates:
                    widget.x = updates["x"]
                if "y" in updates:
                    widget.y = updates["y"]
                if "width" in updates:
                    widget.width = updates["width"]
                if "height" in updates:
                    widget.height = updates["height"]
                if "config" in updates:
                    widget.config.update(updates["config"])
                
                self.save_layout(user_id, layout)
                return widget
        
        return None
    
    def _dict_to_layout(self, data: dict) -> DashboardLayout:
        """Convert dict to DashboardLayout."""
        widgets = [
            DashboardWidget(
                id=w["id"],
                type=w["type"],
                title=w["title"],
                x=w["x"],
                y=w["y"],
                width=w["width"],
                height=w["height"],
                config=w.get("config", {}),
            )
            for w in data.get("widgets", [])
        ]
        
        return DashboardLayout(
            user_id=data["user_id"],
            widgets=widgets,
            theme=data.get("theme", "default"),
            columns=data.get("columns", 12),
            row_height=data.get("row_height", 100),
        )


# Global instance
_dashboard_service: Optional[DashboardService] = None


def get_dashboard_service() -> DashboardService:
    """Get or create dashboard service instance."""
    global _dashboard_service
    if _dashboard_service is None:
        try:
            from backend.core.dependencies import get_redis_client
            redis = get_redis_client()
            _dashboard_service = DashboardService(redis)
        except Exception:
            _dashboard_service = DashboardService()
    return _dashboard_service
