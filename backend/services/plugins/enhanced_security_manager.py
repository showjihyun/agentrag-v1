"""
Enhanced Plugin Security Manager

Provides comprehensive security validation with RBAC, enhanced input validation,
and improved threat detection for plugins.
"""

import ast
import hashlib
import hmac
import re
import subprocess
import tempfile
import zipfile
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
from pydantic import BaseModel, validator, Field

from backend.core.logging_standards import StandardLogger
from backend.models.plugin import PluginManifest
from backend.core.error_handling.plugin_errors import (
    PluginSecurityError,
    PluginValidationException,
    PluginErrorCode
)

import logging

logger = logging.getLogger(__name__)


class PluginPermission(Enum):
    """플러그인 권한 정의"""
    EXECUTE = "execute"
    INSTALL = "install"
    UNINSTALL = "uninstall"
    VIEW = "view"
    MODIFY = "modify"
    ADMIN = "admin"
    CREATE_CUSTOM = "create_custom"
    MANAGE_USERS = "manage_users"


class UserRole(Enum):
    """사용자 역할 정의"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    GUEST = "guest"


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats"""
    MALICIOUS_CODE = "malicious_code"
    SUSPICIOUS_IMPORTS = "suspicious_imports"
    DANGEROUS_FUNCTIONS = "dangerous_functions"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM_ACCESS = "file_system_access"
    PROCESS_EXECUTION = "process_execution"
    SIGNATURE_INVALID = "signature_invalid"
    DEPENDENCY_VULNERABILITY = "dependency_vulnerability"
    PERMISSION_VIOLATION = "permission_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INPUT_VALIDATION_FAILED = "input_validation_failed"


@dataclass
class SecurityContext:
    """보안 컨텍스트"""
    user_id: str
    user_role: UserRole
    permissions: Set[PluginPermission]
    rate_limit_remaining: int
    session_id: str
    ip_address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityThreat:
    """Represents a security threat found in plugin code"""
    threat_type: ThreatType
    level: ThreatLevel
    description: str
    location: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of security validation"""
    is_valid: bool
    threats: List[SecurityThreat]
    score: float  # 0-100, higher is safer
    validation_time: float = 0.0
    
    @classmethod
    def combine(cls, results: List['ValidationResult']) -> 'ValidationResult':
        """Combine multiple validation results"""
        all_threats = []
        min_score = 100.0
        total_time = 0.0
        
        for result in results:
            all_threats.extend(result.threats)
            min_score = min(min_score, result.score)
            total_time += result.validation_time
        
        # Plugin is valid only if all validations pass and no critical threats
        is_valid = all(r.is_valid for r in results) and not any(
            t.level == ThreatLevel.CRITICAL for t in all_threats
        )
        
        return cls(
            is_valid=is_valid,
            threats=all_threats,
            score=min_score,
            validation_time=total_time
        )


class SecureAgentExecutionRequest(BaseModel):
    """보안이 강화된 Agent 실행 요청"""
    agent_type: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', max_length=100)
    input_data: Dict[str, Any] = Field(..., max_items=50)
    execution_timeout: int = Field(default=300, ge=1, le=3600)  # 1초~1시간
    priority: int = Field(default=5, ge=1, le=10)  # 1=highest, 10=lowest
    
    @validator('input_data')
    def validate_input_size(cls, v):
        serialized = json.dumps(v, ensure_ascii=False)
        if len(serialized.encode('utf-8')) > 1024 * 1024:  # 1MB 제한
            raise ValueError('Input data exceeds 1MB limit')
        return v
    
    @validator('input_data')
    def validate_no_dangerous_content(cls, v):
        """위험한 내용 검증"""
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',
            r'data:text/html',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'subprocess\.',
            r'os\.system',
            r'shell=True',
        ]
        
        serialized = json.dumps(v, ensure_ascii=False)
        for pattern in dangerous_patterns:
            if re.search(pattern, serialized, re.IGNORECASE | re.DOTALL):
                raise ValueError(f'Dangerous content detected: {pattern}')
        return v
    
    @validator('input_data')
    def validate_data_types(cls, v):
        """허용된 데이터 타입만 검증"""
        allowed_types = (str, int, float, bool, list, dict, type(None))
        
        def check_type(obj, path=""):
            if not isinstance(obj, allowed_types):
                raise ValueError(f'Invalid data type at {path}: {type(obj)}')
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if not isinstance(key, str):
                        raise ValueError(f'Dictionary keys must be strings at {path}')
                    check_type(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_type(item, f"{path}[{i}]")
        
        check_type(v)
        return v


class PluginPermissionManager:
    """플러그인 권한 관리자"""
    
    def __init__(self):
        self.role_permissions = {
            UserRole.ADMIN: {PluginPermission.ADMIN},  # 모든 권한
            UserRole.DEVELOPER: {
                PluginPermission.EXECUTE,
                PluginPermission.INSTALL,
                PluginPermission.VIEW,
                PluginPermission.MODIFY,
                PluginPermission.CREATE_CUSTOM
            },
            UserRole.USER: {
                PluginPermission.EXECUTE,
                PluginPermission.VIEW
            },
            UserRole.GUEST: {
                PluginPermission.VIEW
            }
        }
        
        # 사용자별 추가 권한
        self.user_permissions: Dict[str, Set[PluginPermission]] = defaultdict(set)
        
        # 플러그인별 접근 제어
        self.plugin_access_control: Dict[str, Dict[str, Any]] = {}
    
    def has_permission(
        self, 
        user_id: str, 
        user_role: UserRole, 
        permission: PluginPermission,
        plugin_id: Optional[str] = None
    ) -> bool:
        """사용자가 특정 권한을 가지고 있는지 확인"""
        
        # Admin은 모든 권한
        if user_role == UserRole.ADMIN:
            return True
        
        # 역할 기반 권한 확인
        role_perms = self.role_permissions.get(user_role, set())
        if permission in role_perms:
            # 플러그인별 접근 제어 확인
            if plugin_id and plugin_id in self.plugin_access_control:
                access_rules = self.plugin_access_control[plugin_id]
                
                # 블랙리스트 확인
                if user_id in access_rules.get('blacklist', []):
                    return False
                
                # 화이트리스트 확인 (있는 경우)
                whitelist = access_rules.get('whitelist', [])
                if whitelist and user_id not in whitelist:
                    return False
            
            return True
        
        # 사용자별 추가 권한 확인
        user_perms = self.user_permissions.get(user_id, set())
        return permission in user_perms
    
    def grant_permission(self, user_id: str, permission: PluginPermission):
        """사용자에게 권한 부여"""
        self.user_permissions[user_id].add(permission)
    
    def revoke_permission(self, user_id: str, permission: PluginPermission):
        """사용자 권한 취소"""
        self.user_permissions[user_id].discard(permission)
    
    def set_plugin_access_control(
        self, 
        plugin_id: str, 
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None
    ):
        """플러그인별 접근 제어 설정"""
        self.plugin_access_control[plugin_id] = {
            'whitelist': whitelist or [],
            'blacklist': blacklist or []
        }


class RateLimitManager:
    """속도 제한 관리자"""
    
    def __init__(self):
        # 사용자별 요청 기록 {user_id: [(timestamp, count), ...]}
        self.request_history: Dict[str, List[tuple]] = defaultdict(list)
        
        # 역할별 제한 설정
        self.rate_limits = {
            UserRole.ADMIN: {'requests_per_minute': 1000, 'requests_per_hour': 10000},
            UserRole.DEVELOPER: {'requests_per_minute': 100, 'requests_per_hour': 1000},
            UserRole.USER: {'requests_per_minute': 30, 'requests_per_hour': 300},
            UserRole.GUEST: {'requests_per_minute': 5, 'requests_per_hour': 50}
        }
    
    def check_rate_limit(self, user_id: str, user_role: UserRole) -> tuple[bool, int]:
        """속도 제한 확인"""
        now = time.time()
        limits = self.rate_limits.get(user_role, self.rate_limits[UserRole.GUEST])
        
        # 기록 정리 (1시간 이상 된 것 제거)
        history = self.request_history[user_id]
        history[:] = [(ts, count) for ts, count in history if now - ts < 3600]
        
        # 분당 제한 확인
        minute_requests = sum(
            count for ts, count in history if now - ts < 60
        )
        
        # 시간당 제한 확인
        hour_requests = sum(count for ts, count in history)
        
        if minute_requests >= limits['requests_per_minute']:
            return False, 0
        
        if hour_requests >= limits['requests_per_hour']:
            return False, 0
        
        # 남은 요청 수 계산
        remaining = min(
            limits['requests_per_minute'] - minute_requests,
            limits['requests_per_hour'] - hour_requests
        )
        
        return True, remaining
    
    def record_request(self, user_id: str, count: int = 1):
        """요청 기록"""
        now = time.time()
        self.request_history[user_id].append((now, count))


class EnhancedPluginSecurityManager:
    """향상된 플러그인 보안 관리자"""
    
    # 위험한 import 확장
    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'sys', 'shutil', 'tempfile', 'socket', 
        'urllib', 'requests', 'http', 'ftplib', 'smtplib', 'telnetlib',
        'pickle', 'marshal', 'shelve', 'dbm', 'eval', 'exec', 'compile',
        '__import__', 'importlib', 'ctypes', 'multiprocessing', 'threading',
        'asyncio.subprocess', 'concurrent.futures', 'queue', 'signal',
        'pty', 'tty', 'termios', 'fcntl', 'select', 'mmap', 'resource'
    }
    
    # 위험한 함수 호출 확장
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'execfile', 'reload', 'vars', 'globals',
        'locals', 'dir', 'hasattr', 'getattr', 'setattr', 'delattr',
        'breakpoint', 'help', 'exit', 'quit', 'license', 'credits'
    }
    
    # 악성 코드 패턴 확장
    MALICIOUS_PATTERNS = [
        r'rm\s+-rf\s+/',  # Delete root filesystem
        r'format\s+c:',   # Format C drive
        r'del\s+/[sq]',   # Delete system directories
        r'sudo\s+rm',     # Sudo delete commands
        r'chmod\s+777',   # Dangerous permissions
        r'wget.*\|\s*sh', # Download and execute
        r'curl.*\|\s*sh', # Download and execute
        r'base64.*decode', # Encoded malicious code
        r'reverse_shell', # Reverse shell attempts
        r'backdoor',      # Backdoor references
        r'keylogger',     # Keylogger references
        r'password.*steal', # Password stealing
        r'crypto.*mine',  # Cryptocurrency mining
        r'ddos',          # DDoS attacks
        r'botnet',        # Botnet references
        r'rootkit',       # Rootkit references
        r'trojan',        # Trojan references
        r'virus',         # Virus references
        r'malware',       # Malware references
    ]
    
    def __init__(self, docker_client: Optional['docker.DockerClient'] = None):
        """Initialize enhanced security manager"""
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        
        if DOCKER_AVAILABLE:
            self.docker_client = docker_client or docker.from_env()
        else:
            self.docker_client = None
            self.logger.warning("Docker not available - sandboxing features disabled")
        self.sandbox_image = "python:3.10-slim"
        
        # 보안 컴포넌트 초기화
        self.permission_manager = PluginPermissionManager()
        self.rate_limit_manager = RateLimitManager()
        
        # 보안 컨텍스트 캐시
        self.security_contexts: Dict[str, SecurityContext] = {}
        
        # 보안 이벤트 로그
        self.security_events: List[Dict[str, Any]] = []
    
    def create_security_context(
        self, 
        user_id: str, 
        user_role: UserRole,
        session_id: str,
        ip_address: Optional[str] = None
    ) -> SecurityContext:
        """보안 컨텍스트 생성"""
        
        # 속도 제한 확인
        allowed, remaining = self.rate_limit_manager.check_rate_limit(user_id, user_role)
        if not allowed:
            raise PluginSecurityError(
                code=PluginErrorCode.RATE_LIMIT_EXCEEDED,
                message="Rate limit exceeded",
                details={"user_id": user_id, "role": user_role.value}
            )
        
        # 권한 수집
        permissions = set()
        if user_role == UserRole.ADMIN:
            permissions = set(PluginPermission)
        else:
            permissions = self.permission_manager.role_permissions.get(user_role, set())
            permissions.update(self.permission_manager.user_permissions.get(user_id, set()))
        
        context = SecurityContext(
            user_id=user_id,
            user_role=user_role,
            permissions=permissions,
            rate_limit_remaining=remaining,
            session_id=session_id,
            ip_address=ip_address
        )
        
        self.security_contexts[session_id] = context
        return context
    
    def validate_execution_request(
        self, 
        request: SecureAgentExecutionRequest,
        security_context: SecurityContext
    ) -> ValidationResult:
        """실행 요청 검증"""
        start_time = time.time()
        threats = []
        score = 100.0
        
        try:
            # 권한 확인
            if not self.permission_manager.has_permission(
                security_context.user_id,
                security_context.user_role,
                PluginPermission.EXECUTE,
                request.agent_type
            ):
                threats.append(SecurityThreat(
                    threat_type=ThreatType.PERMISSION_VIOLATION,
                    level=ThreatLevel.HIGH,
                    description=f"User {security_context.user_id} lacks EXECUTE permission for {request.agent_type}",
                    context={"user_role": security_context.user_role.value}
                ))
                score = 0
            
            # 속도 제한 재확인
            allowed, remaining = self.rate_limit_manager.check_rate_limit(
                security_context.user_id, 
                security_context.user_role
            )
            if not allowed:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.RATE_LIMIT_EXCEEDED,
                    level=ThreatLevel.MEDIUM,
                    description="Rate limit exceeded during validation"
                ))
                score -= 30
            
            # 입력 데이터 심층 검증
            input_threats = self._validate_input_data_deep(request.input_data)
            threats.extend(input_threats)
            score -= len(input_threats) * 10
            
            # 요청 기록
            self.rate_limit_manager.record_request(security_context.user_id)
            
        except Exception as e:
            logger.error(f"Request validation failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.INPUT_VALIDATION_FAILED,
                level=ThreatLevel.HIGH,
                description=f"Validation error: {str(e)}"
            ))
            score = 0
        
        validation_time = time.time() - start_time
        is_valid = score >= 70 and not any(t.level == ThreatLevel.CRITICAL for t in threats)
        
        return ValidationResult(
            is_valid=is_valid,
            threats=threats,
            score=max(0, score),
            validation_time=validation_time
        )
    
    def _validate_input_data_deep(self, input_data: Dict[str, Any]) -> List[SecurityThreat]:
        """입력 데이터 심층 검증"""
        threats = []
        
        def check_value(value, path=""):
            if isinstance(value, str):
                # SQL 인젝션 패턴 검사
                sql_patterns = [
                    r"union\s+select", r"drop\s+table", r"delete\s+from",
                    r"insert\s+into", r"update\s+.*set", r"exec\s*\(",
                    r"xp_cmdshell", r"sp_executesql"
                ]
                
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        threats.append(SecurityThreat(
                            threat_type=ThreatType.INPUT_VALIDATION_FAILED,
                            level=ThreatLevel.HIGH,
                            description=f"Potential SQL injection at {path}: {pattern}",
                            context={"value": value[:100]}  # 처음 100자만 로그
                        ))
                
                # 스크립트 인젝션 검사
                script_patterns = [
                    r"<script", r"javascript:", r"vbscript:", r"onload=",
                    r"onerror=", r"onclick=", r"eval\s*\("
                ]
                
                for pattern in script_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        threats.append(SecurityThreat(
                            threat_type=ThreatType.INPUT_VALIDATION_FAILED,
                            level=ThreatLevel.MEDIUM,
                            description=f"Potential script injection at {path}: {pattern}",
                            context={"value": value[:100]}
                        ))
                
                # 파일 경로 조작 검사
                path_patterns = [
                    r"\.\./", r"\.\.\\", r"/etc/passwd", r"/etc/shadow",
                    r"c:\\windows", r"c:\\system32"
                ]
                
                for pattern in path_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        threats.append(SecurityThreat(
                            threat_type=ThreatType.INPUT_VALIDATION_FAILED,
                            level=ThreatLevel.HIGH,
                            description=f"Potential path traversal at {path}: {pattern}",
                            context={"value": value[:100]}
                        ))
            
            elif isinstance(value, dict):
                for key, val in value.items():
                    check_value(val, f"{path}.{key}")
            
            elif isinstance(value, list):
                for i, val in enumerate(value):
                    check_value(val, f"{path}[{i}]")
        
        check_value(input_data)
        return threats
    
    def log_security_event(
        self, 
        event_type: str, 
        user_id: str, 
        details: Dict[str, Any],
        severity: str = "info"
    ):
        """보안 이벤트 로깅"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "severity": severity,
            "details": details
        }
        
        self.security_events.append(event)
        
        # 최근 1000개 이벤트만 유지
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
        
        # 심각한 이벤트는 즉시 로깅
        if severity in ["error", "critical"]:
            logger.error(f"Security event: {event}")
        elif severity == "warning":
            logger.warning(f"Security event: {event}")
        else:
            logger.info(f"Security event: {event}")
    
    async def validate_plugin_comprehensive(
        self, 
        plugin_path: str, 
        manifest: PluginManifest,
        security_context: SecurityContext
    ) -> ValidationResult:
        """포괄적인 플러그인 검증"""
        start_time = time.time()
        
        # 권한 확인
        if not self.permission_manager.has_permission(
            security_context.user_id,
            security_context.user_role,
            PluginPermission.INSTALL
        ):
            self.log_security_event(
                "plugin_validation_denied",
                security_context.user_id,
                {"plugin": manifest.name, "reason": "insufficient_permissions"},
                "warning"
            )
            
            return ValidationResult(
                is_valid=False,
                threats=[SecurityThreat(
                    threat_type=ThreatType.PERMISSION_VIOLATION,
                    level=ThreatLevel.CRITICAL,
                    description="Insufficient permissions to install plugin"
                )],
                score=0.0,
                validation_time=time.time() - start_time
            )
        
        # 기존 검증 로직 실행
        results = []
        
        try:
            # 정적 코드 분석
            static_result = await self._static_code_analysis_enhanced(plugin_path)
            results.append(static_result)
            
            # 악성 코드 패턴 검사
            malware_result = await self._scan_malware_patterns_enhanced(plugin_path)
            results.append(malware_result)
            
            # 의존성 보안 검사
            dep_result = await self._check_dependency_security_enhanced(manifest.dependencies)
            results.append(dep_result)
            
            # 서명 검증 (있는 경우)
            if hasattr(manifest, 'signature') and manifest.signature:
                sig_result = await self._verify_signature_enhanced(plugin_path, manifest.signature)
                results.append(sig_result)
            
            combined_result = ValidationResult.combine(results)
            
            # 보안 이벤트 로깅
            self.log_security_event(
                "plugin_validation_completed",
                security_context.user_id,
                {
                    "plugin": manifest.name,
                    "valid": combined_result.is_valid,
                    "score": combined_result.score,
                    "threats_count": len(combined_result.threats),
                    "validation_time": combined_result.validation_time
                },
                "info" if combined_result.is_valid else "warning"
            )
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Comprehensive validation failed for {manifest.name}: {str(e)}")
            
            self.log_security_event(
                "plugin_validation_error",
                security_context.user_id,
                {"plugin": manifest.name, "error": str(e)},
                "error"
            )
            
            return ValidationResult(
                is_valid=False,
                threats=[SecurityThreat(
                    threat_type=ThreatType.MALICIOUS_CODE,
                    level=ThreatLevel.CRITICAL,
                    description=f"Validation error: {str(e)}"
                )],
                score=0.0,
                validation_time=time.time() - start_time
            )
    
    async def _static_code_analysis_enhanced(self, plugin_path: str) -> ValidationResult:
        """향상된 정적 코드 분석"""
        start_time = time.time()
        threats = []
        score = 100.0
        
        try:
            python_files = self._find_python_files(plugin_path)
            
            for file_path in python_files:
                file_threats = await self._analyze_python_file_enhanced(file_path)
                threats.extend(file_threats)
        
        except Exception as e:
            logger.error(f"Enhanced static code analysis failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=ThreatLevel.HIGH,
                description=f"Code analysis error: {str(e)}"
            ))
        
        # 점수 계산 (가중치 적용)
        for threat in threats:
            if threat.level == ThreatLevel.CRITICAL:
                score -= 50
            elif threat.level == ThreatLevel.HIGH:
                score -= 25
            elif threat.level == ThreatLevel.MEDIUM:
                score -= 10
            elif threat.level == ThreatLevel.LOW:
                score -= 5
        
        score = max(0, score)
        is_valid = score >= 70 and not any(t.level == ThreatLevel.CRITICAL for t in threats)
        
        return ValidationResult(
            is_valid=is_valid, 
            threats=threats, 
            score=score,
            validation_time=time.time() - start_time
        )
    
    async def _analyze_python_file_enhanced(self, file_path: str) -> List[SecurityThreat]:
        """향상된 Python 파일 분석"""
        threats = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST 파싱
            tree = ast.parse(content, filename=file_path)
            
            # 향상된 AST 분석
            for node in ast.walk(tree):
                # Import 분석
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    threats.extend(self._analyze_import_node(node, file_path))
                
                # 함수 호출 분석
                elif isinstance(node, ast.Call):
                    threats.extend(self._analyze_call_node(node, file_path))
                
                # 문자열 리터럴 분석 (인코딩된 코드 검사)
                elif isinstance(node, ast.Str):
                    threats.extend(self._analyze_string_literal(node, file_path))
                
                # 속성 접근 분석
                elif isinstance(node, ast.Attribute):
                    threats.extend(self._analyze_attribute_access(node, file_path))
        
        except SyntaxError as e:
            threats.append(SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=ThreatLevel.MEDIUM,
                description=f"Syntax error in {file_path}: {str(e)}",
                location=file_path,
                line_number=getattr(e, 'lineno', None)
            ))
        
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
        
        return threats
    
    def _analyze_import_node(self, node: Union[ast.Import, ast.ImportFrom], file_path: str) -> List[SecurityThreat]:
        """Import 노드 분석"""
        threats = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.DANGEROUS_IMPORTS:
                    level = ThreatLevel.HIGH if alias.name in ['os', 'subprocess', 'sys'] else ThreatLevel.MEDIUM
                    threats.append(SecurityThreat(
                        threat_type=ThreatType.SUSPICIOUS_IMPORTS,
                        level=level,
                        description=f"Dangerous import: {alias.name}",
                        location=file_path,
                        line_number=node.lineno,
                        context={"import_name": alias.name}
                    ))
        
        elif isinstance(node, ast.ImportFrom):
            if node.module in self.DANGEROUS_IMPORTS:
                level = ThreatLevel.HIGH if node.module in ['os', 'subprocess', 'sys'] else ThreatLevel.MEDIUM
                threats.append(SecurityThreat(
                    threat_type=ThreatType.SUSPICIOUS_IMPORTS,
                    level=level,
                    description=f"Dangerous import from: {node.module}",
                    location=file_path,
                    line_number=node.lineno,
                    context={"module_name": node.module}
                ))
        
        return threats
    
    def _analyze_call_node(self, node: ast.Call, file_path: str) -> List[SecurityThreat]:
        """함수 호출 노드 분석"""
        threats = []
        
        # 직접 함수 호출
        if isinstance(node.func, ast.Name):
            if node.func.id in self.DANGEROUS_FUNCTIONS:
                level = ThreatLevel.CRITICAL if node.func.id in ['eval', 'exec'] else ThreatLevel.HIGH
                threats.append(SecurityThreat(
                    threat_type=ThreatType.DANGEROUS_FUNCTIONS,
                    level=level,
                    description=f"Dangerous function call: {node.func.id}",
                    location=file_path,
                    line_number=node.lineno,
                    context={"function_name": node.func.id}
                ))
        
        # 속성 함수 호출 (예: os.system)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                func_name = node.func.attr
                
                dangerous_combinations = [
                    ('os', 'system'), ('subprocess', 'call'), ('subprocess', 'run'),
                    ('subprocess', 'Popen'), ('os', 'popen'), ('os', 'spawn'),
                    ('shutil', 'rmtree'), ('tempfile', 'mktemp')
                ]
                
                if (module_name, func_name) in dangerous_combinations:
                    threats.append(SecurityThreat(
                        threat_type=ThreatType.DANGEROUS_FUNCTIONS,
                        level=ThreatLevel.CRITICAL,
                        description=f"Dangerous method call: {module_name}.{func_name}",
                        location=file_path,
                        line_number=node.lineno,
                        context={"module": module_name, "function": func_name}
                    ))
        
        return threats
    
    def _analyze_string_literal(self, node: ast.Str, file_path: str) -> List[SecurityThreat]:
        """문자열 리터럴 분석"""
        threats = []
        
        # Base64 인코딩된 코드 검사
        if len(node.s) > 50 and re.match(r'^[A-Za-z0-9+/]+=*$', node.s):
            try:
                import base64
                decoded = base64.b64decode(node.s).decode('utf-8', errors='ignore')
                
                # 디코딩된 내용에서 위험한 패턴 검사
                for pattern in self.MALICIOUS_PATTERNS:
                    if re.search(pattern, decoded, re.IGNORECASE):
                        threats.append(SecurityThreat(
                            threat_type=ThreatType.MALICIOUS_CODE,
                            level=ThreatLevel.CRITICAL,
                            description=f"Encoded malicious code detected: {pattern}",
                            location=file_path,
                            line_number=node.lineno,
                            context={"encoded_content": node.s[:100]}
                        ))
            except:
                pass  # Base64 디코딩 실패는 무시
        
        return threats
    
    def _analyze_attribute_access(self, node: ast.Attribute, file_path: str) -> List[SecurityThreat]:
        """속성 접근 분석"""
        threats = []
        
        # 위험한 속성 접근 패턴
        dangerous_attributes = [
            '__globals__', '__locals__', '__builtins__', '__import__',
            '__subclasses__', '__bases__', '__mro__'
        ]
        
        if node.attr in dangerous_attributes:
            threats.append(SecurityThreat(
                threat_type=ThreatType.DANGEROUS_FUNCTIONS,
                level=ThreatLevel.HIGH,
                description=f"Dangerous attribute access: {node.attr}",
                location=file_path,
                line_number=node.lineno,
                context={"attribute": node.attr}
            ))
        
        return threats
    
    async def _scan_malware_patterns_enhanced(self, plugin_path: str) -> ValidationResult:
        """향상된 악성 코드 패턴 스캔"""
        start_time = time.time()
        threats = []
        score = 100.0
        
        try:
            text_files = self._find_text_files(plugin_path)
            
            for file_path in text_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 기본 패턴 검사
                    for pattern in self.MALICIOUS_PATTERNS:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            threats.append(SecurityThreat(
                                threat_type=ThreatType.MALICIOUS_CODE,
                                level=ThreatLevel.CRITICAL,
                                description=f"Malicious pattern detected: {pattern}",
                                location=file_path,
                                line_number=line_num,
                                code_snippet=match.group()[:100]  # 처음 100자만
                            ))
                            score -= 30
                    
                    # 추가 휴리스틱 검사
                    heuristic_threats = self._heuristic_analysis(content, file_path)
                    threats.extend(heuristic_threats)
                    score -= len(heuristic_threats) * 5
                
                except Exception as e:
                    logger.warning(f"Could not scan file {file_path}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Enhanced malware pattern scanning failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=ThreatLevel.HIGH,
                description=f"Malware scan error: {str(e)}"
            ))
        
        score = max(0, score)
        is_valid = not any(t.level == ThreatLevel.CRITICAL for t in threats)
        
        return ValidationResult(
            is_valid=is_valid, 
            threats=threats, 
            score=score,
            validation_time=time.time() - start_time
        )
    
    def _heuristic_analysis(self, content: str, file_path: str) -> List[SecurityThreat]:
        """휴리스틱 분석"""
        threats = []
        
        # 의심스러운 문자열 패턴
        suspicious_patterns = [
            (r'[a-f0-9]{32,}', "Potential hash or encoded data"),
            (r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', "Potential base64 encoded data"),
            (r'\\x[0-9a-f]{2}', "Hex encoded data"),
            (r'chr\(\d+\)', "Character encoding"),
            (r'ord\([\'"][^\'"]\[\'"\]', "Character to number conversion")
        ]
        
        for pattern, description in suspicious_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if len(matches) > 10:  # 많은 수의 매치는 의심스러움
                threats.append(SecurityThreat(
                    threat_type=ThreatType.MALICIOUS_CODE,
                    level=ThreatLevel.MEDIUM,
                    description=f"Suspicious pattern frequency: {description} ({len(matches)} occurrences)",
                    location=file_path,
                    context={"pattern": pattern, "count": len(matches)}
                ))
        
        return threats
    
    async def _check_dependency_security_enhanced(self, dependencies: List[str]) -> ValidationResult:
        """향상된 의존성 보안 검사"""
        start_time = time.time()
        threats = []
        score = 100.0
        
        # 확장된 취약한 패키지 목록
        VULNERABLE_PACKAGES = {
            'pickle5': ('Known security vulnerabilities', ThreatLevel.HIGH),
            'pyyaml': ('Versions < 5.1 have vulnerabilities', ThreatLevel.MEDIUM),
            'requests': ('Versions < 2.20.0 have vulnerabilities', ThreatLevel.MEDIUM),
            'urllib3': ('Versions < 1.24.2 have vulnerabilities', ThreatLevel.MEDIUM),
            'pillow': ('Multiple CVEs in older versions', ThreatLevel.MEDIUM),
            'django': ('Check for latest security patches', ThreatLevel.LOW),
            'flask': ('Check for latest security patches', ThreatLevel.LOW),
            'numpy': ('Buffer overflow in older versions', ThreatLevel.MEDIUM),
            'tensorflow': ('Multiple security issues in older versions', ThreatLevel.MEDIUM),
            'torch': ('Potential security issues', ThreatLevel.LOW)
        }
        
        # 금지된 패키지
        BANNED_PACKAGES = {
            'pickle', 'dill', 'cloudpickle',  # 직렬화 관련
            'paramiko', 'fabric',  # SSH 관련
            'scapy',  # 네트워크 패킷 조작
            'nmap',  # 네트워크 스캐닝
        }
        
        for dep in dependencies:
            # 패키지 이름 추출
            package_name = re.split(r'[<>=!]', dep)[0].strip()
            
            # 금지된 패키지 확인
            if package_name in BANNED_PACKAGES:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.DEPENDENCY_VULNERABILITY,
                    level=ThreatLevel.CRITICAL,
                    description=f"Banned package: {package_name}",
                    context={"package": package_name, "dependency": dep}
                ))
                score = 0
            
            # 취약한 패키지 확인
            elif package_name in VULNERABLE_PACKAGES:
                description, level = VULNERABLE_PACKAGES[package_name]
                threats.append(SecurityThreat(
                    threat_type=ThreatType.DEPENDENCY_VULNERABILITY,
                    level=level,
                    description=f"Potentially vulnerable dependency: {package_name} - {description}",
                    context={"package": package_name, "dependency": dep}
                ))
                
                if level == ThreatLevel.HIGH:
                    score -= 25
                elif level == ThreatLevel.MEDIUM:
                    score -= 15
                else:
                    score -= 5
        
        score = max(0, score)
        is_valid = score >= 70 and not any(t.level == ThreatLevel.CRITICAL for t in threats)
        
        return ValidationResult(
            is_valid=is_valid, 
            threats=threats, 
            score=score,
            validation_time=time.time() - start_time
        )
    
    async def _verify_signature_enhanced(self, plugin_path: str, signature: str) -> ValidationResult:
        """향상된 서명 검증"""
        start_time = time.time()
        threats = []
        score = 100.0
        
        try:
            # 파일 해시 계산
            file_hash = self._calculate_file_hash(plugin_path)
            
            # 향상된 서명 검증 (실제 구현에서는 RSA/ECDSA 사용)
            expected_signature = hmac.new(
                b'enhanced_plugin_signing_key_2024',  # 실제로는 안전한 키 관리 필요
                file_hash.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                threats.append(SecurityThreat(
                    threat_type=ThreatType.SIGNATURE_INVALID,
                    level=ThreatLevel.CRITICAL,
                    description="Invalid plugin signature - potential tampering detected",
                    context={"expected_hash": file_hash[:16]}  # 해시의 일부만 로그
                ))
                score = 0
            else:
                # 서명이 유효한 경우 보너스 점수
                score = min(100, score + 10)
        
        except Exception as e:
            logger.error(f"Enhanced signature verification failed: {str(e)}")
            threats.append(SecurityThreat(
                threat_type=ThreatType.SIGNATURE_INVALID,
                level=ThreatLevel.HIGH,
                description=f"Signature verification error: {str(e)}"
            ))
            score = 0
        
        is_valid = len(threats) == 0
        return ValidationResult(
            is_valid=is_valid, 
            threats=threats, 
            score=score,
            validation_time=time.time() - start_time
        )
    
    def _find_python_files(self, path: str) -> List[str]:
        """Python 파일 찾기"""
        python_files = []
        path_obj = Path(path)
        
        if path_obj.is_file() and path_obj.suffix == '.py':
            return [str(path_obj)]
        
        if path_obj.is_dir():
            for file_path in path_obj.rglob('*.py'):
                python_files.append(str(file_path))
        
        return python_files
    
    def _find_text_files(self, path: str) -> List[str]:
        """텍스트 파일 찾기"""
        text_files = []
        path_obj = Path(path)
        
        text_extensions = {'.py', '.txt', '.md', '.yml', '.yaml', '.json', '.sh', '.bat', '.ps1'}
        
        if path_obj.is_file():
            if path_obj.suffix in text_extensions:
                return [str(path_obj)]
            return []
        
        if path_obj.is_dir():
            for file_path in path_obj.rglob('*'):
                if file_path.is_file() and file_path.suffix in text_extensions:
                    text_files.append(str(file_path))
        
        return text_files
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        hasher = hashlib.sha256()
        
        path_obj = Path(file_path)
        if path_obj.is_file():
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        elif path_obj.is_dir():
            # 디렉토리의 모든 파일 해시
            for file_path in sorted(path_obj.rglob('*')):
                if file_path.is_file():
                    hasher.update(str(file_path).encode())
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def get_security_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자별 보안 요약 정보"""
        user_events = [e for e in self.security_events if e.get('user_id') == user_id]
        
        return {
            "user_id": user_id,
            "total_events": len(user_events),
            "recent_events": user_events[-10:],  # 최근 10개 이벤트
            "threat_summary": {
                "critical": len([e for e in user_events if e.get('severity') == 'critical']),
                "high": len([e for e in user_events if e.get('severity') == 'error']),
                "medium": len([e for e in user_events if e.get('severity') == 'warning']),
                "low": len([e for e in user_events if e.get('severity') == 'info'])
            },
            "rate_limit_status": self.rate_limit_manager.request_history.get(user_id, [])
        }