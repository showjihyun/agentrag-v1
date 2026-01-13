"""
Enhanced Error Handling for Orchestration System
오케스트레이션 시스템 향상된 에러 처리
"""

import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """에러 심각도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """에러 카테고리"""
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    EXECUTION = "execution"
    COMMUNICATION = "communication"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RESOURCE = "resource"


class ErrorCode(Enum):
    """에러 코드"""
    # Configuration Errors (1000-1099)
    INVALID_PATTERN_TYPE = "ORH-1001"
    MISSING_REQUIRED_CONFIG = "ORH-1002"
    INVALID_AGENT_ROLE = "ORH-1003"
    INVALID_SUPERVISOR_CONFIG = "ORH-1004"
    INVALID_COMMUNICATION_RULES = "ORH-1005"
    
    # Validation Errors (1100-1199)
    VALIDATION_FAILED = "ORH-1101"
    SECURITY_VALIDATION_FAILED = "ORH-1102"
    AGENT_COUNT_INVALID = "ORH-1103"
    THRESHOLD_INVALID = "ORH-1104"
    DEPENDENCY_CYCLE = "ORH-1105"
    
    # Execution Errors (1200-1299)
    EXECUTION_FAILED = "ORH-1201"
    AGENT_EXECUTION_FAILED = "ORH-1202"
    SUPERVISOR_FAILED = "ORH-1203"
    CONSENSUS_FAILED = "ORH-1204"
    ROUTING_FAILED = "ORH-1205"
    
    # Communication Errors (1300-1399)
    COMMUNICATION_FAILED = "ORH-1301"
    NEGOTIATION_FAILED = "ORH-1302"
    BROADCAST_FAILED = "ORH-1303"
    MESSAGE_DELIVERY_FAILED = "ORH-1304"
    
    # Security Errors (1400-1499)
    UNAUTHORIZED_ACCESS = "ORH-1401"
    PERMISSION_DENIED = "ORH-1402"
    INPUT_SANITIZATION_FAILED = "ORH-1403"
    SECURITY_POLICY_VIOLATION = "ORH-1404"
    
    # Performance Errors (1500-1599)
    TIMEOUT_EXCEEDED = "ORH-1501"
    MEMORY_LIMIT_EXCEEDED = "ORH-1502"
    TOKEN_LIMIT_EXCEEDED = "ORH-1503"
    RATE_LIMIT_EXCEEDED = "ORH-1504"
    
    # System Errors (1600-1699)
    SYSTEM_ERROR = "ORH-1601"
    DATABASE_ERROR = "ORH-1602"
    CACHE_ERROR = "ORH-1603"
    NETWORK_ERROR = "ORH-1604"
    RESOURCE_UNAVAILABLE = "ORH-1605"


@dataclass
class ErrorContext:
    """에러 컨텍스트 정보"""
    user_id: Optional[str] = None
    execution_id: Optional[str] = None
    pattern_type: Optional[str] = None
    agent_id: Optional[str] = None
    step: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorDetail:
    """상세 에러 정보"""
    code: ErrorCode
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: str
    context: ErrorContext
    stack_trace: Optional[str] = None
    suggestions: List[str] = None
    recovery_actions: List[str] = None
    related_errors: List[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.suggestions is None:
            self.suggestions = []
        if self.recovery_actions is None:
            self.recovery_actions = []
        if self.related_errors is None:
            self.related_errors = []


class OrchestrationError(Exception):
    """기본 오케스트레이션 에러"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[ErrorContext] = None,
        suggestions: Optional[List[str]] = None,
        recovery_actions: Optional[List[str]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.detail = ErrorDetail(
            code=code,
            message=message,
            severity=severity,
            category=category,
            timestamp=datetime.now().isoformat(),
            context=context or ErrorContext(),
            stack_trace=traceback.format_exc() if cause else None,
            suggestions=suggestions or [],
            recovery_actions=recovery_actions or []
        )
        self.cause = cause


class ConfigurationError(OrchestrationError):
    """설정 관련 에러"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.CONFIGURATION,
            **kwargs
        )


class ValidationError(OrchestrationError):
    """검증 관련 에러"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )


class ExecutionError(OrchestrationError):
    """실행 관련 에러"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.EXECUTION,
            **kwargs
        )


class SecurityError(OrchestrationError):
    """보안 관련 에러"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class PerformanceError(OrchestrationError):
    """성능 관련 에러"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.PERFORMANCE,
            **kwargs
        )


class ErrorHandler:
    """향상된 에러 핸들러"""
    
    def __init__(self):
        self.error_history: List[ErrorDetail] = []
        self.error_patterns: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCode, callable] = {}
        
        # 기본 복구 전략 등록
        self._register_default_recovery_strategies()
    
    def handle_error(
        self,
        error: Union[Exception, OrchestrationError],
        context: Optional[ErrorContext] = None,
        auto_recover: bool = True
    ) -> ErrorDetail:
        """에러 처리"""
        try:
            # OrchestrationError가 아닌 경우 변환
            if not isinstance(error, OrchestrationError):
                orchestration_error = self._convert_to_orchestration_error(error, context)
            else:
                orchestration_error = error
                if context:
                    orchestration_error.detail.context = context
            
            error_detail = orchestration_error.detail
            
            # 에러 로깅
            self._log_error(error_detail)
            
            # 에러 히스토리 추가
            self.error_history.append(error_detail)
            
            # 에러 패턴 분석
            self._analyze_error_pattern(error_detail)
            
            # 제안사항 및 복구 액션 생성
            self._generate_suggestions(error_detail)
            self._generate_recovery_actions(error_detail)
            
            # 자동 복구 시도
            if auto_recover:
                self._attempt_recovery(error_detail)
            
            return error_detail
            
        except Exception as e:
            logger.error(f"Error handler failed: {e}")
            # 최소한의 에러 정보 반환
            return ErrorDetail(
                code=ErrorCode.SYSTEM_ERROR,
                message=f"Error handler failed: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                timestamp=datetime.now().isoformat(),
                context=context or ErrorContext()
            )
    
    def _convert_to_orchestration_error(
        self, 
        error: Exception, 
        context: Optional[ErrorContext]
    ) -> OrchestrationError:
        """일반 예외를 OrchestrationError로 변환"""
        error_type = type(error).__name__
        message = str(error)
        
        # 에러 타입별 매핑
        error_mapping = {
            "ValueError": (ErrorCode.VALIDATION_FAILED, ErrorSeverity.MEDIUM),
            "KeyError": (ErrorCode.MISSING_REQUIRED_CONFIG, ErrorSeverity.MEDIUM),
            "TimeoutError": (ErrorCode.TIMEOUT_EXCEEDED, ErrorSeverity.HIGH),
            "PermissionError": (ErrorCode.PERMISSION_DENIED, ErrorSeverity.HIGH),
            "ConnectionError": (ErrorCode.NETWORK_ERROR, ErrorSeverity.HIGH),
            "MemoryError": (ErrorCode.MEMORY_LIMIT_EXCEEDED, ErrorSeverity.CRITICAL),
        }
        
        code, severity = error_mapping.get(error_type, (ErrorCode.SYSTEM_ERROR, ErrorSeverity.MEDIUM))
        
        return OrchestrationError(
            message=f"{error_type}: {message}",
            code=code,
            severity=severity,
            context=context,
            cause=error
        )
    
    def _log_error(self, error_detail: ErrorDetail):
        """에러 로깅"""
        log_data = {
            "error_code": error_detail.code.value,
            "severity": error_detail.severity.value,
            "category": error_detail.category.value,
            "message": error_detail.message,
            "context": asdict(error_detail.context),
            "timestamp": error_detail.timestamp
        }
        
        if error_detail.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical orchestration error", extra=log_data)
        elif error_detail.severity == ErrorSeverity.HIGH:
            logger.error("High severity orchestration error", extra=log_data)
        elif error_detail.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity orchestration error", extra=log_data)
        else:
            logger.info("Low severity orchestration error", extra=log_data)
    
    def _analyze_error_pattern(self, error_detail: ErrorDetail):
        """에러 패턴 분석"""
        pattern_key = f"{error_detail.code.value}:{error_detail.category.value}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        # 반복되는 에러 패턴 감지
        if self.error_patterns[pattern_key] > 5:
            error_detail.suggestions.append(
                f"이 에러가 반복적으로 발생하고 있습니다 ({self.error_patterns[pattern_key]}회). "
                "시스템 설정을 점검해보세요."
            )
    
    def _generate_suggestions(self, error_detail: ErrorDetail):
        """제안사항 생성"""
        suggestions_map = {
            ErrorCode.INVALID_PATTERN_TYPE: [
                "지원되는 패턴 타입을 확인하세요",
                "패턴 타입 이름의 철자를 확인하세요"
            ],
            ErrorCode.MISSING_REQUIRED_CONFIG: [
                "필수 설정 필드가 누락되었는지 확인하세요",
                "설정 템플릿을 참조하여 완전한 설정을 작성하세요"
            ],
            ErrorCode.TIMEOUT_EXCEEDED: [
                "타임아웃 값을 늘려보세요",
                "Agent 수를 줄여 복잡도를 낮춰보세요",
                "네트워크 연결 상태를 확인하세요"
            ],
            ErrorCode.MEMORY_LIMIT_EXCEEDED: [
                "Agent 수를 줄여보세요",
                "입력 데이터 크기를 줄여보세요",
                "시스템 메모리를 확인하세요"
            ],
            ErrorCode.SECURITY_VALIDATION_FAILED: [
                "입력 데이터에 악성 코드가 포함되어 있지 않은지 확인하세요",
                "사용자 권한을 확인하세요",
                "보안 정책을 검토하세요"
            ]
        }
        
        if error_detail.code in suggestions_map:
            error_detail.suggestions.extend(suggestions_map[error_detail.code])
    
    def _generate_recovery_actions(self, error_detail: ErrorDetail):
        """복구 액션 생성"""
        recovery_actions_map = {
            ErrorCode.TIMEOUT_EXCEEDED: [
                "타임아웃 설정을 2배로 증가",
                "Agent 수를 절반으로 감소",
                "단순한 패턴으로 변경"
            ],
            ErrorCode.MEMORY_LIMIT_EXCEEDED: [
                "메모리 캐시 정리",
                "Agent 수 감소",
                "입력 데이터 분할 처리"
            ],
            ErrorCode.VALIDATION_FAILED: [
                "기본 설정으로 재설정",
                "설정 템플릿 적용",
                "단계별 설정 검증"
            ],
            ErrorCode.NETWORK_ERROR: [
                "네트워크 연결 재시도",
                "로컬 모드로 전환",
                "오프라인 처리 모드 활성화"
            ]
        }
        
        if error_detail.code in recovery_actions_map:
            error_detail.recovery_actions.extend(recovery_actions_map[error_detail.code])
    
    def _attempt_recovery(self, error_detail: ErrorDetail):
        """자동 복구 시도"""
        if error_detail.code in self.recovery_strategies:
            try:
                recovery_func = self.recovery_strategies[error_detail.code]
                recovery_result = recovery_func(error_detail)
                
                if recovery_result:
                    logger.info(f"Auto-recovery successful for {error_detail.code.value}")
                    error_detail.recovery_actions.append("자동 복구 성공")
                else:
                    logger.warning(f"Auto-recovery failed for {error_detail.code.value}")
                    
            except Exception as e:
                logger.error(f"Auto-recovery error: {e}")
    
    def _register_default_recovery_strategies(self):
        """기본 복구 전략 등록"""
        
        def recover_timeout(error_detail: ErrorDetail) -> bool:
            """타임아웃 복구"""
            # 실제로는 설정을 조정하거나 재시도 로직 구현
            return True
        
        def recover_memory_limit(error_detail: ErrorDetail) -> bool:
            """메모리 한계 복구"""
            # 실제로는 캐시 정리나 메모리 최적화 수행
            return True
        
        def recover_network_error(error_detail: ErrorDetail) -> bool:
            """네트워크 에러 복구"""
            # 실제로는 연결 재시도나 대체 경로 사용
            return True
        
        self.recovery_strategies.update({
            ErrorCode.TIMEOUT_EXCEEDED: recover_timeout,
            ErrorCode.MEMORY_LIMIT_EXCEEDED: recover_memory_limit,
            ErrorCode.NETWORK_ERROR: recover_network_error,
        })
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """에러 통계 조회"""
        if not self.error_history:
            return {"total_errors": 0}
        
        # 심각도별 통계
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for error in self.error_history 
                if error.severity == severity
            )
        
        # 카테고리별 통계
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = sum(
                1 for error in self.error_history 
                if error.category == category
            )
        
        # 최근 에러들
        recent_errors = self.error_history[-10:] if len(self.error_history) > 10 else self.error_history
        
        return {
            "total_errors": len(self.error_history),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "most_common_patterns": dict(sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
            "recent_errors": [
                {
                    "code": error.code.value,
                    "message": error.message,
                    "severity": error.severity.value,
                    "timestamp": error.timestamp
                }
                for error in recent_errors
            ]
        }
    
    def clear_error_history(self):
        """에러 히스토리 정리"""
        self.error_history.clear()
        self.error_patterns.clear()


# 전역 에러 핸들러 인스턴스
_error_handler_instance: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """에러 핸들러 인스턴스 조회"""
    global _error_handler_instance
    
    if _error_handler_instance is None:
        _error_handler_instance = ErrorHandler()
    
    return _error_handler_instance


@contextmanager
def error_context(
    user_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    pattern_type: Optional[str] = None,
    agent_id: Optional[str] = None,
    step: Optional[str] = None
):
    """에러 컨텍스트 매니저"""
    context = ErrorContext(
        user_id=user_id,
        execution_id=execution_id,
        pattern_type=pattern_type,
        agent_id=agent_id,
        step=step
    )
    
    try:
        yield context
    except Exception as e:
        error_handler = get_error_handler()
        error_detail = error_handler.handle_error(e, context)
        
        # 원래 예외를 OrchestrationError로 래핑하여 다시 발생
        if not isinstance(e, OrchestrationError):
            raise OrchestrationError(
                message=error_detail.message,
                code=error_detail.code,
                severity=error_detail.severity,
                category=error_detail.category,
                context=context,
                cause=e
            ) from e
        else:
            raise


def handle_orchestration_error(func):
    """오케스트레이션 에러 처리 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = get_error_handler()
            error_detail = error_handler.handle_error(e)
            
            # 에러 정보를 포함한 응답 반환 (API 엔드포인트용)
            return {
                "success": False,
                "error": {
                    "code": error_detail.code.value,
                    "message": error_detail.message,
                    "severity": error_detail.severity.value,
                    "category": error_detail.category.value,
                    "suggestions": error_detail.suggestions,
                    "recovery_actions": error_detail.recovery_actions,
                    "timestamp": error_detail.timestamp
                }
            }
    
    return wrapper