"""
Agent Plugin WebSocket API
실시간 플러그인 상태 업데이트를 위한 WebSocket 엔드포인트
"""
from typing import Dict, Any
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException

from backend.core.dependencies import get_current_user_websocket
from backend.core.realtime.plugin_realtime import plugin_realtime_manager
from backend.core.cache.plugin_cache import plugin_cache_manager
from backend.core.monitoring.enhanced_plugin_monitor import enhanced_plugin_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-plugins", tags=["Agent Plugin WebSocket"])

@router.websocket("/ws/{user_id}")
async def plugin_websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """플러그인 실시간 업데이트 WebSocket 엔드포인트"""
    try:
        # 실시간 매니저 초기화
        await plugin_realtime_manager.initialize()
        
        # WebSocket 연결
        await plugin_realtime_manager.connect_websocket(websocket, user_id)
        
        logger.info(f"WebSocket connected for user: {user_id}")
        
        try:
            while True:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 메시지 타입에 따른 처리
                await handle_websocket_message(websocket, user_id, message)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            await websocket.close(code=1011, reason="Internal server error")
        finally:
            # 연결 정리
            await plugin_realtime_manager.disconnect_websocket(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011, reason="Connection failed")

async def handle_websocket_message(
    websocket: WebSocket, 
    user_id: str, 
    message: Dict[str, Any]
):
    """WebSocket 메시지 처리"""
    try:
        message_type = message.get("type")
        
        if message_type == "ping":
            # Ping-Pong for connection health
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": message.get("timestamp")
            }))
            
        elif message_type == "subscribe_plugin":
            # 특정 플러그인 구독
            plugin_id = message.get("plugin_id")
            if plugin_id:
                await handle_plugin_subscription(websocket, user_id, plugin_id)
                
        elif message_type == "unsubscribe_plugin":
            # 플러그인 구독 해제
            plugin_id = message.get("plugin_id")
            if plugin_id:
                await handle_plugin_unsubscription(websocket, user_id, plugin_id)
                
        elif message_type == "get_real_time_metrics":
            # 실시간 메트릭 요청
            await handle_real_time_metrics_request(websocket, user_id)
            
        elif message_type == "get_cache_stats":
            # 캐시 통계 요청
            await handle_cache_stats_request(websocket, user_id)
            
        else:
            # 알 수 없는 메시지 타입
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Message processing failed"
        }))

async def handle_plugin_subscription(
    websocket: WebSocket, 
    user_id: str, 
    plugin_id: str
):
    """플러그인 구독 처리"""
    try:
        # 구독 확인 응답
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "plugin_id": plugin_id,
            "message": f"Subscribed to plugin: {plugin_id}"
        }))
        
        # 플러그인 초기 상태 전송
        # TODO: 실제 플러그인 상태 조회 로직 구현
        initial_status = {
            "type": "plugin_status",
            "plugin_id": plugin_id,
            "status": "active",  # 실제 상태로 대체
            "metrics": {
                "execution_count": 0,
                "success_rate": 100.0,
                "avg_response_time": 0.0
            }
        }
        
        await websocket.send_text(json.dumps(initial_status))
        
    except Exception as e:
        logger.error(f"Plugin subscription error: {e}")

async def handle_plugin_unsubscription(
    websocket: WebSocket, 
    user_id: str, 
    plugin_id: str
):
    """플러그인 구독 해제 처리"""
    try:
        await websocket.send_text(json.dumps({
            "type": "unsubscription_confirmed",
            "plugin_id": plugin_id,
            "message": f"Unsubscribed from plugin: {plugin_id}"
        }))
        
    except Exception as e:
        logger.error(f"Plugin unsubscription error: {e}")

async def handle_real_time_metrics_request(websocket: WebSocket, user_id: str):
    """실시간 메트릭 요청 처리"""
    try:
        # 실시간 메트릭 조회
        metrics = await enhanced_plugin_monitor.get_real_time_metrics()
        
        await websocket.send_text(json.dumps({
            "type": "real_time_metrics",
            "data": metrics
        }))
        
    except Exception as e:
        logger.error(f"Real-time metrics request error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to get real-time metrics"
        }))

async def handle_cache_stats_request(websocket: WebSocket, user_id: str):
    """캐시 통계 요청 처리"""
    try:
        # 캐시 통계 조회
        cache_stats = await plugin_cache_manager.get_cache_stats()
        
        await websocket.send_text(json.dumps({
            "type": "cache_stats",
            "data": cache_stats
        }))
        
    except Exception as e:
        logger.error(f"Cache stats request error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to get cache stats"
        }))

@router.get("/ws/stats")
async def get_websocket_stats():
    """WebSocket 연결 통계 조회"""
    try:
        stats = await plugin_realtime_manager.get_connection_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"WebSocket stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebSocket stats")