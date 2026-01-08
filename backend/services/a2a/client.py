"""
A2A Protocol Client.

외부 A2A 에이전트와 통신하기 위한 클라이언트 구현.
"""

import asyncio
import json
import uuid
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime

import httpx

from models.a2a import (
    AgentCard,
    Message,
    Task,
    TaskState,
    TaskStatus,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageConfiguration,
    StreamResponse,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    A2AAgentConfig,
    ProtocolBinding,
    ListTasksRequest,
    ListTasksResponse,
)

logger = logging.getLogger(__name__)


class A2AClientError(Exception):
    """A2A client error."""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class A2AClient:
    """
    A2A Protocol Client.
    
    외부 A2A 에이전트와 통신하기 위한 클라이언트입니다.
    HTTP+JSON, JSON-RPC 바인딩을 지원합니다.
    """
    
    def __init__(self, config: A2AAgentConfig):
        """
        Initialize A2A client.
        
        Args:
            config: A2A agent configuration
        """
        self.config = config
        self._agent_card: Optional[AgentCard] = config.cached_agent_card
        self._http_client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        await self._ensure_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._http_client is None:
            headers = {"Content-Type": "application/json"}
            
            # Add authentication headers
            if self.config.auth_type == "api_key" and self.config.auth_config:
                api_key = self.config.auth_config.get("api_key", "")
                header_name = self.config.auth_config.get("header_name", "X-API-Key")
                headers[header_name] = api_key
            elif self.config.auth_type == "bearer" and self.config.auth_config:
                token = self.config.auth_config.get("token", "")
                headers["Authorization"] = f"Bearer {token}"
                
            # Add custom headers
            if self.config.headers:
                headers.update(self.config.headers)
                
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout_seconds),
                headers=headers,
            )
            
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            
    async def fetch_agent_card(self) -> AgentCard:
        """
        Fetch Agent Card from remote agent.
        
        Returns:
            AgentCard: Remote agent's capabilities and metadata
        """
        await self._ensure_client()
        
        try:
            response = await self._http_client.get(self.config.agent_card_url)
            response.raise_for_status()
            
            data = response.json()
            self._agent_card = AgentCard(**data)
            return self._agent_card
            
        except httpx.HTTPStatusError as e:
            raise A2AClientError(
                f"Failed to fetch agent card: {e.response.status_code}",
                code="AGENT_CARD_FETCH_ERROR",
                details={"status_code": e.response.status_code}
            )
        except Exception as e:
            raise A2AClientError(
                f"Failed to fetch agent card: {str(e)}",
                code="AGENT_CARD_FETCH_ERROR"
            )
            
    @property
    def agent_card(self) -> Optional[AgentCard]:
        """Get cached agent card."""
        return self._agent_card
        
    def _get_base_url(self) -> str:
        """Get base URL for API calls."""
        if self.config.base_url:
            return self.config.base_url.rstrip("/")
            
        if self._agent_card and self._agent_card.supported_interfaces:
            # Find matching interface
            for interface in self._agent_card.supported_interfaces:
                if interface.protocol_binding == self.config.protocol_binding:
                    return interface.url.rstrip("/")
            # Fallback to first interface
            return self._agent_card.supported_interfaces[0].url.rstrip("/")
            
        # Derive from agent card URL
        return self.config.agent_card_url.rsplit("/", 1)[0]
        
    async def send_message(
        self,
        message: Message,
        configuration: Optional[SendMessageConfiguration] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendMessageResponse:
        """
        Send a message to the remote agent.
        
        Args:
            message: Message to send
            configuration: Optional request configuration
            metadata: Optional metadata
            
        Returns:
            SendMessageResponse: Task or direct message response
        """
        await self._ensure_client()
        
        base_url = self._get_base_url()
        
        request = SendMessageRequest(
            message=message,
            configuration=configuration,
            metadata=metadata,
        )
        
        if self.config.protocol_binding == ProtocolBinding.HTTP_JSON:
            # HTTP+JSON binding
            url = f"{base_url}/v1/message:send"
            response = await self._http_client.post(
                url,
                json=request.model_dump(by_alias=True, exclude_none=True),
            )
            
        else:
            # JSON-RPC binding
            url = base_url
            rpc_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "SendMessage",
                "params": request.model_dump(by_alias=True, exclude_none=True),
            }
            response = await self._http_client.post(url, json=rpc_request)
            
        response.raise_for_status()
        data = response.json()
        
        # Handle JSON-RPC response
        if "result" in data:
            data = data["result"]
        elif "error" in data:
            error = data["error"]
            raise A2AClientError(
                error.get("message", "Unknown error"),
                code=str(error.get("code", "UNKNOWN")),
                details=error.get("data", {})
            )
            
        return SendMessageResponse(**data)
        
    async def send_message_streaming(
        self,
        message: Message,
        configuration: Optional[SendMessageConfiguration] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Send a message and receive streaming updates.
        
        Args:
            message: Message to send
            configuration: Optional request configuration
            metadata: Optional metadata
            
        Yields:
            StreamResponse: Streaming updates (task, status, artifacts)
        """
        await self._ensure_client()
        
        base_url = self._get_base_url()
        
        request = SendMessageRequest(
            message=message,
            configuration=configuration,
            metadata=metadata,
        )
        
        if self.config.protocol_binding == ProtocolBinding.HTTP_JSON:
            url = f"{base_url}/v1/message:stream"
            request_data = request.model_dump(by_alias=True, exclude_none=True)
        else:
            url = base_url
            request_data = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "SendStreamingMessage",
                "params": request.model_dump(by_alias=True, exclude_none=True),
            }
            
        async with self._http_client.stream(
            "POST",
            url,
            json=request_data,
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line:
                    continue
                    
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                        
                    try:
                        data = json.loads(data_str)
                        yield StreamResponse(**data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE data: {data_str}")
                        
    async def get_task(
        self,
        task_id: str,
        history_length: Optional[int] = None,
    ) -> Task:
        """
        Get task status and details.
        
        Args:
            task_id: Task identifier
            history_length: Optional history length limit
            
        Returns:
            Task: Task details
        """
        await self._ensure_client()
        
        base_url = self._get_base_url()
        
        if self.config.protocol_binding == ProtocolBinding.HTTP_JSON:
            url = f"{base_url}/v1/tasks/{task_id}"
            params = {}
            if history_length is not None:
                params["historyLength"] = history_length
                
            response = await self._http_client.get(url, params=params)
            
        else:
            url = base_url
            rpc_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "GetTask",
                "params": {
                    "name": f"tasks/{task_id}",
                    "historyLength": history_length,
                },
            }
            response = await self._http_client.post(url, json=rpc_request)
            
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            data = data["result"]
        elif "error" in data:
            error = data["error"]
            raise A2AClientError(
                error.get("message", "Unknown error"),
                code=str(error.get("code", "UNKNOWN")),
                details=error.get("data", {})
            )
            
        return Task(**data)
        
    async def list_tasks(
        self,
        context_id: Optional[str] = None,
        status: Optional[TaskState] = None,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> ListTasksResponse:
        """
        List tasks with optional filtering.
        
        Args:
            context_id: Filter by context
            status: Filter by status
            page_size: Page size
            page_token: Pagination token
            
        Returns:
            ListTasksResponse: List of tasks
        """
        await self._ensure_client()
        
        base_url = self._get_base_url()
        
        if self.config.protocol_binding == ProtocolBinding.HTTP_JSON:
            url = f"{base_url}/v1/tasks"
            params = {"pageSize": page_size}
            if context_id:
                params["contextId"] = context_id
            if status:
                params["status"] = status.value
            if page_token:
                params["pageToken"] = page_token
                
            response = await self._http_client.get(url, params=params)
            
        else:
            url = base_url
            rpc_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "ListTasks",
                "params": {
                    "contextId": context_id,
                    "status": status.value if status else None,
                    "pageSize": page_size,
                    "pageToken": page_token,
                },
            }
            response = await self._http_client.post(url, json=rpc_request)
            
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            data = data["result"]
        elif "error" in data:
            error = data["error"]
            raise A2AClientError(
                error.get("message", "Unknown error"),
                code=str(error.get("code", "UNKNOWN")),
                details=error.get("data", {})
            )
            
        return ListTasksResponse(**data)
        
    async def cancel_task(self, task_id: str) -> Task:
        """
        Cancel a running task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task: Updated task
        """
        await self._ensure_client()
        
        base_url = self._get_base_url()
        
        if self.config.protocol_binding == ProtocolBinding.HTTP_JSON:
            url = f"{base_url}/v1/tasks/{task_id}:cancel"
            response = await self._http_client.post(url)
            
        else:
            url = base_url
            rpc_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "CancelTask",
                "params": {"name": f"tasks/{task_id}"},
            }
            response = await self._http_client.post(url, json=rpc_request)
            
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            data = data["result"]
        elif "error" in data:
            error = data["error"]
            raise A2AClientError(
                error.get("message", "Unknown error"),
                code=str(error.get("code", "UNKNOWN")),
                details=error.get("data", {})
            )
            
        return Task(**data)
        
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
        await self._ensure_client()
        
        base_url = self._get_base_url()
        
        if self.config.protocol_binding == ProtocolBinding.HTTP_JSON:
            url = f"{base_url}/v1/tasks/{task_id}:subscribe"
            request_data = {}
        else:
            url = base_url
            request_data = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "SubscribeToTask",
                "params": {"name": f"tasks/{task_id}"},
            }
            
        async with self._http_client.stream(
            "POST",
            url,
            json=request_data,
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line:
                    continue
                    
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                        
                    try:
                        data = json.loads(data_str)
                        yield StreamResponse(**data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE data: {data_str}")


# Helper functions for creating messages
def create_text_message(
    text: str,
    role: Role = Role.USER,
    context_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> Message:
    """Create a simple text message."""
    return Message(
        message_id=str(uuid.uuid4()),
        context_id=context_id,
        task_id=task_id,
        role=role,
        parts=[Part(text=text)],
    )


def create_data_message(
    data: Dict[str, Any],
    role: Role = Role.USER,
    context_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> Message:
    """Create a structured data message."""
    from models.a2a import DataPart
    return Message(
        message_id=str(uuid.uuid4()),
        context_id=context_id,
        task_id=task_id,
        role=role,
        parts=[Part(data=DataPart(data=data))],
    )
