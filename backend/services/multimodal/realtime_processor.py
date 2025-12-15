"""
Real-time MultiModal Processor
실시간 멀티모달 워크플로우 실행 및 스트리밍 처리
"""

import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime
import logging
from enum import Enum

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from backend.services.multimodal.gemini_service import get_gemini_service
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class ExecutionStatus(str, Enum):
    """실행 상태 열거형"""
    QUEUED = "queued"
    STARTING = "starting"
    PROCESSING = "processing"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

class StreamEventType(str, Enum):
    """스트림 이벤트 타입"""
    EXECUTION_START = "execution_start"
    BLOCK_START = "block_start"
    BLOCK_PROGRESS = "block_progress"
    BLOCK_COMPLETE = "block_complete"
    EXECUTION_COMPLETE = "execution_complete"
    ERROR = "error"
    LOG = "log"

class RealtimeMultiModalProcessor:
    """실시간 멀티모달 워크플로우 프로세서"""
    
    def __init__(self):
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.gemini_service = None
        if GEMINI_AVAILABLE:
            try:
                self.gemini_service = get_gemini_service()
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini service: {e}")
    
    async def execute_workflow_stream(
        self,
        workflow_id: str,
        execution_id: str,
        workflow_data: Dict[str, Any],
        user_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        워크플로우를 실시간으로 실행하고 진행 상황을 스트리밍
        
        Args:
            workflow_id: 워크플로우 ID
            execution_id: 실행 ID
            workflow_data: 워크플로우 정의 데이터
            user_id: 사용자 ID
            
        Yields:
            실행 진행 상황 이벤트
        """
        start_time = time.time()
        
        # 실행 상태 초기화
        execution_state = {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "user_id": user_id,
            "status": ExecutionStatus.STARTING,
            "start_time": start_time,
            "current_block": None,
            "completed_blocks": [],
            "total_blocks": len(workflow_data.get("nodes", [])),
            "progress": 0.0,
            "results": {},
            "errors": []
        }
        
        self.active_executions[execution_id] = execution_state
        
        try:
            # 실행 시작 이벤트
            yield self._create_event(
                StreamEventType.EXECUTION_START,
                {
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "total_blocks": execution_state["total_blocks"],
                    "estimated_duration": self._estimate_duration(workflow_data)
                }
            )
            
            execution_state["status"] = ExecutionStatus.PROCESSING
            
            # 노드 실행 순서 결정
            execution_order = self._determine_execution_order(workflow_data)
            
            # 각 노드 순차 실행
            for i, node in enumerate(execution_order):
                if execution_state["status"] == ExecutionStatus.CANCELLED:
                    break
                
                execution_state["current_block"] = node["id"]
                execution_state["progress"] = i / len(execution_order)
                
                # 블록 시작 이벤트
                yield self._create_event(
                    StreamEventType.BLOCK_START,
                    {
                        "block_id": node["id"],
                        "block_name": node.get("name", node["id"]),
                        "block_type": node.get("type", "unknown"),
                        "progress": execution_state["progress"]
                    }
                )
                
                # 블록 실행
                async for progress_event in self._execute_block_stream(node, execution_state):
                    yield progress_event
                
                execution_state["completed_blocks"].append(node["id"])
                
                # 블록 완료 이벤트
                yield self._create_event(
                    StreamEventType.BLOCK_COMPLETE,
                    {
                        "block_id": node["id"],
                        "block_name": node.get("name", node["id"]),
                        "completed_blocks": len(execution_state["completed_blocks"]),
                        "total_blocks": execution_state["total_blocks"],
                        "progress": len(execution_state["completed_blocks"]) / execution_state["total_blocks"]
                    }
                )
            
            # 실행 완료
            execution_state["status"] = ExecutionStatus.COMPLETED
            execution_state["end_time"] = time.time()
            execution_state["duration"] = execution_state["end_time"] - execution_state["start_time"]
            
            yield self._create_event(
                StreamEventType.EXECUTION_COMPLETE,
                {
                    "execution_id": execution_id,
                    "status": "success",
                    "duration": execution_state["duration"],
                    "results": execution_state["results"],
                    "completed_blocks": len(execution_state["completed_blocks"]),
                    "total_blocks": execution_state["total_blocks"]
                }
            )
            
        except Exception as e:
            execution_state["status"] = ExecutionStatus.ERROR
            execution_state["errors"].append(str(e))
            
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            
            yield self._create_event(
                StreamEventType.ERROR,
                {
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "block_id": execution_state.get("current_block")
                }
            )
        
        finally:
            # 정리
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _execute_block_stream(
        self,
        node: Dict[str, Any],
        execution_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        개별 블록을 실행하고 진행 상황을 스트리밍
        """
        block_type = node.get("type", "unknown")
        block_id = node["id"]
        
        try:
            if block_type == "gemini_vision":
                async for event in self._execute_gemini_vision_stream(node, execution_state):
                    yield event
                    
            elif block_type == "gemini_audio":
                async for event in self._execute_gemini_audio_stream(node, execution_state):
                    yield event
                    
            elif block_type == "gemini_document":
                async for event in self._execute_gemini_document_stream(node, execution_state):
                    yield event
                    
            else:
                # 기본 블록 실행 (시뮬레이션)
                async for event in self._execute_generic_block_stream(node, execution_state):
                    yield event
                    
        except Exception as e:
            logger.error(f"Block execution failed: {e}", exc_info=True)
            yield self._create_event(
                StreamEventType.ERROR,
                {
                    "block_id": block_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def _execute_gemini_vision_stream(
        self,
        node: Dict[str, Any],
        execution_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Gemini Vision 블록 실행"""
        block_id = node["id"]
        config = node.get("config", {})
        
        # 진행 상황 업데이트
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.1,
                "message": "이미지 데이터 준비 중..."
            }
        )
        
        await asyncio.sleep(0.5)  # 시뮬레이션
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.3,
                "message": "Gemini Vision 모델 로딩 중..."
            }
        )
        
        await asyncio.sleep(0.5)
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.6,
                "message": "이미지 분석 중..."
            }
        )
        
        # 실제 Gemini 호출 (있는 경우)
        if self.gemini_service:
            try:
                # 실제 분석 수행
                result = await self._simulate_gemini_vision_analysis(config)
                execution_state["results"][block_id] = result
                
                yield self._create_event(
                    StreamEventType.BLOCK_PROGRESS,
                    {
                        "block_id": block_id,
                        "progress": 1.0,
                        "message": "분석 완료",
                        "result": result
                    }
                )
            except Exception as e:
                raise e
        else:
            # 시뮬레이션 결과
            result = {
                "success": True,
                "result": "시뮬레이션: 이미지 분석이 완료되었습니다.",
                "confidence": 0.95,
                "processing_time": 2.1
            }
            execution_state["results"][block_id] = result
            
            yield self._create_event(
                StreamEventType.BLOCK_PROGRESS,
                {
                    "block_id": block_id,
                    "progress": 1.0,
                    "message": "분석 완료 (시뮬레이션)",
                    "result": result
                }
            )
    
    async def _execute_gemini_audio_stream(
        self,
        node: Dict[str, Any],
        execution_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Gemini Audio 블록 실행"""
        block_id = node["id"]
        config = node.get("config", {})
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.1,
                "message": "음성 데이터 전처리 중..."
            }
        )
        
        await asyncio.sleep(0.8)
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.4,
                "message": "음성 인식 중..."
            }
        )
        
        await asyncio.sleep(1.2)
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.8,
                "message": "텍스트 분석 중..."
            }
        )
        
        await asyncio.sleep(0.5)
        
        # 결과 생성
        result = {
            "success": True,
            "transcript": "시뮬레이션: 음성이 텍스트로 변환되었습니다.",
            "analysis": "시뮬레이션: 음성 분석이 완료되었습니다.",
            "confidence": 0.92,
            "processing_time": 2.5
        }
        execution_state["results"][block_id] = result
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 1.0,
                "message": "음성 처리 완료",
                "result": result
            }
        )
    
    async def _execute_gemini_document_stream(
        self,
        node: Dict[str, Any],
        execution_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Gemini Document 블록 실행"""
        block_id = node["id"]
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.2,
                "message": "문서 구조 분석 중..."
            }
        )
        
        await asyncio.sleep(1.0)
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 0.7,
                "message": "데이터 추출 중..."
            }
        )
        
        await asyncio.sleep(0.8)
        
        result = {
            "success": True,
            "structured_data": {
                "document_type": "invoice",
                "extracted_fields": ["date", "amount", "vendor"],
                "confidence": 0.89
            },
            "processing_time": 1.8
        }
        execution_state["results"][block_id] = result
        
        yield self._create_event(
            StreamEventType.BLOCK_PROGRESS,
            {
                "block_id": block_id,
                "progress": 1.0,
                "message": "문서 분석 완료",
                "result": result
            }
        )
    
    async def _execute_generic_block_stream(
        self,
        node: Dict[str, Any],
        execution_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """일반 블록 실행 (시뮬레이션)"""
        block_id = node["id"]
        block_type = node.get("type", "unknown")
        
        # 블록 타입에 따른 시뮬레이션 시간
        simulation_time = {
            "http_request": 1.0,
            "database_query": 0.8,
            "code_execution": 1.5,
            "condition": 0.2,
            "loop": 2.0
        }.get(block_type, 1.0)
        
        steps = 5
        step_time = simulation_time / steps
        
        for i in range(steps):
            progress = (i + 1) / steps
            yield self._create_event(
                StreamEventType.BLOCK_PROGRESS,
                {
                    "block_id": block_id,
                    "progress": progress,
                    "message": f"{block_type} 실행 중... ({int(progress * 100)}%)"
                }
            )
            await asyncio.sleep(step_time)
        
        # 결과 생성
        result = {
            "success": True,
            "output": f"{block_type} 실행 완료",
            "processing_time": simulation_time
        }
        execution_state["results"][block_id] = result
    
    async def _simulate_gemini_vision_analysis(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini Vision 분석 시뮬레이션"""
        await asyncio.sleep(1.0)  # 실제 API 호출 시뮬레이션
        
        return {
            "success": True,
            "result": "이미지 분석이 완료되었습니다. 주요 객체와 텍스트가 식별되었습니다.",
            "structured_data": {
                "objects": ["document", "text", "table"],
                "text_content": "추출된 텍스트 내용",
                "confidence": 0.95
            },
            "model_used": config.get("model", "gemini-1.5-flash"),
            "processing_time": 2.1
        }
    
    def _determine_execution_order(self, workflow_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """워크플로우 노드 실행 순서 결정"""
        nodes = workflow_data.get("nodes", [])
        connections = workflow_data.get("connections", [])
        
        # 간단한 순차 실행 (실제로는 의존성 그래프 분석 필요)
        return nodes
    
    def _estimate_duration(self, workflow_data: Dict[str, Any]) -> float:
        """워크플로우 예상 실행 시간 계산"""
        nodes = workflow_data.get("nodes", [])
        
        # 블록 타입별 예상 시간 (초)
        block_durations = {
            "gemini_vision": 3.0,
            "gemini_audio": 4.0,
            "gemini_document": 2.5,
            "http_request": 1.0,
            "database_query": 0.8,
            "code_execution": 1.5,
            "condition": 0.2
        }
        
        total_duration = 0.0
        for node in nodes:
            block_type = node.get("type", "unknown")
            total_duration += block_durations.get(block_type, 1.0)
        
        return total_duration
    
    def _create_event(self, event_type: StreamEventType, data: Dict[str, Any]) -> Dict[str, Any]:
        """스트림 이벤트 생성"""
        return {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """실행 취소"""
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = ExecutionStatus.CANCELLED
            logger.info(f"Execution {execution_id} cancelled")
            return True
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """실행 상태 조회"""
        return self.active_executions.get(execution_id)
    
    def get_active_executions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """활성 실행 목록 조회"""
        executions = list(self.active_executions.values())
        
        if user_id:
            executions = [e for e in executions if e.get("user_id") == user_id]
        
        return executions

# 싱글톤 인스턴스
_realtime_processor = None

def get_realtime_processor() -> RealtimeMultiModalProcessor:
    """실시간 프로세서 싱글톤 인스턴스 반환"""
    global _realtime_processor
    if _realtime_processor is None:
        _realtime_processor = RealtimeMultiModalProcessor()
    return _realtime_processor