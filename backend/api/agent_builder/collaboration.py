"""
Real-time Collaboration API

Provides WebSocket-based real-time collaboration for workflows and agents.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Set, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import json
import asyncio
from backend.core.dependencies import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/collaboration", tags=["Collaboration"])


# Models
class UserPresence(BaseModel):
    user_id: str
    username: str
    email: str
    color: str
    cursor_position: Optional[Dict] = None
    selection: Optional[Dict] = None
    last_seen: str


class CollaborationEvent(BaseModel):
    type: str  # user-joined, user-left, change, cursor, selection, conflict
    user_id: str
    timestamp: str
    data: Dict


class Change(BaseModel):
    type: str  # insert, delete, update
    path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    version: int


class Conflict(BaseModel):
    id: str
    type: str
    path: str
    local_value: Any
    remote_value: Any
    timestamp: str


# Connection Manager
class CollaborationManager:
    def __init__(self):
        # resource_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # resource_id -> user_id -> UserPresence
        self.user_presence: Dict[str, Dict[str, UserPresence]] = {}
        # resource_id -> version
        self.resource_versions: Dict[str, int] = {}
        # resource_id -> lock info
        self.locks: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, resource_type: str, resource_id: str, user_id: str):
        """Connect a user to a resource"""
        await websocket.accept()
        
        key = f"{resource_type}:{resource_id}"
        
        if key not in self.active_connections:
            self.active_connections[key] = set()
            self.user_presence[key] = {}
            self.resource_versions[key] = 0
        
        self.active_connections[key].add(websocket)
        
        # Add user presence
        self.user_presence[key][user_id] = UserPresence(
            user_id=user_id,
            username=f"User {user_id}",
            email=f"user{user_id}@example.com",
            color=self._generate_color(user_id),
            last_seen=datetime.utcnow().isoformat()
        )
        
        # Notify others
        await self.broadcast(key, {
            "type": "user-joined",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "user": self.user_presence[key][user_id].dict(),
                "active_users": [u.dict() for u in self.user_presence[key].values()]
            }
        }, exclude=websocket)
        
        # Send current state to new user
        await websocket.send_json({
            "type": "initial-state",
            "data": {
                "active_users": [u.dict() for u in self.user_presence[key].values()],
                "version": self.resource_versions[key]
            }
        })
    
    def disconnect(self, websocket: WebSocket, resource_type: str, resource_id: str, user_id: str):
        """Disconnect a user from a resource"""
        key = f"{resource_type}:{resource_id}"
        
        if key in self.active_connections:
            self.active_connections[key].discard(websocket)
            
            if user_id in self.user_presence.get(key, {}):
                del self.user_presence[key][user_id]
            
            # Clean up if no connections
            if not self.active_connections[key]:
                del self.active_connections[key]
                if key in self.user_presence:
                    del self.user_presence[key]
                if key in self.resource_versions:
                    del self.resource_versions[key]
    
    async def broadcast(self, key: str, message: dict, exclude: Optional[WebSocket] = None):
        """Broadcast message to all connected users"""
        if key not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[key]:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.add(connection)
        
        # Remove disconnected
        for connection in disconnected:
            self.active_connections[key].discard(connection)
    
    async def handle_change(self, key: str, user_id: str, change: dict):
        """Handle a change event"""
        # Increment version
        self.resource_versions[key] = self.resource_versions.get(key, 0) + 1
        
        # Broadcast change
        await self.broadcast(key, {
            "type": "change",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "change": change,
                "version": self.resource_versions[key]
            }
        })
    
    async def handle_cursor(self, key: str, user_id: str, cursor: dict):
        """Handle cursor movement"""
        if key in self.user_presence and user_id in self.user_presence[key]:
            self.user_presence[key][user_id].cursor_position = cursor
            self.user_presence[key][user_id].last_seen = datetime.utcnow().isoformat()
        
        await self.broadcast(key, {
            "type": "cursor",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"cursor": cursor}
        })
    
    async def handle_selection(self, key: str, user_id: str, selection: dict):
        """Handle selection change"""
        if key in self.user_presence and user_id in self.user_presence[key]:
            self.user_presence[key][user_id].selection = selection
            self.user_presence[key][user_id].last_seen = datetime.utcnow().isoformat()
        
        await self.broadcast(key, {
            "type": "selection",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"selection": selection}
        })
    
    def _generate_color(self, user_id: str) -> str:
        """Generate a consistent color for a user"""
        colors = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
            "#8B5CF6", "#EC4899", "#14B8A6", "#F97316"
        ]
        # Simple hash to pick color
        hash_val = sum(ord(c) for c in user_id)
        return colors[hash_val % len(colors)]


# Global manager instance
manager = CollaborationManager()


# WebSocket endpoint
@router.websocket("/ws/{resource_type}/{resource_id}")
async def collaboration_websocket(
    websocket: WebSocket,
    resource_type: str,
    resource_id: str,
    user_id: str = "anonymous"
):
    """
    WebSocket endpoint for real-time collaboration
    
    resource_type: agent, workflow, block
    resource_id: UUID of the resource
    user_id: User identifier (from query param or auth)
    """
    await manager.connect(websocket, resource_type, resource_id, user_id)
    key = f"{resource_type}:{resource_id}"
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            event_type = message.get("type")
            
            if event_type == "change":
                await manager.handle_change(key, user_id, message.get("data"))
            
            elif event_type == "cursor":
                await manager.handle_cursor(key, user_id, message.get("data"))
            
            elif event_type == "selection":
                await manager.handle_selection(key, user_id, message.get("data"))
            
            elif event_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown event type: {event_type}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, resource_type, resource_id, user_id)
        
        # Notify others
        await manager.broadcast(key, {
            "type": "user-left",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "active_users": [u.dict() for u in manager.user_presence.get(key, {}).values()]
            }
        })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, resource_type, resource_id, user_id)


# REST endpoints for collaboration info
@router.get("/{resource_type}/{resource_id}/users")
async def get_active_users(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db)
):
    """
    Get currently active users for a resource
    """
    try:
        key = f"{resource_type}:{resource_id}"
        users = manager.user_presence.get(key, {})
        
        return {
            "active_users": [u.dict() for u in users.values()],
            "count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resource_type}/{resource_id}/version")
async def get_resource_version(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current version of a resource
    """
    try:
        key = f"{resource_type}:{resource_id}"
        version = manager.resource_versions.get(key, 0)
        
        return {
            "version": version,
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get resource version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{resource_type}/{resource_id}/lock")
async def acquire_lock(
    resource_type: str,
    resource_id: str,
    user_id: str,
    timeout: int = 300,  # 5 minutes
    db: Session = Depends(get_db)
):
    """
    Acquire a lock on a resource
    """
    try:
        key = f"{resource_type}:{resource_id}"
        
        # Check if already locked
        if key in manager.locks:
            lock_info = manager.locks[key]
            if lock_info["user_id"] != user_id:
                return {
                    "success": False,
                    "message": "Resource is locked by another user",
                    "locked_by": lock_info["user_id"],
                    "locked_at": lock_info["locked_at"]
                }
        
        # Acquire lock
        manager.locks[key] = {
            "user_id": user_id,
            "locked_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=timeout)).isoformat()
        }
        
        return {
            "success": True,
            "message": "Lock acquired",
            "expires_at": manager.locks[key]["expires_at"]
        }
        
    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{resource_type}/{resource_id}/lock")
async def release_lock(
    resource_type: str,
    resource_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Release a lock on a resource
    """
    try:
        key = f"{resource_type}:{resource_id}"
        
        if key in manager.locks:
            if manager.locks[key]["user_id"] == user_id:
                del manager.locks[key]
                return {"success": True, "message": "Lock released"}
            else:
                raise HTTPException(
                    status_code=403,
                    detail="You don't own this lock"
                )
        
        return {"success": True, "message": "No lock to release"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to release lock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import timedelta
from datetime import timedelta
