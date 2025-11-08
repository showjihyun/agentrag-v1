"""Notification service for managing user notifications."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.db.models.notification import Notification, NotificationSettings, NotificationType
from backend.models.enums import NotificationType as NotificationTypeEnum
from backend.core.context_managers import db_transaction, timer
from backend.core.enhanced_error_handler import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_notification(
        self,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            user_id: User ID
            type: Notification type
            title: Notification title
            message: Notification message
            action_url: Optional action URL
            action_label: Optional action label
            metadata: Optional metadata
            
        Returns:
            Created notification
        """
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                action_url=action_url,
                action_label=action_label,
                extra_data=metadata or {}
            )
            
            async with db_transaction(self.db):
                self.db.add(notification)
                self.db.flush()
                self.db.refresh(notification)
                
                logger.info(
                    "Notification created",
                    extra={
                        "notification_id": str(notification.id),
                        "user_id": str(user_id),
                        "type": type.value
                    }
                )
                return notification
        
        except IntegrityError as e:
            logger.warning(
                "Invalid notification reference",
                extra={"user_id": str(user_id)}
            )
            raise ValidationError(
                message="Invalid user reference",
                details={"user_id": str(user_id)}
            )
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "create_notification"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to create notification",
                extra={
                    "user_id": str(user_id),
                    "type": type.value,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to create notification",
                details={"user_id": str(user_id), "type": type.value},
                original_error=e
            )
    
    async def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get user's notifications with performance optimization.
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of notifications
        """
        with timer("get_notifications", logger):
            try:
                # Use joinedload to prevent N+1 queries
                query = (
                    self.db.query(Notification)
                    .options(joinedload(Notification.user))
                    .filter(Notification.user_id == user_id)
                )
                
                if unread_only:
                    query = query.filter(Notification.is_read == False)
                
                # Order by created_at descending
                query = query.order_by(desc(Notification.created_at))
                
                # Apply pagination
                notifications = query.limit(limit).offset(offset).all()
                
                logger.debug(f"Retrieved {len(notifications)} notifications for user {user_id}")
                return notifications
                
            except Exception as e:
                logger.error(f"Failed to get notifications: {e}", exc_info=True)
                raise DatabaseError(
                    message="Failed to retrieve notifications",
                    details={"user_id": str(user_id)},
                    original_error=e
                )
    
    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> Optional[Notification]:
        """
        Mark notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)
            
        Returns:
            Updated notification or None
        """
        try:
            notification = self.db.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                return None
            
            async with db_transaction(self.db):
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                
                self.db.flush()
                self.db.refresh(notification)
                
                logger.info(
                    "Notification marked as read",
                    extra={
                        "notification_id": str(notification_id),
                        "user_id": str(user_id)
                    }
                )
                return notification
        
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "mark_as_read"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to mark notification as read",
                extra={
                    "notification_id": str(notification_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to mark notification as read",
                details={"notification_id": str(notification_id)},
                original_error=e
            )
    
    async def mark_all_as_read(
        self,
        user_id: UUID
    ) -> int:
        """
        Mark all notifications as read for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        try:
            count = self.db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).update({
                "is_read": True,
                "read_at": datetime.utcnow()
            })
            
            async with db_transaction(self.db):
                pass  # Update already executed, just commit
            
            logger.info(
                "All notifications marked as read",
                extra={
                    "user_id": str(user_id),
                    "count": count
                }
            )
            return count
        
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "mark_all_as_read"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to mark all notifications as read",
                extra={
                    "user_id": str(user_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to mark all notifications as read",
                details={"user_id": str(user_id)},
                original_error=e
            )
    
    async def delete_notification(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        try:
            notification = self.db.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                return False
            
            async with db_transaction(self.db):
                self.db.delete(notification)
                
                logger.info(
                    "Notification deleted",
                    extra={
                        "notification_id": str(notification_id),
                        "user_id": str(user_id)
                    }
                )
                return True
        
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "delete_notification"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to delete notification",
                extra={
                    "notification_id": str(notification_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to delete notification",
                details={"notification_id": str(notification_id)},
                original_error=e
            )
    
    async def get_unread_count(
        self,
        user_id: UUID
    ) -> int:
        """
        Get count of unread notifications.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of unread notifications
        """
        try:
            count = self.db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to get unread count",
                details={"user_id": str(user_id)},
                original_error=e
            )
    
    async def cleanup_old_notifications(
        self,
        days: int = 30
    ) -> int:
        """
        Delete old read notifications.
        
        Args:
            days: Delete notifications older than this many days
            
        Returns:
            Number of notifications deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            count = self.db.query(Notification).filter(
                and_(
                    Notification.is_read == True,
                    Notification.created_at < cutoff_date
                )
            ).delete()
            
            async with db_transaction(self.db):
                pass  # Delete already executed, just commit
            
            logger.info(
                "Old notifications cleaned up",
                extra={
                    "count": count,
                    "days": days
                }
            )
            return count
        
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "cleanup_notifications"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to cleanup old notifications",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to cleanup old notifications",
                original_error=e
            )
    
    # Notification Settings
    
    async def get_settings(
        self,
        user_id: UUID
    ) -> NotificationSettings:
        """
        Get user's notification settings.
        
        Args:
            user_id: User ID
            
        Returns:
            Notification settings
        """
        try:
            settings = self.db.query(NotificationSettings).filter(
                NotificationSettings.user_id == user_id
            ).first()
            
            # Create default settings if not exists
            if not settings:
                async with db_transaction(self.db):
                    settings = NotificationSettings(user_id=user_id)
                    self.db.add(settings)
                    self.db.flush()
                    self.db.refresh(settings)
            
            return settings
            
        except Exception as e:
            logger.error(f"Failed to get notification settings: {e}", exc_info=True)
            raise DatabaseError(
                message="Failed to get notification settings",
                details={"user_id": str(user_id)},
                original_error=e
            )
    
    async def update_settings(
        self,
        user_id: UUID,
        **kwargs
    ) -> NotificationSettings:
        """
        Update user's notification settings.
        
        Args:
            user_id: User ID
            **kwargs: Settings to update
            
        Returns:
            Updated settings
        """
        try:
            settings = await self.get_settings(user_id)
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            async with db_transaction(self.db):
                settings.updated_at = datetime.utcnow()
                
                self.db.flush()
                self.db.refresh(settings)
                
                logger.info(
                    "Notification settings updated",
                    extra={
                        "user_id": str(user_id),
                        "updated_fields": list(kwargs.keys())
                    }
                )
                return settings
        
        except OperationalError as e:
            logger.error(
                "Database connection error",
                extra={"error": str(e)},
                exc_info=True
            )
            raise DatabaseError(
                message="Database unavailable",
                details={"operation": "update_settings"},
                original_error=e
            )
        except Exception as e:
            logger.error(
                "Failed to update notification settings",
                extra={
                    "user_id": str(user_id),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to update notification settings",
                details={"user_id": str(user_id)},
                original_error=e
            )


def get_notification_service(db: Session) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)
