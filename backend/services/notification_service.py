"""
Notification Service

Provides multi-channel notification capabilities:
- Email notifications
- Slack webhooks
- In-app notifications
- Browser push notifications (via WebSocket)
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import asyncio

import httpx

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SLACK = "slack"
    IN_APP = "in_app"
    BROWSER = "browser"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"


class NotificationType(str, Enum):
    """Types of notifications."""
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    AGENT_ALERT = "agent_alert"
    SYSTEM_UPDATE = "system_update"
    SECURITY_ALERT = "security_alert"
    QUOTA_WARNING = "quota_warning"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationService:
    """
    Multi-channel notification service.
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._in_app_notifications: Dict[str, List[dict]] = {}
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        channels: List[NotificationChannel],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        user_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notification through specified channels.
        
        Returns dict of channel -> success status.
        """
        results = {}
        
        notification = {
            "id": f"notif_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "type": notification_type.value,
            "title": title,
            "message": message,
            "priority": priority.value,
            "data": data or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "read": False,
        }
        
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    results[channel.value] = await self._send_email(
                        user_id, notification, user_settings
                    )
                elif channel == NotificationChannel.SLACK:
                    results[channel.value] = await self._send_slack(
                        notification, user_settings
                    )
                elif channel == NotificationChannel.IN_APP:
                    results[channel.value] = await self._send_in_app(
                        user_id, notification
                    )
                elif channel == NotificationChannel.WEBHOOK:
                    results[channel.value] = await self._send_webhook(
                        notification, user_settings
                    )
                elif channel == NotificationChannel.PAGERDUTY:
                    results[channel.value] = await self._send_pagerduty(
                        notification, user_settings
                    )
                else:
                    results[channel.value] = False
                    
            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {e}")
                results[channel.value] = False
        
        return results
    
    async def _send_email(
        self,
        user_id: str,
        notification: dict,
        user_settings: Optional[dict]
    ) -> bool:
        """Send email notification using EmailService."""
        if not user_settings:
            return False
        
        email_address = user_settings.get("email_address")
        if not email_address:
            logger.warning(f"No email address for user {user_id}")
            return False
        
        try:
            from backend.services.email_service import get_email_service
            
            email_service = get_email_service()
            result = await email_service.send_email(
                to_email=email_address,
                subject=notification['title'],
                html_content=self._format_email_html(notification),
                text_content=notification['message'],
            )
            
            if result.get("success"):
                logger.info(f"Email sent to {email_address}: {notification['title']}")
                return True
            else:
                logger.error(f"Email send failed: {result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False
    
    async def _send_slack(
        self,
        notification: dict,
        user_settings: Optional[dict]
    ) -> bool:
        """Send Slack webhook notification."""
        if not user_settings:
            return False
        
        webhook_url = user_settings.get("slack_webhook_url")
        if not webhook_url:
            return False
        
        try:
            # Format Slack message
            slack_message = {
                "text": notification["title"],
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": notification["title"],
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": notification["message"],
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Type:* {notification['type']} | *Priority:* {notification['priority']}"
                            }
                        ]
                    }
                ]
            }
            
            # Add color based on type
            if notification["type"] in ["workflow_error", "security_alert"]:
                slack_message["attachments"] = [{"color": "#ff0000"}]
            elif notification["type"] == "workflow_complete":
                slack_message["attachments"] = [{"color": "#00ff00"}]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=slack_message,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Slack notification sent: {notification['title']}")
                    return True
                else:
                    logger.error(f"Slack webhook failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False
    
    async def _send_in_app(
        self,
        user_id: str,
        notification: dict
    ) -> bool:
        """Store in-app notification."""
        try:
            if user_id not in self._in_app_notifications:
                self._in_app_notifications[user_id] = []
            
            self._in_app_notifications[user_id].insert(0, notification)
            
            # Keep only last 100 notifications
            self._in_app_notifications[user_id] = self._in_app_notifications[user_id][:100]
            
            # Also store in Redis for persistence
            if self.redis:
                key = f"notifications:{user_id}"
                self.redis.lpush(key, json.dumps(notification))
                self.redis.ltrim(key, 0, 99)
                self.redis.expire(key, 86400 * 30)  # 30 days
            
            logger.info(f"In-app notification stored for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"In-app notification failed: {e}")
            return False
    
    async def _send_webhook(
        self,
        notification: dict,
        user_settings: Optional[dict]
    ) -> bool:
        """Send to custom webhook."""
        if not user_settings:
            return False
        
        webhook_url = user_settings.get("webhook_url")
        if not webhook_url:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=notification,
                    timeout=10.0
                )
                return response.status_code < 400
                
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            return False
    
    async def _send_pagerduty(
        self,
        notification: dict,
        user_settings: Optional[dict]
    ) -> bool:
        """Send alert to PagerDuty."""
        try:
            from backend.services.pagerduty_service import get_pagerduty_service, PagerDutySeverity
            
            # Map notification priority to PagerDuty severity
            severity_map = {
                "urgent": PagerDutySeverity.CRITICAL,
                "high": PagerDutySeverity.ERROR,
                "normal": PagerDutySeverity.WARNING,
                "low": PagerDutySeverity.INFO,
            }
            
            severity = severity_map.get(
                notification.get("priority", "normal"),
                PagerDutySeverity.WARNING
            )
            
            pagerduty = get_pagerduty_service()
            result = await pagerduty.trigger_alert(
                summary=notification["title"],
                severity=severity,
                source="notification_service",
                dedup_key=notification.get("id"),
                custom_details={
                    "message": notification["message"],
                    "type": notification["type"],
                    "user_id": notification.get("user_id"),
                },
            )
            
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"PagerDuty send failed: {e}")
            return False
    
    def get_in_app_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[dict]:
        """Get in-app notifications for user."""
        notifications = self._in_app_notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read")]
        
        return notifications[:limit]
    
    def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read."""
        if user_id not in self._in_app_notifications:
            return False
        
        for notification in self._in_app_notifications[user_id]:
            if notification.get("id") == notification_id:
                notification["read"] = True
                return True
        
        return False
    
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read."""
        if user_id not in self._in_app_notifications:
            return 0
        
        count = 0
        for notification in self._in_app_notifications[user_id]:
            if not notification.get("read"):
                notification["read"] = True
                count += 1
        
        return count
    
    def _format_email_html(self, notification: dict) -> str:
        """Format notification as HTML email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
                .priority-urgent {{ border-left: 4px solid #ef4444; }}
                .priority-high {{ border-left: 4px solid #f59e0b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{notification['title']}</h1>
                </div>
                <div class="content priority-{notification['priority']}">
                    <p>{notification['message']}</p>
                    <p><small>Type: {notification['type']}</small></p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from Agentic RAG System</p>
                </div>
            </div>
        </body>
        </html>
        """


# Global instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create notification service instance."""
    global _notification_service
    if _notification_service is None:
        try:
            from backend.core.dependencies import get_redis_client
            redis = get_redis_client()
            _notification_service = NotificationService(redis)
        except Exception:
            _notification_service = NotificationService(None)
    return _notification_service


async def send_workflow_notification(
    user_id: str,
    workflow_name: str,
    success: bool,
    execution_id: str,
    error_message: Optional[str] = None,
    user_settings: Optional[dict] = None,
):
    """Convenience function for workflow notifications."""
    service = get_notification_service()
    
    if success:
        notification_type = NotificationType.WORKFLOW_COMPLETE
        title = f"Workflow Completed: {workflow_name}"
        message = f"Your workflow '{workflow_name}' has completed successfully."
        priority = NotificationPriority.NORMAL
    else:
        notification_type = NotificationType.WORKFLOW_ERROR
        title = f"Workflow Failed: {workflow_name}"
        message = f"Your workflow '{workflow_name}' has failed. Error: {error_message or 'Unknown error'}"
        priority = NotificationPriority.HIGH
    
    # Determine channels based on user settings
    channels = [NotificationChannel.IN_APP]
    
    if user_settings:
        if success and user_settings.get("email_on_workflow_complete"):
            channels.append(NotificationChannel.EMAIL)
        if not success and user_settings.get("email_on_workflow_error"):
            channels.append(NotificationChannel.EMAIL)
        if success and user_settings.get("slack_on_workflow_complete"):
            channels.append(NotificationChannel.SLACK)
        if not success and user_settings.get("slack_on_workflow_error"):
            channels.append(NotificationChannel.SLACK)
    
    await service.send_notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        channels=channels,
        priority=priority,
        data={"execution_id": execution_id, "workflow_name": workflow_name},
        user_settings=user_settings,
    )
