"""
Orchestration Security
오케스트레이션 보안 검증 및 권한 관리
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.core.structured_logging import get_logger
from backend.db.models.user import User

logger = get_logger(__name__)


@dataclass
class SecurityValidationResult:
    """보안 검증 결과"""
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    risk_level: str = "low"  # low, medium, high, critical
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class OrchestrationSecurity:
    """오케스트레이션 보안 관리자"""
    
    # 기본 제한값
    DEFAULT_LIMITS = {
        "max_agents": 20,
        "max_execution_time": 3600,  # 1시간
        "max_token_usage": 50000,
        "max_name_length": 100,
        "max_description_length": 1000,
        "max_tags": 10,
        "max_tag_length": 50
    }
    
    # 위험한 키워드 패턴
    DANGEROUS_PATTERNS = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'subprocess',
        r'os\.system',
        r'shell=True',
        r'rm\s+-rf',
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
        r'UPDATE\s+.*\s+SET'
    ]
    
    @classmethod
    async def validate_execution_request(
        cls,
        config: Dict[str, Any],
        input_data: Dict[str, Any],
        user: User
    ) -> SecurityValidationResult:
        """
        실행 요청 보안 검증
        
        Args:
            config: 오케스트레이션 설정
            input_data: 입력 데이터
            user: 사용자 정보
            
        Returns:
            SecurityValidationResult: 검증 결과
        """
        errors = []
        warnings = []
        risk_level = "low"
        
        try:
            # 1. 기본 입력 검증
            input_errors = cls._validate_input_data(config, input_data)
            errors.extend(input_errors)
            
            # 2. 사용자 권한 확인
            permission_errors = cls._validate_user_permissions(config, user)
            errors.extend(permission_errors)
            
            # 3. 리소스 제한 확인
            resource_errors, resource_warnings = cls._validate_resource_limits(config, user)
            errors.extend(resource_errors)
            warnings.extend(resource_warnings)
            
            # 4. 보안 위험 검사
            security_errors, security_warnings, detected_risk = cls._validate_security_risks(config, input_data)
            errors.extend(security_errors)
            warnings.extend(security_warnings)
            risk_level = max(risk_level, detected_risk, key=cls._risk_level_priority)
            
            # 5. 실행 빈도 제한 확인
            rate_errors = await cls._validate_rate_limits(user)
            errors.extend(rate_errors)
            
            return SecurityValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return SecurityValidationResult(
                valid=False,
                errors=[f"Security validation failed: {str(e)}"],
                risk_level="critical"
            )
    
    @classmethod
    def _validate_input_data(cls, config: Dict[str, Any], input_data: Dict[str, Any]) -> List[str]:
        """입력 데이터 검증"""
        errors = []
        
        # 설정 이름 검증
        name = config.get("name", "")
        if not name or not name.strip():
            errors.append("Orchestration name is required")
        elif len(name) > cls.DEFAULT_LIMITS["max_name_length"]:
            errors.append(f"Name too long (max {cls.DEFAULT_LIMITS['max_name_length']} characters)")
        elif not re.match(r'^[a-zA-Z0-9가-힣\s\-_\.]+$', name):
            errors.append("Name contains invalid characters")
        
        # 설명 검증
        description = config.get("description", "")
        if description and len(description) > cls.DEFAULT_LIMITS["max_description_length"]:
            errors.append(f"Description too long (max {cls.DEFAULT_LIMITS['max_description_length']} characters)")
        
        # 태그 검증
        tags = config.get("tags", [])
        if len(tags) > cls.DEFAULT_LIMITS["max_tags"]:
            errors.append(f"Too many tags (max {cls.DEFAULT_LIMITS['max_tags']})")
        
        for tag in tags:
            if len(tag) > cls.DEFAULT_LIMITS["max_tag_length"]:
                errors.append(f"Tag '{tag}' too long (max {cls.DEFAULT_LIMITS['max_tag_length']} characters)")
            elif not re.match(r'^[a-zA-Z0-9가-힣\-_]+$', tag):
                errors.append(f"Tag '{tag}' contains invalid characters")
        
        # Agent 역할 검증
        agent_roles = config.get("agent_roles", [])
        for i, agent in enumerate(agent_roles):
            agent_name = agent.get("name", f"Agent_{i}")
            if not agent_name or not agent_name.strip():
                errors.append(f"Agent {i+1} name is required")
            elif len(agent_name) > 50:
                errors.append(f"Agent {i+1} name too long (max 50 characters)")
        
        return errors
    
    @classmethod
    def _validate_user_permissions(cls, config: Dict[str, Any], user: User) -> List[str]:
        """사용자 권한 검증"""
        errors = []
        
        # 기본 실행 권한 확인
        if not hasattr(user, 'has_permission') or not user.has_permission("orchestration.execute"):
            errors.append("Insufficient permissions to execute orchestrations")
        
        # 고급 패턴 권한 확인
        advanced_patterns = [
            "consensus_building", "dynamic_routing", "swarm_intelligence",
            "neuromorphic", "quantum_enhanced", "bio_inspired"
        ]
        
        orchestration_type = config.get("orchestration_type", "")
        if orchestration_type in advanced_patterns:
            if not hasattr(user, 'has_permission') or not user.has_permission("orchestration.advanced"):
                errors.append(f"Insufficient permissions for advanced pattern: {orchestration_type}")
        
        return errors
    
    @classmethod
    def _validate_resource_limits(cls, config: Dict[str, Any], user: User) -> tuple[List[str], List[str]]:
        """리소스 제한 검증"""
        errors = []
        warnings = []
        
        # Agent 수 제한
        agent_roles = config.get("agent_roles", [])
        max_agents = getattr(user, 'max_agents', cls.DEFAULT_LIMITS["max_agents"])
        
        if len(agent_roles) > max_agents:
            errors.append(f"Too many agents: {len(agent_roles)} (max {max_agents})")
        elif len(agent_roles) > max_agents * 0.8:
            warnings.append(f"High agent count: {len(agent_roles)} (approaching limit of {max_agents})")
        
        # 실행 시간 제한
        performance_thresholds = config.get("performance_thresholds", {})
        max_execution_time = performance_thresholds.get("max_execution_time", 300000)
        user_max_time = getattr(user, 'max_execution_time', cls.DEFAULT_LIMITS["max_execution_time"]) * 1000
        
        if max_execution_time > user_max_time:
            errors.append(f"Execution time too long: {max_execution_time}ms (max {user_max_time}ms)")
        
        # 토큰 사용량 제한
        max_token_usage = performance_thresholds.get("max_token_usage", 10000)
        user_max_tokens = getattr(user, 'max_token_usage', cls.DEFAULT_LIMITS["max_token_usage"])
        
        if max_token_usage > user_max_tokens:
            errors.append(f"Token usage too high: {max_token_usage} (max {user_max_tokens})")
        
        return errors, warnings
    
    @classmethod
    def _validate_security_risks(
        cls, 
        config: Dict[str, Any], 
        input_data: Dict[str, Any]
    ) -> tuple[List[str], List[str], str]:
        """보안 위험 검사"""
        errors = []
        warnings = []
        risk_level = "low"
        
        # 전체 설정을 문자열로 변환하여 검사
        config_str = str(config) + str(input_data)
        
        # 위험한 패턴 검사
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, config_str, re.IGNORECASE):
                errors.append(f"Potentially dangerous pattern detected: {pattern}")
                risk_level = "high"
        
        # 외부 URL 검사
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, config_str)
        
        for url in urls:
            # 내부 도메인이 아닌 경우 경고
            if not any(domain in url for domain in ['localhost', '127.0.0.1', 'internal.company.com']):
                warnings.append(f"External URL detected: {url}")
                risk_level = max(risk_level, "medium", key=cls._risk_level_priority)
        
        # 민감한 키워드 검사
        sensitive_keywords = ['password', 'secret', 'key', 'token', 'credential']
        for keyword in sensitive_keywords:
            if keyword.lower() in config_str.lower():
                warnings.append(f"Sensitive keyword detected: {keyword}")
                risk_level = max(risk_level, "medium", key=cls._risk_level_priority)
        
        return errors, warnings, risk_level
    
    @classmethod
    async def _validate_rate_limits(cls, user: User) -> List[str]:
        """실행 빈도 제한 확인"""
        errors = []
        
        # TODO: Redis를 사용한 실제 rate limiting 구현
        # 현재는 기본 검증만 수행
        
        # 사용자별 일일 실행 제한 (예시)
        daily_limit = getattr(user, 'daily_execution_limit', 100)
        
        # 실제 구현에서는 Redis에서 오늘의 실행 횟수를 조회
        # current_executions = await redis.get(f"executions:{user.id}:{datetime.now().date()}")
        # if current_executions and int(current_executions) >= daily_limit:
        #     errors.append(f"Daily execution limit exceeded: {daily_limit}")
        
        return errors
    
    @staticmethod
    def _risk_level_priority(risk_level: str) -> int:
        """위험 수준 우선순위"""
        priorities = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return priorities.get(risk_level, 1)
    
    @classmethod
    def sanitize_input(cls, data: Any) -> Any:
        """입력 데이터 정화"""
        if isinstance(data, str):
            # HTML 태그 제거
            data = re.sub(r'<[^>]+>', '', data)
            # 스크립트 태그 제거
            data = re.sub(r'<script.*?</script>', '', data, flags=re.IGNORECASE | re.DOTALL)
            # 위험한 문자 이스케이프
            data = data.replace('<', '&lt;').replace('>', '&gt;')
            
        elif isinstance(data, dict):
            return {key: cls.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_input(item) for item in data]
        
        return data
    
    @classmethod
    def create_execution_context(cls, user: User, config: Dict[str, Any]) -> Dict[str, Any]:
        """실행 컨텍스트 생성"""
        return {
            "user_id": user.id,
            "user_email": getattr(user, 'email', 'unknown'),
            "execution_time": datetime.now().isoformat(),
            "orchestration_type": config.get("orchestration_type"),
            "agent_count": len(config.get("agent_roles", [])),
            "security_validated": True,
            "ip_address": "127.0.0.1",  # 실제로는 request에서 가져옴
            "user_agent": "AgenticRAG/1.0"  # 실제로는 request에서 가져옴
        }


# 데코레이터 함수들
def require_orchestration_permission(permission: str):
    """오케스트레이션 권한 확인 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 실제 구현에서는 사용자 권한 확인
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_execution_timeout(max_seconds: int = 3600):
    """실행 시간 제한 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import asyncio
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=max_seconds)
            except asyncio.TimeoutError:
                logger.error(f"Execution timeout after {max_seconds} seconds")
                raise Exception(f"Execution timeout after {max_seconds} seconds")
        return wrapper
    return decorator