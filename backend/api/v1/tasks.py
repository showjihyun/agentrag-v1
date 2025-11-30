"""
Task Queue API v1

Provides endpoints for managing background tasks:
- Enqueue tasks
- Check task status
- View queue statistics
- Manage dead letter queue
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from backend.core.api_response import api_response, ErrorCode
from backend.core.redis_queue import (
    RedisQueue,
    TaskPriority,
    TaskStatus,
    Task,
)
from backend.core.dependencies import get_redis_client


router = APIRouter(prefix="/api/v1/tasks", tags=["Task Queue v1"])


# ============================================================================
# Request/Response Models
# ============================================================================

class EnqueueTaskRequest(BaseModel):
    """Request to enqueue a task."""
    task_name: str = Field(..., description="Name of the registered task handler")
    args: List[Any] = Field(default_factory=list, description="Positional arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments")
    priority: str = Field(default="normal", description="Task priority: low, normal, high, critical")
    delay: Optional[float] = Field(None, description="Delay in seconds before execution")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    timeout: float = Field(default=300.0, ge=1.0, le=3600.0, description="Task timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskResponse(BaseModel):
    """Task information response."""
    id: str
    name: str
    status: str
    priority: int
    created_at: str
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int
    max_retries: int
    result: Optional[Any] = None
    error: Optional[str] = None


class QueueStatsResponse(BaseModel):
    """Queue statistics response."""
    queue_size: int
    scheduled_size: int
    processing_size: int
    dlq_size: int
    workers_running: int
    total_enqueued: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_retries: int = 0


# ============================================================================
# Helper Functions
# ============================================================================

def get_priority_value(priority: str) -> TaskPriority:
    """Convert priority string to TaskPriority enum."""
    priority_map = {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "critical": TaskPriority.CRITICAL,
    }
    return priority_map.get(priority.lower(), TaskPriority.NORMAL)


async def get_queue(queue_name: str = "default") -> RedisQueue:
    """Get Redis queue instance."""
    redis = await get_redis_client()
    return RedisQueue(redis, queue_name)


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/enqueue",
    summary="Enqueue Task",
    description="Add a new task to the queue for background processing.",
)
async def enqueue_task(request: EnqueueTaskRequest):
    """
    Enqueue a task for background processing.
    
    The task will be processed by a worker based on its priority.
    Use `delay` to schedule the task for later execution.
    """
    queue = await get_queue()
    
    try:
        task_id = await queue.enqueue(
            task_name=request.task_name,
            args=tuple(request.args),
            kwargs=request.kwargs,
            priority=get_priority_value(request.priority),
            delay=request.delay,
            max_retries=request.max_retries,
            timeout=request.timeout,
            metadata=request.metadata,
        )
        
        return api_response(
            data={
                "task_id": task_id,
                "status": "queued",
                "message": f"Task '{request.task_name}' enqueued successfully",
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": f"Failed to enqueue task: {str(e)}"}
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get Task Status",
    description="Get the current status and details of a task.",
)
async def get_task_status(task_id: str):
    """Get task status by ID."""
    queue = await get_queue()
    task = await queue.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Task not found: {task_id}"}
        )
    
    return TaskResponse(
        id=task.id,
        name=task.name,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at,
        scheduled_at=task.scheduled_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
        result=task.result,
        error=task.error,
    )


@router.delete(
    "/{task_id}",
    summary="Cancel Task",
    description="Cancel a pending task.",
)
async def cancel_task(task_id: str):
    """Cancel a pending task."""
    queue = await get_queue()
    
    success = await queue.cancel_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Cannot cancel task: {task_id}. Task may not exist or is already running."}
        )
    
    return api_response(
        data={
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully",
        }
    )


@router.get(
    "/",
    summary="List Tasks",
    description="List tasks with optional filtering.",
)
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tasks to return"),
):
    """List tasks with optional status filter."""
    queue = await get_queue()
    
    # Get recent tasks from queue stats
    # Note: This is a simplified implementation
    # In production, you might want to add more sophisticated querying
    
    stats = await queue.get_stats()
    
    return api_response(
        data={
            "tasks": [],  # Would need to implement task listing
            "stats": stats,
        }
    )


@router.get(
    "/stats",
    response_model=QueueStatsResponse,
    summary="Queue Statistics",
    description="Get queue statistics and metrics.",
)
async def get_queue_stats(queue_name: str = Query("default", description="Queue name")):
    """Get queue statistics."""
    redis = await get_redis_client()
    queue = RedisQueue(redis, queue_name)
    
    stats = await queue.get_stats()
    
    return QueueStatsResponse(
        queue_size=stats.get("queue_size", 0),
        scheduled_size=stats.get("scheduled_size", 0),
        processing_size=stats.get("processing_size", 0),
        dlq_size=stats.get("dlq_size", 0),
        workers_running=stats.get("workers_running", 0),
        total_enqueued=stats.get("total_enqueued", 0),
        total_completed=stats.get("total_completed", 0),
        total_failed=stats.get("total_failed", 0),
        total_retries=stats.get("total_retries", 0),
    )


@router.get(
    "/dlq",
    summary="Dead Letter Queue",
    description="Get tasks from the dead letter queue.",
)
async def get_dlq_tasks(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tasks"),
    queue_name: str = Query("default", description="Queue name"),
):
    """Get tasks from dead letter queue."""
    redis = await get_redis_client()
    queue = RedisQueue(redis, queue_name)
    
    tasks = await queue.get_dlq_tasks(limit=limit)
    
    return api_response(
        data={
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "error": t.error,
                    "retry_count": t.retry_count,
                    "created_at": t.created_at,
                    "completed_at": t.completed_at,
                }
                for t in tasks
            ],
            "total": len(tasks),
        }
    )


@router.post(
    "/dlq/{task_id}/retry",
    summary="Retry DLQ Task",
    description="Retry a task from the dead letter queue.",
)
async def retry_dlq_task(
    task_id: str,
    queue_name: str = Query("default", description="Queue name"),
):
    """Retry a task from the dead letter queue."""
    redis = await get_redis_client()
    queue = RedisQueue(redis, queue_name)
    
    success = await queue.retry_dlq_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Cannot retry task: {task_id}. Task may not exist in DLQ."}
        )
    
    return api_response(
        data={
            "task_id": task_id,
            "status": "queued",
            "message": "Task re-queued for retry",
        }
    )


@router.post(
    "/dlq/retry-all",
    summary="Retry All DLQ Tasks",
    description="Retry all tasks in the dead letter queue.",
)
async def retry_all_dlq_tasks(
    queue_name: str = Query("default", description="Queue name"),
):
    """Retry all tasks in the dead letter queue."""
    redis = await get_redis_client()
    queue = RedisQueue(redis, queue_name)
    
    tasks = await queue.get_dlq_tasks(limit=1000)
    retried = 0
    
    for task in tasks:
        if await queue.retry_dlq_task(task.id):
            retried += 1
    
    return api_response(
        data={
            "retried": retried,
            "total": len(tasks),
            "message": f"Retried {retried} tasks from DLQ",
        }
    )


@router.delete(
    "/completed",
    summary="Clear Completed Tasks",
    description="Clear completed tasks older than specified hours.",
)
async def clear_completed_tasks(
    older_than_hours: int = Query(24, ge=1, le=720, description="Clear tasks older than X hours"),
    queue_name: str = Query("default", description="Queue name"),
):
    """Clear completed tasks older than specified hours."""
    redis = await get_redis_client()
    queue = RedisQueue(redis, queue_name)
    
    deleted = await queue.clear_completed_tasks(older_than_hours=older_than_hours)
    
    return api_response(
        data={
            "deleted": deleted,
            "message": f"Cleared {deleted} completed tasks older than {older_than_hours}h",
        }
    )
