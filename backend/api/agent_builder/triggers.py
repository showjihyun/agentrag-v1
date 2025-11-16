"""Triggers API endpoints for workflow trigger management."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.agent_builder import (
    Workflow,
    WorkflowWebhook,
    WorkflowSchedule,
    TriggerExecution,
)
from backend.db.query_helpers import get_workflow_with_relations
from backend.core.triggers.manager import TriggerManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triggers", tags=["triggers"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class TriggerBase(BaseModel):
    """Base trigger schema."""
    name: str = Field(..., description="Trigger name")
    description: Optional[str] = Field(None, description="Trigger description")
    trigger_type: str = Field(..., description="Type of trigger (webhook, schedule, api, chat, manual)")
    is_active: bool = Field(True, description="Whether trigger is active")


class WebhookTriggerConfig(BaseModel):
    """Webhook trigger configuration."""
    http_method: str = Field("POST", description="HTTP method")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret for signature verification")


class ScheduleTriggerConfig(BaseModel):
    """Schedule trigger configuration."""
    cron_expression: str = Field(..., description="Cron expression")
    timezone: str = Field("UTC", description="Timezone")
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Default input data")


class TriggerCreate(TriggerBase):
    """Create trigger request."""
    workflow_id: str = Field(..., description="Workflow ID")
    config: Dict[str, Any] = Field(default_factory=dict, description="Trigger configuration")


class TriggerUpdate(BaseModel):
    """Update trigger request."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class TriggerResponse(BaseModel):
    """Trigger response."""
    id: str
    workflow_id: str
    workflow_name: str
    name: str
    description: Optional[str]
    trigger_type: str
    is_active: bool
    config: Dict[str, Any]
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TriggerExecutionResponse(BaseModel):
    """Trigger execution response."""
    id: str
    workflow_id: str
    trigger_type: str
    trigger_id: Optional[str]
    trigger_name: Optional[str]
    status: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    triggered_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TriggerStatsResponse(BaseModel):
    """Trigger statistics response."""
    total_triggers: int
    active_triggers: int
    inactive_triggers: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    by_type: Dict[str, int]


class ManualExecutionRequest(BaseModel):
    """Manual trigger execution request."""
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input data for execution")


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("", response_model=List[TriggerResponse])
async def list_triggers(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all triggers.
    
    Returns triggers accessible by the current user, optionally filtered.
    """
    logger.info(f"Listing triggers for user {current_user.id}")
    
    try:
        triggers = []
        
        # Build workflow filter
        workflow_query = db.query(Workflow).filter(Workflow.user_id == current_user.id)
        if workflow_id:
            workflow_query = workflow_query.filter(Workflow.id == workflow_id)
        
        workflows = workflow_query.all()
        workflow_map = {str(w.id): w for w in workflows}
        
        # Get webhooks
        if not trigger_type or trigger_type == "webhook":
            webhook_query = db.query(WorkflowWebhook).filter(
                WorkflowWebhook.workflow_id.in_([w.id for w in workflows])
            )
            if is_active is not None:
                webhook_query = webhook_query.filter(WorkflowWebhook.is_active == is_active)
            
            webhooks = webhook_query.all()
            for webhook in webhooks:
                workflow = workflow_map.get(str(webhook.workflow_id))
                triggers.append(TriggerResponse(
                    id=str(webhook.id),
                    workflow_id=str(webhook.workflow_id),
                    workflow_name=workflow.name if workflow else "Unknown",
                    name=f"Webhook: {webhook.webhook_path}",
                    description=f"HTTP {webhook.http_method} webhook",
                    trigger_type="webhook",
                    is_active=webhook.is_active,
                    config={
                        "webhook_path": webhook.webhook_path,
                        "http_method": webhook.http_method,
                        "webhook_url": f"/api/webhooks/{webhook.webhook_path}",
                    },
                    last_triggered_at=webhook.last_triggered_at,
                    trigger_count=webhook.trigger_count,
                    created_at=webhook.created_at,
                    updated_at=webhook.updated_at,
                ))
        
        # Get schedules
        if not trigger_type or trigger_type == "schedule":
            schedule_query = db.query(WorkflowSchedule).filter(
                WorkflowSchedule.workflow_id.in_([w.id for w in workflows])
            )
            if is_active is not None:
                schedule_query = schedule_query.filter(WorkflowSchedule.is_active == is_active)
            
            schedules = schedule_query.all()
            for schedule in schedules:
                workflow = workflow_map.get(str(schedule.workflow_id))
                triggers.append(TriggerResponse(
                    id=str(schedule.id),
                    workflow_id=str(schedule.workflow_id),
                    workflow_name=workflow.name if workflow else "Unknown",
                    name=f"Schedule: {schedule.cron_expression}",
                    description=f"Runs on schedule: {schedule.cron_expression}",
                    trigger_type="schedule",
                    is_active=schedule.is_active,
                    config={
                        "cron_expression": schedule.cron_expression,
                        "timezone": schedule.timezone,
                        "next_execution_at": schedule.next_execution_at.isoformat() if schedule.next_execution_at else None,
                    },
                    last_triggered_at=schedule.last_execution_at,
                    trigger_count=0,  # TODO: Count from TriggerExecution
                    created_at=schedule.created_at,
                    updated_at=schedule.updated_at,
                ))
        
        logger.info(f"Found {len(triggers)} triggers")
        return triggers
        
    except Exception as e:
        logger.error(f"Failed to list triggers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list triggers: {str(e)}")


@router.get("/{trigger_id}", response_model=TriggerResponse)
async def get_trigger(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trigger details."""
    logger.info(f"Getting trigger {trigger_id} of type {trigger_type}")
    
    try:
        if trigger_type == "webhook":
            trigger = db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == trigger_id
            ).first()
            
            if not trigger:
                raise HTTPException(status_code=404, detail="Trigger not found")
            
            # Check permissions
            workflow = db.query(Workflow).filter(Workflow.id == trigger.workflow_id).first()
            if not workflow or str(workflow.user_id) != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            return TriggerResponse(
                id=str(trigger.id),
                workflow_id=str(trigger.workflow_id),
                workflow_name=workflow.name,
                name=f"Webhook: {trigger.webhook_path}",
                description=f"HTTP {trigger.http_method} webhook",
                trigger_type="webhook",
                is_active=trigger.is_active,
                config={
                    "webhook_path": trigger.webhook_path,
                    "http_method": trigger.http_method,
                    "webhook_url": f"/api/webhooks/{trigger.webhook_path}",
                },
                last_triggered_at=trigger.last_triggered_at,
                trigger_count=trigger.trigger_count,
                created_at=trigger.created_at,
                updated_at=trigger.updated_at,
            )
            
        elif trigger_type == "schedule":
            trigger = db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == trigger_id
            ).first()
            
            if not trigger:
                raise HTTPException(status_code=404, detail="Trigger not found")
            
            # Check permissions
            workflow = db.query(Workflow).filter(Workflow.id == trigger.workflow_id).first()
            if not workflow or str(workflow.user_id) != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            return TriggerResponse(
                id=str(trigger.id),
                workflow_id=str(trigger.workflow_id),
                workflow_name=workflow.name,
                name=f"Schedule: {trigger.cron_expression}",
                description=f"Runs on schedule: {trigger.cron_expression}",
                trigger_type="schedule",
                is_active=trigger.is_active,
                config={
                    "cron_expression": trigger.cron_expression,
                    "timezone": trigger.timezone,
                    "next_execution_at": trigger.next_execution_at.isoformat() if trigger.next_execution_at else None,
                },
                last_triggered_at=trigger.last_execution_at,
                trigger_count=0,
                created_at=trigger.created_at,
                updated_at=trigger.updated_at,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported trigger type: {trigger_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trigger: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get trigger: {str(e)}")


@router.post("", response_model=TriggerResponse)
async def create_trigger(
    request: TriggerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trigger."""
    logger.info(f"Creating trigger for workflow {request.workflow_id}")
    
    try:
        # Verify workflow exists and user has access
        workflow = get_workflow_with_relations(db, request.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if str(workflow.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create trigger using TriggerManager
        trigger_manager = TriggerManager(db)
        result = await trigger_manager.register_trigger(
            workflow_id=request.workflow_id,
            trigger_type=request.trigger_type,
            config=request.config
        )
        
        # Get the created trigger
        trigger_id = result.get("trigger_id")
        return await get_trigger(trigger_id, request.trigger_type, current_user, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trigger: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create trigger: {str(e)}")


@router.put("/{trigger_id}")
async def update_trigger(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    request: TriggerUpdate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update trigger."""
    logger.info(f"Updating trigger {trigger_id}")
    
    try:
        if trigger_type == "webhook":
            trigger = db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == trigger_id
            ).first()
            
            if not trigger:
                raise HTTPException(status_code=404, detail="Trigger not found")
            
            # Check permissions
            workflow = db.query(Workflow).filter(Workflow.id == trigger.workflow_id).first()
            if not workflow or str(workflow.user_id) != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Update fields
            if request.is_active is not None:
                trigger.is_active = request.is_active
            if request.config:
                if "http_method" in request.config:
                    trigger.http_method = request.config["http_method"]
            
            trigger.updated_at = datetime.utcnow()
            db.commit()
            
        elif trigger_type == "schedule":
            trigger = db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == trigger_id
            ).first()
            
            if not trigger:
                raise HTTPException(status_code=404, detail="Trigger not found")
            
            # Check permissions
            workflow = db.query(Workflow).filter(Workflow.id == trigger.workflow_id).first()
            if not workflow or str(workflow.user_id) != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Update fields
            if request.is_active is not None:
                trigger.is_active = request.is_active
            if request.config:
                if "cron_expression" in request.config:
                    trigger.cron_expression = request.config["cron_expression"]
                if "timezone" in request.config:
                    trigger.timezone = request.config["timezone"]
            
            trigger.updated_at = datetime.utcnow()
            db.commit()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported trigger type: {trigger_type}")
        
        return {"success": True, "message": "Trigger updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update trigger: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update trigger: {str(e)}")


@router.delete("/{trigger_id}")
async def delete_trigger(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete trigger."""
    logger.info(f"Deleting trigger {trigger_id}")
    
    try:
        if trigger_type == "webhook":
            trigger = db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == trigger_id
            ).first()
            
            if not trigger:
                raise HTTPException(status_code=404, detail="Trigger not found")
            
            # Check permissions
            workflow = db.query(Workflow).filter(Workflow.id == trigger.workflow_id).first()
            if not workflow or str(workflow.user_id) != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            db.delete(trigger)
            db.commit()
            
        elif trigger_type == "schedule":
            trigger = db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == trigger_id
            ).first()
            
            if not trigger:
                raise HTTPException(status_code=404, detail="Trigger not found")
            
            # Check permissions
            workflow = db.query(Workflow).filter(Workflow.id == trigger.workflow_id).first()
            if not workflow or str(workflow.user_id) != str(current_user.id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            db.delete(trigger)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported trigger type: {trigger_type}")
        
        return {"success": True, "message": "Trigger deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete trigger: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete trigger: {str(e)}")


@router.post("/{trigger_id}/activate")
async def activate_trigger(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate trigger."""
    return await update_trigger(
        trigger_id,
        trigger_type,
        TriggerUpdate(is_active=True),
        current_user,
        db
    )


@router.post("/{trigger_id}/deactivate")
async def deactivate_trigger(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate trigger."""
    return await update_trigger(
        trigger_id,
        trigger_type,
        TriggerUpdate(is_active=False),
        current_user,
        db
    )


@router.post("/{trigger_id}/execute")
async def execute_trigger_manually(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    request: ManualExecutionRequest = ManualExecutionRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually execute a trigger."""
    logger.info(f"Manually executing trigger {trigger_id}")
    
    try:
        # Get workflow ID based on trigger type
        workflow_id = None
        
        if trigger_type == "webhook":
            trigger = db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == trigger_id
            ).first()
            if trigger:
                workflow_id = str(trigger.workflow_id)
                
        elif trigger_type == "schedule":
            trigger = db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == trigger_id
            ).first()
            if trigger:
                workflow_id = str(trigger.workflow_id)
        
        if not workflow_id:
            raise HTTPException(status_code=404, detail="Trigger not found")
        
        # Check permissions
        workflow = get_workflow_with_relations(db, workflow_id)
        if not workflow or str(workflow.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Execute workflow
        trigger_manager = TriggerManager(db)
        result = await trigger_manager.execute_trigger(
            workflow_id=workflow_id,
            trigger_type="manual",
            trigger_data={
                "manual_execution": True,
                "trigger_id": trigger_id,
                "original_trigger_type": trigger_type,
                **request.input_data
            },
            user_id=str(current_user.id)
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute trigger: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute trigger: {str(e)}")


@router.get("/{trigger_id}/history", response_model=List[TriggerExecutionResponse])
async def get_trigger_history(
    trigger_id: str,
    trigger_type: str = Query(..., description="Type of trigger"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trigger execution history."""
    logger.info(f"Getting history for trigger {trigger_id}")
    
    try:
        # Verify trigger exists and user has access
        workflow_id = None
        
        if trigger_type == "webhook":
            trigger = db.query(WorkflowWebhook).filter(
                WorkflowWebhook.id == trigger_id
            ).first()
            if trigger:
                workflow_id = trigger.workflow_id
                
        elif trigger_type == "schedule":
            trigger = db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == trigger_id
            ).first()
            if trigger:
                workflow_id = trigger.workflow_id
        
        if not workflow_id:
            raise HTTPException(status_code=404, detail="Trigger not found")
        
        # Check permissions
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow or str(workflow.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get execution history
        executions = db.query(TriggerExecution).filter(
            TriggerExecution.trigger_id == trigger_id,
            TriggerExecution.trigger_type == trigger_type
        ).order_by(
            TriggerExecution.triggered_at.desc()
        ).limit(limit).all()
        
        return [
            TriggerExecutionResponse(
                id=str(e.id),
                workflow_id=str(e.workflow_id),
                trigger_type=e.trigger_type,
                trigger_id=e.trigger_id,
                trigger_name=e.trigger_name,
                status=e.status,
                error_message=e.error_message,
                duration_ms=e.duration_ms,
                triggered_at=e.triggered_at,
                completed_at=e.completed_at,
            )
            for e in executions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trigger history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get trigger history: {str(e)}")


@router.get("/stats/summary", response_model=TriggerStatsResponse)
async def get_trigger_stats(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trigger statistics."""
    logger.info(f"Getting trigger stats for user {current_user.id}")
    
    try:
        # Build workflow filter
        workflow_query = db.query(Workflow).filter(Workflow.user_id == current_user.id)
        if workflow_id:
            workflow_query = workflow_query.filter(Workflow.id == workflow_id)
        
        workflows = workflow_query.all()
        workflow_ids = [w.id for w in workflows]
        
        # Count webhooks
        webhook_count = db.query(WorkflowWebhook).filter(
            WorkflowWebhook.workflow_id.in_(workflow_ids)
        ).count()
        
        active_webhook_count = db.query(WorkflowWebhook).filter(
            WorkflowWebhook.workflow_id.in_(workflow_ids),
            WorkflowWebhook.is_active == True
        ).count()
        
        # Count schedules
        schedule_count = db.query(WorkflowSchedule).filter(
            WorkflowSchedule.workflow_id.in_(workflow_ids)
        ).count()
        
        active_schedule_count = db.query(WorkflowSchedule).filter(
            WorkflowSchedule.workflow_id.in_(workflow_ids),
            WorkflowSchedule.is_active == True
        ).count()
        
        # Count executions
        execution_query = db.query(TriggerExecution).filter(
            TriggerExecution.workflow_id.in_(workflow_ids)
        )
        
        total_executions = execution_query.count()
        successful_executions = execution_query.filter(
            TriggerExecution.status == "success"
        ).count()
        failed_executions = execution_query.filter(
            TriggerExecution.status == "failed"
        ).count()
        
        return TriggerStatsResponse(
            total_triggers=webhook_count + schedule_count,
            active_triggers=active_webhook_count + active_schedule_count,
            inactive_triggers=(webhook_count - active_webhook_count) + (schedule_count - active_schedule_count),
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            by_type={
                "webhook": webhook_count,
                "schedule": schedule_count,
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get trigger stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get trigger stats: {str(e)}")
