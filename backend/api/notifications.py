"""
Notifications API

Provides endpoints for managing notifications and settings.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from backend.db.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class NotificationSettings(BaseModel):
    emailNotifications: bool = True
    pushNotifications: bool = True
    notifyOnShare: bool = True
    notifyOnComment: bool = True
    notifyOnMention: bool = True
    notifyOnSystemUpdate: bool = False
    quietHoursEnabled: bool = False
    quietHoursStart: str = "22:00"
    quietHoursEnd: str = "08:00"


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
    unread_only: bool = False, limit: int = 50, db: Session = Depends(get_db)
):
    """Get user's notifications."""
    try:
        # TODO: Implement actual database operations
        # For now, return mock data

        notifications = [
            {
                "id": "notif_1",
                "type": "info",
                "title": "Welcome!",
                "message": "Welcome to the notification system",
                "timestamp": datetime.utcnow().isoformat(),
                "isRead": False,
                "actionUrl": None,
                "actionLabel": None,
            },
            {
                "id": "notif_2",
                "type": "success",
                "title": "Document Uploaded",
                "message": "Your document has been successfully uploaded",
                "timestamp": datetime.utcnow().isoformat(),
                "isRead": True,
                "actionUrl": "/documents/doc_123",
                "actionLabel": "View Document",
            },
        ]

        if unread_only:
            notifications = [n for n in notifications if not n["isRead"]]

        return {"notifications": notifications[:limit]}

    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get notifications: {str(e)}"
        )


@router.patch("/{notification_id}/read")
async def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    """Mark notification as read."""
    try:
        # TODO: Implement actual database operations

        return {"success": True, "notificationId": notification_id}

    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to mark notification as read: {str(e)}"
        )


@router.patch("/read-all")
async def mark_all_notifications_read(db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    try:
        # TODO: Implement actual database operations

        return {"success": True, "message": "All notifications marked as read"}

    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark all notifications as read: {str(e)}",
        )


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, db: Session = Depends(get_db)):
    """Delete a notification."""
    try:
        # TODO: Implement actual database operations

        return {"success": True, "message": "Notification deleted"}

    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete notification: {str(e)}"
        )


@router.get("/settings")
async def get_notification_settings(db: Session = Depends(get_db)):
    """Get user's notification settings."""
    try:
        # TODO: Implement actual database operations
        # For now, return default settings

        default_settings = NotificationSettings()

        return {"settings": default_settings.dict()}

    except Exception as e:
        logger.error(f"Failed to get notification settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get notification settings: {str(e)}"
        )


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettings, db: Session = Depends(get_db)
):
    """Update user's notification settings."""
    try:
        # TODO: Implement actual database operations

        return {
            "success": True,
            "message": "Notification settings updated",
            "settings": settings.dict(),
        }

    except Exception as e:
        logger.error(f"Failed to update notification settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update notification settings: {str(e)}"
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
