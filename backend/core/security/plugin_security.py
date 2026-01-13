"""
Agent Plugin 보안 관리자
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
from fastapi import HTTPException
import re
import json
from datetime import datetime, timedelta

class PluginPermission(Enum):
    """플러그인 권한 레벨"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    INSTALL = "install"
    DELETE = "delete"

class SecurityPolicy(BaseModel):
    """보안 정책"""
    max_input_size: int = 1024 * 1024  # 1MB
    max_execution_time: int = 300  # 5분
    allowed_domains: List[str] = []
    blocked_patterns: List[str] = []
    rate_limit_per_minute: int = 60
    require_approval: bool = True

class PluginSecurityManager:
    """플러그인 보안 관리자"""
    
    def __init__(self):
        self.security_policy = SecurityPolicy()
        self.rate_limits: Dict[str, List[datetime]] = {}
        
    def validate_user_permissions(
        self, 
        user_id: str, 
        required_permission: PluginPermission,
        plugin_id: Optional[str] = None
    ) -> bool:
        """사용자 권한 검증"""
        # TODO: 실제 RBAC 시스템과 연동
        # 현재는 기본 구현
        return True
    
    def validate_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """입력 데이터 검증 및 정화"""
        # 크기 제한 검증
        data_size = len(json.dumps(data, ensure_ascii=False))
        if data_size > self.security_policy.max_input_size:
            raise HTTPException(
                status_code=413,
                detail=f"Input data too large: {data_size} bytes (max: {self.security_policy.max_input_size})"
            )
        
        # 악성 패턴 검증
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in self.security_policy.blocked_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Blocked pattern detected in field: {key}"
                        )
        
        return data
    
    def check_rate_limit(self, user_id: str) -> bool:
        """레이트 리미팅 검증"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # 사용자별 요청 기록 정리
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # 1분 이전 기록 제거
        self.rate_limits[user_id] = [
            req_time for req_time in self.rate_limits[user_id] 
            if req_time > minute_ago
        ]
        
        # 현재 요청 수 확인
        current_requests = len(self.rate_limits[user_id])
        if current_requests >= self.security_policy.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {current_requests}/{self.security_policy.rate_limit_per_minute} requests per minute"
            )
        
        # 현재 요청 기록
        self.rate_limits[user_id].append(now)
        return True
    
    def validate_plugin_source(self, plugin_source: str) -> bool:
        """플러그인 소스 검증"""
        # URL 형식 검증
        if plugin_source.startswith(('http://', 'https://')):
            # 허용된 도메인 검증
            if self.security_policy.allowed_domains:
                domain_allowed = any(
                    domain in plugin_source 
                    for domain in self.security_policy.allowed_domains
                )
                if not domain_allowed:
                    raise HTTPException(
                        status_code=403,
                        detail="Plugin source domain not allowed"
                    )
        
        return True
    
    def sanitize_error_message(self, error: Exception) -> str:
        """에러 메시지 정화 (민감한 정보 제거)"""
        error_msg = str(error)
        
        # 파일 경로 제거
        error_msg = re.sub(r'/[^\s]+/', '[PATH]/', error_msg)
        
        # IP 주소 제거
        error_msg = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', error_msg)
        
        # 기타 민감한 패턴 제거
        sensitive_patterns = [
            r'password[=:]\s*\S+',
            r'token[=:]\s*\S+',
            r'key[=:]\s*\S+',
        ]
        
        for pattern in sensitive_patterns:
            error_msg = re.sub(pattern, '[REDACTED]', error_msg, flags=re.IGNORECASE)
        
        return error_msg

# 전역 인스턴스
plugin_security_manager = PluginSecurityManager()