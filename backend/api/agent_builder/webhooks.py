"""Webhook API endpoints for workflow triggers."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional

from backend.db.database import get_db
from backend.db.models.agent_builder import WorkflowWebhook
from backend.core.triggers.manager import TriggerManager
from backend.core.triggers.webhook import WebhookTrigger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/{webhook_path}")
@router.get("/{webhook_path}")
@router.put("/{webhook_path}")
@router.patch("/{webhook_path}")
@router.delete("/{webhook_path}")
async def handle_webhook(
    webhook_path: str,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle incoming webhook requests.
    
    This endpoint receives webhook requests and triggers workflow execution.
    
    Args:
        webhook_path: Unique webhook path
        request: FastAPI request object
        x_webhook_signature: Webhook signature for verification
        db: Database session
        
    Returns:
        Execution result
    """
    logger.info(
        f"Received webhook request: path={webhook_path}, "
        f"method={request.method}"
    )
    
    try:
        # Find webhook by path
        webhook = db.query(WorkflowWebhook).filter(
            WorkflowWebhook.webhook_path == webhook_path,
            WorkflowWebhook.is_active == True
        ).first()
        
        if not webhook:
            logger.warning(f"Webhook not found or inactive: {webhook_path}")
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Verify HTTP method
        if webhook.http_method != request.method:
            logger.warning(
                f"Invalid HTTP method: expected={webhook.http_method}, "
                f"got={request.method}"
            )
            raise HTTPException(
                status_code=405,
                detail=f"Method not allowed. Expected {webhook.http_method}"
            )
        
        # Read request body
        body = await request.body()
        content_type = request.headers.get("content-type", "")
        
        # Create webhook trigger instance
        webhook_trigger = WebhookTrigger(
            workflow_id=str(webhook.workflow_id),
            config={
                "webhook_id": str(webhook.id),
                "webhook_path": webhook.webhook_path,
                "webhook_secret": webhook.webhook_secret,
                "http_method": webhook.http_method,
                "is_active": webhook.is_active,
            },
            db_session=db
        )
        
        # Verify signature if provided
        if x_webhook_signature:
            if not webhook_trigger.verify_signature(body, x_webhook_signature):
                logger.warning(f"Invalid webhook signature: {webhook_path}")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse payload
        payload = webhook_trigger.parse_payload(body, content_type)
        
        # Add request metadata
        trigger_data = {
            "payload": payload,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "method": request.method,
            "path": webhook_path,
        }
        
        # Execute workflow
        trigger_manager = TriggerManager(db)
        
        # Get workflow owner (user_id) from webhook
        workflow = webhook.workflow
        user_id = str(workflow.user_id)
        
        result = await trigger_manager.execute_trigger(
            workflow_id=str(webhook.workflow_id),
            trigger_type="webhook",
            trigger_data=trigger_data,
            user_id=user_id
        )
        
        if result.get("success"):
            logger.info(
                f"Webhook executed successfully: path={webhook_path}, "
                f"execution_id={result.get('execution_id')}"
            )
            return {
                "success": True,
                "execution_id": result.get("execution_id"),
                "status": result.get("status"),
                "message": "Workflow execution started"
            }
        else:
            logger.error(
                f"Webhook execution failed: path={webhook_path}, "
                f"error={result.get('error')}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Workflow execution failed: {result.get('error')}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Webhook handler error: path={webhook_path}, error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
