"""
Notifications API

Provides endpoints for managing user notifications.
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.notification_service import (
    get_notification_service,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ============================================================================
# Models
# ============================================================================

class NotificationResponse(BaseModel):
    """Notification response model."""
    id: str
    type: str
    title: str
    message: str
    priority: str
    data: dict
    created_at: str
    read: bool


class NotificationListResponse(BaseModel):
    """List of notifications response."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    title: str
    message: str
    type: str = "info"
    priority: str = "normal"
    channels: List[str] = ["in_app"]
    data: Optional[dict] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum notifications to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List notifications for the current user.
    """
    service = get_notification_service()
    user_id = str(current_user.id)
    
    notifications = service.get_in_app_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
    )
    
    all_notifications = service.get_in_app_notifications(user_id=user_id, limit=100)
    unread_count = len([n for n in all_notifications if not n.get("read")])
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.get("id", ""),
                type=n.get("type", "info"),
                title=n.get("title", ""),
                message=n.get("message", ""),
                priority=n.get("priority", "normal"),
                data=n.get("data", {}),
                created_at=n.get("created_at", ""),
                read=n.get("read", False),
            )
            for n in notifications
        ],
        total=len(notifications),
        unread_count=unread_count,
    )


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a notification as read.
    """
    service = get_notification_service()
    user_id = str(current_user.id)
    
    success = service.mark_as_read(user_id, notification_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all notifications as read.
    """
    service = get_notification_service()
    user_id = str(current_user.id)
    
    count = service.mark_all_as_read(user_id)
    
    return {"message": f"Marked {count} notifications as read", "count": count}


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a notification (for testing or manual triggers).
    """
    service = get_notification_service()
    user_id = str(current_user.id)
    
    # Map string channels to enum
    channels = []
    for ch in request.channels:
        try:
            channels.append(NotificationChannel(ch))
        except ValueError:
            pass
    
    if not channels:
        channels = [NotificationChannel.IN_APP]
    
    # Map type
    try:
        notification_type = NotificationType(request.type)
    except ValueError:
        notification_type = NotificationType.SYSTEM_UPDATE
    
    # Map priority
    try:
        priority = NotificationPriority(request.priority)
    except ValueError:
        priority = NotificationPriority.NORMAL
    
    results = await service.send_notification(
        user_id=user_id,
        notification_type=notification_type,
        title=request.title,
        message=request.message,
        channels=channels,
        priority=priority,
        data=request.data,
    )
    
    return {
        "message": "Notification sent",
        "results": results,
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get count of unread notifications.
    """
    service = get_notification_service()
    user_id = str(current_user.id)
    
    notifications = service.get_in_app_notifications(user_id=user_id, limit=100)
    unread_count = len([n for n in notifications if not n.get("read")])
    
    return {"unread_count": unread_count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a notification.
    """
    service = get_notification_service()
    user_id = str(current_user.id)
    
    # Get notifications and filter out the one to delete
    notifications = service.get_in_app_notifications(user_id=user_id, limit=100)
    original_count = len(notifications)
    
    # Remove from in-memory storage
    if user_id in service._in_app_notifications:
        service._in_app_notifications[user_id] = [
            n for n in service._in_app_notifications[user_id]
            if n.get("id") != notification_id
        ]
        
        if len(service._in_app_notifications[user_id]) < original_count:
            return {"success": True, "message": "Notification deleted"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification not found"
    )


@router.post("/test")
async def send_test_notification(
    channel: str = "in_app",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a test notification to verify channel configuration.
    """
    service = get_notification_service()
    user_id = str(current_user.id)
    
    try:
        channel_enum = NotificationChannel(channel)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel: {channel}"
        )
    
    results = await service.send_notification(
        user_id=user_id,
        notification_type=NotificationType.SYSTEM_UPDATE,
        title="Test Notification",
        message=f"This is a test notification sent via {channel}.",
        channels=[channel_enum],
        priority=NotificationPriority.NORMAL,
        data={"test": True},
    )
    
    success = results.get(channel, False)
    
    return {
        "success": success,
        "message": f"Test notification {'sent' if success else 'failed'} via {channel}",
        "channel": channel,
    }
