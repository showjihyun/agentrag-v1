"""Execution Scheduler for managing scheduled agent/workflow executions."""

import logging
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from croniter import croniter
import pytz

from backend.db.models.agent_builder import ExecutionSchedule, Agent

logger = logging.getLogger(__name__)


class ExecutionScheduler:
    """Service for managing execution schedules."""
    
    def __init__(self, db: Session):
        """
        Initialize Execution Scheduler.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_schedule(
        self,
        agent_id: str,
        user_id: str,
        cron_expression: str,
        input_data: Dict[str, Any],
        timezone_str: str = "UTC",
        is_active: bool = True
    ) -> ExecutionSchedule:
        """
        Create a new execution schedule.
        
        Args:
            agent_id: Agent ID to execute
            user_id: User ID creating the schedule
            cron_expression: Cron expression for scheduling
            input_data: Input data for execution
            timezone_str: Timezone for schedule
            is_active: Whether schedule is active
            
        Returns:
            Created ExecutionSchedule model
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate agent exists
            agent = self.db.query(Agent).filter(
                Agent.id == agent_id,
                Agent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Validate cron expression
            if not self._validate_cron(cron_expression):
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            
            # Validate timezone
            try:
                tz = pytz.timezone(timezone_str)
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError(f"Invalid timezone: {timezone_str}")
            
            # Calculate next execution time
            next_execution = self._calculate_next_execution(
                cron_expression,
                timezone_str
            )
            
            schedule = ExecutionSchedule(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                user_id=user_id,
                cron_expression=cron_expression,
                timezone=timezone_str,
                input_data=input_data or {},
                is_active=is_active,
                next_execution_at=next_execution
            )
            
            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)
            
            logger.info(f"Created schedule: {schedule.id} for agent {agent_id}")
            return schedule
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create schedule: {e}", exc_info=True)
            raise
    
    def get_schedule(self, schedule_id: str) -> Optional[ExecutionSchedule]:
        """
        Get schedule by ID.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            ExecutionSchedule model or None if not found
        """
        return self.db.query(ExecutionSchedule).filter(
            ExecutionSchedule.id == schedule_id
        ).first()
    
    async def update_schedule(
        self,
        schedule_id: str,
        cron_expression: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        timezone_str: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> ExecutionSchedule:
        """
        Update execution schedule.
        
        Args:
            schedule_id: Schedule ID
            cron_expression: New cron expression (optional)
            input_data: New input data (optional)
            timezone_str: New timezone (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated ExecutionSchedule model
            
        Raises:
            ValueError: If schedule not found or validation fails
        """
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            # Update cron expression
            if cron_expression is not None:
                if not self._validate_cron(cron_expression):
                    raise ValueError(f"Invalid cron expression: {cron_expression}")
                schedule.cron_expression = cron_expression
            
            # Update timezone
            if timezone_str is not None:
                try:
                    pytz.timezone(timezone_str)
                except pytz.exceptions.UnknownTimeZoneError:
                    raise ValueError(f"Invalid timezone: {timezone_str}")
                schedule.timezone = timezone_str
            
            # Update input data
            if input_data is not None:
                schedule.input_data = input_data
            
            # Update active status
            if is_active is not None:
                schedule.is_active = is_active
            
            # Recalculate next execution time
            schedule.next_execution_at = self._calculate_next_execution(
                schedule.cron_expression,
                schedule.timezone
            )
            
            self.db.commit()
            self.db.refresh(schedule)
            
            logger.info(f"Updated schedule: {schedule_id}")
            return schedule
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update schedule: {e}", exc_info=True)
            raise
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete execution schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return False
            
            self.db.delete(schedule)
            self.db.commit()
            
            logger.info(f"Deleted schedule: {schedule_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete schedule: {e}", exc_info=True)
            raise
    
    def list_schedules(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[ExecutionSchedule]:
        """
        List execution schedules with filters.
        
        Args:
            user_id: Filter by user ID (optional)
            agent_id: Filter by agent ID (optional)
            is_active: Filter by active status (optional)
            
        Returns:
            List of ExecutionSchedule models
        """
        query = self.db.query(ExecutionSchedule)
        
        if user_id:
            query = query.filter(ExecutionSchedule.user_id == user_id)
        
        if agent_id:
            query = query.filter(ExecutionSchedule.agent_id == agent_id)
        
        if is_active is not None:
            query = query.filter(ExecutionSchedule.is_active == is_active)
        
        return query.order_by(ExecutionSchedule.created_at.desc()).all()
    
    async def pause_schedule(self, schedule_id: str) -> ExecutionSchedule:
        """
        Pause execution schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            Updated ExecutionSchedule model
        """
        return await self.update_schedule(schedule_id, is_active=False)
    
    async def resume_schedule(self, schedule_id: str) -> ExecutionSchedule:
        """
        Resume paused execution schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            Updated ExecutionSchedule model
        """
        return await self.update_schedule(schedule_id, is_active=True)
    
    def get_due_schedules(self) -> List[ExecutionSchedule]:
        """
        Get schedules that are due for execution.
        
        Returns:
            List of ExecutionSchedule models that should be executed now
        """
        now = datetime.utcnow()
        
        schedules = self.db.query(ExecutionSchedule).filter(
            ExecutionSchedule.is_active == True,
            ExecutionSchedule.next_execution_at <= now
        ).all()
        
        return schedules
    
    async def execute_scheduled_jobs(self) -> int:
        """
        Execute all due scheduled jobs.
        
        This method should be called periodically (e.g., every minute)
        by a background worker or cron job.
        
        Returns:
            Number of jobs executed
        """
        try:
            due_schedules = self.get_due_schedules()
            
            if not due_schedules:
                return 0
            
            executed_count = 0
            failed_count = 0
            
            # Import AgentExecutor
            from backend.services.agent_builder.agent_executor import AgentExecutor
            executor = AgentExecutor(self.db)
            
            # Execute schedules with retry logic
            for schedule in due_schedules:
                execution = None
                retry_count = 0
                max_retries = 2
                
                while retry_count <= max_retries:
                    try:
                        # Execute agent
                        execution = await executor.execute_agent(
                            agent_id=schedule.agent_id,
                            user_id=schedule.user_id,
                            input_data=schedule.input_data,
                            session_id=f"scheduled_{schedule.id}_{retry_count}",
                            variables={
                                "schedule_id": str(schedule.id),
                                "retry_count": retry_count
                            }
                        )
                        
                        logger.info(
                            f"Executed scheduled job: {schedule.id}, "
                            f"execution: {execution.id}"
                        )
                        
                        # Update schedule
                        schedule.last_execution_at = datetime.utcnow()
                        schedule.next_execution_at = self._calculate_next_execution(
                            schedule.cron_expression,
                            schedule.timezone
                        )
                        
                        executed_count += 1
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        retry_count += 1
                        
                        if retry_count > max_retries:
                            logger.error(
                                f"Failed to execute schedule {schedule.id} "
                                f"after {max_retries} retries: {e}",
                                exc_info=True
                            )
                            
                            # Mark execution as failed if it was created
                            if execution:
                                execution.status = "failed"
                                execution.error_message = str(e)
                                execution.completed_at = datetime.utcnow()
                            
                            failed_count += 1
                            break
                        else:
                            logger.warning(
                                f"Schedule {schedule.id} failed on attempt {retry_count}, "
                                f"retrying: {e}"
                            )
                            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            
            # Commit all changes
            try:
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to commit schedule updates: {e}")
                self.db.rollback()
            
            logger.info(
                f"Executed {executed_count} scheduled jobs "
                f"({failed_count} failed)"
            )
            return executed_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to execute scheduled jobs: {e}", exc_info=True)
            return 0
    
    def _validate_cron(self, cron_expression: str) -> bool:
        """
        Validate cron expression.
        
        Args:
            cron_expression: Cron expression to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            croniter(cron_expression)
            return True
        except Exception:
            return False
    
    def _calculate_next_execution(
        self,
        cron_expression: str,
        timezone_str: str
    ) -> datetime:
        """
        Calculate next execution time based on cron expression.
        
        Args:
            cron_expression: Cron expression
            timezone_str: Timezone string
            
        Returns:
            Next execution datetime (UTC)
        """
        try:
            # Get current time in specified timezone
            tz = pytz.timezone(timezone_str)
            now_tz = datetime.now(tz)
            
            # Calculate next execution in timezone
            cron = croniter(cron_expression, now_tz)
            next_tz = cron.get_next(datetime)
            
            # Convert to UTC
            next_utc = next_tz.astimezone(pytz.UTC).replace(tzinfo=None)
            
            return next_utc
            
        except Exception as e:
            logger.error(f"Failed to calculate next execution: {e}")
            # Fallback: return 1 hour from now
            return datetime.utcnow() + timedelta(hours=1)
