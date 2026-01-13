"""
Runtime Security Monitor

런타임 보안 모니터링 및 위협 탐지 시스템
"""
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import hashlib
import json
import re
import psutil
import time
from collections import defaultdict, deque

from backend.core.event_bus.validated_event_bus import ValidatedEventBus, EventType
from backend.services.plugins.enhanced_security_manager import (
    SecurityThreat, ThreatType, ThreatLevel, SecurityContext
)

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """행동 타입"""
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    ANOMALOUS = "anomalous"


class SecurityAction(Enum):
    """보안 액션"""
    ALLOW = "allow"
    MONITOR = "monitor"
    THROTTLE = "throttle"
    BLOCK = "block"
    QUARANTINE = "quarantine"


@dataclass
class BehaviorPattern:
    """행동 패턴"""
    pattern_id: str
    plugin_id: str
    user_id: str
    behavior_type: BehaviorType
    frequency: int
    last_seen: datetime
    risk_score: float  # 0-100
    indicators: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityIncident:
    """보안 사고"""
    incident_id: str
    threat_type: ThreatType
    severity: ThreatLevel
    plugin_id: str
    user_id: str
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "open"  # open, investigating, resolved
    actions_taken: List[str] = field(default_factory=list)


@dataclass
class RuntimeContext:
    """런타임 컨텍스트"""
    plugin_id: str
    user_id: str
    execution_id: str
    start_time: datetime
    resource_usage: Dict[str, float] = field(default_factory=dict)
    network_activity: List[Dict[str, Any]] = field(default_factory=list)
    file_operations: List[Dict[str, Any]] = field(default_factory=list)
    system_calls: List[str] = field(default_factory=list)


class BehaviorAnalyzer:
    """행동 분석기"""
    
    def __init__(self):
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}
        self.baseline_behaviors: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.anomaly_threshold = 0.7  # 70% 이상 차이시 이상으로 판단
    
    async def analyze_behavior(
        self, 
        plugin_id: str, 
        user_id: str,
        execution_context: RuntimeContext
    ) -> List[BehaviorPattern]:
        """행동 분석"""
        
        patterns = []
        
        # 리소스 사용 패턴 분석
        resource_pattern = await self._analyze_resource_usage(
            plugin_id, user_id, execution_context.resource_usage
        )
        if resource_pattern:
            patterns.append(resource_pattern)
        
        # 네트워크 활동 패턴 분석
        network_pattern = await self._analyze_network_activity(
            plugin_id, user_id, execution_context.network_activity
        )
        if network_pattern:
            patterns.append(network_pattern)
        
        # 파일 작업 패턴 분석
        file_pattern = await self._analyze_file_operations(
            plugin_id, user_id, execution_context.file_operations
        )
        if file_pattern:
            patterns.append(file_pattern)
        
        # 시스템 호출 패턴 분석
        syscall_pattern = await self._analyze_system_calls(
            plugin_id, user_id, execution_context.system_calls
        )
        if syscall_pattern:
            patterns.append(syscall_pattern)
        
        return patterns
    
    async def _analyze_resource_usage(
        self, 
        plugin_id: str, 
        user_id: str, 
        resource_usage: Dict[str, float]
    ) -> Optional[BehaviorPattern]:
        """리소스 사용 패턴 분석"""
        
        baseline_key = f"{plugin_id}:{user_id}"
        
        # 베이스라인 업데이트
        if baseline_key not in self.baseline_behaviors:
            self.baseline_behaviors[baseline_key]['resource'] = {
                'cpu_avg': 0.0,
                'memory_avg': 0.0,
                'samples': 0
            }
        
        baseline = self.baseline_behaviors[baseline_key]['resource']
        
        # 현재 사용량
        current_cpu = resource_usage.get('cpu_percent', 0.0)
        current_memory = resource_usage.get('memory_mb', 0.0)
        
        # 베이스라인과 비교
        cpu_deviation = abs(current_cpu - baseline['cpu_avg']) / max(baseline['cpu_avg'], 1.0)
        memory_deviation = abs(current_memory - baseline['memory_avg']) / max(baseline['memory_avg'], 1.0)
        
        # 이상 행동 탐지
        if cpu_deviation > self.anomaly_threshold or memory_deviation > self.anomaly_threshold:
            risk_score = min(100, (cpu_deviation + memory_deviation) * 50)
            
            behavior_type = BehaviorType.SUSPICIOUS if risk_score > 70 else BehaviorType.ANOMALOUS
            
            pattern = BehaviorPattern(
                pattern_id=f"resource_{plugin_id}_{user_id}_{int(time.time())}",
                plugin_id=plugin_id,
                user_id=user_id,
                behavior_type=behavior_type,
                frequency=1,
                last_seen=datetime.now(),
                risk_score=risk_score,
                indicators=[
                    f"CPU usage deviation: {cpu_deviation:.2f}",
                    f"Memory usage deviation: {memory_deviation:.2f}"
                ],
                context={
                    'current_cpu': current_cpu,
                    'baseline_cpu': baseline['cpu_avg'],
                    'current_memory': current_memory,
                    'baseline_memory': baseline['memory_avg']
                }
            )
            
            # 베이스라인 업데이트 (이상치 제외)
            if risk_score < 50:
                self._update_baseline(baseline, current_cpu, current_memory)
            
            return pattern
        
        # 정상 행동인 경우 베이스라인 업데이트
        self._update_baseline(baseline, current_cpu, current_memory)
        return None
    
    def _update_baseline(self, baseline: Dict[str, Any], cpu: float, memory: float):
        """베이스라인 업데이트"""
        samples = baseline['samples']
        baseline['cpu_avg'] = (baseline['cpu_avg'] * samples + cpu) / (samples + 1)
        baseline['memory_avg'] = (baseline['memory_avg'] * samples + memory) / (samples + 1)
        baseline['samples'] = min(samples + 1, 1000)  # 최대 1000개 샘플
    
    async def _analyze_network_activity(
        self, 
        plugin_id: str, 
        user_id: str, 
        network_activity: List[Dict[str, Any]]
    ) -> Optional[BehaviorPattern]:
        """네트워크 활동 패턴 분석"""
        
        if not network_activity:
            return None
        
        suspicious_indicators = []
        risk_score = 0.0
        
        for activity in network_activity:
            destination = activity.get('destination', '')
            port = activity.get('port', 0)
            protocol = activity.get('protocol', '')
            
            # 의심스러운 목적지 확인
            if self._is_suspicious_destination(destination):
                suspicious_indicators.append(f"Suspicious destination: {destination}")
                risk_score += 30
            
            # 의심스러운 포트 확인
            if self._is_suspicious_port(port):
                suspicious_indicators.append(f"Suspicious port: {port}")
                risk_score += 20
            
            # 비정상적인 프로토콜 확인
            if protocol not in ['HTTP', 'HTTPS', 'DNS']:
                suspicious_indicators.append(f"Unusual protocol: {protocol}")
                risk_score += 10
        
        if suspicious_indicators:
            behavior_type = BehaviorType.MALICIOUS if risk_score > 70 else BehaviorType.SUSPICIOUS
            
            return BehaviorPattern(
                pattern_id=f"network_{plugin_id}_{user_id}_{int(time.time())}",
                plugin_id=plugin_id,
                user_id=user_id,
                behavior_type=behavior_type,
                frequency=len(network_activity),
                last_seen=datetime.now(),
                risk_score=min(100, risk_score),
                indicators=suspicious_indicators,
                context={'network_activity': network_activity}
            )
        
        return None
    
    def _is_suspicious_destination(self, destination: str) -> bool:
        """의심스러운 목적지 확인"""
        suspicious_domains = [
            'tor2web.org', 'onion.to', 'pastebin.com',
            'bit.ly', 'tinyurl.com', 'raw.githubusercontent.com'
        ]
        
        # IP 주소 패턴 (사설 IP 제외)
        ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        if re.match(ip_pattern, destination):
            # 사설 IP 범위 확인
            if not (destination.startswith('192.168.') or 
                   destination.startswith('10.') or 
                   destination.startswith('172.')):
                return True
        
        return any(domain in destination.lower() for domain in suspicious_domains)
    
    def _is_suspicious_port(self, port: int) -> bool:
        """의심스러운 포트 확인"""
        # 일반적이지 않은 포트들
        suspicious_ports = {
            1337, 31337,  # 해커 포트
            4444, 5555,   # 백도어 포트
            6666, 6667,   # IRC
            9999,         # 일반적인 백도어
        }
        
        return port in suspicious_ports
    
    async def _analyze_file_operations(
        self, 
        plugin_id: str, 
        user_id: str, 
        file_operations: List[Dict[str, Any]]
    ) -> Optional[BehaviorPattern]:
        """파일 작업 패턴 분석"""
        
        if not file_operations:
            return None
        
        suspicious_indicators = []
        risk_score = 0.0
        
        for operation in file_operations:
            file_path = operation.get('path', '')
            operation_type = operation.get('type', '')
            
            # 시스템 파일 접근 확인
            if self._is_system_file_access(file_path):
                suspicious_indicators.append(f"System file access: {file_path}")
                risk_score += 40
            
            # 실행 파일 생성 확인
            if operation_type == 'create' and file_path.endswith(('.exe', '.bat', '.sh', '.py')):
                suspicious_indicators.append(f"Executable file creation: {file_path}")
                risk_score += 30
            
            # 대량 파일 삭제 확인
            if operation_type == 'delete':
                risk_score += 5
        
        # 대량 삭제 패턴 확인
        delete_count = sum(1 for op in file_operations if op.get('type') == 'delete')
        if delete_count > 10:
            suspicious_indicators.append(f"Mass file deletion: {delete_count} files")
            risk_score += 25
        
        if suspicious_indicators:
            behavior_type = BehaviorType.MALICIOUS if risk_score > 70 else BehaviorType.SUSPICIOUS
            
            return BehaviorPattern(
                pattern_id=f"file_{plugin_id}_{user_id}_{int(time.time())}",
                plugin_id=plugin_id,
                user_id=user_id,
                behavior_type=behavior_type,
                frequency=len(file_operations),
                last_seen=datetime.now(),
                risk_score=min(100, risk_score),
                indicators=suspicious_indicators,
                context={'file_operations': file_operations}
            )
        
        return None
    
    def _is_system_file_access(self, file_path: str) -> bool:
        """시스템 파일 접근 확인"""
        system_paths = [
            '/etc/', '/sys/', '/proc/', '/dev/',  # Linux
            'C:\\Windows\\', 'C:\\System32\\',    # Windows
            '/System/', '/Library/'               # macOS
        ]
        
        return any(file_path.startswith(path) for path in system_paths)
    
    async def _analyze_system_calls(
        self, 
        plugin_id: str, 
        user_id: str, 
        system_calls: List[str]
    ) -> Optional[BehaviorPattern]:
        """시스템 호출 패턴 분석"""
        
        if not system_calls:
            return None
        
        suspicious_indicators = []
        risk_score = 0.0
        
        # 위험한 시스템 호출 확인
        dangerous_calls = {
            'execve', 'fork', 'clone',     # 프로세스 생성
            'ptrace',                      # 디버깅
            'mount', 'umount',             # 파일시스템 조작
            'setuid', 'setgid',            # 권한 변경
            'socket', 'bind', 'connect'    # 네트워크
        }
        
        for call in system_calls:
            if call in dangerous_calls:
                suspicious_indicators.append(f"Dangerous system call: {call}")
                risk_score += 15
        
        # 시스템 호출 빈도 분석
        call_frequency = len(system_calls)
        if call_frequency > 100:  # 100회 이상
            suspicious_indicators.append(f"High system call frequency: {call_frequency}")
            risk_score += 20
        
        if suspicious_indicators:
            behavior_type = BehaviorType.MALICIOUS if risk_score > 70 else BehaviorType.SUSPICIOUS
            
            return BehaviorPattern(
                pattern_id=f"syscall_{plugin_id}_{user_id}_{int(time.time())}",
                plugin_id=plugin_id,
                user_id=user_id,
                behavior_type=behavior_type,
                frequency=call_frequency,
                last_seen=datetime.now(),
                risk_score=min(100, risk_score),
                indicators=suspicious_indicators,
                context={'system_calls': system_calls}
            )
        
        return None


class RuntimeThreatDetector:
    """런타임 위협 탐지기"""
    
    def __init__(self):
        self.threat_signatures = self._load_threat_signatures()
        self.active_threats: Dict[str, SecurityThreat] = {}
    
    def _load_threat_signatures(self) -> Dict[str, Dict[str, Any]]:
        """위협 시그니처 로드"""
        return {
            'crypto_mining': {
                'indicators': ['mining', 'hashrate', 'cryptocurrency', 'bitcoin'],
                'cpu_threshold': 80.0,
                'network_patterns': ['stratum+tcp', 'mining.pool']
            },
            'data_exfiltration': {
                'indicators': ['upload', 'transfer', 'send', 'export'],
                'network_threshold': 1024 * 1024,  # 1MB
                'file_patterns': ['.zip', '.tar', '.gz']
            },
            'privilege_escalation': {
                'indicators': ['sudo', 'admin', 'root', 'administrator'],
                'system_calls': ['setuid', 'setgid', 'chmod']
            },
            'backdoor_installation': {
                'indicators': ['backdoor', 'shell', 'remote', 'access'],
                'file_patterns': ['.exe', '.bat', '.sh'],
                'network_ports': [4444, 5555, 31337]
            }
        }
    
    async def scan_runtime_threats(
        self, 
        plugin_id: str, 
        execution_context: RuntimeContext
    ) -> List[SecurityThreat]:
        """런타임 위협 스캔"""
        
        threats = []
        
        # 각 위협 타입별 스캔
        for threat_name, signature in self.threat_signatures.items():
            threat = await self._scan_specific_threat(
                threat_name, signature, plugin_id, execution_context
            )
            if threat:
                threats.append(threat)
        
        return threats
    
    async def _scan_specific_threat(
        self, 
        threat_name: str, 
        signature: Dict[str, Any], 
        plugin_id: str, 
        execution_context: RuntimeContext
    ) -> Optional[SecurityThreat]:
        """특정 위협 스캔"""
        
        indicators_found = []
        risk_score = 0.0
        
        # 텍스트 기반 지표 확인
        text_indicators = signature.get('indicators', [])
        context_text = json.dumps(execution_context.__dict__, default=str).lower()
        
        for indicator in text_indicators:
            if indicator in context_text:
                indicators_found.append(f"Text indicator: {indicator}")
                risk_score += 20
        
        # CPU 사용량 확인
        cpu_threshold = signature.get('cpu_threshold')
        if cpu_threshold:
            current_cpu = execution_context.resource_usage.get('cpu_percent', 0.0)
            if current_cpu > cpu_threshold:
                indicators_found.append(f"High CPU usage: {current_cpu}%")
                risk_score += 30
        
        # 네트워크 패턴 확인
        network_patterns = signature.get('network_patterns', [])
        for activity in execution_context.network_activity:
            destination = activity.get('destination', '').lower()
            for pattern in network_patterns:
                if pattern in destination:
                    indicators_found.append(f"Network pattern: {pattern}")
                    risk_score += 25
        
        # 파일 패턴 확인
        file_patterns = signature.get('file_patterns', [])
        for operation in execution_context.file_operations:
            file_path = operation.get('path', '').lower()
            for pattern in file_patterns:
                if file_path.endswith(pattern):
                    indicators_found.append(f"File pattern: {pattern}")
                    risk_score += 15
        
        # 시스템 호출 확인
        dangerous_syscalls = signature.get('system_calls', [])
        for syscall in execution_context.system_calls:
            if syscall in dangerous_syscalls:
                indicators_found.append(f"Dangerous syscall: {syscall}")
                risk_score += 25
        
        # 네트워크 포트 확인
        suspicious_ports = signature.get('network_ports', [])
        for activity in execution_context.network_activity:
            port = activity.get('port', 0)
            if port in suspicious_ports:
                indicators_found.append(f"Suspicious port: {port}")
                risk_score += 30
        
        # 위협 생성
        if indicators_found and risk_score > 50:
            threat_level = ThreatLevel.CRITICAL if risk_score > 80 else ThreatLevel.HIGH
            
            return SecurityThreat(
                threat_type=ThreatType.MALICIOUS_CODE,
                level=threat_level,
                description=f"Runtime threat detected: {threat_name}",
                context={
                    'threat_name': threat_name,
                    'indicators_found': indicators_found,
                    'risk_score': risk_score,
                    'plugin_id': plugin_id,
                    'execution_context': execution_context.__dict__
                }
            )
        
        return None


class RuntimeSecurityMonitor:
    """런타임 보안 모니터"""
    
    def __init__(self, event_bus: ValidatedEventBus):
        self.event_bus = event_bus
        self.behavior_analyzer = BehaviorAnalyzer()
        self.threat_detector = RuntimeThreatDetector()
        
        # 보안 사고 관리
        self.security_incidents: Dict[str, SecurityIncident] = {}
        self.incident_counter = 0
        
        # 모니터링 상태
        self.active_contexts: Dict[str, RuntimeContext] = {}
        self.monitoring_enabled = True
        
        # 자동 대응 규칙
        self.auto_response_rules = {
            ThreatLevel.CRITICAL: SecurityAction.QUARANTINE,
            ThreatLevel.HIGH: SecurityAction.BLOCK,
            ThreatLevel.MEDIUM: SecurityAction.THROTTLE,
            ThreatLevel.LOW: SecurityAction.MONITOR
        }
        
        # 보안 이벤트 콜백
        self.security_callbacks: List[Callable] = []
    
    async def start_monitoring_session(
        self, 
        plugin_id: str, 
        user_id: str, 
        execution_id: str
    ) -> RuntimeContext:
        """모니터링 세션 시작"""
        
        context = RuntimeContext(
            plugin_id=plugin_id,
            user_id=user_id,
            execution_id=execution_id,
            start_time=datetime.now()
        )
        
        self.active_contexts[execution_id] = context
        
        # 모니터링 시작 이벤트
        await self.event_bus.publish(
            'runtime_monitoring_started',
            {
                'plugin_id': plugin_id,
                'user_id': user_id,
                'execution_id': execution_id,
                'timestamp': context.start_time.isoformat()
            },
            source='runtime_security_monitor'
        )
        
        return context
    
    async def update_runtime_context(
        self, 
        execution_id: str, 
        resource_usage: Optional[Dict[str, float]] = None,
        network_activity: Optional[List[Dict[str, Any]]] = None,
        file_operations: Optional[List[Dict[str, Any]]] = None,
        system_calls: Optional[List[str]] = None
    ):
        """런타임 컨텍스트 업데이트"""
        
        if execution_id not in self.active_contexts:
            return
        
        context = self.active_contexts[execution_id]
        
        if resource_usage:
            context.resource_usage.update(resource_usage)
        
        if network_activity:
            context.network_activity.extend(network_activity)
        
        if file_operations:
            context.file_operations.extend(file_operations)
        
        if system_calls:
            context.system_calls.extend(system_calls)
    
    async def analyze_runtime_security(self, execution_id: str) -> Dict[str, Any]:
        """런타임 보안 분석"""
        
        if execution_id not in self.active_contexts:
            return {'error': 'Context not found'}
        
        context = self.active_contexts[execution_id]
        
        # 행동 분석
        behavior_patterns = await self.behavior_analyzer.analyze_behavior(
            context.plugin_id, context.user_id, context
        )
        
        # 위협 탐지
        threats = await self.threat_detector.scan_runtime_threats(
            context.plugin_id, context
        )
        
        # 보안 사고 생성 및 대응
        incidents = []
        for threat in threats:
            incident = await self._create_security_incident(threat, context)
            incidents.append(incident)
            
            # 자동 대응
            await self._execute_security_response(threat, context)
        
        # 결과 반환
        analysis_result = {
            'execution_id': execution_id,
            'plugin_id': context.plugin_id,
            'user_id': context.user_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'behavior_patterns': [
                {
                    'pattern_id': p.pattern_id,
                    'behavior_type': p.behavior_type.value,
                    'risk_score': p.risk_score,
                    'indicators': p.indicators
                }
                for p in behavior_patterns
            ],
            'threats': [
                {
                    'threat_type': t.threat_type.value,
                    'level': t.level.value,
                    'description': t.description,
                    'context': t.context
                }
                for t in threats
            ],
            'incidents': [
                {
                    'incident_id': i.incident_id,
                    'severity': i.severity.value,
                    'description': i.description,
                    'status': i.status
                }
                for i in incidents
            ]
        }
        
        # 보안 이벤트 발행
        await self.event_bus.publish(
            EventType.SECURITY_ALERT,
            analysis_result,
            source='runtime_security_monitor'
        )
        
        return analysis_result
    
    async def _create_security_incident(
        self, 
        threat: SecurityThreat, 
        context: RuntimeContext
    ) -> SecurityIncident:
        """보안 사고 생성"""
        
        self.incident_counter += 1
        incident_id = f"SEC-{datetime.now().strftime('%Y%m%d')}-{self.incident_counter:04d}"
        
        incident = SecurityIncident(
            incident_id=incident_id,
            threat_type=threat.threat_type,
            severity=threat.level,
            plugin_id=context.plugin_id,
            user_id=context.user_id,
            description=threat.description,
            evidence={
                'threat_context': threat.context,
                'runtime_context': {
                    'execution_id': context.execution_id,
                    'start_time': context.start_time.isoformat(),
                    'resource_usage': context.resource_usage,
                    'network_activity_count': len(context.network_activity),
                    'file_operations_count': len(context.file_operations),
                    'system_calls_count': len(context.system_calls)
                }
            }
        )
        
        self.security_incidents[incident_id] = incident
        
        return incident
    
    async def _execute_security_response(
        self, 
        threat: SecurityThreat, 
        context: RuntimeContext
    ):
        """보안 대응 실행"""
        
        action = self.auto_response_rules.get(threat.level, SecurityAction.MONITOR)
        
        response_data = {
            'action': action.value,
            'threat_level': threat.level.value,
            'plugin_id': context.plugin_id,
            'user_id': context.user_id,
            'execution_id': context.execution_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if action == SecurityAction.QUARANTINE:
            # 플러그인 격리
            await self._quarantine_plugin(context.plugin_id, context.user_id)
            response_data['details'] = 'Plugin quarantined due to critical threat'
            
        elif action == SecurityAction.BLOCK:
            # 실행 차단
            await self._block_execution(context.execution_id)
            response_data['details'] = 'Execution blocked due to high threat'
            
        elif action == SecurityAction.THROTTLE:
            # 실행 제한
            await self._throttle_execution(context.plugin_id, context.user_id)
            response_data['details'] = 'Execution throttled due to medium threat'
            
        # 보안 대응 이벤트 발행
        await self.event_bus.publish(
            'security_response_executed',
            response_data,
            source='runtime_security_monitor'
        )
        
        # 콜백 실행
        for callback in self.security_callbacks:
            try:
                await callback(threat, context, action)
            except Exception as e:
                logger.error(f"Security callback error: {e}")
    
    async def _quarantine_plugin(self, plugin_id: str, user_id: str):
        """플러그인 격리"""
        logger.warning(f"Quarantining plugin {plugin_id} for user {user_id}")
        # 실제 구현에서는 플러그인 비활성화 로직 추가
    
    async def _block_execution(self, execution_id: str):
        """실행 차단"""
        logger.warning(f"Blocking execution {execution_id}")
        # 실제 구현에서는 실행 중단 로직 추가
    
    async def _throttle_execution(self, plugin_id: str, user_id: str):
        """실행 제한"""
        logger.info(f"Throttling execution for plugin {plugin_id}, user {user_id}")
        # 실제 구현에서는 속도 제한 로직 추가
    
    async def end_monitoring_session(self, execution_id: str) -> Dict[str, Any]:
        """모니터링 세션 종료"""
        
        if execution_id not in self.active_contexts:
            return {'error': 'Context not found'}
        
        context = self.active_contexts[execution_id]
        
        # 최종 분석
        final_analysis = await self.analyze_runtime_security(execution_id)
        
        # 세션 정리
        del self.active_contexts[execution_id]
        
        # 종료 이벤트
        await self.event_bus.publish(
            'runtime_monitoring_ended',
            {
                'execution_id': execution_id,
                'plugin_id': context.plugin_id,
                'user_id': context.user_id,
                'duration_seconds': (datetime.now() - context.start_time).total_seconds(),
                'final_analysis': final_analysis
            },
            source='runtime_security_monitor'
        )
        
        return final_analysis
    
    def add_security_callback(self, callback: Callable):
        """보안 콜백 추가"""
        self.security_callbacks.append(callback)
    
    def get_security_incidents(
        self, 
        status: Optional[str] = None,
        severity: Optional[ThreatLevel] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """보안 사고 조회"""
        
        incidents = list(self.security_incidents.values())
        
        # 필터링
        if status:
            incidents = [i for i in incidents if i.status == status]
        
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        
        # 최신순 정렬 및 제한
        incidents.sort(key=lambda x: x.timestamp, reverse=True)
        incidents = incidents[:limit]
        
        return [
            {
                'incident_id': i.incident_id,
                'threat_type': i.threat_type.value,
                'severity': i.severity.value,
                'plugin_id': i.plugin_id,
                'user_id': i.user_id,
                'description': i.description,
                'timestamp': i.timestamp.isoformat(),
                'status': i.status,
                'actions_taken': i.actions_taken
            }
            for i in incidents
        ]
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """모니터링 통계"""
        
        total_incidents = len(self.security_incidents)
        active_sessions = len(self.active_contexts)
        
        # 심각도별 통계
        severity_stats = defaultdict(int)
        for incident in self.security_incidents.values():
            severity_stats[incident.severity.value] += 1
        
        # 플러그인별 통계
        plugin_stats = defaultdict(int)
        for incident in self.security_incidents.values():
            plugin_stats[incident.plugin_id] += 1
        
        return {
            'monitoring_enabled': self.monitoring_enabled,
            'active_sessions': active_sessions,
            'total_incidents': total_incidents,
            'severity_distribution': dict(severity_stats),
            'top_risky_plugins': dict(sorted(
                plugin_stats.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),
            'auto_response_rules': {
                level.value: action.value 
                for level, action in self.auto_response_rules.items()
            }
        }