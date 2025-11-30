"""
Redis Queue - Lightweight Async Task Queue

Provides a simple but robust task queue using Redis:
- Async task execution
- Priority queues
- Task scheduling (delayed execution)
- Dead letter queue for failed tasks
- Task status tracking
- Worker management
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import traceback

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"  # Moved to dead letter queue


class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class Task:
    """Task definition."""
    id: str
    name: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = TaskPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    timeout: float = 300.0  # 5 minutes default
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, data: str) -> "Task":
        return cls.from_dict(json.loads(data))


class RedisQueue:
    """
    Redis-based task queue with priority support.
    
    Features:
    - Priority queues using sorted sets
    - Delayed task scheduling
    - Task status tracking
    - Dead letter queue
    - Automatic retries
    
    Usage:
        queue = RedisQueue(redis_client, "my_queue")
        
        # Register task handler
        @queue.task("process_document")
        async def process_document(doc_id: str):
            # Process document
            return {"status": "processed"}
        
        # Enqueue task
        task_id = await queue.enqueue(
            "process_document",
            args=(doc_id,),
            priority=TaskPriority.HIGH
        )
        
        # Start worker
        await queue.start_worker()
    """
    
    def __init__(
        self,
        redis: Redis,
        queue_name: str = "default",
        max_workers: int = 5,
        poll_interval: float = 1.0,
    ):
        self.redis = redis
        self.queue_name = queue_name
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        
        # Redis keys
        self.queue_key = f"rq:{queue_name}:queue"
        self.scheduled_key = f"rq:{queue_name}:scheduled"
        self.processing_key = f"rq:{queue_name}:processing"
        self.tasks_key = f"rq:{queue_name}:tasks"
        self.dlq_key = f"rq:{queue_name}:dlq"
        self.stats_key = f"rq:{queue_name}:stats"
        
        # Task handlers
        self._handlers: Dict[str, Callable] = {}
        
        # Worker state
        self._running = False
        self._workers: List[asyncio.Task] = []
    
    def task(self, name: str):
        """
        Decorator to register a task handler.
        
        Usage:
            @queue.task("send_email")
            async def send_email(to: str, subject: str, body: str):
                # Send email
                pass
        """
        def decorator(func: Callable):
            self._handlers[name] = func
            logger.info(f"Registered task handler: {name}")
            return func
        return decorator
    
    def register_handler(self, name: str, handler: Callable):
        """Register a task handler programmatically."""
        self._handlers[name] = handler
        logger.info(f"Registered task handler: {name}")
    
    async def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        delay: Optional[float] = None,
        max_retries: int = 3,
        timeout: float = 300.0,
        metadata: dict = None,
    ) -> str:
        """
        Enqueue a task for execution.
        
        Args:
            task_name: Name of the registered task handler
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            priority: Task priority
            delay: Delay in seconds before execution
            max_retries: Maximum retry attempts
            timeout: Task timeout in seconds
            metadata: Additional metadata
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=task_name,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            status=TaskStatus.QUEUED,
            metadata=metadata or {},
        )
        
        # Store task data
        await self.redis.hset(self.tasks_key, task_id, task.to_json())
        
        if delay:
            # Schedule for later
            execute_at = time.time() + delay
            task.scheduled_at = datetime.utcfromtimestamp(execute_at).isoformat()
            await self.redis.zadd(self.scheduled_key, {task_id: execute_at})
            logger.info(f"Scheduled task {task_id} ({task_name}) for {delay}s later")
        else:
            # Add to priority queue (higher score = higher priority)
            score = priority * 1000000000 - time.time()  # Priority + FIFO within priority
            await self.redis.zadd(self.queue_key, {task_id: score})
            logger.info(f"Enqueued task {task_id} ({task_name}) with priority {priority}")
        
        # Update stats
        await self.redis.hincrby(self.stats_key, "total_enqueued", 1)
        
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        data = await self.redis.hget(self.tasks_key, task_id)
        if data:
            return Task.from_json(data)
        return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and result."""
        task = await self.get_task(task_id)
        if task:
            return {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "retry_count": task.retry_count,
            }
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        if task.status not in (TaskStatus.PENDING, TaskStatus.QUEUED):
            return False
        
        # Remove from queues
        await self.redis.zrem(self.queue_key, task_id)
        await self.redis.zrem(self.scheduled_key, task_id)
        
        # Update status
        task.status = TaskStatus.FAILED
        task.error = "Cancelled"
        task.completed_at = datetime.utcnow().isoformat()
        await self.redis.hset(self.tasks_key, task_id, task.to_json())
        
        logger.info(f"Cancelled task {task_id}")
        return True
    
    async def _process_scheduled_tasks(self):
        """Move scheduled tasks to the main queue when ready."""
        now = time.time()
        
        # Get tasks ready for execution
        ready_tasks = await self.redis.zrangebyscore(
            self.scheduled_key, 0, now
        )
        
        for task_id in ready_tasks:
            task_id = task_id.decode() if isinstance(task_id, bytes) else task_id
            task = await self.get_task(task_id)
            
            if task:
                # Move to main queue
                score = task.priority * 1000000000 - time.time()
                await self.redis.zadd(self.queue_key, {task_id: score})
                await self.redis.zrem(self.scheduled_key, task_id)
                logger.debug(f"Moved scheduled task {task_id} to main queue")
    
    async def _get_next_task(self) -> Optional[Task]:
        """Get the next task from the queue."""
        # Get highest priority task
        result = await self.redis.zpopmax(self.queue_key)
        
        if not result:
            return None
        
        task_id = result[0][0]
        task_id = task_id.decode() if isinstance(task_id, bytes) else task_id
        
        task = await self.get_task(task_id)
        if task:
            # Mark as processing
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow().isoformat()
            await self.redis.hset(self.tasks_key, task_id, task.to_json())
            await self.redis.sadd(self.processing_key, task_id)
        
        return task
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a single task."""
        handler = self._handlers.get(task.name)
        
        if not handler:
            logger.error(f"No handler registered for task: {task.name}")
            task.status = TaskStatus.FAILED
            task.error = f"No handler registered for task: {task.name}"
            task.completed_at = datetime.utcnow().isoformat()
            await self.redis.hset(self.tasks_key, task.id, task.to_json())
            await self.redis.srem(self.processing_key, task.id)
            return
        
        try:
            # Execute with timeout
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(
                    handler(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: handler(*task.args, **task.kwargs)
                    ),
                    timeout=task.timeout
                )
            
            # Success
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow().isoformat()
            
            logger.info(f"Task {task.id} ({task.name}) completed successfully")
            await self.redis.hincrby(self.stats_key, "total_completed", 1)
            
        except asyncio.TimeoutError:
            await self._handle_task_failure(
                task, "Task timed out", None
            )
            
        except Exception as e:
            await self._handle_task_failure(
                task, str(e), traceback.format_exc()
            )
        
        finally:
            # Update task and remove from processing
            await self.redis.hset(self.tasks_key, task.id, task.to_json())
            await self.redis.srem(self.processing_key, task.id)
    
    async def _handle_task_failure(
        self,
        task: Task,
        error: str,
        tb: Optional[str],
    ):
        """Handle task failure with retry logic."""
        task.retry_count += 1
        task.error = error
        task.traceback = tb
        
        if task.retry_count <= task.max_retries:
            # Retry with exponential backoff
            delay = min(2 ** task.retry_count, 300)  # Max 5 minutes
            task.status = TaskStatus.RETRYING
            
            logger.warning(
                f"Task {task.id} ({task.name}) failed, "
                f"retry {task.retry_count}/{task.max_retries} in {delay}s: {error}"
            )
            
            # Re-schedule
            execute_at = time.time() + delay
            await self.redis.zadd(self.scheduled_key, {task.id: execute_at})
            await self.redis.hincrby(self.stats_key, "total_retries", 1)
            
        else:
            # Move to dead letter queue
            task.status = TaskStatus.DEAD
            task.completed_at = datetime.utcnow().isoformat()
            
            logger.error(
                f"Task {task.id} ({task.name}) moved to DLQ "
                f"after {task.max_retries} retries: {error}"
            )
            
            await self.redis.lpush(self.dlq_key, task.id)
            await self.redis.hincrby(self.stats_key, "total_failed", 1)
    
    async def _worker_loop(self, worker_id: int):
        """Worker loop for processing tasks."""
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Process scheduled tasks
                await self._process_scheduled_tasks()
                
                # Get next task
                task = await self._get_next_task()
                
                if task:
                    logger.debug(f"Worker {worker_id} processing task {task.id}")
                    await self._execute_task(task)
                else:
                    # No tasks, wait before polling again
                    await asyncio.sleep(self.poll_interval)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start_worker(self, num_workers: Optional[int] = None):
        """Start worker processes."""
        if self._running:
            logger.warning("Workers already running")
            return
        
        self._running = True
        num = num_workers or self.max_workers
        
        for i in range(num):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)
        
        logger.info(f"Started {num} workers for queue '{self.queue_name}'")
    
    async def stop_worker(self, timeout: float = 30.0):
        """Stop all workers gracefully."""
        if not self._running:
            return
        
        logger.info("Stopping workers...")
        self._running = False
        
        # Wait for workers to finish
        if self._workers:
            done, pending = await asyncio.wait(
                self._workers,
                timeout=timeout,
            )
            
            # Cancel any remaining workers
            for task in pending:
                task.cancel()
            
            self._workers.clear()
        
        logger.info("All workers stopped")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = await self.redis.hgetall(self.stats_key)
        
        # Decode bytes
        stats = {
            k.decode() if isinstance(k, bytes) else k: 
            int(v.decode() if isinstance(v, bytes) else v)
            for k, v in stats.items()
        }
        
        # Add current counts
        stats["queue_size"] = await self.redis.zcard(self.queue_key)
        stats["scheduled_size"] = await self.redis.zcard(self.scheduled_key)
        stats["processing_size"] = await self.redis.scard(self.processing_key)
        stats["dlq_size"] = await self.redis.llen(self.dlq_key)
        stats["workers_running"] = len(self._workers) if self._running else 0
        
        return stats
    
    async def get_dlq_tasks(self, limit: int = 100) -> List[Task]:
        """Get tasks from dead letter queue."""
        task_ids = await self.redis.lrange(self.dlq_key, 0, limit - 1)
        
        tasks = []
        for task_id in task_ids:
            task_id = task_id.decode() if isinstance(task_id, bytes) else task_id
            task = await self.get_task(task_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    async def retry_dlq_task(self, task_id: str) -> bool:
        """Retry a task from the dead letter queue."""
        task = await self.get_task(task_id)
        if not task or task.status != TaskStatus.DEAD:
            return False
        
        # Reset task
        task.status = TaskStatus.QUEUED
        task.retry_count = 0
        task.error = None
        task.traceback = None
        task.result = None
        task.started_at = None
        task.completed_at = None
        
        # Remove from DLQ and add to queue
        await self.redis.lrem(self.dlq_key, 1, task_id)
        score = task.priority * 1000000000 - time.time()
        await self.redis.zadd(self.queue_key, {task_id: score})
        await self.redis.hset(self.tasks_key, task_id, task.to_json())
        
        logger.info(f"Retried DLQ task {task_id}")
        return True
    
    async def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Clear completed tasks older than specified hours."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        cutoff_str = cutoff.isoformat()
        
        # Get all task IDs
        all_tasks = await self.redis.hgetall(self.tasks_key)
        
        deleted = 0
        for task_id, task_data in all_tasks.items():
            task_id = task_id.decode() if isinstance(task_id, bytes) else task_id
            task_data = task_data.decode() if isinstance(task_data, bytes) else task_data
            
            try:
                task = Task.from_json(task_data)
                if task.status == TaskStatus.COMPLETED and task.completed_at:
                    if task.completed_at < cutoff_str:
                        await self.redis.hdel(self.tasks_key, task_id)
                        deleted += 1
            except:
                pass
        
        logger.info(f"Cleared {deleted} completed tasks older than {older_than_hours}h")
        return deleted


# ============================================================================
# Global Queue Instance
# ============================================================================

_default_queue: Optional[RedisQueue] = None


async def get_default_queue(redis: Redis) -> RedisQueue:
    """Get or create the default queue."""
    global _default_queue
    if _default_queue is None:
        _default_queue = RedisQueue(redis, "default")
    return _default_queue


async def enqueue_task(
    redis: Redis,
    task_name: str,
    args: tuple = (),
    kwargs: dict = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    delay: Optional[float] = None,
    queue_name: str = "default",
) -> str:
    """
    Convenience function to enqueue a task.
    
    Usage:
        task_id = await enqueue_task(
            redis,
            "process_document",
            args=(doc_id,),
            priority=TaskPriority.HIGH
        )
    """
    queue = RedisQueue(redis, queue_name)
    return await queue.enqueue(
        task_name,
        args=args,
        kwargs=kwargs,
        priority=priority,
        delay=delay,
    )
