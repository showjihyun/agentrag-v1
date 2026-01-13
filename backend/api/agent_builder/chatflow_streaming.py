"""
Chatflow Streaming API with Server-Sent Events (SSE)

Provides real-time streaming for chatflow conversations using SSE instead of WebSocket.
More suitable for one-way communication (server -> client) with automatic reconnection.
"""

import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.services.flow.chatflow_service import ChatflowService
from backend.services.agent_builder.conversation_service import ConversationService
from backend.core.streaming import SSEManager, StreamEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/chatflows", tags=["chatflow-streaming"])


class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class StreamingChatService:
    """Service for handling streaming chat responses"""
    
    def __init__(self, db: Session):
        self.db = db
        self.chatflow_service = ChatflowService(db)
        self.conversation_service = ConversationService(db)
        self.sse_manager = SSEManager()
    
    async def process_message_stream(
        self,
        chatflow_id: str,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Process chat message and yield streaming events
        
        Args:
            chatflow_id: Chatflow ID
            message: User message
            user_id: User ID
            session_id: Optional session ID
            context: Optional context data
            
        Yields:
            StreamEvent: Streaming events (message_start, token, message_complete, etc.)
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Yield session start event
            yield StreamEvent(
                event="session_start",
                data={
                    "session_id": session_id,
                    "chatflow_id": chatflow_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Yield message received event
            yield StreamEvent(
                event="message_received",
                data={
                    "message": message,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Get chatflow configuration
            chatflow = await self.chatflow_service.get_chatflow(chatflow_id)
            if not chatflow:
                yield StreamEvent(
                    event="error",
                    data={"error": "Chatflow not found", "code": "CHATFLOW_NOT_FOUND"}
                )
                return
            
            # Yield processing start event
            yield StreamEvent(
                event="processing_start",
                data={
                    "chatflow_name": chatflow.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Execute chatflow and stream response
            async for chunk in self.chatflow_service.execute_streaming(
                chatflow_id=chatflow_id,
                message=message,
                session_id=session_id,
                user_id=user_id,
                context=context or {}
            ):
                # Transform internal events to SSE events
                if chunk.get("type") == "token":
                    yield StreamEvent(
                        event="token",
                        data={
                            "token": chunk.get("content", ""),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                elif chunk.get("type") == "thinking":
                    yield StreamEvent(
                        event="thinking",
                        data={
                            "step": chunk.get("step", ""),
                            "description": chunk.get("description", ""),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                elif chunk.get("type") == "tool_call":
                    yield StreamEvent(
                        event="tool_call",
                        data={
                            "tool_name": chunk.get("tool_name", ""),
                            "parameters": chunk.get("parameters", {}),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                elif chunk.get("type") == "tool_result":
                    yield StreamEvent(
                        event="tool_result",
                        data={
                            "tool_name": chunk.get("tool_name", ""),
                            "result": chunk.get("result", {}),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            
            # Yield completion event
            yield StreamEvent(
                event="message_complete",
                data={
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error in message stream: {str(e)}", exc_info=True)
            yield StreamEvent(
                event="error",
                data={
                    "error": str(e),
                    "code": "PROCESSING_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


@router.post("/{chatflow_id}/chat/stream")
async def stream_chat_response(
    chatflow_id: str,
    message: ChatMessage,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat response using Server-Sent Events (SSE)
    
    This endpoint accepts a chat message and returns a streaming response
    with real-time updates about the processing status and AI response.
    
    Events:
    - session_start: Session initialization
    - message_received: User message acknowledged
    - processing_start: AI processing begins
    - thinking: AI reasoning steps
    - tool_call: Tool execution
    - tool_result: Tool results
    - token: Response tokens (streaming text)
    - message_complete: Response finished
    - error: Error occurred
    """
    try:
        # Validate chatflow access
        chatflow_service = ChatflowService(db)
        chatflow = await chatflow_service.get_chatflow(chatflow_id)
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found")
        
        # Check user permissions
        if chatflow.user_id != current_user.id and not chatflow.is_public:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create streaming service
        streaming_service = StreamingChatService(db)
        
        # Create event generator
        async def event_generator():
            async for event in streaming_service.process_message_stream(
                chatflow_id=chatflow_id,
                message=message.message,
                user_id=current_user.id,
                session_id=message.session_id,
                context=message.context
            ):
                # Format as SSE
                yield f"event: {event.event}\n"
                yield f"data: {json.dumps(event.data, ensure_ascii=False)}\n\n"
        
        # Return streaming response
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in stream_chat_response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{chatflow_id}/chat/history/{session_id}")
async def get_chat_history(
    chatflow_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a session"""
    try:
        conversation_service = ConversationService(db)
        history = await conversation_service.get_conversation_history(
            session_id=session_id,
            user_id=current_user.id
        )
        
        return {
            "session_id": session_id,
            "chatflow_id": chatflow_id,
            "messages": history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get chat history")


@router.delete("/{chatflow_id}/chat/history/{session_id}")
async def clear_chat_history(
    chatflow_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear chat history for a session"""
    try:
        conversation_service = ConversationService(db)
        await conversation_service.clear_conversation_history(
            session_id=session_id,
            user_id=current_user.id
        )
        
        return {
            "message": "Chat history cleared",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clear chat history")
