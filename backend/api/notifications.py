"""
Notifications API

Provides endpoints for managing notifications and settings.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import json

from backend.db.database import get_db
from sqlalchemy.orm import Session
from backend.api.auth import get_current_user
from backend.db.models.user import User
from backend.services.notification_service import get_notification_service
from backend.core.enhanced_error_handler import handle_error, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class NotificationSettingsUpdate(BaseModel):
    emailNotifications: Optional[bool] = Field(None, alias="email_notifications")
    pushNotifications: Optional[bool] = Field(None, alias="push_notifications")
    notifyOnShare: Optional[bool] = Field(None, alias="notify_on_share")
    notifyOnComment: Optional[bool] = Field(None, alias="notify_on_comment")
    notifyOnMention: Optional[bool] = Field(None, alias="notify_on_mention")
    notifyOnSystemUpdate: Optional[bool] = Field(None, alias="notify_on_system_update")
    quietHoursEnabled: Optional[bool] = Field(None, alias="quiet_hours_enabled")
    quietHoursStart: Optional[str] = Field(None, alias="quiet_hours_start")
    quietHoursEnd: Optional[str] = Field(None, alias="quiet_hours_end")
    
    class Config:
        populate_by_name = True


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_notification(self, notification: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(notification)
            except:
                pass


manager = ConnectionManager()


@router.get("")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notifications with pagination."""
    try:
        notification_service = get_notification_service(db)
        
        # Get notifications
        notifications = await notification_service.get_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        # Get unread count
        unread_count = await notification_service.get_unread_count(user_id=current_user.id)
        
        # Format response
        notification_list = [
            {
                "id": str(n.id),
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "actionUrl": n.action_url,
                "actionLabel": n.action_label,
                "isRead": n.is_read,
                "timestamp": n.created_at.isoformat(),
                "readAt": n.read_at.isoformat() if n.read_at else None,
                "metadata": n.metadata,
            }
            for n in notifications
        ]
        
        return {
            "notifications": notification_list,
            "total": len(notification_list),
            "unread_count": unread_count,
            "has_more": len(notification_list) == limit,
        }

    except DatabaseError as e:
        app_error = handle_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=app_error.message
        )
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to get notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read."""
    try:
        notification_service = get_notification_service(db)
        
        updated_notification = await notification_service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if not updated_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Broadcast update to WebSocket clients
        await broadcast_notification({
            "type": "notification_read",
            "notificationId": str(notification_id),
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "success": True,
            "notificationId": str(notification_id),
            "markedAt": updated_notification.read_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to mark notification as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.patch("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    try:
        notification_service = get_notification_service(db)
        
        count = await notification_service.mark_all_as_read(user_id=current_user.id)
        
        # Broadcast update to WebSocket clients
        await broadcast_notification({
            "type": "all_notifications_read",
            "userId": str(current_user.id),
            "timestamp": datetime.utcnow().isoformat(),
        })

        return {
            "success": True,
            "message": f"Marked {count} notifications as read",
            "count": count,
            "markedAt": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to mark all notifications as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    try:
        notification_service = get_notification_service(db)
        
        deleted = await notification_service.delete_notification(
            notification_id=notification_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return None

    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to delete notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.get("/settings")
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notification settings."""
    try:
        notification_service = get_notification_service(db)
        
        settings = await notification_service.get_settings(user_id=current_user.id)
        
        return {
            "settings": {
                "emailNotifications": settings.email_notifications,
                "pushNotifications": settings.push_notifications,
                "notifyOnShare": settings.notify_on_share,
                "notifyOnComment": settings.notify_on_comment,
                "notifyOnMention": settings.notify_on_mention,
                "notifyOnSystemUpdate": settings.notify_on_system_update,
                "quietHoursEnabled": settings.quiet_hours_enabled,
                "quietHoursStart": settings.quiet_hours_start,
                "quietHoursEnd": settings.quiet_hours_end,
            }
        }

    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to get notification settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification settings"
        )


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's notification settings."""
    try:
        notification_service = get_notification_service(db)
        
        # Build update dict
        update_data = {}
        if settings.emailNotifications is not None:
            update_data["email_notifications"] = settings.emailNotifications
        if settings.pushNotifications is not None:
            update_data["push_notifications"] = settings.pushNotifications
        if settings.notifyOnShare is not None:
            update_data["notify_on_share"] = settings.notifyOnShare
        if settings.notifyOnComment is not None:
            update_data["notify_on_comment"] = settings.notifyOnComment
        if settings.notifyOnMention is not None:
            update_data["notify_on_mention"] = settings.notifyOnMention
        if settings.notifyOnSystemUpdate is not None:
            update_data["notify_on_system_update"] = settings.notifyOnSystemUpdate
        if settings.quietHoursEnabled is not None:
            update_data["quiet_hours_enabled"] = settings.quietHoursEnabled
        if settings.quietHoursStart is not None:
            update_data["quiet_hours_start"] = settings.quietHoursStart
        if settings.quietHoursEnd is not None:
            update_data["quiet_hours_end"] = settings.quietHoursEnd
        
        updated_settings = await notification_service.update_settings(
            user_id=current_user.id,
            **update_data
        )
        
        return {
            "success": True,
            "message": "Notification settings updated",
            "settings": {
                "emailNotifications": updated_settings.email_notifications,
                "pushNotifications": updated_settings.push_notifications,
                "notifyOnShare": updated_settings.notify_on_share,
                "notifyOnComment": updated_settings.notify_on_comment,
                "notifyOnMention": updated_settings.notify_on_mention,
                "notifyOnSystemUpdate": updated_settings.notify_on_system_update,
                "quietHoursEnabled": updated_settings.quiet_hours_enabled,
                "quietHoursStart": updated_settings.quiet_hours_start,
                "quietHoursEnd": updated_settings.quiet_hours_end,
            },
        }

    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to update notification settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Helper function to send notification to all connected clients
async def broadcast_notification(notification: dict):
    """Broadcast notification to all connected WebSocket clients."""
    await manager.send_notification(notification)
