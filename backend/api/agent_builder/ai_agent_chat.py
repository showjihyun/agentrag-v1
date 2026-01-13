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
from pydantic import BaseModel

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.tools.tool_executor_registry import ToolExecutorRegistry
from backend.services.agent_builder.chatflow_service import ChatflowService

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
        
        # Get LLM manager
        from backend.core.dependencies import get_llm_manager
        llm_manager = await get_llm_manager()
        
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
                    
                    # Build LLM request
                    provider = config.get("provider", "ollama")
                    model = config.get("model", "llama3.3:70b")
                    system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
                    temperature = config.get("temperature", 0.7)
                    max_tokens = config.get("max_tokens", 1000)
                    
                    # Execute LLM request
                    try:
                        # Create messages array
                        messages = []
                        if system_prompt:
                            messages.append({"role": "system", "content": system_prompt})
                        messages.append({"role": "user", "content": user_message})
                        
                        # Call LLM
                        response = await llm_manager.generate_response(
                            messages=messages,
                            provider=provider,
                            model=model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=False
                        )
                        
                        if response and response.get("content"):
                            # Send successful response
                            await manager.send_message(session_id, {
                                "type": "message",
                                "role": "assistant",
                                "content": response["content"],
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "metadata": {
                                    "provider": provider,
                                    "model": model,
                                    "tokens_used": response.get("usage", {}).get("total_tokens", 0)
                                },
                            })
                            
                            logger.info(f"✅ AI Agent response sent to {session_id}", extra={
                                "session_id": session_id,
                                "response_length": len(response["content"]),
                            })
                        else:
                            # Send error response
                            await manager.send_message(session_id, {
                                "type": "error",
                                "content": "Failed to get AI response",
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                            })
                            
                            logger.error(f"❌ Empty AI response for {session_id}", extra={
                                "session_id": session_id,
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
                    # Clear conversation history (simple implementation)
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
    """
    # Simple implementation - return empty history for now
    # In a full implementation, this would query a chat history table
    return {
        "session_id": session_id,
        "messages": [],
        "message_count": 0,
    }


@router.delete("/sessions/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clear chat session and history.
    """
    # Simple implementation - always return success
    # In a full implementation, this would delete from chat history table
    return {
        "session_id": session_id,
        "cleared": True,
        "message": "Session cleared",
    }


class ConnectionCheckRequest(BaseModel):
    """Connection check request."""
    provider: str
    model: str
    api_key: Optional[str] = None  # Optional API key from node config


@router.get("/test-connection")
async def test_websocket_connection():
    """
    Test WebSocket endpoint availability.
    
    Returns connection status and endpoint information.
    """
    return {
        "websocket_endpoint": "/api/agent-builder/ai-agent-chat/ws",
        "status": "available",
        "message": "WebSocket endpoint is ready for connections",
        "example_url": "ws://localhost:8000/api/agent-builder/ai-agent-chat/ws?session_id=test&node_id=test",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/check-connection")
async def check_llm_connection(
    request: ConnectionCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Check if LLM connection is working.
    
    Args:
        request: Connection check request with provider, model, and optional API key
        
    Returns:
        Connection status
    """
    provider = request.provider
    model = request.model
    provided_api_key = request.api_key
    import os
    import httpx
    
    try:
        if provider == "ollama":
            # Check Ollama connection
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check if Ollama is running
                response = await client.get(f"{ollama_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    
                    # Check if specific model is available
                    model_available = any(model in m for m in models)
                    
                    return {
                        "connected": True,
                        "provider": provider,
                        "model": model,
                        "model_available": model_available,
                        "available_models": models[:5],  # First 5 models
                        "message": "Ollama is running" if model_available else f"Model '{model}' not found. Available models: {', '.join(models[:3])}"
                    }
                else:
                    return {
                        "connected": False,
                        "provider": provider,
                        "model": model,
                        "error": f"Ollama returned status {response.status_code}"
                    }
        
        elif provider == "openai":
            # Check OpenAI API key - use provided key or fallback to env
            api_key = provided_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {
                    "connected": False,
                    "provider": provider,
                    "model": model,
                    "error": "OPENAI_API_KEY not configured. Please add it in Node Properties > Config or set OPENAI_API_KEY environment variable."
                }
            
            # Try a simple API call
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.status_code == 200:
                    return {
                        "connected": True,
                        "provider": provider,
                        "model": model,
                        "message": "OpenAI API key is valid"
                    }
                elif response.status_code == 401:
                    return {
                        "connected": False,
                        "provider": provider,
                        "model": model,
                        "error": "Invalid OpenAI API key. Please check your API key in Node Properties > Config."
                    }
                else:
                    return {
                        "connected": False,
                        "provider": provider,
                        "model": model,
                        "error": f"OpenAI API returned status {response.status_code}"
                    }
        
        elif provider in ["anthropic", "claude"]:
            # Check Anthropic API key - use provided key or fallback to env
            api_key = provided_api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return {
                    "connected": False,
                    "provider": provider,
                    "model": model,
                    "error": "ANTHROPIC_API_KEY not configured. Please add it in Node Properties > Config or set ANTHROPIC_API_KEY environment variable."
                }
            
            return {
                "connected": True,
                "provider": provider,
                "model": model,
                "message": "Anthropic API key is configured (validation requires actual API call)"
            }
        
        elif provider == "gemini":
            # Check Gemini API key - use provided key or fallback to env
            api_key = provided_api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                return {
                    "connected": False,
                    "provider": provider,
                    "model": model,
                    "error": "GEMINI_API_KEY not configured. Please add it in Node Properties > Config or set GEMINI_API_KEY environment variable."
                }
            
            return {
                "connected": True,
                "provider": provider,
                "model": model,
                "message": "Gemini API key is configured"
            }
        
        else:
            return {
                "connected": False,
                "provider": provider,
                "model": model,
                "error": f"Unsupported provider: {provider}"
            }
    
    except httpx.ConnectError:
        return {
            "connected": False,
            "provider": provider,
            "model": model,
            "error": f"Cannot connect to {provider}. Please ensure the service is running."
        }
    except httpx.TimeoutException:
        return {
            "connected": False,
            "provider": provider,
            "model": model,
            "error": f"Connection timeout to {provider}"
        }
    except Exception as e:
        logger.error(f"Connection check failed: {e}", exc_info=True)
        return {
            "connected": False,
            "provider": provider,
            "model": model,
            "error": str(e)
        }
