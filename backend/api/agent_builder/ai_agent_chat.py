"""
AI Agent Chat WebSocket API

Real-time bidirectional chat with AI agents using WebSocket.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.tools.tool_executor_registry import ToolExecutorRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/ai-agent-chat", tags=["ai-agent-chat"])


class ConnectionManager:
    """Manage WebSocket connections for AI Agent chat."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"🔌 WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"🔌 WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific session."""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)


manager = ConnectionManager()


@router.websocket("/ws")
async def ai_agent_chat_websocket(
    websocket: WebSocket,
    session_id: str = Query(..., description="Unique session ID"),
    node_id: str = Query(..., description="AI Agent node ID"),
):
    """
    WebSocket endpoint for real-time AI Agent chat.
    
    Message format (client -> server):
    {
        "type": "message",
        "content": "user message",
        "config": {
            "provider": "ollama",
            "model": "llama3.3:70b",
            "system_prompt": "...",
            "temperature": 0.7,
            "max_tokens": 1000,
            ...
        }
    }
    
    Message format (server -> client):
    {
        "type": "message" | "error" | "status" | "chunk",
        "content": "response content",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {...}
    }
    """
    
    await manager.connect(session_id, websocket)
    
    try:
        # Send connection confirmation
        await manager.send_message(session_id, {
            "type": "status",
            "content": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": session_id,
            "node_id": node_id,
        })
        
        # Get AI Agent executor
        executor = ToolExecutorRegistry.get_executor("ai_agent")
        if not executor:
            await manager.send_message(session_id, {
                "type": "error",
                "content": "AI Agent executor not found",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
            return
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                logger.info(f"📨 Received message from {session_id}", extra={
                    "session_id": session_id,
                    "node_id": node_id,
                    "message_type": data.get("type"),
                })
                
                if data.get("type") == "message":
                    # Send processing status
                    await manager.send_message(session_id, {
                        "type": "status",
                        "content": "processing",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    })
                    
                    # Extract configuration
                    config = data.get("config", {})
                    user_message = data.get("content", "")
                    
                    # Build parameters for AI Agent
                    params = {
                        "provider": config.get("provider", "ollama"),
                        "model": config.get("model", "llama3.3:70b"),
                        "user_message": user_message,
                        "system_prompt": config.get("system_prompt", ""),
                        "temperature": config.get("temperature", 0.7),
                        "max_tokens": config.get("max_tokens", 1000),
                        "enable_memory": config.get("enable_memory", True),
                        "memory_type": config.get("memory_type", "short_term"),
                        "session_id": session_id,
                    }
                    
                    credentials = config.get("credentials", {})
                    
                    # Execute AI Agent
                    try:
                        result = await executor.execute(params, credentials)
                        
                        if result.success:
                            # Send successful response
                            await manager.send_message(session_id, {
                                "type": "message",
                                "role": "assistant",
                                "content": result.output.get("content", ""),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "metadata": result.output.get("metadata", {}),
                            })
                            
                            logger.info(f"✅ AI Agent response sent to {session_id}", extra={
                                "session_id": session_id,
                                "response_length": len(result.output.get("content", "")),
                            })
                        else:
                            # Send error response
                            await manager.send_message(session_id, {
                                "type": "error",
                                "content": result.error or "Failed to get AI response",
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                            })
                            
                            logger.error(f"❌ AI Agent error for {session_id}", extra={
                                "session_id": session_id,
                                "error": result.error,
                            })
                    
                    except Exception as e:
                        logger.error(f"❌ AI Agent execution failed for {session_id}", extra={
                            "session_id": session_id,
                            "error": str(e),
                        }, exc_info=True)
                        
                        await manager.send_message(session_id, {
                            "type": "error",
                            "content": f"Execution failed: {str(e)}",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        })
                
                elif data.get("type") == "ping":
                    # Respond to ping
                    await manager.send_message(session_id, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    })
                
                elif data.get("type") == "clear":
                    # Clear conversation history
                    # TODO: Implement memory clearing
                    await manager.send_message(session_id, {
                        "type": "status",
                        "content": "cleared",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    })
            
            except WebSocketDisconnect:
                logger.info(f"🔌 Client disconnected: {session_id}")
                break
            
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON from {session_id}: {e}")
                await manager.send_message(session_id, {
                    "type": "error",
                    "content": "Invalid message format",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                })
            
            except Exception as e:
                logger.error(f"❌ Error processing message from {session_id}", extra={
                    "session_id": session_id,
                    "error": str(e),
                }, exc_info=True)
                
                await manager.send_message(session_id, {
                    "type": "error",
                    "content": f"Server error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                })
    
    except Exception as e:
        logger.error(f"❌ WebSocket error for {session_id}", extra={
            "session_id": session_id,
            "error": str(e),
        }, exc_info=True)
    
    finally:
        manager.disconnect(session_id)


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get chat history for a session.
    
    TODO: Implement persistent storage of chat history.
    """
    return {
        "session_id": session_id,
        "messages": [],
        "message": "Chat history not yet implemented"
    }


@router.delete("/sessions/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clear chat session and history.
    
    TODO: Implement session clearing.
    """
    return {
        "session_id": session_id,
        "message": "Session cleared"
    }
