"""
Gemini Real-time Execution API
실시간 멀티모달 워크플로우 실행 API (Server-Sent Events)
"""

import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.multimodal.realtime_processor import get_realtime_processor, ExecutionStatus
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/gemini-realtime", tags=["Gemini Real-time"])

# ============================================================================
# Request/Response Models
# ============================================================================

class WorkflowExecutionRequest(BaseModel):
    """워크플로우 실행 요청"""
    workflow_id: str = Field(..., description="워크플로우 ID")
    workflow_data: Dict[str, Any] = Field(..., description="워크플로우 정의 데이터")
    execution_name: Optional[str] = Field(None, description="실행 이름")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="실행 파라미터")

class ExecutionResponse(BaseModel):
    """실행 응답"""
    execution_id: str
    status: str
    message: str
    stream_url: Optional[str] = None

class ExecutionStatusResponse(BaseModel):
    """실행 상태 응답"""
    execution_id: str
    workflow_id: str
    status: str
    progress: float
    current_block: Optional[str]
    completed_blocks: int
    total_blocks: int
    start_time: float
    duration: Optional[float] = None
    results: Dict[str, Any]
    errors: list

# ============================================================================
# Real-time Execution Endpoints
# ============================================================================

@router.post("/execute", response_model=ExecutionResponse)
async def start_workflow_execution(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    멀티모달 워크플로우 실시간 실행 시작
    
    실행을 시작하고 Server-Sent Events 스트림 URL을 반환합니다.
    클라이언트는 반환된 stream_url로 실시간 진행 상황을 구독할 수 있습니다.
    """
    try:
        # 실행 ID 생성
        execution_id = str(uuid.uuid4())
        
        # 워크플로우 데이터 검증
        if not request.workflow_data.get("nodes"):
            raise HTTPException(status_code=400, detail="Workflow must contain at least one node")
        
        # 실시간 프로세서 가져오기
        processor = get_realtime_processor()
        
        # 실행 상태 로깅
        logger.info(
            f"Starting workflow execution",
            extra={
                'execution_id': execution_id,
                'workflow_id': request.workflow_id,
                'user_id': current_user.id,
                'node_count': len(request.workflow_data.get("nodes", []))
            }
        )
        
        # 백그라운드에서 실행 시작 (실제로는 즉시 스트림 반환)
        # background_tasks.add_task(
        #     processor.execute_workflow_stream,
        #     request.workflow_id,
        #     execution_id,
        #     request.workflow_data,
        #     str(current_user.id)
        # )
        
        return ExecutionResponse(
            execution_id=execution_id,
            status="started",
            message="Workflow execution started successfully",
            stream_url=f"/api/agent-builder/gemini-realtime/stream/{execution_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start workflow execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream/{execution_id}")
async def stream_execution_progress(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    워크플로우 실행 진행 상황 실시간 스트리밍 (Server-Sent Events)
    
    클라이언트는 이 엔드포인트에 연결하여 실시간으로 실행 진행 상황을 받을 수 있습니다.
    """
    
    async def event_stream():
        """SSE 이벤트 스트림 생성기"""
        try:
            processor = get_realtime_processor()
            
            # 더미 워크플로우 데이터 (실제로는 DB에서 조회)
            workflow_data = {
                "nodes": [
                    {
                        "id": "start",
                        "type": "manual_trigger",
                        "name": "시작",
                        "config": {}
                    },
                    {
                        "id": "gemini_vision",
                        "type": "gemini_vision",
                        "name": "이미지 분석",
                        "config": {
                            "model": "gemini-1.5-flash",
                            "prompt": "이미지를 분석해주세요"
                        }
                    },
                    {
                        "id": "gemini_audio",
                        "type": "gemini_audio",
                        "name": "음성 처리",
                        "config": {
                            "model": "gemini-1.5-flash",
                            "context": "음성을 분석해주세요"
                        }
                    },
                    {
                        "id": "http_request",
                        "type": "http_request",
                        "name": "API 호출",
                        "config": {
                            "url": "https://api.example.com/webhook",
                            "method": "POST"
                        }
                    },
                    {
                        "id": "end",
                        "type": "end",
                        "name": "완료",
                        "config": {}
                    }
                ],
                "connections": []
            }
            
            # 실행 스트림 시작
            async for event in processor.execute_workflow_stream(
                workflow_id="demo_workflow",
                execution_id=execution_id,
                workflow_data=workflow_data,
                user_id=str(current_user.id)
            ):
                # SSE 형식으로 이벤트 전송
                event_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_data}\n\n"
                
                # 연결 유지를 위한 짧은 대기
                await asyncio.sleep(0.1)
            
            # 스트림 종료
            yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream execution failed: {str(e)}", exc_info=True)
            error_event = {
                "type": "error",
                "timestamp": "2024-12-12T10:00:00Z",
                "data": {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/status/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    워크플로우 실행 상태 조회
    """
    try:
        processor = get_realtime_processor()
        status = processor.get_execution_status(execution_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # 사용자 권한 확인
        if status.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ExecutionStatusResponse(
            execution_id=execution_id,
            workflow_id=status["workflow_id"],
            status=status["status"],
            progress=status["progress"],
            current_block=status["current_block"],
            completed_blocks=len(status["completed_blocks"]),
            total_blocks=status["total_blocks"],
            start_time=status["start_time"],
            duration=status.get("duration"),
            results=status["results"],
            errors=status["errors"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel/{execution_id}")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    워크플로우 실행 취소
    """
    try:
        processor = get_realtime_processor()
        
        # 실행 상태 확인
        status = processor.get_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # 사용자 권한 확인
        if status.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 실행 취소
        success = await processor.cancel_execution(execution_id)
        
        if success:
            logger.info(f"Execution {execution_id} cancelled by user {current_user.id}")
            return {"success": True, "message": "Execution cancelled successfully"}
        else:
            return {"success": False, "message": "Failed to cancel execution"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_executions(
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 활성 실행 목록 조회
    """
    try:
        processor = get_realtime_processor()
        executions = processor.get_active_executions(user_id=str(current_user.id))
        
        return {
            "executions": executions,
            "total": len(executions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active executions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Demo Endpoints
# ============================================================================

@router.post("/demo/quick-start")
async def demo_quick_start(
    current_user: User = Depends(get_current_user)
):
    """
    데모용 빠른 시작 - 샘플 멀티모달 워크플로우 실행
    """
    try:
        # 샘플 워크플로우 생성
        sample_workflow = {
            "nodes": [
                {
                    "id": "trigger",
                    "type": "manual_trigger",
                    "name": "수동 트리거",
                    "config": {"title": "멀티모달 데모 시작"}
                },
                {
                    "id": "vision_analysis",
                    "type": "gemini_vision",
                    "name": "이미지 분석",
                    "config": {
                        "model": "gemini-1.5-flash",
                        "prompt": "이 이미지의 주요 내용을 분석해주세요",
                        "temperature": 0.7
                    }
                },
                {
                    "id": "audio_processing",
                    "type": "gemini_audio",
                    "name": "음성 처리",
                    "config": {
                        "model": "gemini-1.5-flash",
                        "context": "음성 내용을 요약해주세요"
                    }
                },
                {
                    "id": "result_webhook",
                    "type": "http_request",
                    "name": "결과 전송",
                    "config": {
                        "url": "https://webhook.site/demo",
                        "method": "POST"
                    }
                }
            ],
            "connections": [
                {"from": "trigger", "to": "vision_analysis"},
                {"from": "vision_analysis", "to": "audio_processing"},
                {"from": "audio_processing", "to": "result_webhook"}
            ]
        }
        
        # 실행 시작
        execution_id = str(uuid.uuid4())
        
        return {
            "execution_id": execution_id,
            "workflow_name": "멀티모달 데모 워크플로우",
            "stream_url": f"/api/agent-builder/gemini-realtime/stream/{execution_id}",
            "estimated_duration": "약 10초",
            "blocks": [
                {"name": "이미지 분석", "type": "gemini_vision", "duration": "3초"},
                {"name": "음성 처리", "type": "gemini_audio", "duration": "4초"},
                {"name": "결과 전송", "type": "http_request", "duration": "1초"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Demo quick start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    실시간 실행 서비스 상태 확인
    """
    try:
        processor = get_realtime_processor()
        active_count = len(processor.get_active_executions())
        
        return {
            "status": "healthy",
            "service": "gemini_realtime_execution",
            "active_executions": active_count,
            "features": [
                "real_time_streaming",
                "multimodal_processing",
                "execution_monitoring",
                "cancellation_support"
            ],
            "timestamp": "2024-12-12T10:00:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "gemini_realtime_execution"
        }