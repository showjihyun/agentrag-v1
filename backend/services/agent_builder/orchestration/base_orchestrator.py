"""
Base Orchestrator
모든 오케스트레이션 패턴의 기본 클래스
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class ExecutionStatus(Enum):
    """실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ValidationSeverity(Enum):
    """검증 결과 심각도"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """설정 검증 결과"""
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class ExecutionResult:
    """실행 결과"""
    execution_id: str
    status: ExecutionStatus
    orchestration_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.metrics is None:
            self.metrics = {}


@dataclass
class StreamingUpdate:
    """스트리밍 업데이트"""
    execution_id: str
    timestamp: datetime
    update_type: str  # "progress", "agent_status", "result", "error"
    data: Dict[str, Any]
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


class BaseOrchestrator(ABC):
    """
    모든 오케스트레이션 패턴의 기본 클래스
    
    이 클래스는 모든 오케스트레이터가 구현해야 하는 공통 인터페이스와
    기본 기능을 제공합니다.
    """
    
    def __init__(self, pattern_type: str):
        """
        기본 오케스트레이터 초기화
        
        Args:
            pattern_type: 오케스트레이션 패턴 타입
        """
        self.pattern_type = pattern_type
        self.logger = get_logger(f"orchestrator.{pattern_type}")
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        
    # ============================================================================
    # Abstract Methods (하위 클래스에서 반드시 구현)
    # ============================================================================
    
    @abstractmethod
    async def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """
        오케스트레이션 설정 검증
        
        Args:
            config: 오케스트레이션 설정
            
        Returns:
            ValidationResult: 검증 결과
        """
        pass
    
    @abstractmethod
    async def execute(
        self, 
        config: Dict[str, Any], 
        input_data: Dict[str, Any], 
        user_id: str, 
        execution_id: str
    ) -> ExecutionResult:
        """
        오케스트레이션 동기 실행
        
        Args:
            config: 오케스트레이션 설정
            input_data: 입력 데이터
            user_id: 사용자 ID
            execution_id: 실행 ID
            
        Returns:
            ExecutionResult: 실행 결과
        """
        pass
    
    # ============================================================================
    # Common Methods (공통 기능)
    # ============================================================================
    
    async def execute_async(
        self, 
        config: Dict[str, Any], 
        input_data: Dict[str, Any], 
        user_id: str, 
        execution_id: str
    ) -> None:
        """
        오케스트레이션 비동기 실행
        
        Args:
            config: 오케스트레이션 설정
            input_data: 입력 데이터
            user_id: 사용자 ID
            execution_id: 실행 ID
        """
        try:
            self.logger.info(f"Starting async execution: {execution_id}")
            
            # 실행 상태 등록
            self._register_execution(execution_id, config, user_id)
            
            # 동기 실행 호출
            result = await self.execute(config, input_data, user_id, execution_id)
            
            # 실행 완료 처리
            self._complete_execution(execution_id, result)
            
            self.logger.info(f"Async execution completed: {execution_id}")
            
        except Exception as e:
            self.logger.error(f"Async execution failed: {execution_id}, error: {e}")
            self._fail_execution(execution_id, str(e))
    
    async def execute_streaming(
        self, 
        config: Dict[str, Any], 
        input_data: Dict[str, Any], 
        user_id: str, 
        execution_id: str
    ) -> AsyncGenerator[StreamingUpdate, None]:
        """
        오케스트레이션 스트리밍 실행
        
        Args:
            config: 오케스트레이션 설정
            input_data: 입력 데이터
            user_id: 사용자 ID
            execution_id: 실행 ID
            
        Yields:
            StreamingUpdate: 실행 상태 업데이트
        """
        try:
            self.logger.info(f"Starting streaming execution: {execution_id}")
            
            # 시작 업데이트
            yield StreamingUpdate(
                execution_id=execution_id,
                timestamp=datetime.now(),
                update_type="progress",
                data={
                    "status": ExecutionStatus.RUNNING.value,
                    "progress": 0.0,
                    "message": "Execution started"
                }
            )
            
            # 실행 상태 등록
            self._register_execution(execution_id, config, user_id)
            
            # 기본 구현: 동기 실행 후 결과 스트리밍
            # 하위 클래스에서 실제 스트리밍 로직 구현 가능
            result = await self.execute(config, input_data, user_id, execution_id)
            
            # 완료 업데이트
            yield StreamingUpdate(
                execution_id=execution_id,
                timestamp=datetime.now(),
                update_type="result",
                data={
                    "status": result.status.value,
                    "progress": 1.0,
                    "results": result.results,
                    "metrics": result.metrics
                }
            )
            
            self._complete_execution(execution_id, result)
            
        except Exception as e:
            self.logger.error(f"Streaming execution failed: {execution_id}, error: {e}")
            
            # 에러 업데이트
            yield StreamingUpdate(
                execution_id=execution_id,
                timestamp=datetime.now(),
                update_type="error",
                data={
                    "status": ExecutionStatus.FAILED.value,
                    "error": str(e)
                }
            )
            
            self._fail_execution(execution_id, str(e))
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        실행 취소
        
        Args:
            execution_id: 실행 ID
            
        Returns:
            bool: 취소 성공 여부
        """
        try:
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = ExecutionStatus.CANCELLED
                self.logger.info(f"Execution cancelled: {execution_id}")
                return True
            else:
                self.logger.warning(f"Execution not found for cancellation: {execution_id}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        실행 상태 조회
        
        Args:
            execution_id: 실행 ID
            
        Returns:
            Optional[Dict[str, Any]]: 실행 상태 정보
        """
        return self.active_executions.get(execution_id)
    
    def list_active_executions(self) -> List[str]:
        """
        활성 실행 목록 조회
        
        Returns:
            List[str]: 활성 실행 ID 목록
        """
        return [
            exec_id for exec_id, info in self.active_executions.items()
            if info["status"] in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
        ]
    
    # ============================================================================
    # Validation Helpers (검증 도우미 메서드)
    # ============================================================================
    
    def _validate_required_fields(
        self, 
        config: Dict[str, Any], 
        required_fields: List[str]
    ) -> List[str]:
        """
        필수 필드 검증
        
        Args:
            config: 설정 딕셔너리
            required_fields: 필수 필드 목록
            
        Returns:
            List[str]: 누락된 필드 목록
        """
        missing_fields = []
        for field in required_fields:
            if field not in config or config[field] is None:
                missing_fields.append(field)
        return missing_fields
    
    def _validate_numeric_range(
        self, 
        value: Any, 
        field_name: str, 
        min_val: Optional[float] = None, 
        max_val: Optional[float] = None
    ) -> List[str]:
        """
        숫자 범위 검증
        
        Args:
            value: 검증할 값
            field_name: 필드 이름
            min_val: 최소값
            max_val: 최대값
            
        Returns:
            List[str]: 검증 오류 목록
        """
        errors = []
        
        try:
            num_value = float(value)
            
            if min_val is not None and num_value < min_val:
                errors.append(f"{field_name} must be >= {min_val}")
            
            if max_val is not None and num_value > max_val:
                errors.append(f"{field_name} must be <= {max_val}")
                
        except (TypeError, ValueError):
            errors.append(f"{field_name} must be a valid number")
        
        return errors
    
    def _validate_list_length(
        self, 
        value: Any, 
        field_name: str, 
        min_length: Optional[int] = None, 
        max_length: Optional[int] = None
    ) -> List[str]:
        """
        리스트 길이 검증
        
        Args:
            value: 검증할 값
            field_name: 필드 이름
            min_length: 최소 길이
            max_length: 최대 길이
            
        Returns:
            List[str]: 검증 오류 목록
        """
        errors = []
        
        if not isinstance(value, list):
            errors.append(f"{field_name} must be a list")
            return errors
        
        length = len(value)
        
        if min_length is not None and length < min_length:
            errors.append(f"{field_name} must have at least {min_length} items")
        
        if max_length is not None and length > max_length:
            errors.append(f"{field_name} must have at most {max_length} items")
        
        return errors
    
    # ============================================================================
    # Execution Management (실행 관리)
    # ============================================================================
    
    def _register_execution(
        self, 
        execution_id: str, 
        config: Dict[str, Any], 
        user_id: str
    ) -> None:
        """
        실행 등록
        
        Args:
            execution_id: 실행 ID
            config: 오케스트레이션 설정
            user_id: 사용자 ID
        """
        self.active_executions[execution_id] = {
            "execution_id": execution_id,
            "status": ExecutionStatus.RUNNING,
            "orchestration_type": self.pattern_type,
            "user_id": user_id,
            "started_at": datetime.now(),
            "config": config,
            "progress": 0.0
        }
    
    def _complete_execution(
        self, 
        execution_id: str, 
        result: ExecutionResult
    ) -> None:
        """
        실행 완료 처리
        
        Args:
            execution_id: 실행 ID
            result: 실행 결과
        """
        if execution_id in self.active_executions:
            self.active_executions[execution_id].update({
                "status": result.status,
                "completed_at": result.completed_at or datetime.now(),
                "results": result.results,
                "metrics": result.metrics,
                "progress": 1.0
            })
    
    def _fail_execution(self, execution_id: str, error: str) -> None:
        """
        실행 실패 처리
        
        Args:
            execution_id: 실행 ID
            error: 오류 메시지
        """
        if execution_id in self.active_executions:
            self.active_executions[execution_id].update({
                "status": ExecutionStatus.FAILED,
                "completed_at": datetime.now(),
                "error": error,
                "progress": 0.0
            })
    
    def _update_execution_progress(
        self, 
        execution_id: str, 
        progress: float, 
        message: Optional[str] = None
    ) -> None:
        """
        실행 진행률 업데이트
        
        Args:
            execution_id: 실행 ID
            progress: 진행률 (0.0 - 1.0)
            message: 진행 메시지
        """
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["progress"] = max(0.0, min(1.0, progress))
            if message:
                self.active_executions[execution_id]["current_message"] = message
    
    # ============================================================================
    # Utility Methods (유틸리티 메서드)
    # ============================================================================
    
    def _generate_execution_id(self) -> str:
        """
        실행 ID 생성
        
        Returns:
            str: 고유한 실행 ID
        """
        return f"{self.pattern_type}_{uuid.uuid4().hex[:8]}"
    
    def _calculate_execution_metrics(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        agent_count: int, 
        success_count: int
    ) -> Dict[str, Any]:
        """
        실행 메트릭 계산
        
        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            agent_count: 총 Agent 수
            success_count: 성공한 Agent 수
            
        Returns:
            Dict[str, Any]: 실행 메트릭
        """
        duration = (end_time - start_time).total_seconds()
        success_rate = success_count / agent_count if agent_count > 0 else 0.0
        
        return {
            "execution_time_seconds": duration,
            "total_agents": agent_count,
            "successful_agents": success_count,
            "failed_agents": agent_count - success_count,
            "success_rate": success_rate,
            "agents_per_second": agent_count / duration if duration > 0 else 0.0
        }
    
    def __repr__(self) -> str:
        """문자열 표현"""
        return f"{self.__class__.__name__}(pattern_type='{self.pattern_type}')"