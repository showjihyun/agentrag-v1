"""
Enhanced Error Handling System

통합 에러 핸들링 시스템으로 구조화된 에러 타입, 추적, 로깅을 제공합니다.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Type
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """에러 심각도 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """에러 카테고리"""
    DATABASE = "database"
    LLM = "llm"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    NETWORK = "network"
    TIMEOUT = "timeout"


class BaseAppError(Exception):
    """애플리케이션 기본 에러 클래스"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.utcnow()
        self.traceback = traceback.format_exc() if original_error else None
    
    def to_dict(self) -> Dict[str, Any]:
        """에러를 딕셔너리로 변환"""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_error) if self.original_error else None
        }


class DatabaseError(BaseAppError):
    """데이터베이스 관련 에러"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details=details,
            original_error=original_error
        )


class LLMError(BaseAppError):
    """LLM 관련 에러"""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        error_details = details or {}
        if provider:
            error_details["provider"] = provider
        if model:
            error_details["model"] = model
        
        super().__init__(
            message=message,
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.MEDIUM,
            details=error_details,
            original_error=original_error
        )


class ValidationError(BaseAppError):
    """검증 에러"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=error_details
        )


class AuthenticationError(BaseAppError):
    """인증 에러"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            details=details
        )


class AuthorizationError(BaseAppError):
    """인가 에러"""
    
    def __init__(
        self,
        message: str = "Access denied",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if resource:
            error_details["resource"] = resource
        if action:
            error_details["action"] = action
        
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            details=error_details
        )


class RateLimitError(BaseAppError):
    """Rate Limit 에러"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if limit:
            error_details["limit"] = limit
        if window:
            error_details["window"] = window
        if retry_after:
            error_details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            details=error_details
        )


class ExternalServiceError(BaseAppError):
    """외부 서비스 에러"""
    
    def __init__(
        self,
        message: str,
        service: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        error_details = details or {}
        error_details["service"] = service
        
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            details=error_details,
            original_error=original_error
        )


class TimeoutError(BaseAppError):
    """타임아웃 에러"""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if timeout_seconds:
            error_details["timeout_seconds"] = timeout_seconds
        if operation:
            error_details["operation"] = operation
        
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            details=error_details
        )


class ErrorHandler:
    """통합 에러 핸들러"""
    
    def __init__(self, enable_sentry: bool = False):
        """
        Initialize ErrorHandler.
        
        Args:
            enable_sentry: Sentry 통합 활성화 여부
        """
        self.enable_sentry = enable_sentry
        self._error_counts: Dict[str, int] = {}
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> BaseAppError:
        """
        에러를 처리하고 적절한 BaseAppError로 변환
        
        Args:
            error: 원본 에러
            context: 추가 컨텍스트 정보
            
        Returns:
            BaseAppError 인스턴스
        """
        # 이미 BaseAppError인 경우
        if isinstance(error, BaseAppError):
            self._log_error(error, context)
            return error
        
        # 에러 타입에 따라 적절한 에러로 변환
        app_error = self._convert_to_app_error(error, context)
        self._log_error(app_error, context)
        
        # Sentry에 보고 (활성화된 경우)
        if self.enable_sentry:
            self._report_to_sentry(app_error, context)
        
        return app_error
    
    def _convert_to_app_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> BaseAppError:
        """원본 에러를 BaseAppError로 변환"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # 데이터베이스 에러
        if "database" in error_message.lower() or "sql" in error_message.lower():
            return DatabaseError(
                message=f"Database error: {error_message}",
                details=context,
                original_error=error
            )
        
        # 타임아웃 에러
        if "timeout" in error_message.lower():
            return TimeoutError(
                message=f"Operation timed out: {error_message}",
                details=context
            )
        
        # 기본 내부 에러
        return BaseAppError(
            message=f"{error_type}: {error_message}",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            details=context,
            original_error=error
        )
    
    def _log_error(
        self,
        error: BaseAppError,
        context: Optional[Dict[str, Any]] = None
    ):
        """에러 로깅"""
        log_data = {
            "error": error.to_dict(),
            "context": context or {}
        }
        
        # 심각도에 따라 로그 레벨 결정
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error.message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {error.message}", extra=log_data)
        
        # 에러 카운트 증가
        error_key = f"{error.category.value}:{error.severity.value}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
    
    def _report_to_sentry(
        self,
        error: BaseAppError,
        context: Optional[Dict[str, Any]] = None
    ):
        """Sentry에 에러 보고 (향후 구현)"""
        # TODO: Sentry SDK 통합
        pass
    
    def get_error_stats(self) -> Dict[str, int]:
        """에러 통계 반환"""
        return self._error_counts.copy()
    
    def reset_stats(self):
        """에러 통계 초기화"""
        self._error_counts.clear()


# 전역 에러 핸들러 인스턴스
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """전역 에러 핸들러 인스턴스 반환"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> BaseAppError:
    """에러 처리 헬퍼 함수"""
    handler = get_error_handler()
    return handler.handle_error(error, context)
