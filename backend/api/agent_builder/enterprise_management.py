"""
Enterprise Management API
엔터프라이즈 관리 API - Phase 6 구현
"""

from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from backend.services.enterprise.multi_tenant_manager import (
    get_multi_tenant_manager,
    MultiTenantManager,
    TenantConfiguration,
    TenantTier,
    TenantStatus,
    IsolationLevel,
    TenantMetrics,
    TenantAlert
)
from backend.services.enterprise.security_manager import (
    get_enterprise_security_manager,
    EnterpriseSecurityManager,
    SecurityPolicy,
    SecurityLevel,
    AuthMethod,
    SecurityAuditLog,
    SecurityAlert,
    UserRole,
    Permission
)
from backend.core.structured_logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)
security = HTTPBearer()

router = APIRouter(
    prefix="/api/agent-builder/enterprise",
    tags=["enterprise-management"]
)

# Request/Response Models
class CreateTenantRequest(BaseModel):
    """테넌트 생성 요청"""
    name: str = Field(description="테넌트 이름")
    tier: str = Field(description="테넌트 티어 (starter, professional, enterprise, custom)")
    isolation_level: str = Field(description="격리 수준 (shared, dedicated, hybrid)")
    admin_email: str = Field(description="관리자 이메일")
    custom_config: Optional[Dict[str, Any]] = Field(default=None, description="커스텀 설정")

class UpdateTenantRequest(BaseModel):
    """테넌트 업데이트 요청"""
    name: Optional[str] = Field(default=None, description="테넌트 이름")
    status: Optional[str] = Field(default=None, description="테넌트 상태")
    custom_config: Optional[Dict[str, Any]] = Field(default=None, description="커스텀 설정")

class CreateSecurityPolicyRequest(BaseModel):
    """보안 정책 생성 요청"""
    name: str = Field(description="정책 이름")
    security_level: str = Field(description="보안 수준 (low, medium, high, critical)")
    policy_config: Dict[str, Any] = Field(description="정책 설정")

class AuthenticationRequest(BaseModel):
    """인증 요청"""
    username: str = Field(description="사용자명")
    credentials: Dict[str, Any] = Field(description="인증 정보")
    auth_method: str = Field(description="인증 방법")

class AuthorizationRequest(BaseModel):
    """권한 확인 요청"""
    resource: str = Field(description="리소스")
    action: str = Field(description="작업")
    context: Dict[str, Any] = Field(default_factory=dict, description="컨텍스트")

class EncryptionRequest(BaseModel):
    """암호화 요청"""
    data: str = Field(description="암호화할 데이터")
    classification: str = Field(default="internal", description="데이터 분류")

class DecryptionRequest(BaseModel):
    """복호화 요청"""
    encrypted_data: str = Field(description="암호화된 데이터")

class TenantMetricsRequest(BaseModel):
    """테넌트 메트릭 요청"""
    time_range_hours: int = Field(default=24, description="시간 범위 (시간)")
    metric_types: Optional[List[str]] = Field(default=None, description="메트릭 유형 필터")

class SecurityAuditRequest(BaseModel):
    """보안 감사 요청"""
    time_range_hours: int = Field(default=24, description="시간 범위 (시간)")
    event_types: Optional[List[str]] = Field(default=None, description="이벤트 유형 필터")
    severity_filter: Optional[List[str]] = Field(default=None, description="심각도 필터")

# Response Models
class TenantResponse(BaseModel):
    """테넌트 응답"""
    tenant_id: str
    name: str
    tier: str
    status: str
    isolation_level: str
    created_at: datetime
    resource_usage: Dict[str, Any]
    quota_status: Dict[str, Any]

class SecurityPolicyResponse(BaseModel):
    """보안 정책 응답"""
    policy_id: str
    name: str
    security_level: str
    tenant_id: str
    created_at: datetime
    policy_summary: Dict[str, Any]

class AuthenticationResponse(BaseModel):
    """인증 응답"""
    success: bool
    token: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    roles: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None

class TenantMetricsResponse(BaseModel):
    """테넌트 메트릭 응답"""
    tenant_id: str
    metrics: List[Dict[str, Any]]
    summary: Dict[str, Any]
    time_range: Dict[str, datetime]

class SecurityAuditResponse(BaseModel):
    """보안 감사 응답"""
    tenant_id: str
    audit_logs: List[Dict[str, Any]]
    summary: Dict[str, Any]
    risk_analysis: Dict[str, Any]

# Dependency functions
async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Security(security),
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager)
) -> str:
    """현재 테넌트 ID 추출"""
    try:
        # JWT 토큰에서 테넌트 ID 추출
        # 실제 구현에서는 JWT 토큰 검증 및 파싱
        return "tenant_example"
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager)
) -> str:
    """현재 사용자 ID 추출"""
    try:
        # JWT 토큰에서 사용자 ID 추출
        return "user_example"
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# Tenant Management Endpoints
@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    request: CreateTenantRequest,
    tenant_manager: MultiTenantManager = Depends(get_multi_tenant_manager),
    current_user: str = Depends(get_current_user)
):
    """
    새 테넌트 생성
    
    엔터프라이즈 관리자가 새로운 테넌트를 생성합니다.
    """
    try:
        logger.info(f"Creating new tenant: {request.name}")
        
        # 티어 및 격리 수준 변환
        tier = TenantTier(request.tier)
        isolation_level = IsolationLevel(request.isolation_level)
        
        # 테넌트 생성
        config = await tenant_manager.create_tenant(
            name=request.name,
            tier=tier,
            isolation_level=isolation_level,
            admin_email=request.admin_email,
            custom_config=request.custom_config
        )
        
        # 할당량 상태 조회
        quota_status = await tenant_manager.check_tenant_quotas(config.tenant_id)
        
        response = TenantResponse(
            tenant_id=config.tenant_id,
            name=config.name,
            tier=config.tier.value,
            status=config.status.value,
            isolation_level=config.isolation_level.value,
            created_at=config.created_at,
            resource_usage={
                "workflows": 0,
                "agents": 0,
                "storage_gb": 0.0,
                "api_calls": 0
            },
            quota_status=quota_status.get("quota_status", {})
        )
        
        logger.info(f"Tenant created successfully: {config.tenant_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create tenant: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")

@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    tenant_manager: MultiTenantManager = Depends(get_multi_tenant_manager),
    current_user: str = Depends(get_current_user)
):
    """
    테넌트 정보 조회
    
    특정 테넌트의 상세 정보를 조회합니다.
    """
    try:
        # 테넌트 설정 조회
        config = tenant_manager.tenants.get(tenant_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")
        
        # 할당량 상태 조회
        quota_status = await tenant_manager.check_tenant_quotas(tenant_id)
        
        # 현재 사용량 조회
        current_usage = await tenant_manager._get_current_usage(tenant_id)
        
        response = TenantResponse(
            tenant_id=config.tenant_id,
            name=config.name,
            tier=config.tier.value,
            status=config.status.value,
            isolation_level=config.isolation_level.value,
            created_at=config.created_at,
            resource_usage=current_usage,
            quota_status=quota_status.get("quota_status", {})
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get tenant: {str(e)}")

@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    tenant_manager: MultiTenantManager = Depends(get_multi_tenant_manager),
    current_user: str = Depends(get_current_user)
):
    """
    테넌트 목록 조회
    
    모든 테넌트의 목록을 조회합니다.
    """
    try:
        tenants = []
        
        for config in tenant_manager.tenants.values():
            # 할당량 상태 조회
            quota_status = await tenant_manager.check_tenant_quotas(config.tenant_id)
            
            # 현재 사용량 조회
            current_usage = await tenant_manager._get_current_usage(config.tenant_id)
            
            tenant_response = TenantResponse(
                tenant_id=config.tenant_id,
                name=config.name,
                tier=config.tier.value,
                status=config.status.value,
                isolation_level=config.isolation_level.value,
                created_at=config.created_at,
                resource_usage=current_usage,
                quota_status=quota_status.get("quota_status", {})
            )
            
            tenants.append(tenant_response)
        
        return tenants
        
    except Exception as e:
        logger.error(f"Failed to list tenants: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tenants: {str(e)}")

@router.get("/tenants/{tenant_id}/metrics", response_model=TenantMetricsResponse)
async def get_tenant_metrics(
    tenant_id: str,
    request: TenantMetricsRequest = Depends(),
    tenant_manager: MultiTenantManager = Depends(get_multi_tenant_manager),
    current_tenant: str = Depends(get_current_tenant)
):
    """
    테넌트 메트릭 조회
    
    특정 테넌트의 성능 및 사용량 메트릭을 조회합니다.
    """
    try:
        # 권한 확인 (자신의 테넌트만 조회 가능)
        if tenant_id != current_tenant and current_tenant != "system":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 메트릭 조회
        metrics = await tenant_manager.get_tenant_metrics(tenant_id, request.time_range_hours)
        
        # 메트릭 필터링
        if request.metric_types:
            # 실제 구현에서는 메트릭 유형별 필터링
            pass
        
        # 요약 통계 계산
        summary = {}
        if metrics:
            summary = {
                "total_executions": sum(m.total_executions for m in metrics),
                "avg_success_rate": sum(m.success_rate for m in metrics) / len(metrics),
                "avg_response_time": sum(m.avg_execution_time for m in metrics) / len(metrics),
                "total_cost": sum(m.total_cost for m in metrics),
                "uptime_percentage": sum(m.uptime_percentage for m in metrics) / len(metrics)
            }
        
        response = TenantMetricsResponse(
            tenant_id=tenant_id,
            metrics=[m.__dict__ for m in metrics],
            summary=summary,
            time_range={
                "start": datetime.now() - timedelta(hours=request.time_range_hours),
                "end": datetime.now()
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get tenant metrics: {str(e)}")

# Security Management Endpoints
@router.post("/security/policies", response_model=SecurityPolicyResponse)
async def create_security_policy(
    request: CreateSecurityPolicyRequest,
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant),
    current_user: str = Depends(get_current_user)
):
    """
    보안 정책 생성
    
    새로운 보안 정책을 생성합니다.
    """
    try:
        logger.info(f"Creating security policy: {request.name}")
        
        # 보안 수준 변환
        security_level = SecurityLevel(request.security_level)
        
        # 보안 정책 생성
        policy = await security_manager.create_security_policy(
            tenant_id=current_tenant,
            name=request.name,
            security_level=security_level,
            policy_config=request.policy_config
        )
        
        response = SecurityPolicyResponse(
            policy_id=policy.policy_id,
            name=policy.name,
            security_level=policy.security_level.value,
            tenant_id=policy.tenant_id,
            created_at=policy.created_at,
            policy_summary={
                "mfa_required": policy.mfa_required,
                "session_timeout": policy.session_timeout_minutes,
                "encryption_required": policy.encryption_required,
                "audit_level": policy.audit_level
            }
        )
        
        logger.info(f"Security policy created: {policy.policy_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create security policy: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create security policy: {str(e)}")

@router.post("/security/authenticate", response_model=AuthenticationResponse)
async def authenticate_user(
    request: AuthenticationRequest,
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant)
):
    """
    사용자 인증
    
    사용자 인증을 수행하고 JWT 토큰을 발급합니다.
    """
    try:
        logger.info(f"Authenticating user: {request.username}")
        
        # 인증 방법 변환
        auth_method = AuthMethod(request.auth_method)
        
        # 요청 컨텍스트 (실제로는 FastAPI Request에서 추출)
        request_context = {
            "ip_address": "127.0.0.1",
            "user_agent": "API Client"
        }
        
        # 사용자 인증
        auth_result = await security_manager.authenticate_user(
            tenant_id=current_tenant,
            username=request.username,
            credentials=request.credentials,
            auth_method=auth_method,
            request_context=request_context
        )
        
        if auth_result["success"]:
            response = AuthenticationResponse(
                success=True,
                token=auth_result["token"],
                session_id=auth_result["session_id"],
                user_id=auth_result["user_id"],
                roles=auth_result["roles"],
                expires_at=auth_result["expires_at"]
            )
        else:
            response = AuthenticationResponse(
                success=False,
                message="Authentication failed"
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}", exc_info=True)
        return AuthenticationResponse(
            success=False,
            message=f"Authentication error: {str(e)}"
        )

@router.post("/security/authorize")
async def authorize_action(
    request: AuthorizationRequest,
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant),
    current_user: str = Depends(get_current_user)
):
    """
    작업 권한 확인
    
    특정 리소스에 대한 작업 권한을 확인합니다.
    """
    try:
        # 권한 확인
        has_permission = await security_manager.authorize_action(
            tenant_id=current_tenant,
            user_id=current_user,
            resource=request.resource,
            action=request.action,
            context=request.context
        )
        
        return {
            "authorized": has_permission,
            "resource": request.resource,
            "action": request.action,
            "user_id": current_user,
            "checked_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Authorization check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Authorization check failed: {str(e)}")

@router.post("/security/encrypt")
async def encrypt_data(
    request: EncryptionRequest,
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant)
):
    """
    데이터 암호화
    
    민감한 데이터를 암호화합니다.
    """
    try:
        encrypted_data = await security_manager.encrypt_data(
            tenant_id=current_tenant,
            data=request.data,
            classification=request.classification
        )
        
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "classification": request.classification,
            "encrypted_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Data encryption failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Data encryption failed: {str(e)}")

@router.post("/security/decrypt")
async def decrypt_data(
    request: DecryptionRequest,
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant)
):
    """
    데이터 복호화
    
    암호화된 데이터를 복호화합니다.
    """
    try:
        decrypted_data = await security_manager.decrypt_data(
            tenant_id=current_tenant,
            encrypted_data=request.encrypted_data
        )
        
        return {
            "success": True,
            "decrypted_data": decrypted_data,
            "decrypted_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Data decryption failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Data decryption failed: {str(e)}")

@router.get("/security/audit", response_model=SecurityAuditResponse)
async def get_security_audit_logs(
    request: SecurityAuditRequest = Depends(),
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant),
    current_user: str = Depends(get_current_user)
):
    """
    보안 감사 로그 조회
    
    보안 관련 이벤트 로그를 조회합니다.
    """
    try:
        # 시간 범위 필터링
        cutoff_time = datetime.now() - timedelta(hours=request.time_range_hours)
        
        filtered_logs = [
            log for log in security_manager.audit_logs
            if log.tenant_id == current_tenant and log.timestamp >= cutoff_time
        ]
        
        # 이벤트 유형 필터링
        if request.event_types:
            filtered_logs = [
                log for log in filtered_logs
                if log.event_type.value in request.event_types
            ]
        
        # 심각도 필터링
        if request.severity_filter:
            # 실제 구현에서는 로그별 심각도 확인
            pass
        
        # 요약 통계
        summary = {
            "total_events": len(filtered_logs),
            "success_events": len([log for log in filtered_logs if log.result == "success"]),
            "failure_events": len([log for log in filtered_logs if log.result == "failure"]),
            "denied_events": len([log for log in filtered_logs if log.result == "denied"]),
            "unique_users": len(set(log.user_id for log in filtered_logs if log.user_id)),
            "unique_ips": len(set(log.ip_address for log in filtered_logs if log.ip_address))
        }
        
        # 위험 분석
        risk_scores = [log.risk_score for log in filtered_logs]
        risk_analysis = {
            "average_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            "high_risk_events": len([score for score in risk_scores if score > 0.7]),
            "medium_risk_events": len([score for score in risk_scores if 0.4 <= score <= 0.7]),
            "low_risk_events": len([score for score in risk_scores if score < 0.4])
        }
        
        response = SecurityAuditResponse(
            tenant_id=current_tenant,
            audit_logs=[log.__dict__ for log in filtered_logs],
            summary=summary,
            risk_analysis=risk_analysis
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

@router.get("/security/alerts")
async def get_security_alerts(
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant)
):
    """
    보안 알림 조회
    
    현재 활성화된 보안 알림을 조회합니다.
    """
    try:
        # 테넌트별 보안 알림 필터링
        tenant_alerts = [
            alert for alert in security_manager.security_alerts
            if alert.tenant_id == current_tenant and alert.status == "open"
        ]
        
        # 심각도별 분류
        alerts_by_severity = {
            "critical": [alert for alert in tenant_alerts if alert.severity == "critical"],
            "high": [alert for alert in tenant_alerts if alert.severity == "high"],
            "medium": [alert for alert in tenant_alerts if alert.severity == "medium"],
            "low": [alert for alert in tenant_alerts if alert.severity == "low"]
        }
        
        return {
            "tenant_id": current_tenant,
            "total_alerts": len(tenant_alerts),
            "alerts_by_severity": {
                severity: len(alerts) for severity, alerts in alerts_by_severity.items()
            },
            "active_alerts": [alert.__dict__ for alert in tenant_alerts],
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get security alerts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get security alerts: {str(e)}")

@router.get("/dashboard")
async def get_enterprise_dashboard(
    tenant_manager: MultiTenantManager = Depends(get_multi_tenant_manager),
    security_manager: EnterpriseSecurityManager = Depends(get_enterprise_security_manager),
    current_tenant: str = Depends(get_current_tenant)
):
    """
    엔터프라이즈 대시보드
    
    테넌트의 전체적인 상태와 주요 메트릭을 제공합니다.
    """
    try:
        # 테넌트 정보
        config = tenant_manager.tenants.get(current_tenant)
        if not config:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # 할당량 상태
        quota_status = await tenant_manager.check_tenant_quotas(current_tenant)
        
        # 최근 메트릭
        recent_metrics = await tenant_manager.get_tenant_metrics(current_tenant, 24)
        
        # 보안 상태
        recent_alerts = [
            alert for alert in security_manager.security_alerts
            if alert.tenant_id == current_tenant and alert.status == "open"
        ]
        
        # 최근 감사 로그
        recent_logs = [
            log for log in security_manager.audit_logs[-100:]
            if log.tenant_id == current_tenant
        ]
        
        return {
            "tenant_info": {
                "tenant_id": config.tenant_id,
                "name": config.name,
                "tier": config.tier.value,
                "status": config.status.value,
                "created_at": config.created_at
            },
            "resource_status": quota_status,
            "performance_summary": {
                "total_metrics": len(recent_metrics),
                "avg_uptime": sum(m.uptime_percentage for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                "avg_success_rate": sum(m.success_rate for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                "total_cost": sum(m.total_cost for m in recent_metrics) if recent_metrics else 0
            },
            "security_status": {
                "active_alerts": len(recent_alerts),
                "critical_alerts": len([a for a in recent_alerts if a.severity == "critical"]),
                "recent_events": len(recent_logs),
                "failed_logins": len([l for l in recent_logs if l.event_type.value == "login_failure"])
            },
            "generated_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")