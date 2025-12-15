"""
Real-time Updates WebSocket API
실시간 업데이트 WebSocket API - 성능 최적화
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from backend.services.olympics.agent_olympics_manager import get_olympics_manager
from backend.services.emotional.emotional_ai_service import get_emotional_ai_service
from backend.services.evolution.workflow_dna_service import get_workflow_dna_service
from backend.core.performance_optimizer import get_performance_optimizer
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/realtime",
    tags=["realtime-updates"]
)

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결들
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 구독 정보
        self.subscriptions: Dict[str, Set[str]] = {
            "olympics_progress": set(),
            "olympics_leaderboard": set(),
            "emotional_ai_updates": set(),
            "workflow_dna_evolution": set(),
            "system_metrics": set()
        }
        
        # 연결별 메타데이터
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 성능 최적화
        self.performance_optimizer = get_performance_optimizer()
        self.update_throttling = {}
        
        # 백그라운드 업데이트 시작
        asyncio.create_task(self._start_update_loops())
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """클라이언트 연결"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "subscriptions": set(),
            "message_count": 0
        }
        
        logger.info(f"WebSocket client connected: {client_id}")
        
        # 연결 확인 메시지 전송
        await self.send_personal_message(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "available_channels": list(self.subscriptions.keys())
        })
    
    def disconnect(self, client_id: str):
        """클라이언트 연결 해제"""
        if client_id in self.active_connections:
            # 모든 구독에서 제거
            for channel in self.subscriptions:
                self.subscriptions[channel].discard(client_id)
            
            # 연결 정보 제거
            del self.active_connections[client_id]
            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]
            
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_personal_message(self, client_id: str, message: dict):
        """개별 클라이언트에게 메시지 전송"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message))
                    
                    # 메타데이터 업데이트
                    if client_id in self.connection_metadata:
                        self.connection_metadata[client_id]["last_activity"] = datetime.now()
                        self.connection_metadata[client_id]["message_count"] += 1
                else:
                    # 연결이 끊어진 경우 정리
                    self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """채널 구독자들에게 브로드캐스트"""
        if channel in self.subscriptions:
            subscribers = list(self.subscriptions[channel])
            
            # 스로틀링 적용
            throttle_key = f"broadcast_{channel}"
            should_send = await self.performance_optimizer.throttle_updates(
                throttle_key,
                self._do_broadcast,
                subscribers,
                message
            )
            
            if not should_send:
                logger.debug(f"Broadcast throttled for channel: {channel}")
    
    async def _do_broadcast(self, subscribers: List[str], message: dict):
        """실제 브로드캐스트 수행"""
        if subscribers:
            # 메시지에 타임스탬프 추가
            message["timestamp"] = datetime.now().isoformat()
            
            # 병렬로 전송
            tasks = []
            for client_id in subscribers:
                if client_id in self.active_connections:
                    tasks.append(self.send_personal_message(client_id, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, client_id: str, channel: str) -> bool:
        """채널 구독"""
        if channel in self.subscriptions and client_id in self.active_connections:
            self.subscriptions[channel].add(client_id)
            
            # 메타데이터 업데이트
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]["subscriptions"].add(channel)
            
            logger.info(f"Client {client_id} subscribed to {channel}")
            return True
        return False
    
    def unsubscribe(self, client_id: str, channel: str) -> bool:
        """채널 구독 해제"""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(client_id)
            
            # 메타데이터 업데이트
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]["subscriptions"].discard(channel)
            
            logger.info(f"Client {client_id} unsubscribed from {channel}")
            return True
        return False
    
    async def _start_update_loops(self):
        """백그라운드 업데이트 루프 시작"""
        # 올림픽 진행률 업데이트
        asyncio.create_task(self._olympics_progress_loop())
        # 감정 AI 업데이트
        asyncio.create_task(self._emotional_ai_loop())
        # 워크플로우 DNA 진화 업데이트
        asyncio.create_task(self._workflow_dna_loop())
        # 시스템 메트릭 업데이트
        asyncio.create_task(self._system_metrics_loop())
    
    async def _olympics_progress_loop(self):
        """올림픽 진행률 업데이트 루프"""
        while True:
            try:
                if self.subscriptions["olympics_progress"]:
                    olympics_manager = get_olympics_manager()
                    active_competitions = await olympics_manager.get_active_competitions()
                    
                    for competition in active_competitions:
                        comp_id = competition["id"]
                        progress = await olympics_manager.get_live_progress(comp_id)
                        
                        if progress:
                            # 순위 계산
                            rankings = []
                            for agent in competition["participants"]:
                                agent_progress = progress.get(agent["id"], 0.0)
                                rankings.append({
                                    "agent_id": agent["id"],
                                    "name": agent["name"],
                                    "avatar": agent["avatar"],
                                    "progress": agent_progress
                                })
                            
                            rankings.sort(key=lambda x: x["progress"], reverse=True)
                            for i, ranking in enumerate(rankings):
                                ranking["position"] = i + 1
                            
                            await self.broadcast_to_channel("olympics_progress", {
                                "type": "olympics_progress_update",
                                "competition_id": comp_id,
                                "competition_name": competition["name"],
                                "progress": progress,
                                "rankings": rankings,
                                "spectators": competition.get("spectators", 0),
                                "is_completed": max(progress.values()) >= 100.0 if progress else False
                            })
                
                await asyncio.sleep(1)  # 1초마다 업데이트
                
            except Exception as e:
                logger.error(f"Olympics progress loop error: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _emotional_ai_loop(self):
        """감정 AI 업데이트 루프"""
        while True:
            try:
                if self.subscriptions["emotional_ai_updates"]:
                    emotional_ai = get_emotional_ai_service()
                    
                    # 사용자별 감정 상태 업데이트
                    for user_id in emotional_ai.users.keys():
                        user_emotion = await emotional_ai.get_user_emotion(user_id)
                        
                        if user_emotion:
                            await self.broadcast_to_channel("emotional_ai_updates", {
                                "type": "emotion_update",
                                "user_id": user_id,
                                "emotion": user_emotion["current_emotion"],
                                "wellness_metrics": user_emotion["wellness_metrics"],
                                "adaptive_theme": await emotional_ai.get_adaptive_theme(user_id)
                            })
                
                await asyncio.sleep(30)  # 30초마다 업데이트
                
            except Exception as e:
                logger.error(f"Emotional AI loop error: {str(e)}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _workflow_dna_loop(self):
        """워크플로우 DNA 진화 업데이트 루프"""
        while True:
            try:
                if self.subscriptions["workflow_dna_evolution"]:
                    dna_service = get_workflow_dna_service()
                    
                    # 활성 실험들의 진화 상태 업데이트
                    experiments = await dna_service.get_experiments()
                    
                    for experiment in experiments:
                        if experiment["status"] == "running":
                            exp_id = experiment["id"]
                            analytics = await dna_service.get_analytics(exp_id)
                            
                            if analytics:
                                await self.broadcast_to_channel("workflow_dna_evolution", {
                                    "type": "evolution_update",
                                    "experiment_id": exp_id,
                                    "experiment_name": experiment["name"],
                                    "current_generation": experiment["current_generation"],
                                    "best_fitness": analytics.get("average_fitness", 0),
                                    "genetic_diversity": analytics.get("genetic_diversity", 0),
                                    "elite_organisms": analytics.get("elite_organisms", 0)
                                })
                
                await asyncio.sleep(5)  # 5초마다 업데이트
                
            except Exception as e:
                logger.error(f"Workflow DNA loop error: {str(e)}", exc_info=True)
                await asyncio.sleep(30)
    
    async def _system_metrics_loop(self):
        """시스템 메트릭 업데이트 루프"""
        while True:
            try:
                if self.subscriptions["system_metrics"]:
                    metrics = self.performance_optimizer.get_performance_metrics()
                    
                    await self.broadcast_to_channel("system_metrics", {
                        "type": "system_metrics_update",
                        "metrics": metrics,
                        "active_connections": len(self.active_connections),
                        "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values())
                    })
                
                await asyncio.sleep(10)  # 10초마다 업데이트
                
            except Exception as e:
                logger.error(f"System metrics loop error: {str(e)}", exc_info=True)
                await asyncio.sleep(30)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계 조회"""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions_by_channel": {
                channel: len(subscribers) 
                for channel, subscribers in self.subscriptions.items()
            },
            "connection_metadata": {
                client_id: {
                    "connected_at": metadata["connected_at"].isoformat(),
                    "last_activity": metadata["last_activity"].isoformat(),
                    "message_count": metadata["message_count"],
                    "subscriptions": list(metadata["subscriptions"])
                }
                for client_id, metadata in self.connection_metadata.items()
            }
        }

# 전역 연결 관리자
manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket 엔드포인트
    
    실시간 업데이트를 위한 WebSocket 연결을 제공합니다.
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    channel = message.get("channel")
                    if channel:
                        success = manager.subscribe(client_id, channel)
                        await manager.send_personal_message(client_id, {
                            "type": "subscription_response",
                            "channel": channel,
                            "success": success,
                            "message": f"Subscribed to {channel}" if success else f"Failed to subscribe to {channel}"
                        })
                
                elif message_type == "unsubscribe":
                    channel = message.get("channel")
                    if channel:
                        success = manager.unsubscribe(client_id, channel)
                        await manager.send_personal_message(client_id, {
                            "type": "unsubscription_response",
                            "channel": channel,
                            "success": success,
                            "message": f"Unsubscribed from {channel}" if success else f"Failed to unsubscribe from {channel}"
                        })
                
                elif message_type == "ping":
                    await manager.send_personal_message(client_id, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif message_type == "get_stats":
                    stats = manager.get_connection_stats()
                    await manager.send_personal_message(client_id, {
                        "type": "stats_response",
                        "stats": stats
                    })
                
                else:
                    await manager.send_personal_message(client_id, {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
            
            except json.JSONDecodeError:
                await manager.send_personal_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}", exc_info=True)
        manager.disconnect(client_id)

@router.get("/connections/stats")
async def get_connection_stats():
    """
    연결 통계 조회
    
    현재 WebSocket 연결 상태와 통계를 반환합니다.
    """
    try:
        stats = manager.get_connection_stats()
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get connection stats: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/broadcast/{channel}")
async def broadcast_message(channel: str, message: dict):
    """
    채널 브로드캐스트
    
    지정된 채널의 모든 구독자에게 메시지를 브로드캐스트합니다.
    """
    try:
        if channel not in manager.subscriptions:
            return {
                "success": False,
                "error": f"Unknown channel: {channel}",
                "available_channels": list(manager.subscriptions.keys())
            }
        
        await manager.broadcast_to_channel(channel, {
            "type": "custom_broadcast",
            "channel": channel,
            "data": message
        })
        
        return {
            "success": True,
            "channel": channel,
            "subscribers": len(manager.subscriptions[channel]),
            "message": "Broadcast sent successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }