"""
A2A Protocol Server.

로컬 에이전트를 A2A 프로토콜로 노출하기 위한 서버 구현.
"""

import asyncio
import json
import uuid
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List, Callable, Awaitable
from datetime import datetime
from collections import defaultdict

from models.a2a import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    AgentInterface,
    AgentProvider,
    Message,
    Task,
    TaskState,
    TaskStatus,
    Part,
    Role,
    Artifact,
    SendMessageRequest,
    SendMessageResponse,
    StreamResponse,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    A2AServerConfig,
    ProtocolBinding,
    PushNotificationConfig,
)

logger = logging.getLogger(__name__)


class A2AServerError(Exception):
    """A2A server error."""
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR",
        http_status: int = 500,
        details: Optional[Dict] = None
    ):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.details = details or {}


class TaskNotFoundError(A2AServerError):
    """Task not found error."""
    def __init__(self, task_id: str):
        super().__init__(
            f"Task not found: {task_id}",
            code="TASK_NOT_FOUND",
            http_status=404,
            details={"task_id": task_id}
        )


class TaskNotCancelableError(A2AServerError):
    """Task not cancelable error."""
    def __init__(self, task_id: str, state: TaskState):
        super().__init__(
            f"Task {task_id} is not cancelable (state: {state.value})",
            code="TASK_NOT_CANCELABLE",
            http_status=409,
            details={"task_id": task_id, "state": state.value}
        )


# Type for task handler function
TaskHandler = Callable[[Message, Dict[str, Any]], Awaitable[AsyncGenerator[StreamResponse, None]]]


class A2AServer:
    """
    A2A Protocol Server.
    
    로컬 에이전트/워크플로우를 A2A 프로토콜로 노출합니다.
    """
    
    def __init__(
        self,
        config: A2AServerConfig,
        base_url: str,
        handler: Optional[TaskHandler] = None,
    ):
        """
        Initialize A2A server.
        
        Args:
            config: Server configuration
            base_url: Base URL for this server
            handler: Task handler function
        """
        self.config = config
        self.base_url = base_url.rstrip("/")
        self._handler = handler
        
        # In-memory task storage (should be replaced with persistent storage)
        self._tasks: Dict[str, Task] = {}
        self._task_subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._contexts: Dict[str, List[str]] = defaultdict(list)  # context_id -> task_ids
        
    def set_handler(self, handler: TaskHandler):
        """Set task handler function."""
        self._handler = handler
        
    def get_agent_card(self) -> AgentCard:
        """
        Generate Agent Card for this server.
        
        Returns:
            AgentCard: Server's capabilities and metadata
        """
        interfaces = [
            AgentInterface(
                url=f"{self.base_url}/a2a/v1",
                protocol_binding=ProtocolBinding.HTTP_JSON,
            )
        ]
        
        capabilities = AgentCapabilities(
            streaming=self.config.streaming_enabled,
            push_notifications=self.config.push_notifications_enabled,
            state_transition_history=True,
        )
        
        # Default input/output modes
        default_input_modes = ["text/plain", "application/json"]
        default_output_modes = ["text/plain", "application/json"]
        
        # Build security schemes if auth required
        security_schemes = None
        security = None
        if self.config.require_auth:
            from models.a2a import SecurityScheme, HTTPAuthSecurityScheme
            security_schemes = {
                "bearer": SecurityScheme(
                    http_auth=HTTPAuthSecurityScheme(
                        scheme="Bearer",
                        description="Bearer token authentication"
                    )
                )
            }
            security = [{"bearer": []}]
            
        return AgentCard(
            protocol_version="1.0",
            name=self.config.name,
            description=self.config.description,
            supported_interfaces=interfaces,
            version=self.config.version,
            capabilities=capabilities,
            default_input_modes=default_input_modes,
            default_output_modes=default_output_modes,
            skills=self.config.skills or [],
            security_schemes=security_schemes,
            security=security,
            documentation_url=f"{self.base_url}/docs",
        )
        
    async def handle_send_message(
        self,
        request: SendMessageRequest,
        user_id: Optional[str] = None,
    ) -> SendMessageResponse:
        """
        Handle SendMessage request.
        
        Args:
            request: Send message request
            user_id: Authenticated user ID
            
        Returns:
            SendMessageResponse: Task or message response
        """
        if not self._handler:
            raise A2AServerError(
                "No handler configured",
                code="HANDLER_NOT_CONFIGURED",
                http_status=500
            )
            
        message = request.message
        
        # Create or get context
        context_id = message.context_id or str(uuid.uuid4())
        
        # Create task
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp=datetime.utcnow(),
            ),
            history=[message],
        )
        
        self._tasks[task_id] = task
        self._contexts[context_id].append(task_id)
        
        # Check if blocking mode
        blocking = request.configuration and request.configuration.blocking
        
        if blocking:
            # Execute synchronously and wait for completion
            await self._execute_task(task, message, request.metadata or {})
            return SendMessageResponse(task=self._tasks[task_id])
        else:
            # Start async execution
            asyncio.create_task(
                self._execute_task(task, message, request.metadata or {})
            )
            return SendMessageResponse(task=task)
            
    async def handle_send_message_streaming(
        self,
        request: SendMessageRequest,
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Handle SendStreamingMessage request.
        
        Args:
            request: Send message request
            user_id: Authenticated user ID
            
        Yields:
            StreamResponse: Streaming updates
        """
        if not self._handler:
            raise A2AServerError(
                "No handler configured",
                code="HANDLER_NOT_CONFIGURED",
                http_status=500
            )
            
        message = request.message
        context_id = message.context_id or str(uuid.uuid4())
        
        # Create task
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp=datetime.utcnow(),
            ),
            history=[message],
        )
        
        self._tasks[task_id] = task
        self._contexts[context_id].append(task_id)
        
        # Yield initial task
        yield StreamResponse(task=task)
        
        # Execute and stream updates
        try:
            async for response in self._handler(message, request.metadata or {}):
                # Update task state based on response
                if response.status_update:
                    task.status = response.status_update.status
                    self._tasks[task_id] = task
                    
                if response.artifact_update:
                    if task.artifacts is None:
                        task.artifacts = []
                    # Find or add artifact
                    artifact_id = response.artifact_update.artifact.artifact_id
                    existing = next(
                        (a for a in task.artifacts if a.artifact_id == artifact_id),
                        None
                    )
                    if existing and response.artifact_update.append:
                        # Append to existing artifact
                        existing.parts.extend(response.artifact_update.artifact.parts)
                    else:
                        task.artifacts.append(response.artifact_update.artifact)
                    self._tasks[task_id] = task
                    
                yield response
                
                # Notify subscribers
                await self._notify_subscribers(task_id, response)
                
            # Mark as completed if not already terminal
            if task.status.state not in [
                TaskState.COMPLETED, TaskState.FAILED, 
                TaskState.CANCELLED, TaskState.REJECTED
            ]:
                task.status = TaskStatus(
                    state=TaskState.COMPLETED,
                    timestamp=datetime.utcnow(),
                )
                self._tasks[task_id] = task
                
                final_update = StreamResponse(
                    status_update=TaskStatusUpdateEvent(
                        task_id=task_id,
                        context_id=context_id,
                        status=task.status,
                        final=True,
                    )
                )
                yield final_update
                await self._notify_subscribers(task_id, final_update)
                
        except Exception as e:
            logger.exception(f"Task execution failed: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    message_id=str(uuid.uuid4()),
                    role=Role.AGENT,
                    parts=[Part(text=str(e))],
                ),
                timestamp=datetime.utcnow(),
            )
            self._tasks[task_id] = task
            
            error_update = StreamResponse(
                status_update=TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=task.status,
                    final=True,
                )
            )
            yield error_update
            await self._notify_subscribers(task_id, error_update)
            
    async def _execute_task(
        self,
        task: Task,
        message: Message,
        metadata: Dict[str, Any],
    ):
        """Execute task asynchronously."""
        task_id = task.id
        context_id = task.context_id
        
        try:
            # Update to working state
            task.status = TaskStatus(
                state=TaskState.WORKING,
                timestamp=datetime.utcnow(),
            )
            self._tasks[task_id] = task
            
            async for response in self._handler(message, metadata):
                if response.status_update:
                    task.status = response.status_update.status
                    self._tasks[task_id] = task
                    
                if response.artifact_update:
                    if task.artifacts is None:
                        task.artifacts = []
                    artifact_id = response.artifact_update.artifact.artifact_id
                    existing = next(
                        (a for a in task.artifacts if a.artifact_id == artifact_id),
                        None
                    )
                    if existing and response.artifact_update.append:
                        existing.parts.extend(response.artifact_update.artifact.parts)
                    else:
                        task.artifacts.append(response.artifact_update.artifact)
                    self._tasks[task_id] = task
                    
                await self._notify_subscribers(task_id, response)
                
            # Mark completed
            if task.status.state not in [
                TaskState.COMPLETED, TaskState.FAILED,
                TaskState.CANCELLED, TaskState.REJECTED
            ]:
                task.status = TaskStatus(
                    state=TaskState.COMPLETED,
                    timestamp=datetime.utcnow(),
                )
                self._tasks[task_id] = task
                
        except Exception as e:
            logger.exception(f"Task execution failed: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    message_id=str(uuid.uuid4()),
                    role=Role.AGENT,
                    parts=[Part(text=str(e))],
                ),
                timestamp=datetime.utcnow(),
            )
            self._tasks[task_id] = task
            
    async def _notify_subscribers(self, task_id: str, response: StreamResponse):
        """Notify task subscribers."""
        for queue in self._task_subscribers.get(task_id, []):
            try:
                await queue.put(response)
            except Exception as e:
                logger.warning(f"Failed to notify subscriber: {e}")
                
    async def get_task(
        self,
        task_id: str,
        history_length: Optional[int] = None,
    ) -> Task:
        """
        Get task by ID.
        
        Args:
            task_id: Task identifier
            history_length: Optional history limit
            
        Returns:
            Task: Task details
        """
        task = self._tasks.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
            
        # Apply history length limit
        if history_length is not None and task.history:
            task = task.model_copy()
            task.history = task.history[-history_length:]
            
        return task
        
    async def list_tasks(
        self,
        context_id: Optional[str] = None,
        status: Optional[TaskState] = None,
        page_size: int = 50,
        page_token: Optional[str] = None,
        include_artifacts: bool = False,
    ) -> Dict[str, Any]:
        """
        List tasks with filtering.
        
        Args:
            context_id: Filter by context
            status: Filter by status
            page_size: Page size
            page_token: Pagination token
            include_artifacts: Include artifacts in response
            
        Returns:
            Dict with tasks and pagination info
        """
        # Get all tasks
        tasks = list(self._tasks.values())
        
        # Filter by context
        if context_id:
            tasks = [t for t in tasks if t.context_id == context_id]
            
        # Filter by status
        if status:
            tasks = [t for t in tasks if t.status.state == status]
            
        # Sort by timestamp (newest first)
        tasks.sort(
            key=lambda t: t.status.timestamp or datetime.min,
            reverse=True
        )
        
        # Pagination
        start_idx = 0
        if page_token:
            try:
                start_idx = int(page_token)
            except ValueError:
                pass
                
        total = len(tasks)
        tasks = tasks[start_idx:start_idx + page_size]
        
        # Remove artifacts if not requested
        if not include_artifacts:
            tasks = [
                t.model_copy(update={"artifacts": None})
                for t in tasks
            ]
            
        next_token = ""
        if start_idx + page_size < total:
            next_token = str(start_idx + page_size)
            
        return {
            "tasks": tasks,
            "nextPageToken": next_token,
            "pageSize": page_size,
            "totalSize": total,
        }
        
    async def cancel_task(self, task_id: str) -> Task:
        """
        Cancel a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task: Updated task
        """
        task = self._tasks.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
            
        # Check if cancelable
        terminal_states = [
            TaskState.COMPLETED, TaskState.FAILED,
            TaskState.CANCELLED, TaskState.REJECTED
        ]
        if task.status.state in terminal_states:
            raise TaskNotCancelableError(task_id, task.status.state)
            
        # Update status
        task.status = TaskStatus(
            state=TaskState.CANCELLED,
            timestamp=datetime.utcnow(),
        )
        self._tasks[task_id] = task
        
        # Notify subscribers
        await self._notify_subscribers(
            task_id,
            StreamResponse(
                status_update=TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=task.context_id,
                    status=task.status,
                    final=True,
                )
            )
        )
        
        return task
        
    async def subscribe_to_task(
        self,
        task_id: str,
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Subscribe to task updates.
        
        Args:
            task_id: Task identifier
            
        Yields:
            StreamResponse: Task updates
        """
        task = self._tasks.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
            
        # Check if task is in terminal state
        terminal_states = [
            TaskState.COMPLETED, TaskState.FAILED,
            TaskState.CANCELLED, TaskState.REJECTED
        ]
        if task.status.state in terminal_states:
            raise A2AServerError(
                f"Cannot subscribe to task in terminal state: {task.status.state.value}",
                code="UNSUPPORTED_OPERATION",
                http_status=400
            )
            
        # Yield current task state
        yield StreamResponse(task=task)
        
        # Create subscription queue
        queue: asyncio.Queue[StreamResponse] = asyncio.Queue()
        self._task_subscribers[task_id].append(queue)
        
        try:
            while True:
                response = await queue.get()
                yield response
                
                # Check if final
                if response.status_update and response.status_update.final:
                    break
                    
        finally:
            # Remove subscription
            self._task_subscribers[task_id].remove(queue)
            if not self._task_subscribers[task_id]:
                del self._task_subscribers[task_id]
