"""
Background task management for long-running operations.

Provides task queue and status tracking for asynchronous operations
like document processing, batch operations, etc.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTask:
    """Represents a background task."""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}

        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        self.result: Any = None
        self.error: Optional[str] = None
        self.progress: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class BackgroundTaskManager:
    """
    Manager for background tasks.

    Features:
    - Task queue management
    - Status tracking
    - Progress updates
    - Result retrieval
    """

    def __init__(self, max_concurrent_tasks: int = 5):
        """
        Initialize BackgroundTaskManager.

        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        logger.info(
            f"BackgroundTaskManager initialized (max_concurrent={max_concurrent_tasks})"
        )

    def create_task(
        self,
        task_type: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Create a new background task.

        Args:
            task_type: Type of task (e.g., "document_upload")
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            task_id: Optional custom task ID

        Returns:
            str: Task ID
        """
        if task_id is None:
            task_id = f"{task_type}_{uuid.uuid4().hex[:8]}"

        task = BackgroundTask(
            task_id=task_id, task_type=task_type, func=func, args=args, kwargs=kwargs
        )

        self.tasks[task_id] = task

        logger.info(f"Created background task: {task_id} ({task_type})")

        return task_id

    async def execute_task(self, task_id: str) -> None:
        """
        Execute a background task.

        Args:
            task_id: Task identifier
        """
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return

        task = self.tasks[task_id]

        try:
            # Update status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            logger.info(f"Executing task: {task_id}")

            # Execute function
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = await asyncio.to_thread(task.func, *task.args, **task.kwargs)

            # Update status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.progress = 1.0

            duration = (task.completed_at - task.started_at).total_seconds()
            logger.info(f"Task completed: {task_id} in {duration:.2f}s")

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.warning(f"Task cancelled: {task_id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)

            logger.error(f"Task failed: {task_id} - {str(e)}", exc_info=True)

        finally:
            # Remove from running tasks
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def submit_task(
        self, task_type: str, func: Callable, args: tuple = (), kwargs: dict = None
    ) -> str:
        """
        Submit a task for background execution.

        Args:
            task_type: Type of task
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            str: Task ID
        """
        # Create task
        task_id = self.create_task(task_type, func, args, kwargs)

        # Start execution
        asyncio_task = asyncio.create_task(self.execute_task(task_id))
        self.running_tasks[task_id] = asyncio_task

        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Task status dictionary or None if not found
        """
        if task_id not in self.tasks:
            return None

        return self.tasks[task_id].to_dict()

    def update_task_progress(
        self, task_id: str, progress: float, metadata: Dict[str, Any] = None
    ) -> None:
        """
        Update task progress.

        Args:
            task_id: Task identifier
            progress: Progress value (0.0 to 1.0)
            metadata: Optional metadata to update
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task.progress = max(0.0, min(1.0, progress))

        if metadata:
            task.metadata.update(metadata)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: Task identifier

        Returns:
            bool: True if cancelled, False otherwise
        """
        if task_id not in self.running_tasks:
            return False

        asyncio_task = self.running_tasks[task_id]
        asyncio_task.cancel()

        logger.info(f"Cancelled task: {task_id}")

        return True

    def cleanup_old_tasks(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old completed tasks.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            int: Number of tasks cleaned up
        """
        now = datetime.now()
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.status in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ]:
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old tasks")

        return len(to_remove)

    def get_all_tasks(
        self, status: Optional[TaskStatus] = None
    ) -> list[Dict[str, Any]]:
        """
        Get all tasks, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of task dictionaries
        """
        tasks = []

        for task in self.tasks.values():
            if status is None or task.status == status:
                tasks.append(task.to_dict())

        return tasks

    def get_stats(self) -> Dict[str, Any]:
        """
        Get task manager statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "by_status": {},
        }

        for status in TaskStatus:
            count = sum(1 for task in self.tasks.values() if task.status == status)
            stats["by_status"][status.value] = count

        return stats


# Global task manager instance
_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Get or create global task manager instance."""
    global _task_manager

    if _task_manager is None:
        _task_manager = BackgroundTaskManager(max_concurrent_tasks=5)

    return _task_manager


def cleanup_task_manager() -> None:
    """Cleanup global task manager."""
    global _task_manager
    _task_manager = None
