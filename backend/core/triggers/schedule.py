"""Schedule trigger for workflow execution."""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from croniter import croniter
import pytz

from backend.core.triggers.base import BaseTrigger
from backend.db.models.agent_builder import WorkflowSchedule

logger = logging.getLogger(__name__)


class ScheduleTrigger(BaseTrigger):
    """
    Schedule trigger for executing workflows on a schedule.
    
    Features:
    - Cron expression parsing
    - Timezone support
    - Next execution calculation
    - Schedule monitoring
    - Celery integration
    """
    
    def __init__(
        self,
        workflow_id: str,
        config: Dict[str, Any],
        db_session: Session
    ):
        """
        Initialize schedule trigger.
        
        Args:
            workflow_id: Workflow identifier
            config: Schedule configuration
            db_session: Database session
        """
        super().__init__(workflow_id, config)
        self.db = db_session
        self.schedule_id = config.get("schedule_id")
        self.cron_expression = config.get("cron_expression")
        self.timezone = config.get("timezone", "UTC")
        self.input_data = config.get("input_data", {})
    
    async def register(self) -> Dict[str, Any]:
        """
        Register schedule trigger.
        
        Creates schedule in database and registers with Celery.
        
        Returns:
            Registration result with schedule details
        """
        logger.info(
            f"Registering schedule trigger for workflow: {self.workflow_id}, "
            f"cron={self.cron_expression}"
        )
        
        try:
            # Validate cron expression
            if not self._validate_cron_expression(self.cron_expression):
                raise ValueError(f"Invalid cron expression: {self.cron_expression}")
            
            # Calculate next execution time
            next_execution = self._calculate_next_execution()
            
            # Check if schedule already exists
            if self.schedule_id:
                schedule = self.db.query(WorkflowSchedule).filter(
                    WorkflowSchedule.id == self.schedule_id
                ).first()
                
                if schedule:
                    # Update existing schedule
                    schedule.cron_expression = self.cron_expression
                    schedule.timezone = self.timezone
                    schedule.input_data = self.input_data
                    schedule.is_active = self.is_active
                    schedule.next_execution_at = next_execution
                    schedule.updated_at = datetime.utcnow()
                else:
                    # Create new schedule
                    schedule = self._create_schedule(next_execution)
            else:
                # Create new schedule
                schedule = self._create_schedule(next_execution)
            
            self.db.commit()
            self.schedule_id = str(schedule.id)
            
            # Register with Celery
            await self._register_celery_task()
            
            logger.info(
                f"Schedule registered: schedule_id={self.schedule_id}, "
                f"next_execution={next_execution}"
            )
            
            return {
                "trigger_id": self.schedule_id,
                "trigger_type": "schedule",
                "cron_expression": self.cron_expression,
                "timezone": self.timezone,
                "next_execution_at": next_execution.isoformat() if next_execution else None,
                "is_active": self.is_active,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to register schedule: workflow_id={self.workflow_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            self.db.rollback()
            raise
    
    async def unregister(self):
        """Unregister schedule trigger."""
        logger.info(f"Unregistering schedule: schedule_id={self.schedule_id}")
        
        try:
            if self.schedule_id:
                schedule = self.db.query(WorkflowSchedule).filter(
                    WorkflowSchedule.id == self.schedule_id
                ).first()
                
                if schedule:
                    schedule.is_active = False
                    schedule.updated_at = datetime.utcnow()
                    self.db.commit()
                    
                    # Unregister from Celery
                    await self._unregister_celery_task()
                    
                    logger.info(f"Schedule unregistered: schedule_id={self.schedule_id}")
        
        except Exception as e:
            logger.error(
                f"Failed to unregister schedule: schedule_id={self.schedule_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            self.db.rollback()
    
    async def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow on schedule.
        
        Args:
            trigger_data: Schedule execution data
            
        Returns:
            Execution result
        """
        logger.info(
            f"Executing schedule trigger: schedule_id={self.schedule_id}, "
            f"workflow_id={self.workflow_id}"
        )
        
        try:
            # Update schedule statistics
            await self._update_schedule_stats()
            
            # Calculate next execution time
            next_execution = self._calculate_next_execution()
            
            # Update next execution time in database
            schedule = self.db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == self.schedule_id
            ).first()
            
            if schedule:
                schedule.next_execution_at = next_execution
                self.db.commit()
            
            # Log trigger execution
            self.log_trigger(
                trigger_type="schedule",
                success=True,
                trigger_data=trigger_data
            )
            
            return {
                "success": True,
                "schedule_id": self.schedule_id,
                "workflow_id": self.workflow_id,
                "next_execution_at": next_execution.isoformat() if next_execution else None,
            }
            
        except Exception as e:
            logger.error(
                f"Schedule execution failed: schedule_id={self.schedule_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            
            self.log_trigger(
                trigger_type="schedule",
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
        Get schedule status.
        
        Returns:
            Status information
        """
        try:
            schedule = self.db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == self.schedule_id
            ).first()
            
            if not schedule:
                return {
                    "active": False,
                    "error": "Schedule not found"
                }
            
            return {
                "active": schedule.is_active,
                "schedule_id": str(schedule.id),
                "cron_expression": schedule.cron_expression,
                "timezone": schedule.timezone,
                "last_execution_at": schedule.last_execution_at.isoformat() if schedule.last_execution_at else None,
                "next_execution_at": schedule.next_execution_at.isoformat() if schedule.next_execution_at else None,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to get schedule status: schedule_id={self.schedule_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            return {
                "active": False,
                "error": str(e)
            }
    
    def _validate_cron_expression(self, cron_expr: str) -> bool:
        """
        Validate cron expression.
        
        Args:
            cron_expr: Cron expression
            
        Returns:
            True if valid
        """
        try:
            croniter(cron_expr)
            return True
        except Exception as e:
            logger.error(f"Invalid cron expression: {cron_expr}, error={str(e)}")
            return False
    
    def _calculate_next_execution(self) -> Optional[datetime]:
        """
        Calculate next execution time based on cron expression.
        
        Returns:
            Next execution datetime
        """
        try:
            # Get timezone
            tz = pytz.timezone(self.timezone)
            
            # Get current time in timezone
            now = datetime.now(tz)
            
            # Calculate next execution
            cron = croniter(self.cron_expression, now)
            next_run = cron.get_next(datetime)
            
            return next_run
            
        except Exception as e:
            logger.error(
                f"Failed to calculate next execution: schedule_id={self.schedule_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            return None
    
    def _create_schedule(self, next_execution: Optional[datetime]) -> WorkflowSchedule:
        """
        Create new schedule in database.
        
        Args:
            next_execution: Next execution datetime
            
        Returns:
            WorkflowSchedule model
        """
        schedule = WorkflowSchedule(
            workflow_id=uuid.UUID(self.workflow_id),
            cron_expression=self.cron_expression,
            timezone=self.timezone,
            input_data=self.input_data,
            is_active=self.is_active,
            next_execution_at=next_execution,
        )
        
        self.db.add(schedule)
        return schedule
    
    async def _update_schedule_stats(self):
        """Update schedule statistics."""
        try:
            schedule = self.db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == self.schedule_id
            ).first()
            
            if schedule:
                schedule.last_execution_at = datetime.utcnow()
                self.db.commit()
                
        except Exception as e:
            logger.error(
                f"Failed to update schedule stats: schedule_id={self.schedule_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            self.db.rollback()
    
    async def _register_celery_task(self):
        """
        Register schedule with Celery.
        
        Note: This is a placeholder. Actual Celery integration would require:
        1. Celery app configuration
        2. Task definition
        3. Beat scheduler configuration
        """
        logger.info(
            f"Registering Celery task for schedule: schedule_id={self.schedule_id}"
        )
        
        # TODO: Implement Celery task registration
        # Example:
        # from backend.celery_app import celery_app
        # celery_app.add_periodic_task(
        #     crontab(...),
        #     execute_workflow_task.s(self.workflow_id, self.schedule_id)
        # )
        
        pass
    
    async def _unregister_celery_task(self):
        """
        Unregister schedule from Celery.
        
        Note: This is a placeholder for Celery integration.
        """
        logger.info(
            f"Unregistering Celery task for schedule: schedule_id={self.schedule_id}"
        )
        
        # TODO: Implement Celery task unregistration
        
        pass
