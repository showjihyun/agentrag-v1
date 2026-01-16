"""Enhanced webhook management API."""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from backend.db.database import get_db
from backend.services.triggers.webhook_handler import WebhookHandler
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User


router = APIRouter(prefix="/api/v1/webhooks", tags=["webhook-management"])


# Pydantic Models
class WebhookCreate(BaseModel):
    """Create webhook request."""
    agent_id: str
    name: str
    auth_type: str = Field("bearer", description="Authentication type: bearer, hmac, none")
    allowed_methods: List[str] = Field(default=["POST"], description="Allowed HTTP methods")
    is_active: bool = True


class WebhookUpdate(BaseModel):
    """Update webhook request."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    allowed_methods: Optional[List[str]] = None


class WebhookResponse(BaseModel):
    """Webhook response."""
    id: str
    url: str
    name: str
    agent_id: str
    auth_type: str
    allowed_methods: List[str]
    is_active: bool
    trigger_count: int
    created_at: str
    last_triggered_at: Optional[str]


class WebhookWithSecret(WebhookResponse):
    """Webhook response with secret (only on creation)."""
    secret: str


class WebhookTestRequest(BaseModel):
    """Test webhook request."""
    payload: dict = Field(default={}, description="Test payload")
    headers: dict = Field(default={}, description="Additional headers")


# Webhook Management Endpoints
@router.post("", response_model=WebhookWithSecret, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new webhook."""
    handler = WebhookHandler(db)
    
    try:
        webhook = await handler.create_webhook(
            agent_id=webhook_data.agent_id,
            user_id=str(current_user.id),
            name=webhook_data.name,
            auth_type=webhook_data.auth_type,
            allowed_methods=webhook_data.allowed_methods,
            is_active=webhook_data.is_active,
        )
        
        return {
            **webhook,
            "trigger_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "last_triggered_at": None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    agent_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all webhooks for current user."""
    handler = WebhookHandler(db)
    
    webhooks = handler.list_webhooks(
        user_id=str(current_user.id),
        agent_id=agent_id,
        is_active=is_active,
    )
    
    return [
        {
            "id": w.id,
            "url": f"/webhooks/{w.id}",
            "name": w.name,
            "agent_id": str(w.agent_id),
            "auth_type": w.auth_type,
            "allowed_methods": w.allowed_methods,
            "is_active": w.is_active,
            "trigger_count": w.trigger_count or 0,
            "created_at": w.created_at.isoformat(),
            "last_triggered_at": w.last_triggered_at.isoformat() if w.last_triggered_at else None,
        }
        for w in webhooks
    ]


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get webhook details."""
    from backend.db.models.agent_builder import WebhookTrigger
    
    webhook = db.query(WebhookTrigger).filter(
        WebhookTrigger.id == webhook_id,
        WebhookTrigger.user_id == str(current_user.id),
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {
        "id": webhook.id,
        "url": f"/webhooks/{webhook.id}",
        "name": webhook.name,
        "agent_id": str(webhook.agent_id),
        "auth_type": webhook.auth_type,
        "allowed_methods": webhook.allowed_methods,
        "is_active": webhook.is_active,
        "trigger_count": webhook.trigger_count or 0,
        "created_at": webhook.created_at.isoformat(),
        "last_triggered_at": webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
    }


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update webhook."""
    from backend.db.models.agent_builder import WebhookTrigger
    
    webhook = db.query(WebhookTrigger).filter(
        WebhookTrigger.id == webhook_id,
        WebhookTrigger.user_id == str(current_user.id),
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    if webhook_data.name is not None:
        webhook.name = webhook_data.name
    if webhook_data.is_active is not None:
        webhook.is_active = webhook_data.is_active
    if webhook_data.allowed_methods is not None:
        webhook.allowed_methods = webhook_data.allowed_methods
    
    db.commit()
    db.refresh(webhook)
    
    return {
        "id": webhook.id,
        "url": f"/webhooks/{webhook.id}",
        "name": webhook.name,
        "agent_id": str(webhook.agent_id),
        "auth_type": webhook.auth_type,
        "allowed_methods": webhook.allowed_methods,
        "is_active": webhook.is_active,
        "trigger_count": webhook.trigger_count or 0,
        "created_at": webhook.created_at.isoformat(),
        "last_triggered_at": webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
    }


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete webhook."""
    handler = WebhookHandler(db)
    
    # Verify ownership
    from backend.db.models.agent_builder import WebhookTrigger
    webhook = db.query(WebhookTrigger).filter(
        WebhookTrigger.id == webhook_id,
        WebhookTrigger.user_id == str(current_user.id),
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    success = await handler.delete_webhook(webhook_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete webhook")


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    test_data: WebhookTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test webhook with sample payload."""
    from backend.db.models.agent_builder import WebhookTrigger
    
    webhook = db.query(WebhookTrigger).filter(
        WebhookTrigger.id == webhook_id,
        WebhookTrigger.user_id == str(current_user.id),
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    handler = WebhookHandler(db)
    
    # Add authentication header
    headers = test_data.headers.copy()
    if webhook.auth_type == "bearer":
        headers["authorization"] = f"Bearer {webhook.secret}"
    elif webhook.auth_type == "hmac":
        import hmac
        import hashlib
        import json
        
        body_str = json.dumps(test_data.payload, sort_keys=True)
        signature = hmac.new(
            webhook.secret.encode(),
            body_str.encode(),
            hashlib.sha256
        ).hexdigest()
        headers["x-webhook-signature"] = signature
    
    # Execute webhook
    result = await handler.handle_webhook(
        webhook_id=webhook_id,
        method="POST",
        headers=headers,
        body=test_data.payload,
    )
    
    return result


@router.post("/{webhook_id}/regenerate-secret")
async def regenerate_webhook_secret(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate webhook secret."""
    import secrets
    from backend.db.models.agent_builder import WebhookTrigger
    
    webhook = db.query(WebhookTrigger).filter(
        WebhookTrigger.id == webhook_id,
        WebhookTrigger.user_id == str(current_user.id),
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Generate new secret
    new_secret = secrets.token_urlsafe(32)
    webhook.secret = new_secret
    
    db.commit()
    
    return {
        "webhook_id": webhook_id,
        "secret": new_secret,
        "message": "Secret regenerated successfully",
    }
