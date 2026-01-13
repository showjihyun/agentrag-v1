"""
Agent Plugin 실시간 업데이트 시스템
WebSocket/SSE 기반 실시간 상태 동기화
"""
from typing import Dict, Any, List, Optional, Set
import asyncio
import json
import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.core.event_bus.validated_event_bus import EventBus
from backend.core.dependencies import get_redis_client

logger = logging.getLogger(__name__)

class PluginStatusUpdate(BaseModel):
    """플러그인 상태 업데이트 모델"""
    plugin_id: str
    status: str  # 'active', 'inactive', 'error'
    timestamp: str
    metrics: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class PluginExecutionUpdate(BaseModel):
    """플러그인 실행 업데이트 모델"""
    plugin_id: str
    execution_id: str
    status: str  # 'started', 'completed', 'failed'
    progress: Optional[int] = None  # 0-100
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str
    user_id: Optional[str] = None

class PluginRealtimeManager:
    """플러그인 실시간 업데이트 관리자"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus or self._create_event_bus()
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> websockets
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self._initialized = False
    
    def _create_event_bus(self) -> EventBus:
        """Event Bus 인스턴스 생성"""
        redis_client = get_redis_client()
        return EventBus(redis_client)
    
    async def initialize(self):
        """실시간 매니저 초기화"""
        if self._initialized:
            return
        
        # 이벤트 구독
        await self.event_bus.subscribe("plugin_status_changed", self._handle_status_change)
        await self.event_bus.subscribe("plugin_execution_started", self._handle_execution_started)
        await self.event_bus.subscribe("plugin_execution_progress", self._handle_execution_progress)
        await self.event_bus.subscribe("plugin_execution_completed", self._handle_execution_completed)
        await self.event_bus.subscribe("plugin_execution_failed", self._handle_execution_failed)
        
        self._initialized = True
        logger.info("Plugin Realtime Manager initialized")
    
    async def connect_websocket(self, websocket: WebSocket, user_id: str):
        """WebSocket 연결 관리"""
        await websocket.accept()
        
        # 사용자별 연결 관리
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # 연결 메타데이터 저장
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat()
        }
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # 초기 상태 전송
        await self._send_initial_state(websocket, user_id)
    
    async def disconnect_websocket(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        if websocket in self.connection_metadata:
            user_id = self.connection_metadata[websocket]["user_id"]
            
            # 연결 목록에서 제거
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # 메타데이터 제거
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def _send_initial_state(self, websocket: WebSocket, user_id: str):
        """초기 상태 전송"""
        try:
            # 사용자의 플러그인 상태 조회
            initial_data = {
                "type": "initial_state",
                "data": {
                    "plugins": await self._get_user_plugins(user_id),
                    "system_health": await self._get_system_health(),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await websocket.send_text(json.dumps(initial_data))
        except Exception as e:
            logger.error(f"Failed to send initial state: {e}")
    
    async def _get_user_plugins(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 플러그인 목록 조회"""
        # TODO: 실제 플러그인 서비스와 연동
        return []
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        # TODO: 실제 시스템 상태 서비스와 연동
        return {
            "status": "healthy",
            "active_plugins": 0,
            "total_executions": 0,
            "average_response_time": 0,
            "error_rate": 0
        }
    
    async def _handle_status_change(self, event_data: Dict[str, Any]):
        """플러그인 상태 변경 이벤트 처리"""
        try:
            update = PluginStatusUpdate(**event_data)
            
            # 관련 사용자들에게 브로드캐스트
            await self._broadcast_to_users(
                user_ids=[update.user_id] if update.user_id else None,
                message={
                    "type": "plugin_status_update",
                    "data": update.dict()
                }
            )
        except Exception as e:
            logger.error(f"Failed to handle status change: {e}")
    
    async def _handle_execution_started(self, event_data: Dict[str, Any]):
        """플러그인 실행 시작 이벤트 처리"""
        try:
            update = PluginExecutionUpdate(**event_data)
            
            await self._broadcast_to_users(
                user_ids=[update.user_id] if update.user_id else None,
                message={
                    "type": "plugin_execution_started",
                    "data": update.dict()
                }
            )
        except Exception as e:
            logger.error(f"Failed to handle execution started: {e}")
    
    async def _handle_execution_progress(self, event_data: Dict[str, Any]):
        """플러그인 실행 진행 이벤트 처리"""
        try:
            update = PluginExecutionUpdate(**event_data)
            
            await self._broadcast_to_users(
                user_ids=[update.user_id] if update.user_id else None,
                message={
                    "type": "plugin_execution_progress",
                    "data": update.dict()
                }
            )
        except Exception as e:
            logger.error(f"Failed to handle execution progress: {e}")
    
    async def _handle_execution_completed(self, event_data: Dict[str, Any]):
        """플러그인 실행 완료 이벤트 처리"""
        try:
            update = PluginExecutionUpdate(**event_data)
            
            await self._broadcast_to_users(
                user_ids=[update.user_id] if update.user_id else None,
                message={
                    "type": "plugin_execution_completed",
                    "data": update.dict()
                }
            )
        except Exception as e:
            logger.error(f"Failed to handle execution completed: {e}")
    
    async def _handle_execution_failed(self, event_data: Dict[str, Any]):
        """플러그인 실행 실패 이벤트 처리"""
        try:
            update = PluginExecutionUpdate(**event_data)
            
            await self._broadcast_to_users(
                user_ids=[update.user_id] if update.user_id else None,
                message={
                    "type": "plugin_execution_failed",
                    "data": update.dict()
                }
            )
        except Exception as e:
            logger.error(f"Failed to handle execution failed: {e}")
    
    async def _broadcast_to_users(
        self, 
        user_ids: Optional[List[str]] = None, 
        message: Dict[str, Any] = None
    ):
        """특정 사용자들에게 메시지 브로드캐스트"""
        if not message:
            return
        
        message_text = json.dumps(message)
        
        # 모든 사용자에게 브로드캐스트
        if user_ids is None:
            for user_connections in self.active_connections.values():
                await self._send_to_connections(user_connections, message_text)
        else:
            # 특정 사용자들에게만 브로드캐스트
            for user_id in user_ids:
                if user_id in self.active_connections:
                    await self._send_to_connections(
                        self.active_connections[user_id], 
                        message_text
                    )
    
    async def _send_to_connections(self, connections: Set[WebSocket], message: str):
        """연결된 WebSocket들에게 메시지 전송"""
        disconnected = set()
        
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to websocket: {e}")
                disconnected.add(websocket)
        
        # 연결이 끊어진 WebSocket 정리
        for websocket in disconnected:
            await self.disconnect_websocket(websocket)
    
    async def publish_status_update(
        self, 
        plugin_id: str, 
        status: str, 
        user_id: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """플러그인 상태 업데이트 발행"""
        update_data = {
            "plugin_id": plugin_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "metrics": metrics
        }
        
        await self.event_bus.publish("plugin_status_changed", update_data)
    
    async def publish_execution_update(
        self,
        plugin_id: str,
        execution_id: str,
        status: str,
        user_id: Optional[str] = None,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """플러그인 실행 업데이트 발행"""
        update_data = {
            "plugin_id": plugin_id,
            "execution_id": execution_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "progress": progress,
            "result": result,
            "error": error
        }
        
        event_name = f"plugin_execution_{status}"
        await self.event_bus.publish(event_name, update_data)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계 조회"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "active_users": len(self.active_connections),
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.active_connections.items()
            },
            "timestamp": datetime.now().isoformat()
        }

# 전역 인스턴스
plugin_realtime_manager = PluginRealtimeManager()