"""
A2A Protocol API Endpoints.

Google A2A 프로토콜을 통한 외부 에이전트 연동 API.
"""

import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try to import A2A models and services
try:
    from models.a2a import (
        # Core types
        AgentCard,
        Message,
        Task,
        TaskState,
        TaskStatus,
        Part,
        Role,
        Artifact,
        StreamResponse,
        TaskStatusUpdateEvent,
        TaskArtifactUpdateEvent,
        # Request/Response
        SendMessageRequest,
        SendMessageResponse,
        ListTasksResponse,
        # Configuration
        A2AAgentConfig,
        A2AAgentConfigCreate,
        A2AAgentConfigUpdate,
        A2AAgentConfigResponse,
        A2AAgentListResponse,
        A2AServerConfig,
        A2AServerConfigCreate,
        A2AServerConfigUpdate,
        A2AServerConfigResponse,
        A2AServerListResponse,
        AgentSkill,
    )
    logger.info("A2A models imported successfully")
except Exception as e:
    logger.error(f"Failed to import A2A models: {e}")
    raise

try:
    from services.a2a import A2AClient, A2AServer, A2AAgentRegistry
    from services.a2a.registry import get_a2a_registry
    from services.a2a.client import create_text_message, A2AClientError
    from services.a2a.server import A2AServerError, TaskNotFoundError
    logger.info("A2A services imported successfully")
except Exception as e:
    logger.error(f"Failed to import A2A services: {e}")
    raise

router = APIRouter(prefix="/a2a", tags=["A2A Protocol"])


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def health_check():
    """A2A 서비스 상태 확인."""
    return {"status": "ok", "service": "A2A Protocol"}


# =============================================================================
# Dependencies
# =============================================================================

def get_registry() -> A2AAgentRegistry:
    """Get A2A registry dependency."""
    return get_a2a_registry()


def get_current_user_id(request: Request) -> str:
    """Get current user ID from request."""
    # TODO: Integrate with actual auth system
    user_id = request.headers.get("X-User-ID", "default-user")
    return user_id


# =============================================================================
# External Agent Configuration (Client)
# =============================================================================

@router.post("/agents", response_model=A2AAgentConfigResponse)
async def create_agent_config(
    config: A2AAgentConfigCreate,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """
    외부 A2A 에이전트 연결 설정을 생성합니다.
    
    - **name**: 표시 이름
    - **agent_card_url**: Agent Card를 가져올 URL
    - **auth_type**: 인증 방식 (none, api_key, bearer, oauth2)
    """
    try:
        return await registry.create_agent_config(user_id, config)
    except Exception as e:
        logger.exception("Failed to create agent config")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=A2AAgentListResponse)
async def list_agent_configs(
    enabled_only: bool = Query(False, description="활성화된 에이전트만 조회"),
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트 연결 설정 목록을 조회합니다."""
    configs = await registry.list_agent_configs(user_id, enabled_only)
    return A2AAgentListResponse(agents=configs, total=len(configs))


@router.get("/agents/{config_id}", response_model=A2AAgentConfigResponse)
async def get_agent_config(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트 연결 설정을 조회합니다."""
    config = await registry.get_agent_config(user_id, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return config


@router.patch("/agents/{config_id}", response_model=A2AAgentConfigResponse)
async def update_agent_config(
    config_id: str,
    update: A2AAgentConfigUpdate,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트 연결 설정을 수정합니다."""
    config = await registry.update_agent_config(user_id, config_id, update)
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return config


@router.delete("/agents/{config_id}")
async def delete_agent_config(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트 연결 설정을 삭제합니다."""
    await registry.delete_agent_config(user_id, config_id)
    return {"success": True}


@router.post("/agents/{config_id}/test", response_model=A2AAgentConfigResponse)
async def test_agent_connection(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트 연결을 테스트합니다."""
    try:
        return await registry.test_agent_connection(user_id, config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/agents/{config_id}/card", response_model=AgentCard)
async def get_agent_card(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트의 Agent Card를 조회합니다."""
    config = await registry.get_agent_config(user_id, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
        
    if not config.agent_card:
        raise HTTPException(status_code=404, detail="Agent card not available")
        
    return config.agent_card


# =============================================================================
# External Agent Communication (Client)
# =============================================================================

class SendMessageToAgentRequest(BaseModel):
    """Request to send message to external agent."""
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    context_id: Optional[str] = None
    blocking: bool = False


@router.post("/agents/{config_id}/message", response_model=SendMessageResponse)
async def send_message_to_agent(
    config_id: str,
    request: SendMessageToAgentRequest,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트에 메시지를 전송합니다."""
    try:
        client = await registry.get_client(user_id, config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    # Create message
    if request.text:
        message = create_text_message(
            request.text,
            context_id=request.context_id,
        )
    elif request.data:
        from services.a2a.client import create_data_message
        message = create_data_message(
            request.data,
            context_id=request.context_id,
        )
    else:
        raise HTTPException(status_code=400, detail="Either text or data is required")
        
    try:
        async with client:
            from models.a2a import SendMessageConfiguration
            config = SendMessageConfiguration(blocking=request.blocking)
            return await client.send_message(message, configuration=config)
    except A2AClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/agents/{config_id}/message/stream")
async def send_message_to_agent_streaming(
    config_id: str,
    request: SendMessageToAgentRequest,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트에 메시지를 전송하고 스트리밍 응답을 받습니다."""
    try:
        client = await registry.get_client(user_id, config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    # Create message
    if request.text:
        message = create_text_message(
            request.text,
            context_id=request.context_id,
        )
    elif request.data:
        from services.a2a.client import create_data_message
        message = create_data_message(
            request.data,
            context_id=request.context_id,
        )
    else:
        raise HTTPException(status_code=400, detail="Either text or data is required")
        
    async def generate():
        try:
            async with client:
                async for response in client.send_message_streaming(message):
                    yield f"data: {response.model_dump_json(by_alias=True)}\n\n"
            yield "data: [DONE]\n\n"
        except A2AClientError as e:
            error_data = {"error": str(e), "code": e.code}
            yield f"data: {json.dumps(error_data)}\n\n"
            
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/agents/{config_id}/tasks/{task_id}", response_model=Task)
async def get_agent_task(
    config_id: str,
    task_id: str,
    history_length: Optional[int] = Query(None),
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트의 태스크 상태를 조회합니다."""
    try:
        client = await registry.get_client(user_id, config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    try:
        async with client:
            return await client.get_task(task_id, history_length)
    except A2AClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/agents/{config_id}/tasks/{task_id}/cancel", response_model=Task)
async def cancel_agent_task(
    config_id: str,
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """외부 A2A 에이전트의 태스크를 취소합니다."""
    try:
        client = await registry.get_client(user_id, config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    try:
        async with client:
            return await client.cancel_task(task_id)
    except A2AClientError as e:
        raise HTTPException(status_code=502, detail=str(e))


# =============================================================================
# Local Agent A2A Server Configuration
# =============================================================================

@router.post("/servers", response_model=A2AServerConfigResponse)
async def create_server_config(
    config: A2AServerConfigCreate,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """
    로컬 에이전트를 A2A 서버로 노출하는 설정을 생성합니다.
    
    - **agent_id** 또는 **workflow_id**: 노출할 로컬 에이전트/워크플로우
    - **name**: A2A 에이전트 이름
    - **skills**: 노출할 스킬 목록
    """
    try:
        return await registry.create_server_config(user_id, config)
    except Exception as e:
        logger.exception("Failed to create server config")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers", response_model=A2AServerListResponse)
async def list_server_configs(
    enabled_only: bool = Query(False),
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버 설정 목록을 조회합니다."""
    configs = await registry.list_server_configs(user_id, enabled_only)
    return A2AServerListResponse(servers=configs, total=len(configs))


@router.get("/servers/{config_id}", response_model=A2AServerConfigResponse)
async def get_server_config(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버 설정을 조회합니다."""
    config = await registry.get_server_config(user_id, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Server configuration not found")
    return config


@router.patch("/servers/{config_id}", response_model=A2AServerConfigResponse)
async def update_server_config(
    config_id: str,
    update: A2AServerConfigUpdate,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버 설정을 수정합니다."""
    config = await registry.update_server_config(user_id, config_id, update)
    if not config:
        raise HTTPException(status_code=404, detail="Server configuration not found")
    return config


@router.delete("/servers/{config_id}")
async def delete_server_config(
    config_id: str,
    user_id: str = Depends(get_current_user_id),
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버 설정을 삭제합니다."""
    await registry.delete_server_config(user_id, config_id)
    return {"success": True}


# =============================================================================
# A2A Server Endpoints (Public - for external agents to call)
# =============================================================================

# In-memory server instances
_servers: Dict[str, A2AServer] = {}


def get_or_create_server(config: A2AServerConfig, base_url: str) -> A2AServer:
    """Get or create A2A server instance."""
    if config.id not in _servers:
        _servers[config.id] = A2AServer(config, base_url)
    return _servers[config.id]


@router.get("/servers/{config_id}/.well-known/agent-card.json", response_model=AgentCard)
async def get_server_agent_card(
    config_id: str,
    request: Request,
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버의 Agent Card를 반환합니다. (공개 엔드포인트)"""
    config = await registry.get_server_config_by_id(config_id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail="Server not found")
        
    base_url = str(request.base_url).rstrip("/")
    server = get_or_create_server(config, base_url)
    
    return server.get_agent_card()


@router.post("/servers/{config_id}/v1/message:send")
async def server_send_message(
    config_id: str,
    request: Request,
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버로 메시지를 전송합니다. (HTTP+JSON 바인딩)"""
    config = await registry.get_server_config_by_id(config_id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail="Server not found")
        
    base_url = str(request.base_url).rstrip("/")
    server = get_or_create_server(config, base_url)
    
    # TODO: Implement handler that connects to local agent/workflow
    if not server._handler:
        _setup_default_handler(server, config)
        
    try:
        body = await request.json()
        send_request = SendMessageRequest(**body)
        
        # Get user from auth header if required
        user_id = None
        if config.require_auth:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                raise HTTPException(status_code=401, detail="Authentication required")
            # TODO: Validate token
            user_id = "authenticated-user"
            
        response = await server.handle_send_message(send_request, user_id)
        return response.model_dump(by_alias=True, exclude_none=True)
        
    except A2AServerError as e:
        return JSONResponse(
            status_code=e.http_status,
            content={
                "error": {
                    "code": e.code,
                    "message": str(e),
                    "details": e.details,
                }
            }
        )


@router.post("/servers/{config_id}/v1/message:stream")
async def server_send_message_streaming(
    config_id: str,
    request: Request,
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버로 메시지를 전송하고 스트리밍 응답을 받습니다."""
    config = await registry.get_server_config_by_id(config_id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail="Server not found")
        
    if not config.streaming_enabled:
        raise HTTPException(status_code=400, detail="Streaming not supported")
        
    base_url = str(request.base_url).rstrip("/")
    server = get_or_create_server(config, base_url)
    
    if not server._handler:
        _setup_default_handler(server, config)
        
    try:
        body = await request.json()
        send_request = SendMessageRequest(**body)
        
        user_id = None
        if config.require_auth:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                raise HTTPException(status_code=401, detail="Authentication required")
            user_id = "authenticated-user"
            
        async def generate():
            try:
                async for response in server.handle_send_message_streaming(
                    send_request, user_id
                ):
                    yield f"data: {response.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
                yield "data: [DONE]\n\n"
            except A2AServerError as e:
                error_data = {
                    "error": {
                        "code": e.code,
                        "message": str(e),
                    }
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except A2AServerError as e:
        return JSONResponse(
            status_code=e.http_status,
            content={"error": {"code": e.code, "message": str(e)}}
        )


@router.get("/servers/{config_id}/v1/tasks/{task_id}")
async def server_get_task(
    config_id: str,
    task_id: str,
    history_length: Optional[int] = Query(None, alias="historyLength"),
    request: Request = None,
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버의 태스크 상태를 조회합니다."""
    config = await registry.get_server_config_by_id(config_id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail="Server not found")
        
    base_url = str(request.base_url).rstrip("/")
    server = get_or_create_server(config, base_url)
    
    try:
        task = await server.get_task(task_id, history_length)
        return task.model_dump(by_alias=True, exclude_none=True)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/servers/{config_id}/v1/tasks")
async def server_list_tasks(
    config_id: str,
    context_id: Optional[str] = Query(None, alias="contextId"),
    status: Optional[str] = Query(None),
    page_size: int = Query(50, alias="pageSize", ge=1, le=100),
    page_token: Optional[str] = Query(None, alias="pageToken"),
    include_artifacts: bool = Query(False, alias="includeArtifacts"),
    request: Request = None,
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버의 태스크 목록을 조회합니다."""
    config = await registry.get_server_config_by_id(config_id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail="Server not found")
        
    base_url = str(request.base_url).rstrip("/")
    server = get_or_create_server(config, base_url)
    
    task_status = None
    if status:
        try:
            task_status = TaskState(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            
    result = await server.list_tasks(
        context_id=context_id,
        status=task_status,
        page_size=page_size,
        page_token=page_token,
        include_artifacts=include_artifacts,
    )
    
    # Convert tasks to dict
    result["tasks"] = [
        t.model_dump(by_alias=True, exclude_none=True) 
        for t in result["tasks"]
    ]
    
    return result


@router.post("/servers/{config_id}/v1/tasks/{task_id}:cancel")
async def server_cancel_task(
    config_id: str,
    task_id: str,
    request: Request,
    registry: A2AAgentRegistry = Depends(get_registry),
):
    """A2A 서버의 태스크를 취소합니다."""
    config = await registry.get_server_config_by_id(config_id)
    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail="Server not found")
        
    base_url = str(request.base_url).rstrip("/")
    server = get_or_create_server(config, base_url)
    
    try:
        task = await server.cancel_task(task_id)
        return task.model_dump(by_alias=True, exclude_none=True)
    except A2AServerError as e:
        return JSONResponse(
            status_code=e.http_status,
            content={"error": {"code": e.code, "message": str(e)}}
        )


def _setup_default_handler(server: A2AServer, config: A2AServerConfig):
    """Setup default handler for A2A server."""
    
    async def default_handler(message: Message, metadata: Dict[str, Any]):
        """Default handler that echoes the message."""
        # TODO: Connect to actual agent/workflow execution
        
        # Extract text from message
        text = ""
        for part in message.parts:
            if part.text:
                text += part.text
                
        # Yield working status
        yield StreamResponse(
            status_update=TaskStatusUpdateEvent(
                task_id="",  # Will be set by server
                context_id=message.context_id or "",
                status=TaskStatus(
                    state=TaskState.WORKING,
                    timestamp=datetime.utcnow(),
                ),
                final=False,
            )
        )
        
        # Simulate processing
        import asyncio
        await asyncio.sleep(0.5)
        
        # Yield artifact
        yield StreamResponse(
            artifact_update=TaskArtifactUpdateEvent(
                task_id="",
                context_id=message.context_id or "",
                artifact=Artifact(
                    artifact_id=str(uuid.uuid4()),
                    name="response",
                    parts=[Part(text=f"Echo: {text}")],
                ),
                last_chunk=True,
            )
        )
        
    server.set_handler(default_handler)
