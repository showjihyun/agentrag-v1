"""
Background task management API endpoints.

Provides endpoints for checking task status, cancelling tasks,
and retrieving task results.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.core.background_tasks import get_task_manager, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# Response models
class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str = Field(..., description="Task identifier")
    task_type: str = Field(..., description="Task type")
    status: str = Field(..., description="Task status")
    progress: float = Field(..., description="Progress (0.0 to 1.0)")
    created_at: str = Field(..., description="Creation timestamp")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    result: Optional[dict] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: dict = Field(default_factory=dict, description="Task metadata")


class TaskListResponse(BaseModel):
    """Response model for task list."""

    tasks: List[TaskStatusResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")


class TaskStatsResponse(BaseModel):
    """Response model for task statistics."""

    total_tasks: int = Field(..., description="Total number of tasks")
    running_tasks: int = Field(..., description="Number of running tasks")
    max_concurrent: int = Field(..., description="Maximum concurrent tasks")
    by_status: dict = Field(..., description="Task counts by status")


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a background task.

    Args:
        task_id: Task identifier

    Returns:
        Task status and details
    """
    try:
        task_manager = get_task_manager()

        task_status = task_manager.get_task_status(task_id)

        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}",
            )

        return TaskStatusResponse(**task_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List all background tasks.

    Args:
        status_filter: Optional status filter (pending, running, completed, failed, cancelled)
        limit: Maximum number of tasks to return
        offset: Offset for pagination

    Returns:
        List of tasks
    """
    try:
        task_manager = get_task_manager()

        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}",
                )

        # Get tasks
        all_tasks = task_manager.get_all_tasks(status=status_enum)

        # Apply pagination
        total = len(all_tasks)
        tasks = all_tasks[offset : offset + limit]

        # Convert to response models
        task_responses = [TaskStatusResponse(**task) for task in tasks]

        return TaskListResponse(tasks=task_responses, total=total)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}",
        )


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running background task.

    Args:
        task_id: Task identifier

    Returns:
        Cancellation status
    """
    try:
        task_manager = get_task_manager()

        # Check if task exists
        task_status = task_manager.get_task_status(task_id)
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}",
            )

        # Cancel task
        cancelled = task_manager.cancel_task(task_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task cannot be cancelled (status: {task_status['status']})",
            )

        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        )


@router.get("/stats/summary", response_model=TaskStatsResponse)
async def get_task_stats():
    """
    Get task manager statistics.

    Returns:
        Task statistics
    """
    try:
        task_manager = get_task_manager()

        stats = task_manager.get_stats()

        return TaskStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get task stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task stats: {str(e)}",
        )


@router.post("/cleanup")
async def cleanup_old_tasks(
    max_age_seconds: int = Query(3600, ge=60, description="Maximum age in seconds")
):
    """
    Clean up old completed tasks.

    Args:
        max_age_seconds: Maximum age in seconds (default: 1 hour)

    Returns:
        Number of tasks cleaned up
    """
    try:
        task_manager = get_task_manager()

        cleaned = task_manager.cleanup_old_tasks(max_age_seconds=max_age_seconds)

        return {
            "cleaned_tasks": cleaned,
            "max_age_seconds": max_age_seconds,
            "message": f"Cleaned up {cleaned} old tasks",
        }

    except Exception as e:
        logger.error(f"Failed to cleanup tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup tasks: {str(e)}",
        )
