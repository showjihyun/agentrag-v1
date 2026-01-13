"""
Orchestration Patterns API
오케스트레이션 패턴 관리 및 실행 API (향상된 에러 처리 포함)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.core.structured_logging import get_logger
from backend.services.agent_builder.orchestration.orchestration_factory import OrchestrationFactory
from backend.services.agent_builder.orchestration.pattern_registry import PatternRegistry
from backend.core.security.orchestration_security import OrchestrationSecurity, validate_execution_timeout
from backend.core.cache.orchestration_cache import get_orchestration_cache_manager
from backend.core.error_handling.orchestration_errors import (
    get_error_handler,
    error_context,
    OrchestrationError,
    ConfigurationError,
    ValidationError,
    ExecutionError,
    SecurityError,
    PerformanceError,
    ErrorCode,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agent-builder/orchestration", tags=["Orchestration Patterns"])


# ============================================================================
# Request/Response Models
# ============================================================================

from pydantic import BaseModel

class OrchestrationPatternInfo(BaseModel):
    """오케스트레이션 패턴 정보"""
    id: str
    name: str
    description: str
    category: str
    complexity: str
    use_case: str
    benefits: List[str]
    requirements: List[str]
    estimated_setup_time: str


class AgentRoleConfig(BaseModel):
    """Agent 역할 설정"""
    id: str
    name: str
    role: str
    priority: int
    max_retries: int = 3
    timeout_seconds: int = 300
    dependencies: List[str] = []


class SupervisorConfig(BaseModel):
    """Supervisor 설정"""
    enabled: bool = False
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1"
    max_iterations: int = 10
    decision_strategy: str = "llm_based"
    fallback_agent_id: Optional[str] = None


class CommunicationRules(BaseModel):
    """통신 규칙"""
    allow_direct_communication: bool = True
    enable_broadcast: bool = False
    require_consensus: bool = False
    max_negotiation_rounds: int = 3


class PerformanceThresholds(BaseModel):
    """성능 임계값"""
    max_execution_time: int = 300000  # 5분
    min_success_rate: float = 0.8
    max_token_usage: int = 10000


class OrchestrationConfig(BaseModel):
    """오케스트레이션 설정"""
    orchestration_type: str
    name: str
    description: Optional[str] = None
    supervisor_config: SupervisorConfig
    agent_roles: List[AgentRoleConfig]
    communication_rules: CommunicationRules
    performance_thresholds: PerformanceThresholds
    tags: List[str] = []


class ExecuteOrchestrationRequest(BaseModel):
    """오케스트레이션 실행 요청"""
    config: OrchestrationConfig
    input_data: Dict[str, Any]
    execution_mode: str = "async"  # "async" | "sync" | "streaming"


class OrchestrationExecutionStatus(BaseModel):
    """오케스트레이션 실행 상태"""
    execution_id: str
    status: str
    orchestration_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    active_agents: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    current_phase: Optional[str] = None
    agent_statuses: Dict[str, Any] = {}
    communication_log: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = False
    error: Dict[str, Any]


# ============================================================================
# Error Handling Utilities
# ============================================================================

def handle_api_error(func):
    """API 에러 처리 데코레이터"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except OrchestrationError as e:
            error_handler = get_error_handler()
            error_detail = error_handler.handle_error(e)
            
            # HTTP 상태 코드 매핑
            status_code_map = {
                ErrorCategory.CONFIGURATION: 400,
                ErrorCategory.VALIDATION: 400,
                ErrorCategory.SECURITY: 403,
                ErrorCategory.PERFORMANCE: 429,
                ErrorCategory.TIMEOUT: 408,
                ErrorCategory.SYSTEM: 500,
                ErrorCategory.NETWORK: 502,
                ErrorCategory.RESOURCE: 503,
            }
            
            status_code = status_code_map.get(e.detail.category, 500)
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "code": error_detail.code.value,
                    "message": error_detail.message,
                    "severity": error_detail.severity.value,
                    "category": error_detail.category.value,
                    "suggestions": error_detail.suggestions,
                    "recovery_actions": error_detail.recovery_actions,
                    "timestamp": error_detail.timestamp,
                    "context": {
                        "execution_id": error_detail.context.execution_id,
                        "pattern_type": error_detail.context.pattern_type,
                        "step": error_detail.context.step
                    }
                }
            )
        except Exception as e:
            error_handler = get_error_handler()
            error_detail = error_handler.handle_error(e)
            
            logger.error(f"Unexpected error in API: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "ORH-1601",
                    "message": "Internal server error occurred",
                    "severity": "high",
                    "category": "system",
                    "suggestions": ["Please try again later", "Contact support if the issue persists"],
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    return wrapper


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/patterns", response_model=List[OrchestrationPatternInfo])
@handle_api_error
async def get_orchestration_patterns():
    """
    사용 가능한 모든 오케스트레이션 패턴 조회
    """
    with error_context(step="get_patterns"):
        try:
            patterns = PatternRegistry.get_all_patterns()
            return [
                OrchestrationPatternInfo(
                    id=pattern_id,
                    name=pattern_info["name"],
                    description=pattern_info["description"],
                    category=pattern_info["category"],
                    complexity=pattern_info["complexity"],
                    use_case=pattern_info["use_case"],
                    benefits=pattern_info["benefits"],
                    requirements=pattern_info["requirements"],
                    estimated_setup_time=pattern_info["estimated_setup_time"]
                )
                for pattern_id, pattern_info in patterns.items()
            ]
        except KeyError as e:
            raise ConfigurationError(
                message=f"Pattern registry configuration error: {str(e)}",
                code=ErrorCode.MISSING_REQUIRED_CONFIG,
                suggestions=["Check pattern registry configuration", "Restart the service"]
            )


@router.get("/patterns/{pattern_type}")
@handle_api_error
async def get_pattern_details(pattern_type: str):
    """
    특정 오케스트레이션 패턴의 상세 정보 조회 (캐싱 적용)
    """
    with error_context(pattern_type=pattern_type, step="get_pattern_details"):
        try:
            cache_manager = get_orchestration_cache_manager()
            
            # 캐시에서 먼저 조회
            cached_metadata = await cache_manager.get_pattern_metadata(pattern_type)
            if cached_metadata:
                logger.debug(f"Pattern metadata cache hit: {pattern_type}")
                return cached_metadata
            
            # 캐시 미스 시 실제 데이터 조회
            pattern_info = PatternRegistry.get_pattern(pattern_type)
            if not pattern_info:
                raise ConfigurationError(
                    message=f"Pattern '{pattern_type}' not found",
                    code=ErrorCode.INVALID_PATTERN_TYPE,
                    suggestions=[
                        "Check the pattern type spelling",
                        "Use /patterns endpoint to see available patterns",
                        f"Available patterns: {list(PatternRegistry.get_all_patterns().keys())}"
                    ]
                )
            
            result = {
                "pattern_info": pattern_info,
                "recommended_agents": PatternRegistry.get_recommended_agents(pattern_type),
                "configuration_template": PatternRegistry.get_configuration_template(pattern_type),
                "example_workflows": PatternRegistry.get_example_workflows(pattern_type)
            }
            
            # 결과를 캐시에 저장
            await cache_manager.cache_pattern_metadata(pattern_type, result)
            
            return result
            
        except Exception as e:
            if isinstance(e, OrchestrationError):
                raise
            raise ConfigurationError(
                message=f"Failed to retrieve pattern details: {str(e)}",
                code=ErrorCode.SYSTEM_ERROR,
                cause=e
            )


@router.post("/patterns/{pattern_type}/validate")
@handle_api_error
async def validate_orchestration_config(
    pattern_type: str,
    config: OrchestrationConfig,
    current_user: User = Depends(get_current_user)
):
    """
    오케스트레이션 설정 검증 (보안 검증 및 캐싱 포함)
    """
    with error_context(
        user_id=str(current_user.id),
        pattern_type=pattern_type,
        step="validate_config"
    ):
        try:
            cache_manager = get_orchestration_cache_manager()
            
            # 설정 해시 생성
            config_hash = cache_manager.generate_config_hash(config.dict())
            
            # 캐시에서 검증 결과 조회
            cached_result = await cache_manager.get_validation_result(pattern_type, config_hash)
            if cached_result:
                logger.debug(f"Validation cache hit: {pattern_type}:{config_hash}")
                return cached_result
            
            # 1. 보안 검증
            try:
                security_result = await OrchestrationSecurity.validate_execution_request(
                    config.dict(), {}, current_user
                )
            except Exception as e:
                raise SecurityError(
                    message=f"Security validation failed: {str(e)}",
                    code=ErrorCode.SECURITY_VALIDATION_FAILED,
                    suggestions=[
                        "Check input data for malicious content",
                        "Verify user permissions",
                        "Review security policies"
                    ],
                    cause=e
                )
            
            if not security_result.valid:
                raise SecurityError(
                    message="Security validation failed",
                    code=ErrorCode.SECURITY_VALIDATION_FAILED,
                    suggestions=security_result.errors + [
                        "Remove potentially harmful content from configuration",
                        "Contact administrator for permission issues"
                    ]
                )
            
            # 2. 패턴별 설정 검증
            try:
                orchestrator = OrchestrationFactory.create(pattern_type)
            except Exception as e:
                raise ConfigurationError(
                    message=f"Failed to create orchestrator for pattern '{pattern_type}': {str(e)}",
                    code=ErrorCode.INVALID_PATTERN_TYPE,
                    suggestions=[
                        "Verify pattern type is supported",
                        "Check pattern type spelling"
                    ],
                    cause=e
                )
            
            try:
                validation_result = await orchestrator.validate_configuration(config.dict())
            except Exception as e:
                raise ValidationError(
                    message=f"Configuration validation failed: {str(e)}",
                    code=ErrorCode.VALIDATION_FAILED,
                    suggestions=[
                        "Check required configuration fields",
                        "Verify agent role configurations",
                        "Review performance thresholds"
                    ],
                    cause=e
                )
            
            result = {
                "valid": validation_result.valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings + security_result.warnings,
                "suggestions": validation_result.suggestions,
                "security": {
                    "risk_level": security_result.risk_level,
                    "warnings": security_result.warnings
                }
            }
            
            # 검증 결과를 캐시에 저장 (성공한 경우만)
            if validation_result.valid:
                await cache_manager.cache_validation_result(pattern_type, config_hash, result)
            
            return result
            
        except Exception as e:
            if isinstance(e, OrchestrationError):
                raise
            raise ValidationError(
                message=f"Validation process failed: {str(e)}",
                code=ErrorCode.VALIDATION_FAILED,
                cause=e
            )


@router.post("/execute")
@validate_execution_timeout(max_seconds=3600)  # 1시간 제한
@handle_api_error
async def execute_orchestration(
    request: ExecuteOrchestrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    오케스트레이션 실행 (보안 검증 및 캐싱 포함)
    """
    execution_id = str(uuid.uuid4())
    
    with error_context(
        user_id=str(current_user.id),
        execution_id=execution_id,
        pattern_type=request.config.orchestration_type,
        step="execute_orchestration"
    ):
        try:
            cache_manager = get_orchestration_cache_manager()
            
            # 설정 및 입력 데이터 해시 생성
            config_hash = cache_manager.generate_config_hash(request.config.dict())
            input_hash = cache_manager.generate_input_hash(request.input_data)
            
            # 캐시에서 실행 결과 조회 (동기 실행인 경우만)
            if request.execution_mode == "sync":
                cached_result = await cache_manager.get_execution_result(
                    request.config.orchestration_type, config_hash, input_hash
                )
                if cached_result:
                    logger.debug(f"Execution cache hit: {request.config.orchestration_type}:{config_hash}:{input_hash}")
                    cached_result["execution_id"] = execution_id  # 새로운 실행 ID 할당
                    return cached_result
            
            # 1. 보안 검증
            try:
                security_result = await OrchestrationSecurity.validate_execution_request(
                    request.config.dict(), request.input_data, current_user
                )
            except Exception as e:
                raise SecurityError(
                    message=f"Security validation failed during execution: {str(e)}",
                    code=ErrorCode.SECURITY_VALIDATION_FAILED,
                    cause=e
                )
            
            if not security_result.valid:
                raise SecurityError(
                    message="Security validation failed for execution request",
                    code=ErrorCode.SECURITY_VALIDATION_FAILED,
                    suggestions=security_result.errors
                )
            
            # 2. 입력 데이터 정화
            try:
                sanitized_config = OrchestrationSecurity.sanitize_input(request.config.dict())
                sanitized_input = OrchestrationSecurity.sanitize_input(request.input_data)
            except Exception as e:
                raise SecurityError(
                    message=f"Input sanitization failed: {str(e)}",
                    code=ErrorCode.INPUT_SANITIZATION_FAILED,
                    cause=e
                )
            
            # 3. 오케스트레이터 생성
            try:
                orchestrator = OrchestrationFactory.create(request.config.orchestration_type)
            except Exception as e:
                raise ConfigurationError(
                    message=f"Failed to create orchestrator: {str(e)}",
                    code=ErrorCode.INVALID_PATTERN_TYPE,
                    cause=e
                )
            
            # 4. 설정 검증
            try:
                validation_result = await orchestrator.validate_configuration(sanitized_config)
                if not validation_result.valid:
                    raise ValidationError(
                        message="Configuration validation failed during execution",
                        code=ErrorCode.VALIDATION_FAILED,
                        suggestions=validation_result.errors
                    )
            except Exception as e:
                if isinstance(e, OrchestrationError):
                    raise
                raise ValidationError(
                    message=f"Configuration validation error: {str(e)}",
                    code=ErrorCode.VALIDATION_FAILED,
                    cause=e
                )
            
            # 5. 실행 컨텍스트 생성
            try:
                execution_context = OrchestrationSecurity.create_execution_context(
                    current_user, sanitized_config
                )
            except Exception as e:
                raise SecurityError(
                    message=f"Failed to create execution context: {str(e)}",
                    code=ErrorCode.SECURITY_POLICY_VIOLATION,
                    cause=e
                )
            
            logger.info(f"Starting orchestration execution: {execution_id}", extra=execution_context)
            
            if request.execution_mode == "sync":
                # 동기 실행
                try:
                    result = await orchestrator.execute(
                        config=sanitized_config,
                        input_data=sanitized_input,
                        user_id=str(current_user.id),
                        execution_id=execution_id
                    )
                    
                    execution_result = {
                        "execution_id": execution_id,
                        "status": result.status.value if hasattr(result, 'status') else "completed",
                        "results": result.results if hasattr(result, 'results') else result,
                        "metrics": result.metrics if hasattr(result, 'metrics') else {},
                        "security": {
                            "risk_level": security_result.risk_level,
                            "warnings": security_result.warnings
                        }
                    }
                    
                    # 성공한 실행 결과를 캐시에 저장
                    if execution_result.get("status") == "completed":
                        await cache_manager.cache_execution_result(
                            request.config.orchestration_type, config_hash, input_hash, execution_result
                        )
                    
                    return execution_result
                    
                except Exception as e:
                    raise ExecutionError(
                        message=f"Synchronous execution failed: {str(e)}",
                        code=ErrorCode.EXECUTION_FAILED,
                        suggestions=[
                            "Check agent configurations",
                            "Verify input data format",
                            "Review performance thresholds"
                        ],
                        cause=e
                    )
            
            elif request.execution_mode == "streaming":
                # 스트리밍 실행 (SSE)
                try:
                    return await orchestrator.execute_streaming(
                        config=sanitized_config,
                        input_data=sanitized_input,
                        user_id=str(current_user.id),
                        execution_id=execution_id
                    )
                except Exception as e:
                    raise ExecutionError(
                        message=f"Streaming execution failed: {str(e)}",
                        code=ErrorCode.EXECUTION_FAILED,
                        cause=e
                    )
            
            else:
                # 비동기 실행 (기본)
                try:
                    background_tasks.add_task(
                        orchestrator.execute_async,
                        config=sanitized_config,
                        input_data=sanitized_input,
                        user_id=str(current_user.id),
                        execution_id=execution_id
                    )
                    
                    return {
                        "execution_id": execution_id,
                        "status": "started",
                        "message": "Orchestration execution started in background",
                        "security": {
                            "risk_level": security_result.risk_level,
                            "warnings": security_result.warnings
                        }
                    }
                except Exception as e:
                    raise ExecutionError(
                        message=f"Asynchronous execution failed to start: {str(e)}",
                        code=ErrorCode.EXECUTION_FAILED,
                        cause=e
                    )
        
        except Exception as e:
            if isinstance(e, OrchestrationError):
                raise
            raise ExecutionError(
                message=f"Execution process failed: {str(e)}",
                code=ErrorCode.EXECUTION_FAILED,
                cause=e
            )


@router.get("/executions/{execution_id}/status")
@handle_api_error
async def get_execution_status(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    오케스트레이션 실행 상태 조회
    """
    with error_context(
        user_id=str(current_user.id),
        execution_id=execution_id,
        step="get_execution_status"
    ):
        try:
            # TODO: 실제 실행 상태를 데이터베이스에서 조회
            # 현재는 mock 데이터 반환
            return OrchestrationExecutionStatus(
                execution_id=execution_id,
                status="running",
                orchestration_type="sequential",
                started_at=datetime.now(),
                progress=0.5,
                active_agents=2,
                completed_tasks=3,
                failed_tasks=0,
                current_phase="agent_execution",
                agent_statuses={
                    "agent_1": {"status": "completed", "progress": 1.0},
                    "agent_2": {"status": "running", "progress": 0.7},
                    "agent_3": {"status": "waiting", "progress": 0.0}
                },
                communication_log=[
                    {
                        "timestamp": datetime.now().isoformat(),
                        "from": "agent_1",
                        "to": "agent_2",
                        "type": "task_result",
                        "message": "Task completed successfully"
                    }
                ],
                metrics={
                    "total_tokens": 1500,
                    "average_response_time": 2.3,
                    "success_rate": 0.85
                }
            )
        except Exception as e:
            raise ExecutionError(
                message=f"Failed to get execution status: {str(e)}",
                code=ErrorCode.SYSTEM_ERROR,
                cause=e
            )


@router.post("/executions/{execution_id}/control")
@handle_api_error
async def control_execution(
    execution_id: str,
    action: str,  # "pause", "resume", "stop", "restart"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    오케스트레이션 실행 제어 (일시정지, 재개, 정지, 재시작)
    """
    with error_context(
        user_id=str(current_user.id),
        execution_id=execution_id,
        step="control_execution"
    ):
        try:
            valid_actions = ["pause", "resume", "stop", "restart"]
            if action not in valid_actions:
                raise ValidationError(
                    message=f"Invalid action '{action}'. Must be one of: {valid_actions}",
                    code=ErrorCode.VALIDATION_FAILED,
                    suggestions=[f"Use one of these actions: {', '.join(valid_actions)}"]
                )
            
            # TODO: 실제 실행 제어 로직 구현
            logger.info(f"Execution {execution_id} action: {action}")
            
            return {
                "execution_id": execution_id,
                "action": action,
                "status": "success",
                "message": f"Execution {action} completed successfully"
            }
        except Exception as e:
            if isinstance(e, OrchestrationError):
                raise
            raise ExecutionError(
                message=f"Failed to control execution: {str(e)}",
                code=ErrorCode.EXECUTION_FAILED,
                cause=e
            )


@router.get("/executions/{execution_id}/stream")
async def stream_execution_updates(execution_id: str):
    """
    오케스트레이션 실행 상태 스트리밍 (SSE)
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def event_generator():
        with error_context(execution_id=execution_id, step="stream_updates"):
            try:
                # TODO: 실제 실행 상태 스트리밍 구현
                for i in range(10):
                    update = {
                        "execution_id": execution_id,
                        "timestamp": datetime.now().isoformat(),
                        "progress": (i + 1) * 0.1,
                        "status": "running" if i < 9 else "completed",
                        "current_agent": f"agent_{i % 3 + 1}",
                        "message": f"Processing step {i + 1}/10"
                    }
                    yield f"data: {json.dumps(update)}\n\n"
                    await asyncio.sleep(1)
            except Exception as e:
                error_handler = get_error_handler()
                error_detail = error_handler.handle_error(e)
                
                error_update = {
                    "execution_id": execution_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": {
                        "code": error_detail.code.value,
                        "message": error_detail.message,
                        "suggestions": error_detail.suggestions
                    }
                }
                yield f"data: {json.dumps(error_update)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/metrics/summary")
@handle_api_error
async def get_orchestration_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    오케스트레이션 메트릭 요약
    """
    with error_context(user_id=str(current_user.id), step="get_metrics"):
        try:
            # TODO: 실제 메트릭 데이터를 데이터베이스에서 조회
            return {
                "total_executions": 156,
                "successful_executions": 142,
                "failed_executions": 14,
                "average_execution_time": 45.2,
                "most_used_patterns": [
                    {"pattern": "sequential", "count": 67},
                    {"pattern": "parallel", "count": 34},
                    {"pattern": "hierarchical", "count": 28},
                    {"pattern": "consensus_building", "count": 15},
                    {"pattern": "swarm_intelligence", "count": 12}
                ],
                "agent_performance": {
                    "average_response_time": 2.1,
                    "success_rate": 0.91,
                    "total_tokens_used": 45670,
                    "cost_estimate": 12.34
                },
                "communication_stats": {
                    "total_messages": 1234,
                    "consensus_reached": 89,
                    "negotiation_rounds_avg": 2.3
                }
            }
        except Exception as e:
            raise ExecutionError(
                message=f"Failed to get orchestration metrics: {str(e)}",
                code=ErrorCode.SYSTEM_ERROR,
                cause=e
            )


@router.get("/cache/stats")
@handle_api_error
async def get_cache_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    캐시 통계 조회
    """
    with error_context(user_id=str(current_user.id), step="get_cache_stats"):
        try:
            cache_manager = get_orchestration_cache_manager()
            cache_stats = cache_manager.cache.get_stats()
            
            return {
                "cache_performance": cache_stats,
                "recommendations": await _generate_cache_recommendations(cache_stats)
            }
        except Exception as e:
            raise PerformanceError(
                message=f"Failed to get cache statistics: {str(e)}",
                code=ErrorCode.CACHE_ERROR,
                cause=e
            )


@router.post("/cache/clear")
@handle_api_error
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    캐시 클리어 (관리자 전용)
    """
    with error_context(user_id=str(current_user.id), step="clear_cache"):
        try:
            # TODO: 관리자 권한 확인
            cache_manager = get_orchestration_cache_manager()
            cleared_count = await cache_manager.cache.clear(pattern)
            
            return {
                "success": True,
                "cleared_entries": cleared_count,
                "pattern": pattern or "all"
            }
        except Exception as e:
            raise PerformanceError(
                message=f"Failed to clear cache: {str(e)}",
                code=ErrorCode.CACHE_ERROR,
                cause=e
            )


@router.get("/errors/statistics")
@handle_api_error
async def get_error_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    에러 통계 조회
    """
    with error_context(user_id=str(current_user.id), step="get_error_stats"):
        try:
            error_handler = get_error_handler()
            return error_handler.get_error_statistics()
        except Exception as e:
            raise ExecutionError(
                message=f"Failed to get error statistics: {str(e)}",
                code=ErrorCode.SYSTEM_ERROR,
                cause=e
            )


async def _generate_cache_recommendations(cache_stats: Dict[str, Any]) -> List[str]:
    """캐시 성능 기반 추천사항 생성"""
    recommendations = []
    
    hit_rate = cache_stats.get("hit_rate", 0.0)
    l1_size = cache_stats.get("l1_size", 0)
    l1_max_size = cache_stats.get("l1_max_size", 1000)
    
    if hit_rate < 0.3:
        recommendations.append("캐시 적중률이 낮습니다. 캐시 TTL 설정을 검토해보세요.")
    elif hit_rate > 0.8:
        recommendations.append("캐시 성능이 우수합니다.")
    
    if l1_size / l1_max_size > 0.9:
        recommendations.append("L1 캐시 사용률이 높습니다. 캐시 크기 증가를 고려해보세요.")
    
    evictions = cache_stats.get("evictions", 0)
    if evictions > 100:
        recommendations.append("캐시 제거가 빈번합니다. 메모리 캐시 크기를 늘려보세요.")
    
    return recommendations