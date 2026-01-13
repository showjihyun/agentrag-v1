"""
Enhanced Agent Plugin 에러 처리 표준화
"""
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from pydantic import BaseModel
from fastapi import HTTPException
import traceback
import logging
import asyncio
import functools
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import uuid

logger = logging.getLogger(__name__)

class PluginErrorCode(Enum):
    """플러그인 에러 코드"""
    # 일반 에러
    UNKNOWN_ERROR = "PLUGIN_UNKNOWN_ERROR"
    VALIDATION_ERROR = "PLUGIN_VALIDATION_ERROR"
    CONFIGURATION_ERROR = "PLUGIN_CONFIGURATION_ERROR"
    
    # 보안 에러
    PERMISSION_DENIED = "PLUGIN_PERMISSION_DENIED"
    AUTHENTICATION_FAILED = "PLUGIN_AUTH_FAILED"
    RATE_LIMIT_EXCEEDED = "PLUGIN_RATE_LIMIT_EXCEEDED"
    SECURITY_VIOLATION = "PLUGIN_SECURITY_VIOLATION"
    
    # 실행 에러
    EXECUTION_FAILED = "PLUGIN_EXECUTION_FAILED"
    TIMEOUT_ERROR = "PLUGIN_TIMEOUT_ERROR"
    RESOURCE_EXHAUSTED = "PLUGIN_RESOURCE_EXHAUSTED"
    MEMORY_LIMIT_EXCEEDED = "PLUGIN_MEMORY_LIMIT_EXCEEDED"
    CPU_LIMIT_EXCEEDED = "PLUGIN_CPU_LIMIT_EXCEEDED"
    
    # 플러그인 관리 에러
    PLUGIN_NOT_FOUND = "PLUGIN_NOT_FOUND"
    PLUGIN_ALREADY_EXISTS = "PLUGIN_ALREADY_EXISTS"
    PLUGIN_INSTALLATION_FAILED = "PLUGIN_INSTALLATION_FAILED"
    PLUGIN_UNINSTALLATION_FAILED = "PLUGIN_UNINSTALLATION_FAILED"
    PLUGIN_CORRUPTED = "PLUGIN_CORRUPTED"
    PLUGIN_INCOMPATIBLE = "PLUGIN_INCOMPATIBLE"
    
    # 의존성 에러
    DEPENDENCY_ERROR = "PLUGIN_DEPENDENCY_ERROR"
    VERSION_CONFLICT = "PLUGIN_VERSION_CONFLICT"
    CIRCULAR_DEPENDENCY = "PLUGIN_CIRCULAR_DEPENDENCY"
    
    # 네트워크 에러
    NETWORK_ERROR = "PLUGIN_NETWORK_ERROR"
    SERVICE_UNAVAILABLE = "PLUGIN_SERVICE_UNAVAILABLE"
    CONNECTION_TIMEOUT = "PLUGIN_CONNECTION_TIMEOUT"
    
    # 데이터 에러
    DATA_CORRUPTION = "PLUGIN_DATA_CORRUPTION"
    SERIALIZATION_ERROR = "PLUGIN_SERIALIZATION_ERROR"
    DESERIALIZATION_ERROR = "PLUGIN_DESERIALIZATION_ERROR"


class ErrorSeverity(Enum):
    """에러 심각도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """에러 카테고리"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    FUNCTIONALITY = "functionality"
    INFRASTRUCTURE = "infrastructure"
    USER_INPUT = "user_input"

class PluginErrorDetail(BaseModel):
    """에러 상세 정보"""
    code: PluginErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    plugin_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None

class PluginException(Exception):
    """플러그인 기본 예외"""
    
    def __init__(
        self,
        code: PluginErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        plugin_id: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.plugin_id = plugin_id
        self.user_id = user_id
        self.trace_id = trace_id
        self.timestamp = datetime.now()
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
                "plugin_id": self.plugin_id,
                "user_id": self.user_id,
                "trace_id": self.trace_id
            }
        }
    
    def to_http_exception(self) -> HTTPException:
        """FastAPI HTTPException으로 변환"""
        status_code = self._get_http_status_code()
        return HTTPException(
            status_code=status_code,
            detail=self.to_dict()
        )
    
    def _get_http_status_code(self) -> int:
        """에러 코드에 따른 HTTP 상태 코드 반환"""
        status_map = {
            PluginErrorCode.VALIDATION_ERROR: 400,
            PluginErrorCode.AUTHENTICATION_FAILED: 401,
            PluginErrorCode.PERMISSION_DENIED: 403,
            PluginErrorCode.PLUGIN_NOT_FOUND: 404,
            PluginErrorCode.PLUGIN_ALREADY_EXISTS: 409,
            PluginErrorCode.RESOURCE_EXHAUSTED: 429,
            PluginErrorCode.EXECUTION_FAILED: 500,
            PluginErrorCode.SERVICE_UNAVAILABLE: 503,
            PluginErrorCode.TIMEOUT_ERROR: 504,
        }
        return status_map.get(self.code, 500)

class PluginValidationException(PluginException):
    """플러그인 검증 예외"""
    
    def __init__(self, message: str, validation_errors: List[str], **kwargs):
        super().__init__(
            code=PluginErrorCode.VALIDATION_ERROR,
            message=message,
            details={"validation_errors": validation_errors},
            **kwargs
        )

class PluginExecutionException(PluginException):
    """플러그인 실행 예외"""
    
    def __init__(self, message: str, execution_context: Dict[str, Any], **kwargs):
        super().__init__(
            code=PluginErrorCode.EXECUTION_FAILED,
            message=message,
            details={"execution_context": execution_context},
            **kwargs
        )

class PluginTimeoutException(PluginException):
    """플러그인 타임아웃 예외"""
    
    def __init__(self, timeout_seconds: int, **kwargs):
        super().__init__(
            code=PluginErrorCode.TIMEOUT_ERROR,
            message=f"Plugin execution timed out after {timeout_seconds} seconds",
            details={"timeout_seconds": timeout_seconds},
            **kwargs
        )

class RecoveryStrategy(Enum):
    """에러 복구 전략"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    MANUAL_INTERVENTION = "manual_intervention"


class PluginErrorHandler:
    """향상된 플러그인 에러 핸들러"""
    
    def __init__(self):
        self.error_history: List[PluginErrorDetail] = []
        self.error_callbacks: List[Callable] = []
        self.recovery_strategies: Dict[PluginErrorCode, RecoveryStrategy] = {
            PluginErrorCode.TIMEOUT_ERROR: RecoveryStrategy.RETRY,
            PluginErrorCode.NETWORK_ERROR: RecoveryStrategy.RETRY,
            PluginErrorCode.RESOURCE_EXHAUSTED: RecoveryStrategy.CIRCUIT_BREAKER,
            PluginErrorCode.MEMORY_LIMIT_EXCEEDED: RecoveryStrategy.GRACEFUL_DEGRADATION,
            PluginErrorCode.SECURITY_VIOLATION: RecoveryStrategy.MANUAL_INTERVENTION,
            PluginErrorCode.PLUGIN_CORRUPTED: RecoveryStrategy.MANUAL_INTERVENTION,
        }
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.retry_counts: Dict[str, int] = {}
    
    def handle_exception(
        self,
        exception: Exception,
        plugin_id: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PluginException:
        """예외를 PluginException으로 변환"""
        
        if isinstance(exception, PluginException):
            # 이미 PluginException인 경우
            plugin_exception = exception
        else:
            # 일반 예외를 PluginException으로 변환
            plugin_exception = self._convert_to_plugin_exception(
                exception, plugin_id, user_id, trace_id, context
            )
        
        # 에러 로깅
        self._log_error(plugin_exception, context)
        
        # 에러 히스토리에 추가
        self._add_to_history(plugin_exception)
        
        return plugin_exception
    
    def _convert_to_plugin_exception(
        self,
        exception: Exception,
        plugin_id: Optional[str],
        user_id: Optional[str],
        trace_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> PluginException:
        """일반 예외를 PluginException으로 변환"""
        
        # 예외 타입에 따른 에러 코드 매핑
        error_code_map = {
            ValueError: PluginErrorCode.VALIDATION_ERROR,
            KeyError: PluginErrorCode.CONFIGURATION_ERROR,
            TimeoutError: PluginErrorCode.TIMEOUT_ERROR,
            ConnectionError: PluginErrorCode.NETWORK_ERROR,
            PermissionError: PluginErrorCode.PERMISSION_DENIED,
        }
        
        error_code = error_code_map.get(type(exception), PluginErrorCode.UNKNOWN_ERROR)
        
        return PluginException(
            code=error_code,
            message=str(exception),
            details={
                "original_exception": type(exception).__name__,
                "traceback": traceback.format_exc(),
                "context": context or {}
            },
            plugin_id=plugin_id,
            user_id=user_id,
            trace_id=trace_id
        )
    
    def _log_error(self, error: PluginException, context: Optional[Dict[str, Any]]):
        """에러 로깅"""
        logger.error(
            f"Plugin Error [{error.code.value}]: {error.message}",
            extra={
                "plugin_id": error.plugin_id,
                "user_id": error.user_id,
                "trace_id": error.trace_id,
                "error_details": error.details,
                "context": context
            }
        )
    
    def _add_to_history(self, error: PluginException):
        """에러 히스토리에 추가"""
        error_detail = PluginErrorDetail(
            code=error.code,
            message=error.message,
            details=error.details,
            timestamp=error.timestamp,
            plugin_id=error.plugin_id,
            user_id=error.user_id,
            trace_id=error.trace_id
        )
        
        self.error_history.append(error_detail)
        
        # 히스토리 크기 제한 (최근 1000개만 유지)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def add_error_callback(self, callback: Callable[[PluginException], None]):
        """에러 콜백 추가"""
        self.error_callbacks.append(callback)
    
    async def attempt_recovery(
        self,
        error: PluginException,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """에러 복구 시도"""
        strategy = self.recovery_strategies.get(error.code, RecoveryStrategy.MANUAL_INTERVENTION)
        
        try:
            if strategy == RecoveryStrategy.RETRY:
                return await self._retry_recovery(error, context)
            elif strategy == RecoveryStrategy.FALLBACK:
                return await self._fallback_recovery(error, context)
            elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                return await self._circuit_breaker_recovery(error, context)
            elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                return await self._graceful_degradation_recovery(error, context)
            else:
                logger.warning(f"Manual intervention required for error: {error.code.value}")
                return None
                
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {str(recovery_error)}")
            return None
    
    async def _retry_recovery(
        self,
        error: PluginException,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """재시도 복구"""
        retry_key = f"{error.plugin_id}:{error.code.value}"
        current_retries = self.retry_counts.get(retry_key, 0)
        max_retries = 3
        
        if current_retries >= max_retries:
            logger.warning(f"Max retries exceeded for {retry_key}")
            return None
        
        self.retry_counts[retry_key] = current_retries + 1
        
        # 지수 백오프
        delay = 2 ** current_retries
        await asyncio.sleep(delay)
        
        return {"recovery_action": "retry", "attempt": current_retries + 1}
    
    async def _fallback_recovery(
        self,
        error: PluginException,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """폴백 복구"""
        return {"recovery_action": "fallback", "fallback_result": "default_response"}
    
    async def _circuit_breaker_recovery(
        self,
        error: PluginException,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """서킷 브레이커 복구"""
        plugin_id = error.plugin_id or "unknown"
        
        if plugin_id not in self.circuit_breakers:
            self.circuit_breakers[plugin_id] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure": None,
                "timeout": 60  # 60초 후 재시도
            }
        
        breaker = self.circuit_breakers[plugin_id]
        breaker["failure_count"] += 1
        breaker["last_failure"] = datetime.now()
        
        if breaker["failure_count"] >= 5:
            breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened for plugin: {plugin_id}")
        
        return {"recovery_action": "circuit_breaker", "state": breaker["state"]}
    
    async def _graceful_degradation_recovery(
        self,
        error: PluginException,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """우아한 성능 저하 복구"""
        return {
            "recovery_action": "graceful_degradation",
            "degraded_service": True,
            "message": "Service running in degraded mode"
        }
    
    def get_plugin_error_summary(self, plugin_id: str, hours: int = 24) -> Dict[str, Any]:
        """플러그인별 에러 요약"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        plugin_errors = [
            error for error in self.error_history
            if error.plugin_id == plugin_id and error.timestamp >= cutoff_time
        ]
        
        error_counts = {}
        for error in plugin_errors:
            code = error.code.value
            error_counts[code] = error_counts.get(code, 0) + 1
        
        return {
            "plugin_id": plugin_id,
            "total_errors": len(plugin_errors),
            "error_by_code": error_counts,
            "recent_errors": [error.dict() for error in plugin_errors[-5:]],
            "circuit_breaker_state": self.circuit_breakers.get(plugin_id, {}).get("state", "closed")
        }

# 전역 에러 핸들러
plugin_error_handler = PluginErrorHandler()


# 에러 처리 데코레이터
def handle_plugin_errors(
    attempt_recovery: bool = False,
    max_retries: int = 3,
    fallback_result: Any = None
):
    """플러그인 에러 처리 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except PluginException as e:
                    if attempt < max_retries and attempt_recovery:
                        recovery_result = await plugin_error_handler.attempt_recovery(e)
                        if recovery_result:
                            continue
                    
                    # 콜백 실행
                    for callback in plugin_error_handler.error_callbacks:
                        try:
                            await callback(e)
                        except Exception as callback_error:
                            logger.error(f"Error callback failed: {str(callback_error)}")
                    
                    if attempt == max_retries and fallback_result is not None:
                        return fallback_result
                    
                    raise
                except Exception as e:
                    plugin_exception = plugin_error_handler.handle_exception(e)
                    
                    if attempt < max_retries and attempt_recovery:
                        recovery_result = await plugin_error_handler.attempt_recovery(plugin_exception)
                        if recovery_result:
                            continue
                    
                    if attempt == max_retries and fallback_result is not None:
                        return fallback_result
                    
                    raise plugin_exception
        
        return wrapper
    return decorator


@asynccontextmanager
async def plugin_error_context(
    plugin_id: Optional[str] = None,
    user_id: Optional[str] = None,
    operation: Optional[str] = None
):
    """플러그인 에러 컨텍스트 매니저"""
    trace_id = str(uuid.uuid4())
    
    try:
        yield trace_id
    except Exception as e:
        plugin_exception = plugin_error_handler.handle_exception(
            e,
            plugin_id=plugin_id,
            user_id=user_id,
            trace_id=trace_id,
            context={"operation": operation}
        )
        raise plugin_exception


# 특화된 에러 클래스들
class PluginSecurityError(PluginException):
    """플러그인 보안 에러"""
    
    def __init__(self, message: str, security_context: Dict[str, Any], **kwargs):
        super().__init__(
            code=PluginErrorCode.SECURITY_VIOLATION,
            message=message,
            details={"security_context": security_context},
            **kwargs
        )
        self.category = ErrorCategory.SECURITY


class PluginResourceError(PluginException):
    """플러그인 리소스 에러"""
    
    def __init__(self, message: str, resource_type: str, limit: Any, current: Any, **kwargs):
        super().__init__(
            code=PluginErrorCode.RESOURCE_EXHAUSTED,
            message=message,
            details={
                "resource_type": resource_type,
                "limit": limit,
                "current": current
            },
            **kwargs
        )
        self.category = ErrorCategory.PERFORMANCE


class PluginNetworkError(PluginException):
    """플러그인 네트워크 에러"""
    
    def __init__(self, message: str, endpoint: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(
            code=PluginErrorCode.NETWORK_ERROR,
            message=message,
            details={
                "endpoint": endpoint,
                "status_code": status_code
            },
            **kwargs
        )
        self.category = ErrorCategory.INFRASTRUCTURE


# 전역 에러 핸들러 인스턴스
enhanced_plugin_error_handler = PluginErrorHandler()

# 기존 호환성을 위한 별칭
plugin_error_handler = enhanced_plugin_error_handler