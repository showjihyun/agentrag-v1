"""Trigger Manager for managing workflow triggers."""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.core.triggers.base import BaseTrigger
from backend.core.triggers.webhook import WebhookTrigger
from backend.core.triggers.schedule import ScheduleTrigger
from backend.core.triggers.api import APITrigger
from backend.core.triggers.chat import ChatTrigger
from backend.core.execution.executor import WorkflowExecutor
from backend.db.models.agent_builder import (
    Workflow,
    WorkflowWebhook,
    WorkflowSchedule,
)

logger = logging.getLogger(__name__)


class TriggerManager:
    """
    Manages all workflow triggers.
    
    Responsibilities:
    - Register/unregister triggers
    - Execute workflows in response to triggers
    - Monitor trigger status
    - Log trigger executions
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize TriggerManager.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.executor = WorkflowExecutor(db_session)
        self._active_triggers: Dict[str, BaseTrigger] = {}
    
    async def register_trigger(
        self,
        workflow_id: str,
        trigger_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a new trigger for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            trigger_type: Type of trigger (webhook, schedule, api, chat)
            config: Trigger configuration
            
        Returns:
            Registration result with trigger details
            
        Raises:
            ValueError: If trigger type is invalid
        """
        logger.info(
            f"Registering trigger: workflow_id={workflow_id}, "
            f"type={trigger_type}"
        )
        
        # Verify workflow exists
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create trigger instance
        trigger = self._create_trigger(workflow_id, trigger_type, config)
        
        # Register trigger
        result = await trigger.register()
        
        # Store active trigger
        trigger_id = result.get("trigger_id")
        if trigger_id:
            self._active_triggers[trigger_id] = trigger
        
        logger.info(
            f"Trigger registered: workflow_id={workflow_id}, "
            f"trigger_id={trigger_id}, type={trigger_type}"
        )
        
        return result
    
    async def unregister_trigger(
        self,
        trigger_id: str,
        trigger_type: str
    ):
        """
        Unregister a trigger.
        
        Args:
            trigger_id: Trigger identifier
            trigger_type: Type of trigger
        """
        logger.info(f"Unregistering trigger: trigger_id={trigger_id}, type={trigger_type}")
        
        # Get trigger from active triggers
        trigger = self._active_triggers.get(trigger_id)
        
        if trigger:
            await trigger.unregister()
            del self._active_triggers[trigger_id]
        
        logger.info(f"Trigger unregistered: trigger_id={trigger_id}")
    
    async def execute_trigger(
        self,
        workflow_id: str,
        trigger_type: str,
        trigger_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute workflow in response to trigger.
        
        Args:
            workflow_id: Workflow identifier
            trigger_type: Type of trigger
            trigger_data: Data from trigger event
            user_id: User identifier
            
        Returns:
            Execution result
        """
        logger.info(
            f"Executing trigger: workflow_id={workflow_id}, "
            f"type={trigger_type}, user_id={user_id}"
        )
        
        try:
            # Execute workflow
            context = await self.executor.execute(
                workflow_id=workflow_id,
                user_id=user_id,
                trigger=trigger_type,
                input_data=trigger_data
            )
            
            # Log successful trigger
            self._log_trigger_execution(
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                success=True,
                execution_id=context.execution_id,
                trigger_data=trigger_data
            )
            
            return {
                "success": True,
                "execution_id": context.execution_id,
                "status": context.status,
                "outputs": context.get_final_outputs(),
            }
            
        except Exception as e:
            logger.error(
                f"Trigger execution failed: workflow_id={workflow_id}, "
                f"type={trigger_type}, error={str(e)}",
                exc_info=True
            )
            
            # Log failed trigger
            self._log_trigger_execution(
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                success=False,
                error=str(e),
                trigger_data=trigger_data
            )
            
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_trigger_status(
        self,
        trigger_id: str
    ) -> Dict[str, Any]:
        """
        Get status of a trigger.
        
        Args:
            trigger_id: Trigger identifier
            
        Returns:
            Status information
        """
        trigger = self._active_triggers.get(trigger_id)
        
        if not trigger:
            return {
                "active": False,
                "error": "Trigger not found"
            }
        
        return await trigger.get_status()
    
    async def list_triggers(
        self,
        workflow_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all triggers for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of trigger information
        """
        triggers = []
        
        # Get webhooks
        webhooks = self.db.query(WorkflowWebhook).filter(
            WorkflowWebhook.workflow_id == workflow_id
        ).all()
        
        for webhook in webhooks:
            triggers.append({
                "id": str(webhook.id),
                "type": "webhook",
                "is_active": webhook.is_active,
                "config": {
                    "webhook_path": webhook.webhook_path,
                    "http_method": webhook.http_method,
                },
                "last_triggered_at": webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
                "trigger_count": webhook.trigger_count,
            })
        
        # Get schedules
        schedules = self.db.query(WorkflowSchedule).filter(
            WorkflowSchedule.workflow_id == workflow_id
        ).all()
        
        for schedule in schedules:
            triggers.append({
                "id": str(schedule.id),
                "type": "schedule",
                "is_active": schedule.is_active,
                "config": {
                    "cron_expression": schedule.cron_expression,
                    "timezone": schedule.timezone,
                },
                "last_execution_at": schedule.last_execution_at.isoformat() if schedule.last_execution_at else None,
                "next_execution_at": schedule.next_execution_at.isoformat() if schedule.next_execution_at else None,
            })
        
        return triggers
    
    async def load_active_triggers(self):
        """
        Load all active triggers from database.
        
        Called on system startup to restore trigger state.
        """
        logger.info("Loading active triggers from database")
        
        # Load active webhooks
        webhooks = self.db.query(WorkflowWebhook).filter(
            WorkflowWebhook.is_active == True
        ).all()
        
        for webhook in webhooks:
            try:
                config = {
                    "webhook_id": str(webhook.id),
                    "webhook_path": webhook.webhook_path,
                    "webhook_secret": webhook.webhook_secret,
                    "http_method": webhook.http_method,
                    "is_active": webhook.is_active,
                }
                
                trigger = WebhookTrigger(
                    workflow_id=str(webhook.workflow_id),
                    config=config,
                    db_session=self.db
                )
                
                self._active_triggers[str(webhook.id)] = trigger
                
            except Exception as e:
                logger.error(
                    f"Failed to load webhook trigger: {webhook.id}, error={str(e)}",
                    exc_info=True
                )
        
        # Load active schedules
        schedules = self.db.query(WorkflowSchedule).filter(
            WorkflowSchedule.is_active == True
        ).all()
        
        for schedule in schedules:
            try:
                config = {
                    "schedule_id": str(schedule.id),
                    "cron_expression": schedule.cron_expression,
                    "timezone": schedule.timezone,
                    "input_data": schedule.input_data,
                    "is_active": schedule.is_active,
                }
                
                trigger = ScheduleTrigger(
                    workflow_id=str(schedule.workflow_id),
                    config=config,
                    db_session=self.db
                )
                
                # Register schedule with Celery
                await trigger.register()
                
                self._active_triggers[str(schedule.id)] = trigger
                
            except Exception as e:
                logger.error(
                    f"Failed to load schedule trigger: {schedule.id}, error={str(e)}",
                    exc_info=True
                )
        
        logger.info(f"Loaded {len(self._active_triggers)} active triggers")
    
    def _create_trigger(
        self,
        workflow_id: str,
        trigger_type: str,
        config: Dict[str, Any]
    ) -> BaseTrigger:
        """
        Create trigger instance based on type.
        
        Args:
            workflow_id: Workflow identifier
            trigger_type: Type of trigger
            config: Trigger configuration
            
        Returns:
            Trigger instance
            
        Raises:
            ValueError: If trigger type is invalid
        """
        if trigger_type == "webhook":
            return WebhookTrigger(workflow_id, config, self.db)
        elif trigger_type == "schedule":
            return ScheduleTrigger(workflow_id, config, self.db)
        elif trigger_type == "api":
            return APITrigger(workflow_id, config, self.db)
        elif trigger_type == "chat":
            return ChatTrigger(workflow_id, config, self.db)
        else:
            raise ValueError(f"Invalid trigger type: {trigger_type}")
    
    def _log_trigger_execution(
        self,
        workflow_id: str,
        trigger_type: str,
        success: bool,
        execution_id: Optional[str] = None,
        error: Optional[str] = None,
        trigger_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log trigger execution.
        
        Args:
            workflow_id: Workflow identifier
            trigger_type: Type of trigger
            success: Whether execution was successful
            execution_id: Execution identifier
            error: Error message if failed
            trigger_data: Trigger data
        """
        log_entry = {
            "workflow_id": workflow_id,
            "trigger_type": trigger_type,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if execution_id:
            log_entry["execution_id"] = execution_id
        
        if error:
            log_entry["error"] = error
        
        if trigger_data:
            log_entry["trigger_data"] = trigger_data
        
        if success:
            logger.info(f"Trigger execution logged: {log_entry}")
        else:
            logger.error(f"Trigger execution failed: {log_entry}")
