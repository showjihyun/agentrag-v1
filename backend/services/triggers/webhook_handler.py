"""
Webhook Handler for triggering agents/workflows via HTTP webhooks.

Features:
- Unique webhook URL generation
- Webhook authentication (Bearer token, HMAC)
- Request validation
- Agent/Workflow execution
- Webhook logs
"""

import logging
import hmac
import hashlib
import secrets
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# TODO: WebhookTrigger model needs to be created
# from backend.db.models.agent_builder import WebhookTrigger, Agent
from backend.db.models.agent_builder import Agent
from backend.services.agent_builder.agent_executor import AgentExecutor

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Service for handling webhook triggers."""
    
    def __init__(self, db: Session):
        """
        Initialize Webhook Handler.
        
        Args:
            db: Database session
        """
        self.db = db
        self.agent_executor = AgentExecutor(db)
    
    async def create_webhook(
        self,
        agent_id: str,
        user_id: str,
        name: str,
        auth_type: str = "bearer",  # bearer, hmac, none
        allowed_methods: list = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new webhook trigger.
        
        Args:
            agent_id: Agent ID to trigger
            user_id: User ID creating webhook
            name: Webhook name
            auth_type: Authentication type
            allowed_methods: Allowed HTTP methods
            is_active: Whether webhook is active
            
        Returns:
            Webhook details including URL and secret
        """
        try:
            # Validate agent exists
            agent = self.db.query(Agent).filter(
                Agent.id == agent_id,
                Agent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Generate unique webhook ID and secret
            webhook_id = secrets.token_urlsafe(16)
            webhook_secret = secrets.token_urlsafe(32)
            
            # Create webhook trigger
            webhook = WebhookTrigger(
                id=webhook_id,
                agent_id=agent_id,
                user_id=user_id,
                name=name,
                auth_type=auth_type,
                secret=webhook_secret,
                allowed_methods=allowed_methods or ["POST"],
                is_active=is_active,
                created_at=datetime.utcnow()
            )
            
            self.db.add(webhook)
            self.db.commit()
            self.db.refresh(webhook)
            
            logger.info(f"Created webhook: {webhook_id} for agent {agent_id}")
            
            return {
                "id": webhook_id,
                "url": f"/webhooks/{webhook_id}",
                "secret": webhook_secret,
                "auth_type": auth_type,
                "agent_id": agent_id,
                "is_active": is_active
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create webhook: {e}", exc_info=True)
            raise
    
    async def handle_webhook(
        self,
        webhook_id: str,
        method: str,
        headers: Dict[str, str],
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook request.
        
        Args:
            webhook_id: Webhook ID
            method: HTTP method
            headers: Request headers
            body: Request body
            
        Returns:
            Execution result
        """
        try:
            # Get webhook
            webhook = self.db.query(WebhookTrigger).filter(
                WebhookTrigger.id == webhook_id
            ).first()
            
            if not webhook:
                raise ValueError(f"Webhook {webhook_id} not found")
            
            if not webhook.is_active:
                raise ValueError(f"Webhook {webhook_id} is not active")
            
            # Validate method
            if method not in webhook.allowed_methods:
                raise ValueError(f"Method {method} not allowed")
            
            # Authenticate request
            if not self._authenticate_request(webhook, headers, body):
                raise ValueError("Authentication failed")
            
            # Execute agent
            execution = await self.agent_executor.execute_agent(
                agent_id=webhook.agent_id,
                user_id=webhook.user_id,
                input_data=body,
                session_id=f"webhook_{webhook_id}_{datetime.utcnow().timestamp()}",
                variables={
                    "webhook_id": webhook_id,
                    "trigger_type": "webhook"
                }
            )
            
            # Update webhook stats
            webhook.trigger_count = (webhook.trigger_count or 0) + 1
            webhook.last_triggered_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Webhook {webhook_id} triggered execution {execution.id}")
            
            return {
                "success": True,
                "execution_id": str(execution.id),
                "webhook_id": webhook_id,
                "triggered_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "webhook_id": webhook_id
            }
    
    def _authenticate_request(
        self,
        webhook: WebhookTrigger,
        headers: Dict[str, str],
        body: Dict[str, Any]
    ) -> bool:
        """
        Authenticate webhook request.
        
        Args:
            webhook: Webhook trigger model
            headers: Request headers
            body: Request body
            
        Returns:
            True if authenticated, False otherwise
        """
        if webhook.auth_type == "none":
            return True
        
        elif webhook.auth_type == "bearer":
            # Bearer token authentication
            auth_header = headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return False
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            return secrets.compare_digest(token, webhook.secret)
        
        elif webhook.auth_type == "hmac":
            # HMAC signature authentication
            signature_header = headers.get("x-webhook-signature", "")
            if not signature_header:
                return False
            
            # Calculate expected signature
            import json
            body_str = json.dumps(body, sort_keys=True)
            expected_signature = hmac.new(
                webhook.secret.encode(),
                body_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return secrets.compare_digest(signature_header, expected_signature)
        
        return False
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete webhook trigger.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            webhook = self.db.query(WebhookTrigger).filter(
                WebhookTrigger.id == webhook_id
            ).first()
            
            if not webhook:
                return False
            
            self.db.delete(webhook)
            self.db.commit()
            
            logger.info(f"Deleted webhook: {webhook_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete webhook: {e}", exc_info=True)
            raise
    
    def list_webhooks(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> list:
        """
        List webhooks with filters.
        
        Args:
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            is_active: Filter by active status
            
        Returns:
            List of webhooks
        """
        query = self.db.query(WebhookTrigger)
        
        if user_id:
            query = query.filter(WebhookTrigger.user_id == user_id)
        
        if agent_id:
            query = query.filter(WebhookTrigger.agent_id == agent_id)
        
        if is_active is not None:
            query = query.filter(WebhookTrigger.is_active == is_active)
        
        return query.order_by(WebhookTrigger.created_at.desc()).all()
