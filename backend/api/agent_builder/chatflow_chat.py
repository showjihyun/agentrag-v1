"""
Chatflow Chat API

REST and SSE endpoints for Chatflow conversations.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
# DDD Architecture
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
    ExecutionError,
)
from backend.services.agent_builder.chatflow_service import ChatflowService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/chatflow",
    tags=["chatflow-chat"],
)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    workflow_id: Optional[str] = Field(None, description="Chatflow workflow ID")
    config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "provider": "ollama",
            "model": "llama3.3:70b",
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        description="LLM configuration",
    )


class ChatResponse(BaseModel):
    """Chat response model."""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: str
    message_count: int = 0
    usage: Optional[Dict[str, int]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a chat message and get a response.
    
    This endpoint processes a single message and returns the complete response.
    For streaming responses, use the /chat/stream endpoint.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Initialize service
        service = ChatflowService(db)
        
        # Process chat
        result = await service.chat(
            session_id=session_id,
            user_message=request.message,
            config=request.config,
            user_id=str(current_user.id),
            workflow_id=request.workflow_id,
        )
        
        return ChatResponse(
            success=result.get("success", False),
            response=result.get("response"),
            error=result.get("error"),
            session_id=session_id,
            message_count=result.get("message_count", 0),
            usage=result.get("usage"),
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a chat message and stream the response.
    
    Returns Server-Sent Events (SSE) with the following event types:
    - start: Indicates stream has started
    - content: Contains a chunk of the response
    - done: Indicates stream has completed, includes usage stats
    - error: Indicates an error occurred
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Initialize service
        service = ChatflowService(db)
        
        return StreamingResponse(
            service.chat_stream(
                session_id=session_id,
                user_message=request.message,
                config=request.config,
                user_id=str(current_user.id),
                workflow_id=request.workflow_id,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        
    except Exception as e:
        logger.error(f"Chat stream failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation history for a session."""
    service = ChatflowService(db)
    history = service.get_session_history(session_id)
    
    return {
        "session_id": session_id,
        "messages": history,
        "message_count": len(history),
    }


@router.delete("/sessions/{session_id}")
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear a chat session and its history."""
    service = ChatflowService(db)
    cleared = service.clear_session(session_id)
    
    return {
        "session_id": session_id,
        "cleared": cleared,
        "message": "Session cleared" if cleared else "Session not found",
    }


@router.post("/workflows/{workflow_id}/chat")
async def workflow_chat(
    workflow_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Chat with a specific Chatflow workflow using DDD Facade.
    
    This endpoint loads the workflow configuration and uses it for the chat.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow using Facade
        workflow = facade.get_workflow(workflow_id)
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract chat configuration from workflow
        graph_def = workflow.graph_definition or {}
        nodes = graph_def.get("nodes", [])
        
        # Find AI Agent node for configuration
        ai_config = request.config.copy()
        for node in nodes:
            node_type = node.get("type") or node.get("node_type")
            if node_type == "tool":
                tool_id = node.get("data", {}).get("toolId") or node.get("configuration", {}).get("tool_id")
                if tool_id == "ai_agent":
                    node_config = node.get("data", {}).get("config", {}) or node.get("configuration", {}).get("config", {})
                    ai_config.update({
                        "provider": node_config.get("provider", ai_config.get("provider")),
                        "model": node_config.get("model", ai_config.get("model")),
                        "system_prompt": node_config.get("system_prompt", ""),
                        "temperature": node_config.get("temperature", 0.7),
                        "max_tokens": node_config.get("max_tokens", 1000),
                    })
                    break
        
        # Generate session ID if not provided
        session_id = request.session_id
        if not session_id:
            import uuid
            session_id = f"{workflow_id}:{uuid.uuid4()}"
        
        # Initialize service
        service = ChatflowService(db)
        
        # Process chat
        result = await service.chat(
            session_id=session_id,
            user_message=request.message,
            config=ai_config,
            user_id=str(current_user.id),
            workflow_id=workflow_id,
        )
        
        return ChatResponse(
            success=result.get("success", False),
            response=result.get("response"),
            error=result.get("error"),
            session_id=session_id,
            message_count=result.get("message_count", 0),
            usage=result.get("usage"),
        )
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/chat/stream")
async def workflow_chat_stream(
    workflow_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Chat with a specific Chatflow workflow with streaming response using DDD Facade.
    """
    try:
        facade = AgentBuilderFacade(db)
        
        # Get workflow using Facade
        workflow = facade.get_workflow(workflow_id)
        
        # Check permissions
        if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract chat configuration from workflow
        graph_def = workflow.graph_definition or {}
        nodes = graph_def.get("nodes", [])
        
        # Find AI Agent node for configuration
        ai_config = request.config.copy()
        for node in nodes:
            node_type = node.get("type") or node.get("node_type")
            if node_type == "tool":
                tool_id = node.get("data", {}).get("toolId") or node.get("configuration", {}).get("tool_id")
                if tool_id == "ai_agent":
                    node_config = node.get("data", {}).get("config", {}) or node.get("configuration", {}).get("config", {})
                    ai_config.update({
                        "provider": node_config.get("provider", ai_config.get("provider")),
                        "model": node_config.get("model", ai_config.get("model")),
                        "system_prompt": node_config.get("system_prompt", ""),
                        "temperature": node_config.get("temperature", 0.7),
                        "max_tokens": node_config.get("max_tokens", 1000),
                    })
                    break
        
        # Generate session ID if not provided
        session_id = request.session_id
        if not session_id:
            import uuid
            session_id = f"{workflow_id}:{uuid.uuid4()}"
        
        # Initialize service
        service = ChatflowService(db)
        
        return StreamingResponse(
            service.chat_stream(
                session_id=session_id,
                user_message=request.message,
                config=ai_config,
                user_id=str(current_user.id),
                workflow_id=workflow_id,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow chat stream failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
