"""
Enterprise Security Manager
엔터프라이즈 보안 관리자 - Phase 6 구현
"""

import asyncio
import json
import uuid
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from collections import defaultdict
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class SecurityLevel(Enum):
    """보안 수준"""
    PUBLIC = "public"           # 공개
    INTERNAL = "internal"       # 내부
    CONFIDENTIAL = "confidential"  # 기밀
    RESTRICTED = "restricted"   # 제한
    TOP_SECRET = "top_secret"   # 최고기밀

class AccessLevel(Enum):
    """접근 권한 수준"""
    READ = "read"              # 읽기
    WRITE = "write"            # 쓰기
    EXECUTE = "execute"        # 실행
    ADMIN = "admin"            # 관리자
    OWNER = "owner"            # 소유자

class AuthenticationMethod(Enum):
    """인증 방법"""
    PASSWORD = "password"       # 비밀번호
    MFA = "mfa"                # 다중 인증
    SSO = "sso"                # Single Sign-On
    API_KEY = "api_key"        # API 키
    CERTIFICATE = "certificate" # 인증서
    BIOMETRIC = "biometric"    # 생체 인증

class AuditEventType(Enum):
    """감사 이벤트 유형"""
    LOGIN = "login"            # 로그인
    LOGOUT = "logout"          # 로그아웃
    ACCESS = "access"          # 접근
    MODIFY = "modify"          # 수정
    DELETE = "delete"          # 삭제
    EXPORT = "export"          # 내보내기
    ADMIN = "admin"            # 관리자 작업
    SECURITY = "security"      # 보안 이벤트

@dataclass
class SecurityPolicy:
    """보안 정책"""
    policy_id: str
    name: str
    description: str
    security_level: SecurityLevel
    rules: Dict[str, Any]
    compliance_requirements: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class AccessControl:
    """접근 제어"""
    resource_id: str
    user_id: str
    tenant_id: str
    access_level: AccessLevel
    permissions: List[str]
    conditions: Dict[str, Any]
    expires_at: Optional[datetime] = None
    granted_at: datetime = field(default_factory=datetime.now)
    granted_by: Optional[str] = None

@dataclass
class AuditLog:
    """감사 로그"""
    log_id: str
    event_type: AuditEventType
    user_id: str
    tenant_id: str
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    risk_score: float = 0.0

@dataclass
class SecurityAlert:
    """보안 알림"""
    alert_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    affected_resources: List[str]
    indicators: Dict[str, Any]
    recommended_actions: List[str]
    status: str = "open"  # open, investigating, resolved
    created_at: datetime = field(default_factory=datetime.now)

class EnterpriseSecurityManager:
    """엔터프라이즈 보안 관리자"""
    
    def __init__(self):
        # 보안 설정
        self.encryption_key = self._generate_encryption_key()
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.session_timeout = 3600  # 1시간
        
        # 보안 정책 저장소
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.access_controls: Dict[str, List[AccessControl]] = defaultdict(list)
        self.audit_logs: List[AuditLog] = []
        self.security_alerts: List[SecurityAlert] = []
        
        # 보안 설정
        self.security_config = {
            "password_policy": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special": True,
                "max_age_days": 90,
                "history_count": 12
            },
            "session_policy": {
                "timeout_minutes": 60,
                "max_concurrent_sessions": 5,
                "require_mfa": True,
                "ip_restriction": False
            },
            "api_security": {
                "rate_limit_per_minute": 1000,
                "require_api_key": True,
                "encrypt_payloads": True,
                "log_all_requests": True
            },
            "compliance": {
                "gdpr_enabled": True,
                "sox_enabled": True,
                "hipaa_enabled": False,
                "iso27001_enabled": True
            }
        }
        
        # 기본 보안 정책 초기화
        self._initialize_default_policies()
        
        logger.info("Enterprise Security Manager initialized")
    
    def _generate_encryption_key(self) -> bytes:
        """암호화 키 생성"""
        password = os.getenv("ENCRYPTION_PASSWORD", "default_password").encode()
        salt = os.getenv("ENCRYPTION_SALT", "default_salt").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _initialize_default_policies(self):
        """기본 보안 정책 초기화"""
        # 기본 보안 정책들
        default_policies = [
            {
                "name": "Standard Security Policy",
                "description": "표준 보안 정책",
                "security_level": SecurityLevel.INTERNAL,
                "rules": {
                    "require_mfa": True,
                    "session_timeout": 3600,
                    "password_complexity": "high",
                    "audit_all_actions": True
                },
                "compliance_requirements": ["ISO27001", "SOC2"]
            },
            {
                "name": "High Security Policy",
                "description": "고보안 정책",
                "security_level": SecurityLevel.CONFIDENTIAL,
                "rules": {
                    "require_mfa": True,
                    "session_timeout": 1800,
                    "password_complexity": "maximum",
                    "audit_all_actions": True,
                    "encrypt_all_data": True,
                    "ip_whitelist_only": True
                },
                "compliance_requirements": ["ISO27001", "SOC2", "GDPR"]
            }
        ]
        
        for policy_data in default_policies:
            policy = SecurityPolicy(
                policy_id=f"policy_{uuid.uuid4().hex[:8]}",
                **policy_data
            )
            self.security_policies[policy.policy_id] = policy
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        tenant_id: str,
        ip_address: str,
        user_agent: str,
        mfa_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """사용자 인증"""
        try:
            # 감사 로그 기록
            await self._log_audit_event(
                event_type=AuditEventType.LOGIN,
                user_id=username,
                tenant_id=tenant_id,
                action="login_attempt",
                details={"method": "password"},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # 비밀번호 검증 (실제 구현에서는 데이터베이스 조회)
            is_valid_password = await self._verify_password(username, password, tenant_id)
            
            if not is_valid_password:
                await self._handle_failed_login(username, tenant_id, ip_address)
                return {
                    "success": False,
                    "error": "Invalid credentials",
                    "requires_mfa": False
                }
            
            # MFA 검증 (필요한 경우)
            if self.security_config["session_policy"]["require_mfa"]:
                if not mfa_token:
                    return {
                        "success": False,
                        "error": "MFA token required",
                        "requires_mfa": True
                    }
                
                is_valid_mfa = await self._verify_mfa_token(username, mfa_token, tenant_id)
                if not is_valid_mfa:
                    return {
                        "success": False,
                        "error": "Invalid MFA token",
                        "requires_mfa": True
                    }
            
            # JWT 토큰 생성
            token = await self._generate_jwt_token(username, tenant_id)
            
            # 성공적인 로그인 기록
            await self._log_audit_event(
                event_type=AuditEventType.LOGIN,
                user_id=username,
                tenant_id=tenant_id,
                action="login_success",
                details={"method": "password_mfa" if mfa_token else "password"},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                "success": True,
                "token": token,
                "expires_in": self.session_timeout,
                "user_id": username,
                "tenant_id": tenant_id
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "Authentication system error"
            }
    
    async def _verify_password(self, username: str, password: str, tenant_id: str) -> bool:
        """비밀번호 검증 (시뮬레이션)"""
        # 실제 구현에서는 데이터베이스에서 해시된 비밀번호 조회 및 검증
        # 여기서는 시뮬레이션
        return len(password) >= 8  # 간단한 검증
    
    async def _verify_mfa_token(self, username: str, mfa_token: str, tenant_id: str) -> bool:
        """MFA 토큰 검증 (시뮬레이션)"""
        # 실제 구현에서는 TOTP, SMS, 이메일 등의 MFA 검증
        # 여기서는 시뮬레이션
        return len(mfa_token) == 6 and mfa_token.isdigit()
    
    async def _generate_jwt_token(self, user_id: str, tenant_id: str) -> str:
        """JWT 토큰 생성"""
        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self.session_timeout),
            "jti": str(uuid.uuid4())  # JWT ID
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    async def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return {
                "valid": True,
                "user_id": payload["user_id"],
                "tenant_id": payload["tenant_id"],
                "expires_at": payload["exp"]
            }
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
    
    async def check_access_permission(
        self,
        user_id: str,
        tenant_id: str,
        resource_id: str,
        required_permission: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """접근 권한 확인"""
        try:
            # 사용자의 접근 제어 목록 조회
            user_access_controls = self.access_controls.get(f"{tenant_id}:{user_id}", [])
            
            # 리소스별 권한 확인
            for access_control in user_access_controls:
                if access_control.resource_id == resource_id or access_control.resource_id == "*":
                    # 권한 확인
                    if required_permission in access_control.permissions:
                        # 조건 확인 (시간, IP, 기타 조건)
                        if await self._check_access_conditions(access_control, context):
                            # 만료 시간 확인
                            if not access_control.expires_at or access_control.expires_at > datetime.now():
                                return {
                                    "allowed": True,
                                    "access_level": access_control.access_level.value,
                                    "permissions": access_control.permissions
                                }
            
            # 접근 거부 로그
            await self._log_audit_event(
                event_type=AuditEventType.ACCESS,
                user_id=user_id,
                tenant_id=tenant_id,
                resource_id=resource_id,
                action="access_denied",
                details={"required_permission": required_permission},
                ip_address=context.get("ip_address", "unknown") if context else "unknown",
                user_agent=context.get("user_agent", "unknown") if context else "unknown"
            )
            
            return {
                "allowed": False,
                "error": "Access denied",
                "required_permission": required_permission
            }
            
        except Exception as e:
            logger.error(f"Access permission check failed: {str(e)}", exc_info=True)
            return {
                "allowed": False,
                "error": "Permission check system error"
            }
    
    async def _check_access_conditions(
        self,
        access_control: AccessControl,
        context: Dict[str, Any] = None
    ) -> bool:
        """접근 조건 확인"""
        if not access_control.conditions or not context:
            return True
        
        # IP 주소 제한 확인
        if "allowed_ips" in access_control.conditions:
            user_ip = context.get("ip_address")
            if user_ip and user_ip not in access_control.conditions["allowed_ips"]:
                return False
        
        # 시간 제한 확인
        if "allowed_hours" in access_control.conditions:
            current_hour = datetime.now().hour
            allowed_hours = access_control.conditions["allowed_hours"]
            if current_hour not in allowed_hours:
                return False
        
        # 기타 조건들...
        
        return True
    
    async def grant_access(
        self,
        user_id: str,
        tenant_id: str,
        resource_id: str,
        access_level: AccessLevel,
        permissions: List[str],
        granted_by: str,
        expires_at: Optional[datetime] = None,
        conditions: Dict[str, Any] = None
    ) -> str:
        """접근 권한 부여"""
        try:
            access_control = AccessControl(
                resource_id=resource_id,
                user_id=user_id,
                tenant_id=tenant_id,
                access_level=access_level,
                permissions=permissions,
                conditions=conditions or {},
                expires_at=expires_at,
                granted_by=granted_by
            )
            
            # 접근 제어 저장
            key = f"{tenant_id}:{user_id}"
            self.access_controls[key].append(access_control)
            
            # 감사 로그 기록
            await self._log_audit_event(
                event_type=AuditEventType.ADMIN,
                user_id=granted_by,
                tenant_id=tenant_id,
                resource_id=resource_id,
                action="grant_access",
                details={
                    "target_user": user_id,
                    "access_level": access_level.value,
                    "permissions": permissions
                },
                ip_address="system",
                user_agent="system"
            )
            
            logger.info(f"Access granted to user {user_id} for resource {resource_id}")
            return f"access_{uuid.uuid4().hex[:8]}"
            
        except Exception as e:
            logger.error(f"Failed to grant access: {str(e)}", exc_info=True)
            raise
    
    async def revoke_access(
        self,
        user_id: str,
        tenant_id: str,
        resource_id: str,
        revoked_by: str
    ) -> bool:
        """접근 권한 취소"""
        try:
            key = f"{tenant_id}:{user_id}"
            access_controls = self.access_controls.get(key, [])
            
            # 해당 리소스의 접근 권한 제거
            updated_controls = [
                ac for ac in access_controls
                if ac.resource_id != resource_id
            ]
            
            self.access_controls[key] = updated_controls
            
            # 감사 로그 기록
            await self._log_audit_event(
                event_type=AuditEventType.ADMIN,
                user_id=revoked_by,
                tenant_id=tenant_id,
                resource_id=resource_id,
                action="revoke_access",
                details={"target_user": user_id},
                ip_address="system",
                user_agent="system"
            )
            
            logger.info(f"Access revoked for user {user_id} on resource {resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke access: {str(e)}", exc_info=True)
            return False
    
    async def encrypt_sensitive_data(self, data: str) -> str:
        """민감한 데이터 암호화"""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Data encryption failed: {str(e)}")
            raise
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """민감한 데이터 복호화"""
        try:
            fernet = Fernet(self.encryption_key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Data decryption failed: {str(e)}")
            raise
    
    async def _log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        tenant_id: str,
        action: str,
        ip_address: str,
        user_agent: str,
        resource_id: Optional[str] = None,
        details: Dict[str, Any] = None
    ):
        """감사 이벤트 로깅"""
        try:
            # 위험 점수 계산
            risk_score = await self._calculate_risk_score(
                event_type, user_id, tenant_id, ip_address, details
            )
            
            audit_log = AuditLog(
                log_id=f"audit_{uuid.uuid4().hex[:8]}",
                event_type=event_type,
                user_id=user_id,
                tenant_id=tenant_id,
                resource_id=resource_id,
                action=action,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                risk_score=risk_score
            )
            
            self.audit_logs.append(audit_log)
            
            # 고위험 이벤트 알림
            if risk_score > 0.8:
                await self._create_security_alert(
                    alert_type="high_risk_activity",
                    severity="high",
                    title=f"High Risk Activity Detected",
                    description=f"User {user_id} performed {action} with risk score {risk_score}",
                    affected_resources=[resource_id] if resource_id else [],
                    indicators={"risk_score": risk_score, "event_type": event_type.value}
                )
            
        except Exception as e:
            logger.error(f"Audit logging failed: {str(e)}", exc_info=True)
    
    async def _calculate_risk_score(
        self,
        event_type: AuditEventType,
        user_id: str,
        tenant_id: str,
        ip_address: str,
        details: Dict[str, Any] = None
    ) -> float:
        """위험 점수 계산"""
        risk_score = 0.0
        
        # 이벤트 유형별 기본 위험도
        event_risk = {
            AuditEventType.LOGIN: 0.1,
            AuditEventType.ACCESS: 0.2,
            AuditEventType.MODIFY: 0.4,
            AuditEventType.DELETE: 0.6,
            AuditEventType.EXPORT: 0.5,
            AuditEventType.ADMIN: 0.7,
            AuditEventType.SECURITY: 0.8
        }
        
        risk_score += event_risk.get(event_type, 0.3)
        
        # 시간대별 위험도 (업무 시간 외 활동)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            risk_score += 0.2
        
        # IP 주소 기반 위험도 (알려지지 않은 IP)
        # 실제 구현에서는 IP 화이트리스트, 지역 정보 등 활용
        if ip_address not in ["127.0.0.1", "localhost"]:
            risk_score += 0.1
        
        # 실패한 로그인 시도 횟수
        if details and details.get("failed_attempts", 0) > 3:
            risk_score += 0.3
        
        return min(risk_score, 1.0)
    
    async def _create_security_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        affected_resources: List[str],
        indicators: Dict[str, Any]
    ):
        """보안 알림 생성"""
        try:
            alert = SecurityAlert(
                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                affected_resources=affected_resources,
                indicators=indicators,
                recommended_actions=self._get_recommended_actions(alert_type, severity)
            )
            
            self.security_alerts.append(alert)
            
            # 실시간 알림 (실제 구현에서는 이메일, Slack 등)
            logger.warning(f"Security Alert: {title} - {description}")
            
        except Exception as e:
            logger.error(f"Failed to create security alert: {str(e)}")
    
    def _get_recommended_actions(self, alert_type: str, severity: str) -> List[str]:
        """권장 조치 반환"""
        actions_map = {
            "high_risk_activity": [
                "Review user activity logs",
                "Verify user identity",
                "Consider temporary access restriction",
                "Notify security team"
            ],
            "failed_login_attempts": [
                "Check for brute force attacks",
                "Consider IP blocking",
                "Notify user of suspicious activity",
                "Enable additional MFA"
            ],
            "unauthorized_access": [
                "Immediately revoke access",
                "Investigate access path",
                "Review access controls",
                "Conduct security audit"
            ]
        }
        
        return actions_map.get(alert_type, ["Review and investigate"])
    
    async def _handle_failed_login(self, username: str, tenant_id: str, ip_address: str):
        """실패한 로그인 처리"""
        # 실패 횟수 추적 (실제 구현에서는 Redis 등 사용)
        # 여기서는 간단한 시뮬레이션
        
        # 보안 알림 생성
        await self._create_security_alert(
            alert_type="failed_login_attempts",
            severity="medium",
            title="Failed Login Attempt",
            description=f"Failed login attempt for user {username} from IP {ip_address}",
            affected_resources=[f"user:{username}"],
            indicators={"ip_address": ip_address, "username": username}
        )
    
    async def get_security_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """보안 대시보드 데이터"""
        try:
            # 최근 24시간 감사 로그
            recent_logs = [
                log for log in self.audit_logs
                if log.tenant_id == tenant_id and
                log.timestamp > datetime.now() - timedelta(hours=24)
            ]
            
            # 활성 보안 알림
            active_alerts = [
                alert for alert in self.security_alerts
                if alert.status == "open"
            ]
            
            # 위험 점수 분포
            risk_distribution = {
                "low": len([log for log in recent_logs if log.risk_score < 0.3]),
                "medium": len([log for log in recent_logs if 0.3 <= log.risk_score < 0.7]),
                "high": len([log for log in recent_logs if log.risk_score >= 0.7])
            }
            
            # 이벤트 유형별 통계
            event_stats = {}
            for log in recent_logs:
                event_type = log.event_type.value
                event_stats[event_type] = event_stats.get(event_type, 0) + 1
            
            return {
                "total_events": len(recent_logs),
                "active_alerts": len(active_alerts),
                "risk_distribution": risk_distribution,
                "event_statistics": event_stats,
                "recent_alerts": [alert.__dict__ for alert in active_alerts[-5:]],
                "compliance_status": {
                    "gdpr": True,
                    "sox": True,
                    "iso27001": True,
                    "last_audit": "2024-12-01"
                },
                "security_score": self._calculate_security_score(recent_logs, active_alerts)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate security dashboard: {str(e)}")
            return {}
    
    def _calculate_security_score(self, recent_logs: List[AuditLog], active_alerts: List[SecurityAlert]) -> float:
        """보안 점수 계산"""
        base_score = 100.0
        
        # 고위험 이벤트 감점
        high_risk_events = len([log for log in recent_logs if log.risk_score > 0.7])
        base_score -= high_risk_events * 5
        
        # 활성 알림 감점
        critical_alerts = len([alert for alert in active_alerts if alert.severity == "critical"])
        high_alerts = len([alert for alert in active_alerts if alert.severity == "high"])
        
        base_score -= critical_alerts * 10
        base_score -= high_alerts * 5
        
        return max(0.0, min(100.0, base_score))

# 전역 인스턴스
_security_manager_instance = None

def get_security_manager() -> EnterpriseSecurityManager:
    """보안 관리자 인스턴스 반환"""
    global _security_manager_instance
    if _security_manager_instance is None:
        _security_manager_instance = EnterpriseSecurityManager()
    return _security_manager_instance