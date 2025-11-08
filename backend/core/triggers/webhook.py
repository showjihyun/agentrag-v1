"""Webhook trigger for workflow execution."""

import logging
import uuid
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.core.triggers.base import BaseTrigger
from backend.db.models.agent_builder import WorkflowWebhook

logger = logging.getLogger(__name__)


class WebhookTrigger(BaseTrigger):
    """
    Webhook trigger for executing workflows via HTTP requests.
    
    Features:
    - Unique webhook URLs
    - Signature verification
    - Multiple HTTP methods
    - Payload parsing
    - Execution logging
    """
    
    def __init__(
        self,
        workflow_id: str,
        config: Dict[str, Any],
        db_session: Session
    ):
        """
        Initialize webhook trigger.
        
        Args:
            workflow_id: Workflow identifier
            config: Webhook configuration
            db_session: Database session
        """
        super().__init__(workflow_id, config)
        self.db = db_session
        self.webhook_id = config.get("webhook_id")
        self.webhook_path = config.get("webhook_path")
        self.webhook_secret = config.get("webhook_secret")
        self.http_method = config.get("http_method", "POST")
    
    async def register(self) -> Dict[str, Any]:
        """
        Register webhook trigger.
        
        Creates a unique webhook URL and stores configuration in database.
        
        Returns:
            Registration result with webhook details
        """
        logger.info(f"Registering webhook trigger for workflow: {self.workflow_id}")
        
        try:
            # Generate unique webhook path if not provided
            if not self.webhook_path:
                self.webhook_path = self._generate_webhook_path()
            
            # Generate webhook secret if not provided
            if not self.webhook_secret:
                self.webhook_secret = self._generate_webhook_secret()
            
            # Check if webhook already exists
            if self.webhook_id:
                webhook = self.db.query(WorkflowWebhook).filter(
                    WorkflowWebhook.id == self.webhook_id
                ).first()
                
                if webhook:
                    # Update existing webhook
                    webhook.webhook_path = self.webhook_path
                    webhook.webhook_secret = self.webhook_secret
                    webhook.http_method = self.http_method
                    webhook.is_active = self.is_active
                    webhook.updated_at = datetime.utcnow()
                else:
                    # Create new webhook
                    webhook = self._create_webhook()
            else:
                # Create new webhook
                webhook = self._create_webhook()
            
            self.db.commit()
            self.webhook_id = str(webhook.id)
            
            logger.info(
                f"Webhook registered: webhook_id={self.webhook_id}, "
                f"path={self.webhook_path}"
            )
            
            return {
                "trigger_id": self.webhook_id,
                "trigger_type": "webhook",
                "webhook_url": f"/api/webhooks/{self.webhook_path}",
                "webhook_path": self.webhook_path,
                "webhook_secret": self.webhook_secret,
                "http_method": self.http_method,
                "is_active": self.is_active,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to register webhook: workflow_id={self.workflow_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            self.db.rollback()
            raise
    
    async def unregister(self):
        """Unregister webhook trigger."""
        logger.info(f"Unregistering webhook: webhook_id={self.webhook_id}")
        
        try:
            if self.webhook_id:
                webhook = self.db.query(WorkflowWebhook).filter(
                    WorkflowWebhook.id == self.webhook_id
                ).first()
                
                if webhook:
                    webhook.is_active = False
                    webhook.updated_at = datetime.utcnow()
                    self.db.commit()
                    
                    logger.info(f"Webhook unregistered: webhook_id={self.webhook_id}")
        
        except Exception as e:
            logger.error(
                f"Failed to unregister webhook: webhook_id={self.webhook_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            self.db.rollback()
    
    async def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow in response to webhook.
        
        Args:
            trigger_data: Webhook payload
            
        Returns:
            Execution result
        """
        logger.info(
            f"Executing webhook trigger: webhook_id={self.webhook_id}, "
            f"workflow_id={self.workflow_id}"
        )
        
        try:
            # Update webhook statistics
            await self._update_webhook_stats()
            
            # Log trigger execution
            self.log_trigger(
                trigger_type="webhook",
                success=True,
                trigger_data=trigger_data
            )
            
            return {
                "success": True,
                "webhook_id": self.webhook_id,
                "workflow_id": self.workflow_id,
            }
            
        except Exception as e:
            logger.error(
                f"Webhook execution failed: webhook_id={self.webhook_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            
            self.log_trigger(
                trigger_type="webhook",
                success=False,
                trigger_data=trigger_data,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get webhook status.
        
        Returns:
            Status information
        """
        try:
            webhook = self.db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == self.webhook_id
            ).first()
            
            if not webhook:
                return {
                    "active": False,
                    "error": "Webhook not found"
                }
            
            return {
                "active": webhook.is_active,
                "webhook_id": str(webhook.id),
                "webhook_path": webhook.webhook_path,
                "http_method": webhook.http_method,
                "last_triggered_at": webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
                "trigger_count": webhook.trigger_count,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to get webhook status: webhook_id={self.webhook_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            return {
                "active": False,
                "error": str(e)
            }
    
    def verify_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Request payload
            signature: Signature from request header
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            # No secret configured, skip verification
            return True
        
        try:
            # Compute expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(
                f"Signature verification failed: webhook_id={self.webhook_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            return False
    
    def parse_payload(
        self,
        payload: bytes,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Parse webhook payload.
        
        Args:
            payload: Request payload
            content_type: Content type header
            
        Returns:
            Parsed payload as dictionary
        """
        import json
        
        try:
            if "application/json" in content_type:
                return json.loads(payload.decode())
            elif "application/x-www-form-urlencoded" in content_type:
                from urllib.parse import parse_qs
                parsed = parse_qs(payload.decode())
                # Convert lists to single values
                return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
            else:
                # Return raw payload
                return {"payload": payload.decode()}
                
        except Exception as e:
            logger.error(
                f"Failed to parse payload: webhook_id={self.webhook_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            return {"payload": payload.decode()}
    
    def _generate_webhook_path(self) -> str:
        """
        Generate unique webhook path.
        
        Returns:
            Unique webhook path
        """
        return f"wh_{uuid.uuid4().hex[:16]}"
    
    def _generate_webhook_secret(self) -> str:
        """
        Generate webhook secret for signature verification.
        
        Returns:
            Webhook secret
        """
        return uuid.uuid4().hex
    
    def _create_webhook(self) -> WorkflowWebhook:
        """
        Create new webhook in database.
        
        Returns:
            WorkflowWebhook model
        """
        webhook = WorkflowWebhook(
            workflow_id=uuid.UUID(self.workflow_id),
            webhook_path=self.webhook_path,
            webhook_secret=self.webhook_secret,
            http_method=self.http_method,
            is_active=self.is_active,
        )
        
        self.db.add(webhook)
        return webhook
    
    async def _update_webhook_stats(self):
        """Update webhook statistics."""
        try:
            webhook = self.db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == self.webhook_id
            ).first()
            
            if webhook:
                webhook.last_triggered_at = datetime.utcnow()
                webhook.trigger_count += 1
                self.db.commit()
                
        except Exception as e:
            logger.error(
                f"Failed to update webhook stats: webhook_id={self.webhook_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            self.db.rollback()
