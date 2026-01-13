"""
Server-Sent Events (SSE) Streaming Support

Provides utilities for SSE-based real-time communication.
More suitable than WebSocket for one-way streaming scenarios.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Standard SSE event types"""
    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    
    # Chat events
    SESSION_START = "session_start"
    MESSAGE_RECEIVED = "message_received"
    PROCESSING_START = "processing_start"
    TOKEN = "token"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MESSAGE_COMPLETE = "message_complete"
    
    # Workflow events
    WORKFLOW_START = "workflow_start"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    WORKFLOW_COMPLETE = "workflow_complete"
    
    # System events
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class StreamEvent:
    """SSE event data structure"""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_sse_format(self) -> str:
        """Convert to SSE format string"""
        lines = []
        
        if self.id:
            lines.append(f"id: {self.id}")
        
        if self.retry:
            lines.append(f"retry: {self.retry}")
        
        lines.append(f"event: {self.event}")
        lines.append(f"data: {json.dumps(self.data, ensure_ascii=False)}")
        lines.append("")  # Empty line to end event
        
        return "\n".join(lines)


class SSEManager:
    """Manager for Server-Sent Events streaming"""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_interval = 30  # seconds
    
    def create_stream(self, stream_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new SSE stream"""
        self.active_streams[stream_id] = {
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "metadata": metadata or {},
            "event_count": 0
        }
        
        logger.info(f"SSE stream created: {stream_id}")
        return stream_id
    
    def close_stream(self, stream_id: str):
        """Close an SSE stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
            logger.info(f"SSE stream closed: {stream_id}")
    
    def update_stream_activity(self, stream_id: str):
        """Update stream last activity timestamp"""
        if stream_id in self.active_streams:
            self.active_streams[stream_id]["last_activity"] = datetime.utcnow()
            self.active_streams[stream_id]["event_count"] += 1
    
    async def heartbeat_generator(self, stream_id: str) -> AsyncGenerator[StreamEvent, None]:
        """Generate heartbeat events to keep connection alive"""
        while stream_id in self.active_streams:
            yield StreamEvent(
                event=StreamEventType.HEARTBEAT.value,
                data={
                    "timestamp": datetime.utcnow().isoformat(),
                    "stream_id": stream_id
                }
            )
            await asyncio.sleep(self.heartbeat_interval)
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """Get statistics about active streams"""
        now = datetime.utcnow()
        
        stats = {
            "total_streams": len(self.active_streams),
            "streams": []
        }
        
        for stream_id, info in self.active_streams.items():
            duration = (now - info["created_at"]).total_seconds()
            idle_time = (now - info["last_activity"]).total_seconds()
            
            stats["streams"].append({
                "stream_id": stream_id,
                "duration_seconds": duration,
                "idle_seconds": idle_time,
                "event_count": info["event_count"],
                "metadata": info["metadata"]
            })
        
        return stats


class ChatStreamManager:
    """Specialized manager for chat streaming"""
    
    def __init__(self):
        self.sse_manager = SSEManager()
        self.active_chats: Dict[str, Dict[str, Any]] = {}
    
    async def start_chat_stream(
        self,
        session_id: str,
        chatflow_id: str,
        user_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Start a chat streaming session"""
        
        # Create stream
        stream_id = f"chat_{session_id}"
        self.sse_manager.create_stream(stream_id, {
            "type": "chat",
            "session_id": session_id,
            "chatflow_id": chatflow_id,
            "user_id": user_id
        })
        
        # Track chat session
        self.active_chats[session_id] = {
            "stream_id": stream_id,
            "chatflow_id": chatflow_id,
            "user_id": user_id,
            "started_at": datetime.utcnow(),
            "message_count": 0
        }
        
        try:
            # Send initial connection event
            yield StreamEvent(
                event=StreamEventType.CONNECT.value,
                data={
                    "session_id": session_id,
                    "chatflow_id": chatflow_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Start heartbeat in background
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(stream_id)
            )
            
            # Keep stream alive until explicitly closed
            while session_id in self.active_chats:
                await asyncio.sleep(1)
            
        except asyncio.CancelledError:
            logger.info(f"Chat stream cancelled: {session_id}")
        except Exception as e:
            logger.error(f"Error in chat stream: {e}", exc_info=True)
            yield StreamEvent(
                event=StreamEventType.ERROR.value,
                data={
                    "error": str(e),
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        finally:
            # Cleanup
            heartbeat_task.cancel()
            self.close_chat_stream(session_id)
    
    async def _heartbeat_loop(self, stream_id: str):
        """Background heartbeat loop"""
        try:
            async for event in self.sse_manager.heartbeat_generator(stream_id):
                # Heartbeat events are handled internally
                pass
        except asyncio.CancelledError:
            pass
    
    def close_chat_stream(self, session_id: str):
        """Close a chat streaming session"""
        if session_id in self.active_chats:
            stream_id = self.active_chats[session_id]["stream_id"]
            self.sse_manager.close_stream(stream_id)
            del self.active_chats[session_id]
            logger.info(f"Chat stream closed: {session_id}")
    
    def get_chat_stats(self) -> Dict[str, Any]:
        """Get chat streaming statistics"""
        return {
            "active_chats": len(self.active_chats),
            "chats": list(self.active_chats.values()),
            "sse_stats": self.sse_manager.get_stream_stats()
        }


class WorkflowStreamManager:
    """Specialized manager for workflow execution streaming"""
    
    def __init__(self):
        self.sse_manager = SSEManager()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
    
    async def start_workflow_stream(
        self,
        execution_id: str,
        workflow_id: str,
        user_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Start a workflow execution streaming session"""
        
        stream_id = f"workflow_{execution_id}"
        self.sse_manager.create_stream(stream_id, {
            "type": "workflow",
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "user_id": user_id
        })
        
        self.active_workflows[execution_id] = {
            "stream_id": stream_id,
            "workflow_id": workflow_id,
            "user_id": user_id,
            "started_at": datetime.utcnow(),
            "step_count": 0
        }
        
        try:
            yield StreamEvent(
                event=StreamEventType.WORKFLOW_START.value,
                data={
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Keep stream alive
            while execution_id in self.active_workflows:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in workflow stream: {e}", exc_info=True)
            yield StreamEvent(
                event=StreamEventType.ERROR.value,
                data={
                    "error": str(e),
                    "execution_id": execution_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        finally:
            self.close_workflow_stream(execution_id)
    
    def close_workflow_stream(self, execution_id: str):
        """Close a workflow streaming session"""
        if execution_id in self.active_workflows:
            stream_id = self.active_workflows[execution_id]["stream_id"]
            self.sse_manager.close_stream(stream_id)
            del self.active_workflows[execution_id]


# Global managers
sse_manager = SSEManager()
chat_stream_manager = ChatStreamManager()
workflow_stream_manager = WorkflowStreamManager()