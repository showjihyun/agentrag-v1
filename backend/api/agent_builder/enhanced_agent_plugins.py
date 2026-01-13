"""
Enhanced Agent Plugin API Endpoints

Provides REST API endpoints for the enhanced agent plugin system with improved
security, error handling, and performance monitoring.
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
import logging
from datetime import datetime

from backend.services.plugins.plugin_integration_service import (
    get_plugin_integration_service,
    PluginIntegrationService
)
from backend.services.plugins.enhanced_security_manager import (
    SecurityContext,
    UserRole,
    SecureAgentExecutionRequest
)
from backend.core.error_handling.plugin_errors import (
    PluginException,
    PluginErrorCode,
    handle_plugin_errors
)
from backend.core.dependencies import get_current_user
from backend.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enhanced-agent-plugins", tags=["Enhanced Agent Plugins"])
security = HTTPBearer()


# Request/Response Models
class AgentExecutionRequest(BaseModel):
    """Agent 실행 요청"""
    agent_type: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$', max_length=100)
    input_data: Dict[str, Any] = Field(..., max_items=50)
    priority: int = Field(default=5, ge=1, le=10)
    use_queue: bool = Field(default=False)
    execution_timeout: int = Field(default=300, ge=1, le=3600)
    
    @validator('input_data')
    def validate_input_size(cls, v):
        import json
        serialized = json.dumps(v, ensure_ascii=False)
        if len(serialized.encode('utf-8')) > 1024 * 1024:  # 1MB 제한
            raise ValueError('Input data exceeds 1MB limit')
        return v


class OrchestrationRequest(BaseModel):
    """오케스트레이션 실행 요청"""
    pattern: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    agents: List[str] = Field(..., min_items=1, max_items=10)
    task: Dict[str, Any] = Field(...)
    config: Optional[Dict[str, Any]] = None


class PluginValidationRequest(BaseModel):
    """플러그인 검증 요청"""
    plugin_path: str = Field(...)
    manifest_data: Dict[str, Any] = Field(...)


class AgentExecutionResponse(BaseModel):
    """Agent 실행 응답"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
    trace_id: Optional[str] = None
    agent_type: str
    user_id: str
    metrics: Optional[Dict[str, Any]] = None


class SystemStatusResponse(BaseModel):
    """시스템 상태 응답"""
    integration_service: Dict[str, Any]
    enhanced_agent_manager: Optional[Dict[str, Any]] = None
    legacy_agent_manager: Optional[Dict[str, Any]] = None
    error_statistics: Dict[str, Any]


class SecuritySummaryResponse(BaseModel):
    """보안 요약 응답"""
    user_id: str
    total_events: int
    recent_events: List[Dict[str, Any]]
    threat_summary: Dict[str, int]
    rate_limit_status: List[Any]


# Dependency Functions
async def get_integration_service() -> PluginIntegrationService:
    """통합 서비스 의존성"""
    return await get_plugin_integration_service()


async def create_security_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
) -> SecurityContext:
    """보안 컨텍스트 생성"""
    
    # 사용자 역할 매핑
    role_mapping = {
        "admin": "admin",
        "developer": "developer", 
        "user": "user",
        "guest": "guest"
    }
    
    user_role = role_mapping.get(current_user.role, "user")
    
    return await integration_service.create_security_context(
        user_id=str(current_user.id),
        user_role=user_role,
        session_id=request.headers.get("X-Session-ID", "unknown"),
        ip_address=request.client.host if request.client else None
    )


# API Endpoints
@router.post("/execute", response_model=AgentExecutionResponse)
@handle_plugin_errors(attempt_recovery=True, max_retries=2)
async def execute_agent(
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    security_context: SecurityContext = Depends(create_security_context),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    Enhanced Agent 실행
    
    향상된 보안, 에러 처리, 성능 모니터링이 적용된 Agent 실행 엔드포인트
    """
    try:
        logger.info(f"Executing agent {request.agent_type} for user {security_context.user_id}")
        
        # Agent 실행
        result = await integration_service.execute_agent(
            agent_type=request.agent_type,
            input_data=request.input_data,
            security_context=security_context,
            priority=request.priority,
            use_queue=request.use_queue
        )
        
        # 백그라운드에서 메트릭 업데이트
        background_tasks.add_task(
            _update_execution_metrics,
            integration_service,
            security_context.user_id,
            request.agent_type,
            result.success
        )
        
        return AgentExecutionResponse(
            success=result.success,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time,
            trace_id=result.trace_id,
            agent_type=result.agent_type,
            user_id=result.user_id,
            metrics=result.metrics.__dict__ if result.metrics else None
        )
        
    except PluginException as e:
        logger.error(f"Plugin execution failed: {e}")
        raise HTTPException(
            status_code=e._get_http_status_code(),
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in agent execution: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"original_error": str(e)}
                }
            }
        )


@router.post("/orchestrate")
@handle_plugin_errors(attempt_recovery=True, max_retries=1)
async def execute_orchestration(
    request: OrchestrationRequest,
    background_tasks: BackgroundTasks,
    security_context: SecurityContext = Depends(create_security_context),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    Enhanced 오케스트레이션 실행
    
    다중 Agent 오케스트레이션을 향상된 보안과 함께 실행
    """
    try:
        logger.info(f"Executing orchestration {request.pattern} for user {security_context.user_id}")
        
        result = await integration_service.execute_orchestration(
            pattern=request.pattern,
            agents=request.agents,
            task=request.task,
            security_context=security_context,
            config=request.config
        )
        
        # 백그라운드에서 오케스트레이션 메트릭 업데이트
        background_tasks.add_task(
            _update_orchestration_metrics,
            integration_service,
            security_context.user_id,
            request.pattern,
            len(request.agents)
        )
        
        return {
            "success": True,
            "result": result,
            "pattern": request.pattern,
            "agents": request.agents,
            "user_id": security_context.user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except PluginException as e:
        logger.error(f"Orchestration execution failed: {e}")
        raise HTTPException(
            status_code=e._get_http_status_code(),
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in orchestration: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ORCHESTRATION_ERROR",
                    "message": "Orchestration execution failed",
                    "details": {"original_error": str(e)}
                }
            }
        )


@router.post("/validate-plugin")
async def validate_plugin_security(
    request: PluginValidationRequest,
    security_context: SecurityContext = Depends(create_security_context),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    플러그인 보안 검증
    
    플러그인의 보안성을 종합적으로 검증
    """
    try:
        # Mock manifest 객체 생성 (실제로는 적절한 파싱 필요)
        from types import SimpleNamespace
        manifest = SimpleNamespace(**request.manifest_data)
        
        result = await integration_service.validate_plugin_security(
            plugin_path=request.plugin_path,
            manifest=manifest,
            security_context=security_context
        )
        
        return {
            "validation_result": result,
            "user_id": security_context.user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except PluginException as e:
        logger.error(f"Plugin validation failed: {e}")
        raise HTTPException(
            status_code=e._get_http_status_code(),
            detail=e.to_dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error in plugin validation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Plugin validation failed",
                    "details": {"original_error": str(e)}
                }
            }
        )


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    시스템 상태 조회
    
    Enhanced Plugin 시스템의 전반적인 상태 정보 제공
    """
    try:
        status = await integration_service.get_system_status()
        
        return SystemStatusResponse(
            integration_service=status["integration_service"],
            enhanced_agent_manager=status.get("enhanced_agent_manager"),
            legacy_agent_manager=status.get("legacy_agent_manager"),
            error_statistics=status["error_statistics"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "STATUS_ERROR",
                    "message": "Failed to retrieve system status",
                    "details": {"original_error": str(e)}
                }
            }
        )


@router.get("/security-summary", response_model=SecuritySummaryResponse)
async def get_security_summary(
    security_context: SecurityContext = Depends(create_security_context),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    사용자별 보안 요약 정보
    
    현재 사용자의 보안 이벤트 및 위협 요약 정보 제공
    """
    try:
        summary = await integration_service.get_security_summary(security_context.user_id)
        
        return SecuritySummaryResponse(
            user_id=summary["user_id"],
            total_events=summary["total_events"],
            recent_events=summary["recent_events"],
            threat_summary=summary["threat_summary"],
            rate_limit_status=summary["rate_limit_status"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get security summary: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "SECURITY_SUMMARY_ERROR",
                    "message": "Failed to retrieve security summary",
                    "details": {"original_error": str(e)}
                }
            }
        )


@router.post("/migrate-to-enhanced")
async def migrate_to_enhanced_system(
    current_user: User = Depends(get_current_user),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    Enhanced 시스템으로 마이그레이션
    
    관리자만 사용 가능한 시스템 마이그레이션 엔드포인트
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "Admin privileges required for system migration"
                }
            }
        )
    
    try:
        result = await integration_service.migrate_to_enhanced_system()
        
        if result["success"]:
            logger.info(f"System migration to enhanced mode completed by user {current_user.id}")
        else:
            logger.warning(f"System migration failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Migration to enhanced system failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "MIGRATION_ERROR",
                    "message": "Failed to migrate to enhanced system",
                    "details": {"original_error": str(e)}
                }
            }
        )


@router.post("/rollback-to-legacy")
async def rollback_to_legacy_system(
    current_user: User = Depends(get_current_user),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    Legacy 시스템으로 롤백
    
    관리자만 사용 가능한 시스템 롤백 엔드포인트
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "Admin privileges required for system rollback"
                }
            }
        )
    
    try:
        result = await integration_service.rollback_to_legacy_system()
        
        if result["success"]:
            logger.info(f"System rollback to legacy mode completed by user {current_user.id}")
        else:
            logger.warning(f"System rollback failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Rollback to legacy system failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ROLLBACK_ERROR",
                    "message": "Failed to rollback to legacy system",
                    "details": {"original_error": str(e)}
                }
            }
        )


@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    integration_service: PluginIntegrationService = Depends(get_integration_service)
):
    """
    성능 메트릭 조회
    
    시스템 성능 및 실행 통계 정보 제공
    """
    try:
        status = await integration_service.get_system_status()
        
        performance_data = {
            "user_id": str(current_user.id),
            "timestamp": datetime.now().isoformat(),
            "system_metrics": status.get("enhanced_agent_manager", {}),
            "error_statistics": status["error_statistics"],
            "integration_status": status["integration_service"]
        }
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "METRICS_ERROR",
                    "message": "Failed to retrieve performance metrics",
                    "details": {"original_error": str(e)}
                }
            }
        )


# Background Task Functions
async def _update_execution_metrics(
    integration_service: PluginIntegrationService,
    user_id: str,
    agent_type: str,
    success: bool
):
    """실행 메트릭 업데이트 (백그라운드 작업)"""
    try:
        # 메트릭 업데이트 로직
        logger.debug(f"Updating execution metrics for user {user_id}, agent {agent_type}, success: {success}")
        
        # 실제 구현에서는 메트릭 저장소에 데이터 저장
        # 예: 데이터베이스, Redis, 모니터링 시스템 등
        
    except Exception as e:
        logger.error(f"Failed to update execution metrics: {e}")


async def _update_orchestration_metrics(
    integration_service: PluginIntegrationService,
    user_id: str,
    pattern: str,
    agent_count: int
):
    """오케스트레이션 메트릭 업데이트 (백그라운드 작업)"""
    try:
        # 오케스트레이션 메트릭 업데이트 로직
        logger.debug(f"Updating orchestration metrics for user {user_id}, pattern {pattern}, agents: {agent_count}")
        
        # 실제 구현에서는 오케스트레이션 통계 저장
        
    except Exception as e:
        logger.error(f"Failed to update orchestration metrics: {e}")


# Health Check Endpoint
@router.get("/health")
async def health_check():
    """
    Enhanced Plugin 시스템 헬스 체크
    """
    try:
        integration_service = await get_plugin_integration_service()
        
        health_status = {
            "status": "healthy" if integration_service._initialized else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "enhanced-v1.0",
            "components": {
                "integration_service": integration_service._initialized,
                "enhanced_security": integration_service.use_enhanced_security,
                "enhanced_agent_manager": integration_service.use_enhanced_agent_manager
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }