"""
Smart Error Recovery Service

AI-powered error analysis and automatic recovery for workflows.
Features:
- Error classification and pattern recognition
- AI-generated fix suggestions
- Automatic recovery strategies
- Error history learning
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import hashlib

from backend.config import settings


class ErrorType(str, Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"
    UNKNOWN = "unknown"


class RecoveryType(str, Enum):
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    USE_FALLBACK = "use_fallback"
    USE_CACHE = "use_cache"
    SKIP_NODE = "skip_node"
    MANUAL_INPUT = "manual_input"
    MODIFY_CONFIG = "modify_config"
    CONTACT_SUPPORT = "contact_support"


class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkflowError:
    """Represents a workflow execution error."""
    id: str
    node_id: str
    node_name: str
    node_type: str
    error_type: ErrorType
    message: str
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "error_type": self.error_type.value,
            "error_code": self.error_code,
            "message": self.message,
            "stack_trace": self.stack_trace,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class RecoveryOption:
    """A recovery option for an error."""
    id: str
    type: RecoveryType
    title: str
    description: str
    confidence: float  # 0-100
    estimated_time: Optional[str] = None
    is_recommended: bool = False
    requires_input: bool = False
    input_label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "estimatedTime": self.estimated_time,
            "isRecommended": self.is_recommended,
            "requiresInput": self.requires_input,
            "inputLabel": self.input_label,
            "metadata": self.metadata,
        }


@dataclass
class AIAnalysis:
    """AI-generated error analysis."""
    summary: str
    root_cause: str
    impact: ImpactLevel
    similar_errors: int = 0
    suggested_fix: Optional[str] = None
    code_snippet: Optional[str] = None
    documentation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "rootCause": self.root_cause,
            "impact": self.impact.value,
            "similarErrors": self.similar_errors,
            "suggestedFix": self.suggested_fix,
            "codeSnippet": self.code_snippet,
            "documentation": self.documentation,
        }


@dataclass
class ErrorPattern:
    """Learned error pattern for prediction."""
    pattern_hash: str
    error_type: ErrorType
    node_type: str
    message_pattern: str
    occurrence_count: int = 0
    successful_recoveries: Dict[RecoveryType, int] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.utcnow)


class SmartErrorRecoveryService:
    """
    AI-powered error recovery service.
    
    Features:
    - Automatic error classification
    - Pattern-based error recognition
    - AI-generated recovery suggestions
    - Learning from successful recoveries
    """
    
    def __init__(self):
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.error_history: List[WorkflowError] = []
        self.recovery_history: List[Dict[str, Any]] = []
        self._llm_client = None
        
        # Error classification patterns
        self.classification_patterns = {
            ErrorType.RATE_LIMIT: [
                r"rate.?limit",
                r"too.?many.?requests",
                r"429",
                r"quota.?exceeded",
                r"throttl",
            ],
            ErrorType.TIMEOUT: [
                r"timeout",
                r"timed?.?out",
                r"deadline.?exceeded",
                r"connection.?timed",
            ],
            ErrorType.CONNECTION: [
                r"connection.?(refused|reset|failed)",
                r"network.?error",
                r"ECONNREFUSED",
                r"ENOTFOUND",
                r"socket.?hang",
            ],
            ErrorType.AUTHENTICATION: [
                r"auth(entication|orization)?.?(failed|error|invalid)",
                r"401",
                r"403",
                r"invalid.?(token|key|credential)",
                r"access.?denied",
            ],
            ErrorType.VALIDATION: [
                r"validation.?(error|failed)",
                r"invalid.?(input|parameter|argument)",
                r"required.?field",
                r"type.?error",
                r"schema.?error",
            ],
            ErrorType.RESOURCE_NOT_FOUND: [
                r"not.?found",
                r"404",
                r"does.?not.?exist",
                r"no.?such",
            ],
            ErrorType.PERMISSION_DENIED: [
                r"permission.?denied",
                r"forbidden",
                r"not.?authorized",
                r"insufficient.?permissions",
            ],
        }
    
    def classify_error(self, message: str, error_code: Optional[str] = None) -> ErrorType:
        """Classify error based on message and code."""
        message_lower = message.lower()
        
        for error_type, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return error_type
        
        # Check error code
        if error_code:
            code = str(error_code)
            if code.startswith("4"):
                if code == "401":
                    return ErrorType.AUTHENTICATION
                elif code == "403":
                    return ErrorType.PERMISSION_DENIED
                elif code == "404":
                    return ErrorType.RESOURCE_NOT_FOUND
                elif code == "429":
                    return ErrorType.RATE_LIMIT
                else:
                    return ErrorType.VALIDATION
            elif code.startswith("5"):
                return ErrorType.INTERNAL_ERROR
        
        return ErrorType.UNKNOWN
    
    def _generate_pattern_hash(self, error: WorkflowError) -> str:
        """Generate a hash for error pattern matching."""
        # Normalize message by removing specific values
        normalized_msg = re.sub(r'\d+', 'N', error.message)
        normalized_msg = re.sub(r'[a-f0-9]{8,}', 'ID', normalized_msg, flags=re.IGNORECASE)
        
        pattern_str = f"{error.node_type}:{error.error_type.value}:{normalized_msg}"
        return hashlib.md5(pattern_str.encode()).hexdigest()[:16]
    
    def _learn_pattern(self, error: WorkflowError):
        """Learn from error for future predictions."""
        pattern_hash = self._generate_pattern_hash(error)
        
        if pattern_hash in self.error_patterns:
            pattern = self.error_patterns[pattern_hash]
            pattern.occurrence_count += 1
            pattern.last_seen = datetime.utcnow()
        else:
            self.error_patterns[pattern_hash] = ErrorPattern(
                pattern_hash=pattern_hash,
                error_type=error.error_type,
                node_type=error.node_type,
                message_pattern=error.message[:100],
                occurrence_count=1,
            )
    
    def _find_similar_errors(self, error: WorkflowError) -> int:
        """Find similar errors in history."""
        pattern_hash = self._generate_pattern_hash(error)
        
        if pattern_hash in self.error_patterns:
            return self.error_patterns[pattern_hash].occurrence_count
        
        return 0
    
    def _get_best_recovery_from_history(self, error: WorkflowError) -> Optional[RecoveryType]:
        """Get the most successful recovery type from history."""
        pattern_hash = self._generate_pattern_hash(error)
        
        if pattern_hash in self.error_patterns:
            pattern = self.error_patterns[pattern_hash]
            if pattern.successful_recoveries:
                return max(
                    pattern.successful_recoveries.items(),
                    key=lambda x: x[1]
                )[0]
        
        return None
    
    def generate_recovery_options(
        self,
        error: WorkflowError,
        available_fallbacks: Optional[List[str]] = None,
        has_cache: bool = False,
    ) -> List[RecoveryOption]:
        """Generate recovery options based on error type and context."""
        options: List[RecoveryOption] = []
        best_from_history = self._get_best_recovery_from_history(error)
        
        # Error-type specific options
        if error.error_type == ErrorType.RATE_LIMIT:
            options.append(RecoveryOption(
                id="retry_backoff",
                type=RecoveryType.RETRY_WITH_BACKOFF,
                title="지수 백오프로 재시도",
                description="60초 후 자동 재시도합니다. 실패 시 대기 시간이 점진적으로 증가합니다.",
                confidence=85,
                estimated_time="1-5분",
                is_recommended=best_from_history == RecoveryType.RETRY_WITH_BACKOFF or best_from_history is None,
            ))
            
            if available_fallbacks:
                options.append(RecoveryOption(
                    id="use_fallback",
                    type=RecoveryType.USE_FALLBACK,
                    title="대체 서비스 사용",
                    description=f"대체 서비스로 전환합니다: {', '.join(available_fallbacks[:3])}",
                    confidence=90,
                    estimated_time="즉시",
                    is_recommended=best_from_history == RecoveryType.USE_FALLBACK,
                    metadata={"fallbacks": available_fallbacks},
                ))
        
        elif error.error_type == ErrorType.TIMEOUT:
            options.append(RecoveryOption(
                id="retry_timeout",
                type=RecoveryType.RETRY_WITH_BACKOFF,
                title="타임아웃 증가 후 재시도",
                description="타임아웃을 2배로 늘리고 재시도합니다.",
                confidence=70,
                estimated_time="30초-2분",
                is_recommended=True,
            ))
            
            if has_cache:
                options.append(RecoveryOption(
                    id="use_cache",
                    type=RecoveryType.USE_CACHE,
                    title="캐시된 응답 사용",
                    description="이전에 캐시된 유사한 요청의 응답을 사용합니다.",
                    confidence=75,
                    estimated_time="즉시",
                ))
        
        elif error.error_type == ErrorType.AUTHENTICATION:
            options.append(RecoveryOption(
                id="refresh_auth",
                type=RecoveryType.MODIFY_CONFIG,
                title="인증 정보 갱신",
                description="토큰을 갱신하거나 API 키를 다시 확인합니다.",
                confidence=80,
                estimated_time="즉시",
                is_recommended=True,
            ))
            
            options.append(RecoveryOption(
                id="manual_auth",
                type=RecoveryType.MANUAL_INPUT,
                title="수동으로 인증 정보 입력",
                description="새로운 API 키 또는 토큰을 직접 입력합니다.",
                confidence=95,
                requires_input=True,
                input_label="API Key / Token",
            ))
        
        elif error.error_type == ErrorType.VALIDATION:
            options.append(RecoveryOption(
                id="manual_fix",
                type=RecoveryType.MANUAL_INPUT,
                title="입력 데이터 수정",
                description="올바른 형식의 데이터를 직접 입력합니다.",
                confidence=90,
                requires_input=True,
                input_label="수정된 입력 데이터 (JSON)",
                is_recommended=True,
            ))
            
            options.append(RecoveryOption(
                id="skip_validation",
                type=RecoveryType.SKIP_NODE,
                title="이 노드 건너뛰기",
                description="이 노드를 건너뛰고 다음 노드로 진행합니다.",
                confidence=60,
            ))
        
        elif error.error_type == ErrorType.CONNECTION:
            options.append(RecoveryOption(
                id="retry_connection",
                type=RecoveryType.RETRY_WITH_BACKOFF,
                title="연결 재시도",
                description="네트워크 연결을 다시 시도합니다.",
                confidence=75,
                estimated_time="10-30초",
                is_recommended=True,
            ))
            
            if available_fallbacks:
                options.append(RecoveryOption(
                    id="fallback_endpoint",
                    type=RecoveryType.USE_FALLBACK,
                    title="대체 엔드포인트 사용",
                    description="다른 서버 또는 리전의 엔드포인트를 사용합니다.",
                    confidence=85,
                    estimated_time="즉시",
                ))
        
        # Common options for all error types
        if error.retry_count < error.max_retries:
            if not any(o.type == RecoveryType.RETRY_WITH_BACKOFF for o in options):
                options.append(RecoveryOption(
                    id="simple_retry",
                    type=RecoveryType.RETRY_WITH_BACKOFF,
                    title="단순 재시도",
                    description=f"즉시 재시도합니다. ({error.retry_count + 1}/{error.max_retries})",
                    confidence=50,
                    estimated_time="즉시",
                ))
        
        options.append(RecoveryOption(
            id="skip",
            type=RecoveryType.SKIP_NODE,
            title="노드 건너뛰기",
            description="이 노드를 건너뛰고 워크플로우를 계속 진행합니다.",
            confidence=40,
        ))
        
        options.append(RecoveryOption(
            id="support",
            type=RecoveryType.CONTACT_SUPPORT,
            title="지원 요청",
            description="기술 지원팀에 문의합니다.",
            confidence=30,
        ))
        
        # Sort by confidence and recommendation
        options.sort(key=lambda x: (x.is_recommended, x.confidence), reverse=True)
        
        return options
    
    async def analyze_error_with_ai(
        self,
        error: WorkflowError,
        workflow_context: Optional[Dict[str, Any]] = None,
    ) -> AIAnalysis:
        """Use AI to analyze error and suggest fixes."""
        # Learn from this error
        self._learn_pattern(error)
        similar_count = self._find_similar_errors(error)
        
        # Determine impact level
        impact = self._assess_impact(error, workflow_context)
        
        # Generate analysis based on error type
        analysis = self._generate_analysis(error, similar_count, impact)
        
        # Try to get AI-enhanced analysis if LLM is available
        if self._llm_client:
            try:
                enhanced = await self._get_llm_analysis(error, workflow_context)
                if enhanced:
                    analysis.suggested_fix = enhanced.get("suggested_fix", analysis.suggested_fix)
                    analysis.code_snippet = enhanced.get("code_snippet")
                    analysis.root_cause = enhanced.get("root_cause", analysis.root_cause)
            except Exception:
                pass  # Fall back to rule-based analysis
        
        return analysis
    
    def _assess_impact(
        self,
        error: WorkflowError,
        workflow_context: Optional[Dict[str, Any]] = None,
    ) -> ImpactLevel:
        """Assess the impact level of an error."""
        # Critical errors
        if error.error_type in [ErrorType.AUTHENTICATION, ErrorType.PERMISSION_DENIED]:
            return ImpactLevel.HIGH
        
        # Check if it's a critical node
        if workflow_context:
            critical_nodes = workflow_context.get("critical_nodes", [])
            if error.node_id in critical_nodes:
                return ImpactLevel.CRITICAL
        
        # High retry count indicates persistent issue
        if error.retry_count >= error.max_retries - 1:
            return ImpactLevel.HIGH
        
        # Rate limits are usually medium impact
        if error.error_type == ErrorType.RATE_LIMIT:
            return ImpactLevel.MEDIUM
        
        # Validation errors are usually low impact
        if error.error_type == ErrorType.VALIDATION:
            return ImpactLevel.LOW
        
        return ImpactLevel.MEDIUM
    
    def _generate_analysis(
        self,
        error: WorkflowError,
        similar_count: int,
        impact: ImpactLevel,
    ) -> AIAnalysis:
        """Generate rule-based error analysis."""
        summaries = {
            ErrorType.RATE_LIMIT: "API 호출 한도를 초과했습니다. 잠시 후 다시 시도하거나 대체 서비스를 사용하세요.",
            ErrorType.TIMEOUT: "요청 시간이 초과되었습니다. 네트워크 상태를 확인하거나 타임아웃 설정을 조정하세요.",
            ErrorType.CONNECTION: "서버에 연결할 수 없습니다. 네트워크 연결 상태와 서버 상태를 확인하세요.",
            ErrorType.AUTHENTICATION: "인증에 실패했습니다. API 키 또는 토큰이 유효한지 확인하세요.",
            ErrorType.VALIDATION: "입력 데이터가 올바르지 않습니다. 데이터 형식과 필수 필드를 확인하세요.",
            ErrorType.RESOURCE_NOT_FOUND: "요청한 리소스를 찾을 수 없습니다. URL 또는 ID가 올바른지 확인하세요.",
            ErrorType.PERMISSION_DENIED: "접근 권한이 없습니다. 계정 권한 설정을 확인하세요.",
            ErrorType.INTERNAL_ERROR: "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도하세요.",
            ErrorType.UNKNOWN: "알 수 없는 오류가 발생했습니다. 로그를 확인하고 지원팀에 문의하세요.",
        }
        
        root_causes = {
            ErrorType.RATE_LIMIT: "API 제공자의 호출 한도 정책에 의해 요청이 거부되었습니다.",
            ErrorType.TIMEOUT: "서버 응답 시간이 설정된 타임아웃을 초과했습니다.",
            ErrorType.CONNECTION: "네트워크 문제 또는 서버 다운으로 연결이 실패했습니다.",
            ErrorType.AUTHENTICATION: "제공된 인증 정보가 유효하지 않거나 만료되었습니다.",
            ErrorType.VALIDATION: "입력 데이터가 예상된 스키마 또는 형식과 일치하지 않습니다.",
            ErrorType.RESOURCE_NOT_FOUND: "요청된 리소스가 존재하지 않거나 삭제되었습니다.",
            ErrorType.PERMISSION_DENIED: "현재 사용자/앱에 해당 작업을 수행할 권한이 없습니다.",
            ErrorType.INTERNAL_ERROR: "서버 측에서 예기치 않은 오류가 발생했습니다.",
            ErrorType.UNKNOWN: "오류의 정확한 원인을 파악할 수 없습니다.",
        }
        
        suggested_fixes = {
            ErrorType.RATE_LIMIT: "1. 요청 간격을 늘리세요\n2. 배치 처리를 사용하세요\n3. 캐싱을 활성화하세요",
            ErrorType.TIMEOUT: "1. 타임아웃 값을 늘리세요\n2. 요청 크기를 줄이세요\n3. 비동기 처리를 고려하세요",
            ErrorType.CONNECTION: "1. 네트워크 연결을 확인하세요\n2. 방화벽 설정을 확인하세요\n3. DNS 설정을 확인하세요",
            ErrorType.AUTHENTICATION: "1. API 키가 올바른지 확인하세요\n2. 토큰이 만료되지 않았는지 확인하세요\n3. 권한 범위를 확인하세요",
            ErrorType.VALIDATION: "1. 입력 데이터 형식을 확인하세요\n2. 필수 필드가 모두 있는지 확인하세요\n3. 데이터 타입을 확인하세요",
        }
        
        return AIAnalysis(
            summary=summaries.get(error.error_type, summaries[ErrorType.UNKNOWN]),
            root_cause=root_causes.get(error.error_type, root_causes[ErrorType.UNKNOWN]),
            impact=impact,
            similar_errors=similar_count,
            suggested_fix=suggested_fixes.get(error.error_type),
        )
    
    async def _get_llm_analysis(
        self,
        error: WorkflowError,
        workflow_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get enhanced analysis from LLM."""
        # This would integrate with the LLM service
        # For now, return None to use rule-based analysis
        return None
    
    async def execute_recovery(
        self,
        error: WorkflowError,
        recovery_type: RecoveryType,
        input_data: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Any]]:
        """
        Execute a recovery action.
        
        Returns:
            Tuple of (success, message, result_data)
        """
        try:
            if recovery_type == RecoveryType.RETRY_WITH_BACKOFF:
                # Calculate backoff time
                backoff_seconds = min(60 * (2 ** error.retry_count), 300)
                return True, f"{backoff_seconds}초 후 재시도 예약됨", {"backoff_seconds": backoff_seconds}
            
            elif recovery_type == RecoveryType.USE_FALLBACK:
                return True, "대체 서비스로 전환됨", {"switched_to_fallback": True}
            
            elif recovery_type == RecoveryType.USE_CACHE:
                return True, "캐시된 응답 사용", {"from_cache": True}
            
            elif recovery_type == RecoveryType.SKIP_NODE:
                return True, "노드 건너뜀", {"skipped": True}
            
            elif recovery_type == RecoveryType.MANUAL_INPUT:
                if not input_data:
                    return False, "입력 데이터가 필요합니다", None
                return True, "수동 입력 적용됨", {"manual_input": input_data}
            
            elif recovery_type == RecoveryType.MODIFY_CONFIG:
                return True, "설정 수정됨", {"config_modified": True}
            
            else:
                return False, "지원되지 않는 복구 유형", None
                
        except Exception as e:
            return False, f"복구 실행 실패: {str(e)}", None
    
    def record_recovery_result(
        self,
        error: WorkflowError,
        recovery_type: RecoveryType,
        success: bool,
    ):
        """Record recovery result for learning."""
        pattern_hash = self._generate_pattern_hash(error)
        
        if pattern_hash in self.error_patterns and success:
            pattern = self.error_patterns[pattern_hash]
            if recovery_type not in pattern.successful_recoveries:
                pattern.successful_recoveries[recovery_type] = 0
            pattern.successful_recoveries[recovery_type] += 1
        
        self.recovery_history.append({
            "error_id": error.id,
            "pattern_hash": pattern_hash,
            "recovery_type": recovery_type.value,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        })


# Singleton instance
_smart_recovery_service: Optional[SmartErrorRecoveryService] = None


def get_smart_recovery_service() -> SmartErrorRecoveryService:
    """Get the singleton SmartErrorRecoveryService instance."""
    global _smart_recovery_service
    if _smart_recovery_service is None:
        _smart_recovery_service = SmartErrorRecoveryService()
    return _smart_recovery_service
