"""
Chat History API

Provides endpoints for managing chat sessions and messages.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.chat_history_service import get_chat_history_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat History"])


# ============================================================================
# Models
# ============================================================================

class CreateSessionRequest(BaseModel):
    agent_id: Optional[str] = None
    title: Optional[str] = None
    metadata: Optional[dict] = None


class AddMessageRequest(BaseModel):
    role: str  # user, assistant, system
    content: str
    metadata: Optional[dict] = None


class UpdateTitleRequest(BaseModel):
    title: str


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    metadata: dict
    created_at: str


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    agent_id: Optional[str]
    title: str
    metadata: dict
    message_count: int
    created_at: str
    updated_at: str


class SearchResultResponse(BaseModel):
    message: ChatMessageResponse
    session: ChatSessionResponse


# ============================================================================
# Session Endpoints
# ============================================================================

@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session."""
    service = get_chat_history_service()
    user_id = str(current_user.id)
    
    session_id = service.create_session(
        user_id=user_id,
        agent_id=request.agent_id,
        title=request.title,
        metadata=request.metadata,
    )
    
    return {"session_id": session_id}


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's chat sessions."""
    service = get_chat_history_service()
    user_id = str(current_user.id)
    
    sessions = service.list_sessions(user_id=user_id, limit=limit, offset=offset)
    
    return {
        "sessions": sessions,
        "total": len(sessions),
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific chat session."""
    service = get_chat_history_service()
    
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify ownership
    if session.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a chat session."""
    service = get_chat_history_service()
    user_id = str(current_user.id)
    
    success = service.delete_session(session_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True}


@router.put("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: UpdateTitleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update session title."""
    service = get_chat_history_service()
    
    success = service.update_session_title(session_id, request.title)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True}


@router.post("/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear all messages in a session."""
    service = get_chat_history_service()
    
    success = service.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True}


# ============================================================================
# Message Endpoints
# ============================================================================

@router.post("/sessions/{session_id}/messages")
async def add_message(
    session_id: str,
    request: AddMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a message to a session."""
    service = get_chat_history_service()
    
    # Verify session exists
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    message = service.add_message(
        session_id=session_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )
    
    return message.to_dict()


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages from a session."""
    service = get_chat_history_service()
    
    messages = service.get_messages(session_id=session_id, limit=limit)
    
    return {
        "messages": [m.to_dict() for m in messages],
    }


# ============================================================================
# Search Endpoint
# ============================================================================

@router.get("/search")
async def search_messages(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search messages across user's sessions."""
    service = get_chat_history_service()
    user_id = str(current_user.id)
    
    results = service.search_messages(user_id=user_id, query=query, limit=limit)
    
    return {"results": results}
