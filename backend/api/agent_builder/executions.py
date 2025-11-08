"""
Agent Builder Execution API endpoints.

Provides endpoints for executing agents/workflows and managing execution schedules.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.db.models.agent_builder import ExecutionSchedule, AgentExecution
from backend.services.agent_builder.scheduler import ExecutionScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-builder/executions", tags=["agent-builder-executions"])


# Pydantic Models
class ScheduleCreate(BaseModel):
    """Request model for creating execution schedule."""
    agent_id: str = Field(..., description="Agent ID to execute")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    input_data: dict = Field(default_factory=dict, description="Input data for execution")
    timezone: str = Field(default="UTC", description="Timezone for schedule")
    is_active: bool = Field(default=True, description="Whether schedule is active")


class ScheduleUpdate(BaseModel):
    """Request model for updating execution schedule."""
    cron_expression: Optional[str] = Field(None, description="New cron expression")
    input_data: Optional[dict] = Field(None, description="New input data")
    timezone: Optional[str] = Field(None, description="New timezone")
    is_active: Optional[bool] = Field(None, description="New active status")


class ScheduleResponse(BaseModel):
    """Response model for execution schedule."""
    id: str
    agent_id: str
    user_id: str
    cron_expression: str
    timezone: str
    input_data: dict
    is_active: bool
    last_execution_at: Optional[datetime]
    next_execution_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Response model for agent execution."""
    id: str
    agent_id: str
    user_id: str
    session_id: Optional[str]
    input_data: dict
    output_data: Optional[dict]
    execution_context: dict
    status: str
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    
    class Config:
        from_attributes = True


# Schedule Endpoints

@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new execution schedule.
    
    Creates a cron-based schedule for recurring agent executions.
    """
    try:
        # Initialize scheduler
        scheduler = ExecutionScheduler(db)
        
        # Create schedule
        schedule = await scheduler.create_schedule(
            agent_id=schedule_data.agent_id,
            user_id=str(current_user.id),
            cron_expression=schedule_data.cron_expression,
            input_data=schedule_data.input_data,
            timezone_str=schedule_data.timezone,
            is_active=schedule_data.is_active
        )
        
        logger.info(f"Created schedule {schedule.id} for user {current_user.id}")
        
        return schedule
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule"
        )


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    agent_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List execution schedules.
    
    Returns schedules for the current user with optional filters.
    """
    try:
        scheduler = ExecutionScheduler(db)
        
        schedules = scheduler.list_schedules(
            user_id=str(current_user.id),
            agent_id=agent_id,
            is_active=is_active
        )
        
        return schedules
        
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schedules"
        )


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get execution schedule by ID.
    
    Returns schedule details if user has access.
    """
    try:
        scheduler = ExecutionScheduler(db)
        schedule = scheduler.get_schedule(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        # Check ownership
        if schedule.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schedule"
        )


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update execution schedule.
    
    Updates schedule configuration. User must own the schedule.
    """
    try:
        scheduler = ExecutionScheduler(db)
        
        # Check ownership
        schedule = scheduler.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        if schedule.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update schedule
        updated_schedule = await scheduler.update_schedule(
            schedule_id=schedule_id,
            cron_expression=schedule_data.cron_expression,
            input_data=schedule_data.input_data,
            timezone_str=schedule_data.timezone,
            is_active=schedule_data.is_active
        )
        
        logger.info(f"Updated schedule {schedule_id} for user {current_user.id}")
        
        return updated_schedule
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule"
        )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete execution schedule.
    
    Removes schedule and stops future executions. User must own the schedule.
    """
    try:
        scheduler = ExecutionScheduler(db)
        
        # Check ownership
        schedule = scheduler.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        if schedule.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete schedule
        await scheduler.delete_schedule(schedule_id)
        
        logger.info(f"Deleted schedule {schedule_id} for user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule"
        )


@router.post("/schedules/{schedule_id}/pause", response_model=ScheduleResponse)
async def pause_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pause execution schedule.
    
    Temporarily stops scheduled executions without deleting the schedule.
    """
    try:
        scheduler = ExecutionScheduler(db)
        
        # Check ownership
        schedule = scheduler.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        if schedule.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Pause schedule
        updated_schedule = await scheduler.pause_schedule(schedule_id)
        
        logger.info(f"Paused schedule {schedule_id} for user {current_user.id}")
        
        return updated_schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause schedule"
        )


@router.post("/schedules/{schedule_id}/resume", response_model=ScheduleResponse)
async def resume_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resume paused execution schedule.
    
    Resumes scheduled executions for a paused schedule.
    """
    try:
        scheduler = ExecutionScheduler(db)
        
        # Check ownership
        schedule = scheduler.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        if schedule.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Resume schedule
        updated_schedule = await scheduler.resume_schedule(schedule_id)
        
        logger.info(f"Resumed schedule {schedule_id} for user {current_user.id}")
        
        return updated_schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume schedule"
        )


# Execution Endpoints

@router.get("", response_model=List[ExecutionResponse])
async def list_executions(
    agent_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List agent executions.
    
    Returns execution history for the current user with optional filters.
    """
    try:
        query = db.query(AgentExecution).filter(
            AgentExecution.user_id == str(current_user.id)
        )
        
        if agent_id:
            query = query.filter(AgentExecution.agent_id == agent_id)
        
        if status_filter:
            query = query.filter(AgentExecution.status == status_filter)
        
        executions = query.order_by(
            AgentExecution.started_at.desc()
        ).limit(limit).offset(offset).all()
        
        return executions
        
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list executions"
        )


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get execution details by ID.
    
    Returns execution details if user has access.
    """
    try:
        execution = db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        # Check ownership
        if execution.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution"
        )
