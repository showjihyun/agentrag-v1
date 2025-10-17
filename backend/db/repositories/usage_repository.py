"""Usage repository for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from uuid import UUID

from backend.db.models.usage import UsageLog

logger = logging.getLogger(__name__)


class UsageRepository:
    """Database operations for usage tracking."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def log_usage(
        self,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> UsageLog:
        """Create usage log entry."""
        try:
            usage_log = UsageLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata=metadata or {},
            )

            self.db.add(usage_log)
            self.db.commit()
            self.db.refresh(usage_log)

            return usage_log

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to log usage: {e}")
            raise

    def get_user_usage(self, user_id: UUID, days: int = 30) -> List[UsageLog]:
        """Get user usage logs for specified period."""
        since = datetime.utcnow() - timedelta(days=days)

        return (
            self.db.query(UsageLog)
            .filter(UsageLog.user_id == user_id, UsageLog.created_at >= since)
            .order_by(UsageLog.created_at.desc())
            .all()
        )

    def get_usage_stats(self, user_id: UUID, days: int = 30) -> Dict:
        """Get usage statistics for a user."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total actions
        total = (
            self.db.query(func.count(UsageLog.id))
            .filter(UsageLog.user_id == user_id, UsageLog.created_at >= since)
            .scalar()
            or 0
        )

        # Actions by type
        actions_by_type = {}
        action_counts = (
            self.db.query(UsageLog.action, func.count(UsageLog.id))
            .filter(UsageLog.user_id == user_id, UsageLog.created_at >= since)
            .group_by(UsageLog.action)
            .all()
        )

        for action, count in action_counts:
            actions_by_type[action] = count

        return {
            "total_actions": total,
            "actions_by_type": actions_by_type,
            "period_days": days,
        }

    def get_system_usage_stats(self, days: int = 7) -> Dict:
        """Get system-wide usage statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        total_users = (
            self.db.query(func.count(func.distinct(UsageLog.user_id)))
            .filter(UsageLog.created_at >= since)
            .scalar()
            or 0
        )

        total_actions = (
            self.db.query(func.count(UsageLog.id))
            .filter(UsageLog.created_at >= since)
            .scalar()
            or 0
        )

        return {
            "active_users": total_users,
            "total_actions": total_actions,
            "period_days": days,
        }
