"""
Chatflow Chat API

REST and SSE endpoints for Chatflow conversations.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.config import settings
# DDD Architecture
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.shared.errors import (
    NotFoundError,
    ValidationError,
    ExecutionError,
)
from backend.services.agent_builder.chatflow_service import ChatflowService
from backend.services.performance_monitor import get_performance_monitor
from backend.services.session_cleanup_service import SessionCleanupService
from backend.services.conversation_export_service import get_export_service

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
    Send a chat message and get a response with persistent memory.
    
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
        
        # Process chat with enhanced memory management
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
            session_id=result.get("session_id", session_id),
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
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )
        
    except Exception as e:
        logger.error(f"Chat stream failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/stream")
async def chat_stream_get(
    message: str = Query(..., description="User message"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    workflow_id: Optional[str] = Query(None, description="Workflow ID"),
    config: Optional[str] = Query(None, description="JSON config"),
    token: Optional[str] = Query(None, description="Auth token"),
    db: Session = Depends(get_db),
):
    """
    GET version of chat stream for EventSource compatibility.
    """
    try:
        # Authenticate using token from query params
        if token:
            from backend.core.auth_dependencies import get_user_from_token
            current_user = await get_user_from_token(token, db)
        else:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Parse config if provided
        parsed_config = {}
        if config:
            try:
                parsed_config = json.loads(config)
            except json.JSONDecodeError:
                pass
        
        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Initialize service
        service = ChatflowService(db)
        
        return StreamingResponse(
            service.chat_stream(
                session_id=session_id,
                user_message=message,
                config=parsed_config,
                user_id=str(current_user.id),
                workflow_id=workflow_id,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )
        
    except Exception as e:
        logger.error(f"Chat stream GET failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation history for a session."""
    try:
        service = ChatflowService(db)
        
        # Handle both UUID and token-based session IDs
        if ':' in session_id:
            # This is a session token, extract the actual session ID
            # Format: chatflow_id:user_id:timestamp or similar
            parts = session_id.split(':')
            if len(parts) >= 2:
                # Try to find session by token
                session = await service.session_repo.get_session_by_token(
                    session_id, 
                    current_user.id
                )
                if session:
                    actual_session_id = str(session.id)
                else:
                    raise HTTPException(status_code=404, detail="Session not found")
            else:
                raise HTTPException(status_code=400, detail="Invalid session ID format")
        else:
            # This is a regular UUID session ID
            actual_session_id = session_id
        
        history = await service.get_session_history(actual_session_id, str(current_user.id))
        
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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
    Chat with a specific Chatflow workflow using direct Chatflow query.
    
    This endpoint loads the chatflow configuration and uses it for the chat.
    """
    try:
        # Direct query for Chatflow instead of using Facade
        from backend.db.models.flows import Chatflow
        
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == workflow_id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found")
        
        # Check permissions
        if str(chatflow.user_id) != str(current_user.id) and not chatflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract chat configuration from chatflow
        chat_config = chatflow.chat_config or {}
        
        # Prepare AI config
        ai_config = request.config.copy()
        ai_config.update({
            "provider": chat_config.get("llm_provider", ai_config.get("provider", "ollama")),
            "model": chat_config.get("llm_model", ai_config.get("model", "llama3.3:70b")),
            "system_prompt": chat_config.get("system_prompt", ""),
            "temperature": chat_config.get("temperature", 0.7),
            "max_tokens": chat_config.get("max_tokens", 1000),
        })
        
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
    Chat with a specific Chatflow workflow with streaming response.
    """
    try:
        # Direct query for Chatflow instead of using Facade
        from backend.db.models.flows import Chatflow
        
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == workflow_id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found")
        
        # Check permissions
        if str(chatflow.user_id) != str(current_user.id) and not chatflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract chat configuration from chatflow
        chat_config = chatflow.chat_config or {}
        
        # Prepare AI config
        ai_config = request.config.copy()
        ai_config.update({
            "provider": chat_config.get("llm_provider", ai_config.get("provider", "ollama")),
            "model": chat_config.get("llm_model", ai_config.get("model", "llama3.3:70b")),
            "system_prompt": chat_config.get("system_prompt", ""),
            "temperature": chat_config.get("temperature", 0.7),
            "max_tokens": chat_config.get("max_tokens", 1000),
        })
        
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
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow chat stream failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/chat/stream")
async def workflow_chat_stream_get(
    workflow_id: str,
    message: str = Query(..., description="User message"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    config: Optional[str] = Query(None, description="JSON config"),
    token: Optional[str] = Query(None, description="Auth token"),
    db: Session = Depends(get_db),
):
    """
    GET version of workflow chat stream for EventSource compatibility.
    """
    try:
        # Authenticate using token from query params
        if token:
            from backend.core.auth_dependencies import get_user_from_token
            try:
                # Handle development fake tokens and dummy token
                if (token.startswith('dev-fake-token-') or token == 'dev-dummy-token') and settings.DEBUG:
                    logger.info(f"🔧 Development mode: Using fake/dummy token ({token[:20]}...), creating test user")
                    from backend.db.repositories.user_repository import UserRepository
                    from backend.db.models.user import User
                    from backend.services.auth_service import AuthService
                    
                    user_repo = UserRepository(db)
                    test_user = user_repo.get_user_by_email("test@example.com")
                    
                    if not test_user:
                        logger.info("Creating test user for development mode")
                        test_user = User(
                            email="test@example.com",
                            username="testuser",
                            password_hash=AuthService.hash_password("test1234"),
                            role="admin",
                            is_active=True,
                        )
                        db.add(test_user)
                        db.commit()
                        db.refresh(test_user)
                    
                    current_user = test_user
                else:
                    current_user = await get_user_from_token(token, db)
                
                logger.info(f"User authenticated successfully: {current_user.email}")
            except Exception as e:
                logger.error(f"Token authentication failed: {e}")
                raise HTTPException(status_code=401, detail="Invalid or expired token")
        else:
            logger.warning("No token provided for streaming endpoint")
            logger.warning(f"Available query params: {list(request.query_params.keys()) if 'request' in locals() else 'N/A'}")
            
            # In DEBUG mode, allow access without token
            if settings.DEBUG:
                logger.info("🔧 DEBUG mode: Allowing access without token, creating test user")
                from backend.db.repositories.user_repository import UserRepository
                from backend.db.models.user import User
                from backend.services.auth_service import AuthService
                
                user_repo = UserRepository(db)
                test_user = user_repo.get_user_by_email("test@example.com")
                
                if not test_user:
                    logger.info("Creating test user for DEBUG mode")
                    test_user = User(
                        email="test@example.com",
                        username="testuser",
                        password_hash=AuthService.hash_password("test1234"),
                        role="admin",
                        is_active=True,
                    )
                    db.add(test_user)
                    db.commit()
                    db.refresh(test_user)
                
                current_user = test_user
            else:
                raise HTTPException(
                    status_code=401, 
                    detail="Authentication token required. Please log in and try again."
                )
        
        # Direct query for Chatflow instead of using Facade
        from backend.db.models.flows import Chatflow
        
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == workflow_id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found")
        
        # Check permissions
        if str(chatflow.user_id) != str(current_user.id) and not chatflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Parse config if provided
        parsed_config = {}
        if config:
            try:
                parsed_config = json.loads(config)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse config: {config}")
                pass
        
        # Extract chat configuration from chatflow
        chat_config = chatflow.chat_config or {}
        
        # Prepare AI config
        ai_config = parsed_config.copy()
        ai_config.update({
            "provider": chat_config.get("llm_provider", ai_config.get("provider", "ollama")),
            "model": chat_config.get("llm_model", ai_config.get("model", "llama3.1:8b")),
            "system_prompt": chat_config.get("system_prompt", ""),
            "temperature": chat_config.get("temperature", 0.7),
            "max_tokens": chat_config.get("max_tokens", 1000),
        })
        
        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = f"{workflow_id}:{uuid.uuid4()}"
        
        # Initialize service
        service = ChatflowService(db)
        
        return StreamingResponse(
            service.chat_stream(
                session_id=session_id,
                user_message=message,
                config=ai_config,
                user_id=str(current_user.id),
                workflow_id=workflow_id,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow chat stream GET failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/sessions")
async def list_sessions(
    chatflow_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's chat sessions."""
    try:
        service = ChatflowService(db)
        sessions = await service.list_user_sessions(
            user_id=str(current_user.id),
            chatflow_id=chatflow_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"List sessions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get session details and message history."""
    try:
        from backend.db.repositories.chat_session_repository import ChatSessionRepository
        from backend.db.repositories.chat_message_repository import ChatMessageRepository
        from backend.utils.common import parse_uuid
        from uuid import UUID
        
        session_repo = ChatSessionRepository(db)
        message_repo = ChatMessageRepository(db)
        
        # Validate session_id is a valid UUID
        session_uuid = parse_uuid(session_id)
        if not session_uuid:
            logger.error(f"Invalid UUID format for session_id: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        # Get session
        session = await session_repo.get_session(
            session_uuid,
            UUID(str(current_user.id))
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        messages = await message_repo.get_session_messages(session.id)
        
        return {
            "success": True,
            "session": {
                "id": str(session.id),
                "title": session.title,
                "memory_type": session.memory_type,
                "memory_config": session.memory_config,
                "message_count": session.message_count,
                "total_tokens_used": session.total_tokens_used,
                "created_at": session.created_at.isoformat(),
                "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
                "status": session.status
            },
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "metadata": msg.message_metadata
                }
                for msg in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a chat session."""
    try:
        service = ChatflowService(db)
        success = await service.delete_session(session_id, str(current_user.id))
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export session data as JSON."""
    try:
        service = ChatflowService(db)
        session_data = await service.export_session(session_id, str(current_user.id))
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export session failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear session messages (keep session but remove all messages)."""
    try:
        from backend.db.repositories.chat_session_repository import ChatSessionRepository
        from backend.db.repositories.chat_message_repository import ChatMessageRepository
        from backend.utils.common import parse_uuid
        from uuid import UUID
        
        session_repo = ChatSessionRepository(db)
        message_repo = ChatMessageRepository(db)
        
        # Validate session_id is a valid UUID
        session_uuid = parse_uuid(session_id)
        if not session_uuid:
            logger.error(f"Invalid UUID format for session_id: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        # Verify session ownership
        session = await session_repo.get_session(
            session_uuid,
            UUID(str(current_user.id))
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all messages and delete them
        messages = await message_repo.get_session_messages(session.id)
        for message in messages:
            await message_repo.delete_message(message.id)
        
        # Reset session counters
        session.message_count = 0
        session.total_tokens_used = 0
        session.memory_state = {}
        db.commit()
        
        return {"success": True, "message": "Session cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear session failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEMORY CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/memory/strategies")
async def get_memory_strategies():
    """Get available memory strategies and their configurations."""
    try:
        from backend.core.memory.memory_factory import MemoryStrategyFactory
        
        factory = MemoryStrategyFactory()
        strategies = factory.get_available_strategies()
        
        return {
            "success": True,
            "strategies": strategies
        }
        
    except Exception as e:
        logger.error(f"Get memory strategies failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}/memory")
async def update_session_memory(
    session_id: str,
    memory_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update session memory configuration."""
    try:
        from backend.db.repositories.chat_session_repository import ChatSessionRepository
        from backend.utils.common import parse_uuid
        from uuid import UUID
        
        session_repo = ChatSessionRepository(db)
        
        # Handle both UUID and token-based session IDs
        if ':' in session_id:
            # This is a session token, find the session by token
            session = await session_repo.get_session_by_token(
                session_id, 
                current_user.id
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            # This is a regular UUID session ID
            session_uuid = parse_uuid(session_id)
            if not session_uuid:
                logger.error(f"Invalid UUID format for session_id: {session_id}")
                raise HTTPException(status_code=400, detail="Invalid session ID format")
                
            session = await session_repo.get_session(
                session_uuid,
                UUID(str(current_user.id))
            )
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        
        # Update memory configuration
        session.memory_type = memory_config.get('strategy', memory_config.get('memory_type', session.memory_type))
        session.memory_config = memory_config.get('memory_config', session.memory_config)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Memory configuration updated successfully",
            "memory_type": session.memory_type,
            "memory_config": session.memory_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update session memory failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: PERFORMANCE & EXPORT ENDPOINTS
# ============================================================================

@router.get("/sessions/{session_id}/performance")
async def get_session_performance(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a session."""
    try:
        monitor = get_performance_monitor()
        performance_data = monitor.get_session_performance(session_id)
        
        return {
            "success": True,
            "data": performance_data
        }
    except Exception as e:
        logger.error(f"Failed to get session performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary")
async def get_performance_summary(
    time_window_minutes: int = Query(60, ge=1, le=1440),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance summary."""
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_performance_summary(time_window_minutes)
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/memory-comparison")
async def get_memory_performance_comparison(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get memory strategy performance comparison."""
    try:
        monitor = get_performance_monitor()
        comparison = monitor.get_memory_performance_comparison()
        
        return {
            "success": True,
            "data": comparison
        }
    except Exception as e:
        logger.error(f"Failed to get memory performance comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/export")
async def export_session_advanced(
    session_id: str,
    format: str = Query("json", regex="^(json|csv|txt|markdown)$"),
    include_metadata: bool = Query(True),
    include_analysis: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export a conversation session in various formats."""
    try:
        from backend.utils.common import parse_uuid
        from uuid import UUID
        
        # Validate session_id is a valid UUID
        session_uuid = parse_uuid(session_id)
        if not session_uuid:
            logger.error(f"Invalid UUID format for session_id: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        export_service = get_export_service(db)
        
        result = await export_service.export_session(
            session_id=session_uuid,
            user_id=UUID(str(current_user.id)),
            format=format,
            include_metadata=include_metadata,
            include_analysis=include_analysis
        )
        
        if result['success']:
            return Response(
                content=result['content'],
                media_type=result['content_type'],
                headers={
                    "Content-Disposition": f"attachment; filename={result['filename']}"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Export failed")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/import")
async def import_session(
    chatflow_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import a conversation session."""
    try:
        from uuid import UUID
        
        # Read file content
        content = await file.read()
        
        # Determine format from file extension
        filename = file.filename or ""
        if filename.endswith('.json'):
            format = 'json'
            import_data = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only JSON format supported for import")
        
        export_service = get_export_service(db)
        
        result = await export_service.import_session(
            import_data=import_data,
            user_id=UUID(str(current_user.id)),
            chatflow_id=UUID(chatflow_id),
            format=format
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Session import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cleanup/statistics")
async def get_cleanup_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get session cleanup statistics."""
    try:
        cleanup_service = SessionCleanupService(db)
        stats = await cleanup_service.get_cleanup_statistics()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Failed to get cleanup statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/inactive-sessions")
async def cleanup_inactive_sessions(
    inactive_days: int = Query(30, ge=1, le=365),
    dry_run: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up inactive sessions."""
    try:
        # Only allow admins to perform actual cleanup
        if not dry_run and not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required for actual cleanup")
        
        cleanup_service = SessionCleanupService(db)
        result = await cleanup_service.cleanup_inactive_sessions(
            inactive_days=inactive_days,
            dry_run=dry_run
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/archive")
async def archive_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive a specific session."""
    try:
        from backend.utils.common import parse_uuid
        from uuid import UUID
        
        # Validate session_id is a valid UUID
        session_uuid = parse_uuid(session_id)
        if not session_uuid:
            logger.error(f"Invalid UUID format for session_id: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        cleanup_service = SessionCleanupService(db)
        result = await cleanup_service.archive_session(
            session_id=session_uuid,
            user_id=UUID(str(current_user.id))
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session archiving failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/restore")
async def restore_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restore an archived session."""
    try:
        from backend.utils.common import parse_uuid
        from uuid import UUID
        
        # Validate session_id is a valid UUID
        session_uuid = parse_uuid(session_id)
        if not session_uuid:
            logger.error(f"Invalid UUID format for session_id: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        cleanup_service = SessionCleanupService(db)
        result = await cleanup_service.restore_session(
            session_id=session_uuid,
            user_id=UUID(str(current_user.id))
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session restoration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/export")
async def export_performance_metrics(
    format: str = Query("json", regex="^(json)$"),
    time_window_hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export performance metrics."""
    try:
        monitor = get_performance_monitor()
        metrics_export = monitor.export_metrics(
            format=format,
            time_window_hours=time_window_hours
        )
        
        filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return Response(
            content=metrics_export,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Performance metrics export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))