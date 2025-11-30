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
from backend.services.auth_service import AuthService
from backend.db.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/executions", tags=["agent-builder-executions"])


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
        if str(schedule.user_id) != str(current_user.id):
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
        
        if str(schedule.user_id) != str(current_user.id):
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
        
        if str(schedule.user_id) != str(current_user.id):
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
        
        if str(schedule.user_id) != str(current_user.id):
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
        
        if str(schedule.user_id) != str(current_user.id):
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

@router.get("")
async def list_executions(
    agent_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all executions (agents and workflows).
    
    Returns execution history for the current user with optional filters.
    Combines both AgentExecution and WorkflowExecution records.
    """
    try:
        from backend.db.models.agent_builder import WorkflowExecution
        
        # Query agent executions
        agent_query = db.query(AgentExecution).filter(
            AgentExecution.user_id == str(current_user.id)
        )
        
        if agent_id:
            agent_query = agent_query.filter(AgentExecution.agent_id == agent_id)
        
        if status_filter:
            agent_query = agent_query.filter(AgentExecution.status == status_filter)
        
        # Query workflow executions
        workflow_query = db.query(WorkflowExecution).filter(
            WorkflowExecution.user_id == current_user.id
        )
        
        if status_filter:
            workflow_query = workflow_query.filter(WorkflowExecution.status == status_filter)
        
        # Get all executions
        agent_executions = agent_query.all()
        workflow_executions = workflow_query.all()
        
        # Combine and format executions
        combined_executions = []
        
        # Add agent executions
        for exec in agent_executions:
            combined_executions.append({
                "id": str(exec.id),
                "type": "agent",
                "agent_id": str(exec.agent_id) if exec.agent_id else None,
                "workflow_id": None,
                "user_id": str(exec.user_id),
                "session_id": exec.session_id,
                "input_data": exec.input_data,
                "output_data": exec.output_data,
                "execution_context": exec.execution_context,
                "status": exec.status,
                "error_message": exec.error_message,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                "duration_ms": exec.duration_ms
            })
        
        # Add workflow executions
        for exec in workflow_executions:
            combined_executions.append({
                "id": str(exec.id),
                "type": "workflow",
                "agent_id": None,
                "workflow_id": str(exec.workflow_id) if exec.workflow_id else None,
                "user_id": str(exec.user_id),
                "session_id": None,
                "input_data": exec.input_data,
                "output_data": exec.output_data,
                "execution_context": exec.execution_context,
                "status": exec.status,
                "error_message": exec.error_message,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                "duration_ms": int((exec.completed_at - exec.started_at).total_seconds() * 1000) if exec.completed_at and exec.started_at else None
            })
        
        # Sort by started_at descending
        combined_executions.sort(key=lambda x: x["started_at"] or "", reverse=True)
        
        # Apply pagination
        total = len(combined_executions)
        paginated_executions = combined_executions[offset:offset + limit]
        
        # Return in expected format
        return {
            "executions": paginated_executions,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list executions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list executions"
        )


@router.get("/agents/{agent_id}")
async def list_agent_executions(
    agent_id: str,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List executions for a specific agent.
    
    Returns execution history for a specific agent with optional filters.
    """
    try:
        query = db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.user_id == str(current_user.id)
        )
        
        if status_filter:
            query = query.filter(AgentExecution.status == status_filter)
        
        # Get total count
        total = query.count()
        
        executions = query.order_by(
            AgentExecution.started_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Return in expected format
        return {
            "executions": executions,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list agent executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agent executions"
        )


async def _get_execution_statistics_impl(current_user: User, db: Session):
    """Internal implementation for execution statistics."""
    from backend.db.models.agent_builder import AgentExecution
    
    # Get all executions for current user
    executions = db.query(AgentExecution).filter(
        AgentExecution.user_id == str(current_user.id)
    ).all()
    
    total = len(executions)
    completed = sum(1 for e in executions if e.status == 'completed')
    failed = sum(1 for e in executions if e.status == 'failed')
    running = sum(1 for e in executions if e.status == 'running')
    
    # Calculate average duration for completed executions
    completed_execs = [e for e in executions if e.status == 'completed' and e.duration_ms]
    avg_duration = sum(e.duration_ms for e in completed_execs) / len(completed_execs) if completed_execs else 0
    
    # Get recent executions (last 10)
    recent = db.query(AgentExecution).filter(
        AgentExecution.user_id == str(current_user.id)
    ).order_by(AgentExecution.started_at.desc()).limit(10).all()
    
    return {
        "total_executions": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "success_rate": round((completed / total * 100) if total > 0 else 0, 1),
        "avg_duration_ms": round(avg_duration, 1),
        "recent_executions": [
            {
                "id": str(e.id),
                "agent_id": str(e.agent_id),
                "status": e.status,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "duration_ms": e.duration_ms
            }
            for e in recent
        ]
    }


@router.get("/stats")
async def get_execution_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall execution statistics for the current user.
    
    Alias for /statistics endpoint for backward compatibility.
    
    Returns:
    - Total executions
    - Success/failure rates
    - Average duration
    - Recent activity
    """
    try:
        return await _get_execution_statistics_impl(current_user, db)
    except Exception as e:
        logger.error(f"Failed to get execution statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution statistics"
        )


@router.get("/statistics")
async def get_execution_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall execution statistics for the current user.
    
    Returns:
    - Total executions
    - Success/failure rates
    - Average duration
    - Recent activity
    """
    try:
        return await _get_execution_statistics_impl(current_user, db)
    except Exception as e:
        logger.error(f"Failed to get execution statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution statistics"
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
        if str(execution.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Convert UUID fields to strings for response
        return ExecutionResponse(
            id=str(execution.id),
            agent_id=str(execution.agent_id),
            user_id=str(execution.user_id),
            session_id=execution.session_id,
            input_data=execution.input_data or {},
            output_data=execution.output_data,
            execution_context=execution.execution_context or {},
            status=execution.status,
            error_message=execution.error_message,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration_ms=execution.duration_ms,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution"
        )



# Agent Execution SSE Endpoint

@router.get("/agents/{agent_id}/execute")
async def execute_agent_stream(
    agent_id: str,
    query: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Execute agent with Server-Sent Events streaming.
    
    This endpoint streams agent execution progress in real-time.
    Used by the frontend Agent Builder UI.
    
    Args:
        agent_id: Agent ID to execute
        query: Query/input for the agent
        token: Authentication token (from query param for SSE)
        
    Returns:
        StreamingResponse with SSE events
    """
    from fastapi.responses import StreamingResponse
    from backend.services.auth_service import AuthService
    from backend.services.agent_builder.agent_executor import AgentExecutor
    import json
    import asyncio
    
    async def event_generator():
        """Generate SSE events for agent execution."""
        try:
            # Authenticate user from token
            from uuid import UUID
            from backend.config import settings
            
            user = None
            
            # DEBUG MODE: Use test user if no token provided
            if settings.DEBUG and (not token or token == 'null'):
                logger.debug("DEBUG mode: Using test user for SSE execution")
                user_repo = UserRepository(db)
                user = user_repo.get_user_by_email("test@example.com")
                
                if not user:
                    # Create test user if doesn't exist
                    from backend.db.models.user import User as UserModel
                    user = UserModel(
                        email="test@example.com",
                        username="testuser",
                        password_hash=AuthService.hash_password("test1234"),
                        role="admin",
                        is_active=True,
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    logger.info("Created test user for DEBUG mode")
            
            # Production mode or token provided: validate token
            elif not token or token == 'null':
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Authentication required'}})}\n\n"
                return
            else:
                try:
                    payload = AuthService.decode_token(token)
                    if not payload:
                        yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Invalid token'}})}\n\n"
                        return
                    
                    user_id_str = payload.get("sub")
                    if not user_id_str:
                        yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Invalid token payload'}})}\n\n"
                        return
                    
                    user_id = UUID(user_id_str)
                    user_repo = UserRepository(db)
                    user = user_repo.get_user_by_id(user_id)
                    
                    if not user:
                        yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'User not found'}})}\n\n"
                        return
                        
                except Exception as e:
                    logger.error(f"Authentication failed: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Authentication failed'}})}\n\n"
                    return
            
            if not user:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'User authentication failed'}})}\n\n"
                return
            
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'data': {'agent_id': agent_id, 'query': query}})}\n\n"
            
            # Execute agent
            executor = AgentExecutor(db)
            
            try:
                execution = await executor.execute_agent(
                    agent_id=agent_id,
                    user_id=str(user.id),
                    input_data={"query": query, "input": query},
                    session_id=None,
                    variables={}
                )
                
                # Send progress events (simulated for now)
                yield f"data: {json.dumps({'type': 'step', 'data': {'step': 'processing', 'message': 'Executing agent...'}})}\n\n"
                await asyncio.sleep(0.1)
                
                # Send completion event
                result_data = {
                    'type': 'complete',
                    'data': {
                        'execution_id': str(execution.id),
                        'status': execution.status,
                        'output': execution.output_data.get('output', '') if execution.output_data else '',
                        'duration_ms': execution.duration_ms,
                        'error': execution.error_message
                    }
                }
                yield f"data: {json.dumps(result_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Agent execution failed: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Internal server error'}})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
