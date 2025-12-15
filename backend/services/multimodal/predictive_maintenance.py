"""
Predictive Maintenance & Self-Healing System
예측 유지보수 및 자가 치유 시스템 - Phase 5-4 구현
"""

import asyncio
import json
import uuid
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from collections import defaultdict, deque
import pickle
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib

from backend.services.multimodal.advanced_orchestrator import AdvancedMultiAgentOrchestrator
from backend.services.multimodal.workflow_optimizer import IntelligentWorkflowOptimizer
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class HealthStatus(Enum):
    """시스템 건강 상태"""
    HEALTHY = "healthy"           # 정상
    WARNING = "warning"           # 경고
    CRITICAL = "critical"         # 위험
    DEGRADED = "degraded"         # 성능 저하
    MAINTENANCE = "maintenance"   # 유지보수 중
    FAILED = "failed"            # 실패

class AnomalyType(Enum):
    """이상 징후 유형"""
    PERFORMANCE_DEGRADATION = "performance_degradation"    # 성능 저하
    RESOURCE_EXHAUSTION = "resource_exhaustion"           # 리소스 고갈
    ERROR_SPIKE = "error_spike"                          # 오류 급증
    LATENCY_INCREASE = "latency_increase"                # 지연 시간 증가
    THROUGHPUT_DROP = "throughput_drop"                  # 처리량 감소
    MEMORY_LEAK = "memory_leak"                          # 메모리 누수
    CONNECTION_ISSUES = "connection_issues"               # 연결 문제
    CAPACITY_LIMIT = "capacity_limit"                    # 용량 한계

class MaintenanceAction(Enum):
    """유지보수 작업"""
    RESTART_SERVICE = "restart_service"           # 서비스 재시작
    SCALE_UP = "scale_up"                        # 스케일 업
    SCALE_DOWN = "scale_down"                    # 스케일 다운
    CLEAR_CACHE = "clear_cache"                  # 캐시 정리
    OPTIMIZE_MEMORY = "optimize_memory"          # 메모리 최적화
    REBALANCE_LOAD = "rebalance_load"           # 부하 재분산
    UPDATE_CONFIG = "update_config"              # 설정 업데이트
    FAILOVER = "failover"                        # 장애 조치

@dataclass
class SystemMetrics:
    """시스템 메트릭"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    active_connections: int
    response_time: float
    throughput: float
    error_rate: float
    queue_length: int
    agent_count: int
    execution_success_rate: float

@dataclass
class AnomalyAlert:
    """이상 징후 알림"""
    alert_id: str
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    description: str
    affected_components: List[str]
    metrics: Dict[str, float]
    predicted_impact: Dict[str, Any]
    recommended_actions: List[MaintenanceAction]
    confidence_score: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MaintenanceTask:
    """유지보수 작업"""
    task_id: str
    action: MaintenanceAction
    target_component: str
    priority: str  # low, medium, high, urgent
    estimated_duration: float
    success_probability: float
    rollback_plan: Optional[str]
    dependencies: List[str]
    scheduled_time: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed

@dataclass
class HealthReport:
    """시스템 건강 보고서"""
    report_id: str
    overall_status: HealthStatus
    component_status: Dict[str, HealthStatus]
    active_anomalies: List[AnomalyAlert]
    maintenance_recommendations: List[MaintenanceTask]
    performance_trends: Dict[str, List[float]]
    capacity_forecast: Dict[str, float]
    risk_assessment: Dict[str, float]
    generated_at: datetime = field(default_factory=datetime.now)

class PredictiveMaintenanceSystem:
    """예측 유지보수 시스템"""
    
    def __init__(self, orchestrator: AdvancedMultiAgentOrchestrator, optimizer: IntelligentWorkflowOptimizer):
        self.orchestrator = orchestrator
        self.optimizer = optimizer
        
        # 메트릭 저장소
        self.metrics_history: deque = deque(maxlen=10000)
        self.anomaly_history: List[AnomalyAlert] = []
        self.maintenance_history: List[MaintenanceTask] = []
        
        # ML 모델
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.failure_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        # 시스템 설정
        self.monitoring_config = {
            "collection_interval": 30,  # 초
            "anomaly_threshold": 0.8,
            "prediction_window": 3600,  # 1시간
            "maintenance_window": 7200,  # 2시간
            "auto_healing_enabled": True,
            "max_concurrent_maintenance": 3
        }
        
        # 컴포넌트 상태
        self.component_health: Dict[str, HealthStatus] = {}
        self.active_maintenance: Dict[str, MaintenanceTask] = {}
        
        # 모니터링 시작
        self._initialize_monitoring()
        
        logger.info("Predictive Maintenance System initialized")
    
    def _initialize_monitoring(self):
        """모니터링 초기화"""
        # 컴포넌트 초기 상태 설정
        components = [
            "orchestrator", "optimizer", "database", "redis", "milvus",
            "api_gateway", "load_balancer", "file_system", "network"
        ]
        
        for component in components:
            self.component_health[component] = HealthStatus.HEALTHY
        
        # 백그라운드 모니터링 시작
        asyncio.create_task(self._start_monitoring_loop())
    
    async def _start_monitoring_loop(self):
        """모니터링 루프 시작"""
        while True:
            try:
                # 시스템 메트릭 수집
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # 이상 징후 탐지
                anomalies = await self._detect_anomalies(metrics)
                
                # 예측 유지보수 계획
                maintenance_tasks = await self._plan_predictive_maintenance(metrics, anomalies)
                
                # 자가 치유 실행
                if self.monitoring_config["auto_healing_enabled"]:
                    await self._execute_self_healing(anomalies, maintenance_tasks)
                
                # 대기
                await asyncio.sleep(self.monitoring_config["collection_interval"])
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # 오류 시 1분 대기
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집"""
        try:
            # 실제 시스템 메트릭 수집 (시뮬레이션)
            import psutil
            import random
            
            # CPU 및 메모리 사용률
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 네트워크 I/O
            network = psutil.net_io_counters()
            network_io = (network.bytes_sent + network.bytes_recv) / 1024 / 1024  # MB
            
            # 오케스트레이터 메트릭
            agent_count = len(self.orchestrator.agents)
            active_executions = len(self.orchestrator.active_executions)
            
            # 성능 메트릭 (시뮬레이션)
            response_time = random.uniform(50, 200)  # ms
            throughput = random.uniform(100, 1000)   # requests/min
            error_rate = random.uniform(0, 0.05)     # 0-5%
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io=network_io,
                active_connections=active_executions,
                response_time=response_time,
                throughput=throughput,
                error_rate=error_rate,
                queue_length=len(self.orchestrator.task_queue),
                agent_count=agent_count,
                execution_success_rate=random.uniform(0.9, 1.0)
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")
            # 기본값 반환
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=50.0, memory_usage=60.0, disk_usage=30.0,
                network_io=10.0, active_connections=5, response_time=100.0,
                throughput=500.0, error_rate=0.01, queue_length=2,
                agent_count=5, execution_success_rate=0.95
            )
    
    async def _detect_anomalies(self, current_metrics: SystemMetrics) -> List[AnomalyAlert]:
        """이상 징후 탐지"""
        anomalies = []
        
        try:
            # 충분한 히스토리가 있는 경우에만 ML 기반 탐지
            if len(self.metrics_history) >= 50:
                anomalies.extend(await self._ml_anomaly_detection(current_metrics))
            
            # 규칙 기반 이상 징후 탐지
            anomalies.extend(await self._rule_based_anomaly_detection(current_metrics))
            
            # 트렌드 기반 이상 징후 탐지
            anomalies.extend(await self._trend_based_anomaly_detection(current_metrics))
            
            # 중복 제거 및 우선순위 정렬
            unique_anomalies = self._deduplicate_anomalies(anomalies)
            
            # 이상 징후 히스토리에 추가
            self.anomaly_history.extend(unique_anomalies)
            
            return unique_anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}", exc_info=True)
            return []
    
    async def _ml_anomaly_detection(self, current_metrics: SystemMetrics) -> List[AnomalyAlert]:
        """ML 기반 이상 징후 탐지"""
        anomalies = []
        
        try:
            # 특성 벡터 생성
            features = self._extract_features_from_metrics(list(self.metrics_history))
            current_features = self._extract_features_from_metrics([current_metrics])
            
            if len(features) < 10:
                return anomalies
            
            # 이상 징후 탐지 모델 훈련
            features_scaled = self.scaler.fit_transform(features)
            self.anomaly_detector.fit(features_scaled)
            
            # 현재 메트릭 이상 여부 확인
            current_scaled = self.scaler.transform(current_features)
            anomaly_score = self.anomaly_detector.decision_function(current_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(current_scaled)[0] == -1
            
            if is_anomaly and abs(anomaly_score) > self.monitoring_config["anomaly_threshold"]:
                # 이상 유형 분류
                anomaly_type = self._classify_anomaly_type(current_metrics)
                
                anomaly = AnomalyAlert(
                    alert_id=f"ml_anomaly_{uuid.uuid4().hex[:8]}",
                    anomaly_type=anomaly_type,
                    severity=self._calculate_severity(abs(anomaly_score)),
                    description=f"ML 모델이 {anomaly_type.value} 이상 징후를 탐지했습니다",
                    affected_components=self._identify_affected_components(current_metrics),
                    metrics=self._extract_relevant_metrics(current_metrics),
                    predicted_impact={"performance_degradation": abs(anomaly_score) * 0.3},
                    recommended_actions=self._get_recommended_actions(anomaly_type),
                    confidence_score=abs(anomaly_score)
                )
                
                anomalies.append(anomaly)
            
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {str(e)}")
        
        return anomalies
    
    async def _rule_based_anomaly_detection(self, metrics: SystemMetrics) -> List[AnomalyAlert]:
        """규칙 기반 이상 징후 탐지"""
        anomalies = []
        
        # CPU 사용률 이상
        if metrics.cpu_usage > 90:
            anomalies.append(AnomalyAlert(
                alert_id=f"cpu_high_{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.RESOURCE_EXHAUSTION,
                severity="critical" if metrics.cpu_usage > 95 else "high",
                description=f"CPU 사용률이 {metrics.cpu_usage:.1f}%로 높습니다",
                affected_components=["orchestrator", "api_gateway"],
                metrics={"cpu_usage": metrics.cpu_usage},
                predicted_impact={"response_time_increase": 0.5, "throughput_decrease": 0.3},
                recommended_actions=[MaintenanceAction.SCALE_UP, MaintenanceAction.REBALANCE_LOAD],
                confidence_score=0.9
            ))
        
        # 메모리 사용률 이상
        if metrics.memory_usage > 85:
            anomalies.append(AnomalyAlert(
                alert_id=f"memory_high_{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.MEMORY_LEAK,
                severity="critical" if metrics.memory_usage > 95 else "high",
                description=f"메모리 사용률이 {metrics.memory_usage:.1f}%로 높습니다",
                affected_components=["database", "redis", "milvus"],
                metrics={"memory_usage": metrics.memory_usage},
                predicted_impact={"system_crash_risk": 0.4, "performance_degradation": 0.6},
                recommended_actions=[MaintenanceAction.OPTIMIZE_MEMORY, MaintenanceAction.CLEAR_CACHE],
                confidence_score=0.95
            ))
        
        # 응답 시간 이상
        if metrics.response_time > 1000:  # 1초 이상
            anomalies.append(AnomalyAlert(
                alert_id=f"latency_high_{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.LATENCY_INCREASE,
                severity="medium" if metrics.response_time < 2000 else "high",
                description=f"응답 시간이 {metrics.response_time:.0f}ms로 증가했습니다",
                affected_components=["api_gateway", "load_balancer"],
                metrics={"response_time": metrics.response_time},
                predicted_impact={"user_experience_degradation": 0.7},
                recommended_actions=[MaintenanceAction.REBALANCE_LOAD, MaintenanceAction.SCALE_UP],
                confidence_score=0.8
            ))
        
        # 오류율 이상
        if metrics.error_rate > 0.05:  # 5% 이상
            anomalies.append(AnomalyAlert(
                alert_id=f"error_spike_{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.ERROR_SPIKE,
                severity="high" if metrics.error_rate > 0.1 else "medium",
                description=f"오류율이 {metrics.error_rate*100:.1f}%로 증가했습니다",
                affected_components=["orchestrator", "database"],
                metrics={"error_rate": metrics.error_rate},
                predicted_impact={"service_reliability": 0.8},
                recommended_actions=[MaintenanceAction.RESTART_SERVICE, MaintenanceAction.UPDATE_CONFIG],
                confidence_score=0.85
            ))
        
        return anomalies
    
    async def _trend_based_anomaly_detection(self, current_metrics: SystemMetrics) -> List[AnomalyAlert]:
        """트렌드 기반 이상 징후 탐지"""
        anomalies = []
        
        if len(self.metrics_history) < 10:
            return anomalies
        
        try:
            # 최근 메트릭 트렌드 분석
            recent_metrics = list(self.metrics_history)[-10:]
            
            # CPU 사용률 트렌드
            cpu_trend = [m.cpu_usage for m in recent_metrics]
            if self._is_increasing_trend(cpu_trend, threshold=0.1):
                anomalies.append(AnomalyAlert(
                    alert_id=f"cpu_trend_{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION,
                    severity="medium",
                    description="CPU 사용률이 지속적으로 증가하고 있습니다",
                    affected_components=["orchestrator"],
                    metrics={"cpu_trend": np.mean(np.diff(cpu_trend))},
                    predicted_impact={"future_overload": 0.6},
                    recommended_actions=[MaintenanceAction.SCALE_UP],
                    confidence_score=0.7
                ))
            
            # 메모리 사용률 트렌드
            memory_trend = [m.memory_usage for m in recent_metrics]
            if self._is_increasing_trend(memory_trend, threshold=0.05):
                anomalies.append(AnomalyAlert(
                    alert_id=f"memory_trend_{uuid.uuid4().hex[:8]}",
                    anomaly_type=AnomalyType.MEMORY_LEAK,
                    severity="medium",
                    description="메모리 사용률이 지속적으로 증가하고 있습니다 (메모리 누수 의심)",
                    affected_components=["database", "redis"],
                    metrics={"memory_trend": np.mean(np.diff(memory_trend))},
                    predicted_impact={"memory_exhaustion": 0.5},
                    recommended_actions=[MaintenanceAction.OPTIMIZE_MEMORY, MaintenanceAction.RESTART_SERVICE],
                    confidence_score=0.75
                ))
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {str(e)}")
        
        return anomalies
    
    def _is_increasing_trend(self, values: List[float], threshold: float = 0.1) -> bool:
        """증가 트렌드 확인"""
        if len(values) < 3:
            return False
        
        diffs = np.diff(values)
        positive_diffs = [d for d in diffs if d > 0]
        
        return len(positive_diffs) > len(diffs) * 0.7 and np.mean(positive_diffs) > threshold
    
    def _extract_features_from_metrics(self, metrics_list: List[SystemMetrics]) -> np.ndarray:
        """메트릭에서 특성 추출"""
        features = []
        
        for metrics in metrics_list:
            feature_vector = [
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.disk_usage,
                metrics.network_io,
                metrics.active_connections,
                metrics.response_time,
                metrics.throughput,
                metrics.error_rate,
                metrics.queue_length,
                metrics.agent_count,
                metrics.execution_success_rate
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def _classify_anomaly_type(self, metrics: SystemMetrics) -> AnomalyType:
        """이상 유형 분류"""
        if metrics.cpu_usage > 90 or metrics.memory_usage > 90:
            return AnomalyType.RESOURCE_EXHAUSTION
        elif metrics.response_time > 1000:
            return AnomalyType.LATENCY_INCREASE
        elif metrics.error_rate > 0.05:
            return AnomalyType.ERROR_SPIKE
        elif metrics.throughput < 100:
            return AnomalyType.THROUGHPUT_DROP
        else:
            return AnomalyType.PERFORMANCE_DEGRADATION
    
    def _calculate_severity(self, anomaly_score: float) -> str:
        """심각도 계산"""
        if anomaly_score > 0.9:
            return "critical"
        elif anomaly_score > 0.7:
            return "high"
        elif anomaly_score > 0.5:
            return "medium"
        else:
            return "low"
    
    def _identify_affected_components(self, metrics: SystemMetrics) -> List[str]:
        """영향받는 컴포넌트 식별"""
        affected = []
        
        if metrics.cpu_usage > 80:
            affected.extend(["orchestrator", "api_gateway"])
        if metrics.memory_usage > 80:
            affected.extend(["database", "redis", "milvus"])
        if metrics.response_time > 500:
            affected.extend(["load_balancer", "network"])
        if metrics.error_rate > 0.02:
            affected.extend(["orchestrator", "database"])
        
        return list(set(affected))
    
    def _extract_relevant_metrics(self, metrics: SystemMetrics) -> Dict[str, float]:
        """관련 메트릭 추출"""
        return {
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "response_time": metrics.response_time,
            "error_rate": metrics.error_rate,
            "throughput": metrics.throughput
        }
    
    def _get_recommended_actions(self, anomaly_type: AnomalyType) -> List[MaintenanceAction]:
        """권장 조치 반환"""
        action_map = {
            AnomalyType.RESOURCE_EXHAUSTION: [MaintenanceAction.SCALE_UP, MaintenanceAction.OPTIMIZE_MEMORY],
            AnomalyType.LATENCY_INCREASE: [MaintenanceAction.REBALANCE_LOAD, MaintenanceAction.SCALE_UP],
            AnomalyType.ERROR_SPIKE: [MaintenanceAction.RESTART_SERVICE, MaintenanceAction.UPDATE_CONFIG],
            AnomalyType.THROUGHPUT_DROP: [MaintenanceAction.SCALE_UP, MaintenanceAction.REBALANCE_LOAD],
            AnomalyType.MEMORY_LEAK: [MaintenanceAction.RESTART_SERVICE, MaintenanceAction.OPTIMIZE_MEMORY],
            AnomalyType.PERFORMANCE_DEGRADATION: [MaintenanceAction.OPTIMIZE_MEMORY, MaintenanceAction.CLEAR_CACHE]
        }
        
        return action_map.get(anomaly_type, [MaintenanceAction.RESTART_SERVICE])
    
    def _deduplicate_anomalies(self, anomalies: List[AnomalyAlert]) -> List[AnomalyAlert]:
        """이상 징후 중복 제거"""
        unique_anomalies = []
        seen_types = set()
        
        # 심각도 순으로 정렬
        sorted_anomalies = sorted(anomalies, key=lambda x: {
            "critical": 4, "high": 3, "medium": 2, "low": 1
        }.get(x.severity, 0), reverse=True)
        
        for anomaly in sorted_anomalies:
            if anomaly.anomaly_type not in seen_types:
                unique_anomalies.append(anomaly)
                seen_types.add(anomaly.anomaly_type)
        
        return unique_anomalies
    
    async def _plan_predictive_maintenance(
        self,
        current_metrics: SystemMetrics,
        anomalies: List[AnomalyAlert]
    ) -> List[MaintenanceTask]:
        """예측 유지보수 계획"""
        maintenance_tasks = []
        
        try:
            # 이상 징후 기반 유지보수 작업 생성
            for anomaly in anomalies:
                for action in anomaly.recommended_actions:
                    task = MaintenanceTask(
                        task_id=f"maint_{action.value}_{uuid.uuid4().hex[:8]}",
                        action=action,
                        target_component=anomaly.affected_components[0] if anomaly.affected_components else "system",
                        priority=self._map_severity_to_priority(anomaly.severity),
                        estimated_duration=self._estimate_maintenance_duration(action),
                        success_probability=self._estimate_success_probability(action, anomaly),
                        rollback_plan=self._create_rollback_plan(action),
                        dependencies=self._get_maintenance_dependencies(action),
                        scheduled_time=self._calculate_optimal_maintenance_time(anomaly.severity)
                    )
                    maintenance_tasks.append(task)
            
            # 예방적 유지보수 작업 추가
            preventive_tasks = await self._generate_preventive_maintenance(current_metrics)
            maintenance_tasks.extend(preventive_tasks)
            
            # 작업 우선순위 정렬 및 충돌 해결
            optimized_tasks = self._optimize_maintenance_schedule(maintenance_tasks)
            
            return optimized_tasks
            
        except Exception as e:
            logger.error(f"Maintenance planning failed: {str(e)}", exc_info=True)
            return []
    
    async def _generate_preventive_maintenance(self, metrics: SystemMetrics) -> List[MaintenanceTask]:
        """예방적 유지보수 작업 생성"""
        preventive_tasks = []
        
        # 메모리 사용률이 70% 이상이면 캐시 정리 예약
        if metrics.memory_usage > 70:
            preventive_tasks.append(MaintenanceTask(
                task_id=f"preventive_cache_{uuid.uuid4().hex[:8]}",
                action=MaintenanceAction.CLEAR_CACHE,
                target_component="redis",
                priority="low",
                estimated_duration=300,  # 5분
                success_probability=0.95,
                rollback_plan="캐시 정리는 롤백이 필요하지 않습니다",
                dependencies=[],
                scheduled_time=datetime.now() + timedelta(hours=2)
            ))
        
        # 디스크 사용률이 80% 이상이면 정리 작업 예약
        if metrics.disk_usage > 80:
            preventive_tasks.append(MaintenanceTask(
                task_id=f"preventive_disk_{uuid.uuid4().hex[:8]}",
                action=MaintenanceAction.OPTIMIZE_MEMORY,
                target_component="file_system",
                priority="medium",
                estimated_duration=600,  # 10분
                success_probability=0.9,
                rollback_plan="디스크 정리 전 백업 생성",
                dependencies=[],
                scheduled_time=datetime.now() + timedelta(hours=4)
            ))
        
        # 에이전트 수가 많으면 부하 재분산 예약
        if metrics.agent_count > 20:
            preventive_tasks.append(MaintenanceTask(
                task_id=f"preventive_rebalance_{uuid.uuid4().hex[:8]}",
                action=MaintenanceAction.REBALANCE_LOAD,
                target_component="orchestrator",
                priority="medium",
                estimated_duration=900,  # 15분
                success_probability=0.85,
                rollback_plan="이전 부하 분산 설정으로 복원",
                dependencies=[],
                scheduled_time=datetime.now() + timedelta(hours=6)
            ))
        
        return preventive_tasks
    
    def _map_severity_to_priority(self, severity: str) -> str:
        """심각도를 우선순위로 매핑"""
        mapping = {
            "critical": "urgent",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        return mapping.get(severity, "medium")
    
    def _estimate_maintenance_duration(self, action: MaintenanceAction) -> float:
        """유지보수 작업 소요 시간 추정 (초)"""
        duration_map = {
            MaintenanceAction.RESTART_SERVICE: 120,      # 2분
            MaintenanceAction.SCALE_UP: 300,             # 5분
            MaintenanceAction.SCALE_DOWN: 180,           # 3분
            MaintenanceAction.CLEAR_CACHE: 60,           # 1분
            MaintenanceAction.OPTIMIZE_MEMORY: 600,      # 10분
            MaintenanceAction.REBALANCE_LOAD: 900,       # 15분
            MaintenanceAction.UPDATE_CONFIG: 240,        # 4분
            MaintenanceAction.FAILOVER: 1800             # 30분
        }
        return duration_map.get(action, 300)
    
    def _estimate_success_probability(self, action: MaintenanceAction, anomaly: AnomalyAlert) -> float:
        """성공 확률 추정"""
        base_probability = {
            MaintenanceAction.RESTART_SERVICE: 0.95,
            MaintenanceAction.SCALE_UP: 0.9,
            MaintenanceAction.SCALE_DOWN: 0.85,
            MaintenanceAction.CLEAR_CACHE: 0.98,
            MaintenanceAction.OPTIMIZE_MEMORY: 0.8,
            MaintenanceAction.REBALANCE_LOAD: 0.75,
            MaintenanceAction.UPDATE_CONFIG: 0.7,
            MaintenanceAction.FAILOVER: 0.6
        }
        
        # 이상 징후 심각도에 따른 조정
        severity_adjustment = {
            "critical": -0.1,
            "high": -0.05,
            "medium": 0.0,
            "low": 0.05
        }
        
        base_prob = base_probability.get(action, 0.8)
        adjustment = severity_adjustment.get(anomaly.severity, 0.0)
        
        return max(0.1, min(1.0, base_prob + adjustment))
    
    def _create_rollback_plan(self, action: MaintenanceAction) -> str:
        """롤백 계획 생성"""
        rollback_plans = {
            MaintenanceAction.RESTART_SERVICE: "서비스 재시작 실패 시 이전 버전으로 복원",
            MaintenanceAction.SCALE_UP: "스케일 업 실패 시 원래 인스턴스 수로 복원",
            MaintenanceAction.SCALE_DOWN: "스케일 다운 실패 시 인스턴스 재생성",
            MaintenanceAction.CLEAR_CACHE: "캐시 정리는 롤백이 필요하지 않음",
            MaintenanceAction.OPTIMIZE_MEMORY: "메모리 최적화 실패 시 서비스 재시작",
            MaintenanceAction.REBALANCE_LOAD: "부하 재분산 실패 시 이전 설정으로 복원",
            MaintenanceAction.UPDATE_CONFIG: "설정 업데이트 실패 시 백업 설정으로 복원",
            MaintenanceAction.FAILOVER: "장애 조치 실패 시 수동 개입 필요"
        }
        return rollback_plans.get(action, "수동 롤백 필요")
    
    def _get_maintenance_dependencies(self, action: MaintenanceAction) -> List[str]:
        """유지보수 작업 의존성"""
        dependencies = {
            MaintenanceAction.RESTART_SERVICE: [],
            MaintenanceAction.SCALE_UP: ["health_check"],
            MaintenanceAction.SCALE_DOWN: ["load_analysis"],
            MaintenanceAction.CLEAR_CACHE: [],
            MaintenanceAction.OPTIMIZE_MEMORY: ["memory_analysis"],
            MaintenanceAction.REBALANCE_LOAD: ["load_analysis", "agent_status"],
            MaintenanceAction.UPDATE_CONFIG: ["config_backup"],
            MaintenanceAction.FAILOVER: ["backup_ready", "secondary_system"]
        }
        return dependencies.get(action, [])
    
    def _calculate_optimal_maintenance_time(self, severity: str) -> datetime:
        """최적 유지보수 시간 계산"""
        now = datetime.now()
        
        if severity == "critical":
            return now + timedelta(minutes=5)  # 즉시
        elif severity == "high":
            return now + timedelta(minutes=30)  # 30분 후
        elif severity == "medium":
            return now + timedelta(hours=2)     # 2시간 후
        else:
            return now + timedelta(hours=24)    # 24시간 후
    
    def _optimize_maintenance_schedule(self, tasks: List[MaintenanceTask]) -> List[MaintenanceTask]:
        """유지보수 일정 최적화"""
        # 우선순위별 정렬
        priority_order = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 0), reverse=True)
        
        # 동시 실행 제한 적용
        optimized_tasks = []
        scheduled_times = {}
        
        for task in tasks:
            # 의존성 확인
            if self._check_dependencies(task, optimized_tasks):
                # 동시 실행 제한 확인
                if len([t for t in optimized_tasks if t.scheduled_time == task.scheduled_time]) < self.monitoring_config["max_concurrent_maintenance"]:
                    optimized_tasks.append(task)
                else:
                    # 다음 가능한 시간으로 연기
                    task.scheduled_time = task.scheduled_time + timedelta(minutes=30)
                    optimized_tasks.append(task)
        
        return optimized_tasks
    
    def _check_dependencies(self, task: MaintenanceTask, scheduled_tasks: List[MaintenanceTask]) -> bool:
        """의존성 확인"""
        for dependency in task.dependencies:
            # 의존성이 있는 작업이 완료되었는지 확인
            dependency_completed = any(
                t.task_id == dependency and t.status == "completed"
                for t in scheduled_tasks
            )
            if not dependency_completed:
                return False
        return True
    
    async def _execute_self_healing(
        self,
        anomalies: List[AnomalyAlert],
        maintenance_tasks: List[MaintenanceTask]
    ):
        """자가 치유 실행"""
        try:
            # 긴급한 이상 징후에 대한 즉시 대응
            critical_anomalies = [a for a in anomalies if a.severity == "critical"]
            
            for anomaly in critical_anomalies:
                await self._execute_emergency_response(anomaly)
            
            # 예약된 유지보수 작업 실행
            immediate_tasks = [
                t for t in maintenance_tasks
                if t.scheduled_time <= datetime.now() + timedelta(minutes=5)
                and t.priority in ["urgent", "high"]
            ]
            
            for task in immediate_tasks:
                if len(self.active_maintenance) < self.monitoring_config["max_concurrent_maintenance"]:
                    await self._execute_maintenance_task(task)
            
        except Exception as e:
            logger.error(f"Self-healing execution failed: {str(e)}", exc_info=True)
    
    async def _execute_emergency_response(self, anomaly: AnomalyAlert):
        """긴급 대응 실행"""
        try:
            logger.warning(f"Executing emergency response for {anomaly.anomaly_type.value}")
            
            # 긴급 조치 실행
            if anomaly.anomaly_type == AnomalyType.RESOURCE_EXHAUSTION:
                await self._emergency_scale_up()
            elif anomaly.anomaly_type == AnomalyType.MEMORY_LEAK:
                await self._emergency_memory_cleanup()
            elif anomaly.anomaly_type == AnomalyType.ERROR_SPIKE:
                await self._emergency_service_restart()
            
            logger.info(f"Emergency response completed for {anomaly.anomaly_type.value}")
            
        except Exception as e:
            logger.error(f"Emergency response failed: {str(e)}", exc_info=True)
    
    async def _emergency_scale_up(self):
        """긴급 스케일 업"""
        try:
            # 새 에이전트 인스턴스 추가
            from backend.services.multimodal.advanced_orchestrator import AgentType, AgentCapability
            
            agent_config = {
                "agent_type": "multimodal_generalist",
                "capabilities": {
                    "agent_type": AgentType.MULTIMODAL_GENERALIST,
                    "specializations": ["emergency_processing"],
                    "performance_metrics": {"accuracy": 0.8, "speed": 0.9, "reliability": 0.85},
                    "resource_requirements": {"gpu": False, "memory_gb": 4, "cpu_cores": 2},
                    "max_concurrent_tasks": 5,
                    "average_processing_time": 20.0,
                    "accuracy_score": 0.8,
                    "cost_per_task": 0.03
                }
            }
            
            new_agent_id = await self.orchestrator.add_agent(agent_config)
            logger.info(f"Emergency agent added: {new_agent_id}")
            
        except Exception as e:
            logger.error(f"Emergency scale up failed: {str(e)}")
    
    async def _emergency_memory_cleanup(self):
        """긴급 메모리 정리"""
        try:
            # 캐시 정리
            import gc
            gc.collect()
            
            # Redis 캐시 정리 (시뮬레이션)
            logger.info("Emergency memory cleanup executed")
            
        except Exception as e:
            logger.error(f"Emergency memory cleanup failed: {str(e)}")
    
    async def _emergency_service_restart(self):
        """긴급 서비스 재시작"""
        try:
            # 에이전트 상태 리셋
            for agent in self.orchestrator.agents.values():
                if agent.current_status.value == "error":
                    agent.current_status = agent.current_status.__class__.IDLE
                    agent.current_load = 0.0
                    agent.active_tasks.clear()
            
            logger.info("Emergency service restart completed")
            
        except Exception as e:
            logger.error(f"Emergency service restart failed: {str(e)}")
    
    async def _execute_maintenance_task(self, task: MaintenanceTask):
        """유지보수 작업 실행"""
        try:
            task.status = "running"
            self.active_maintenance[task.task_id] = task
            
            logger.info(f"Executing maintenance task: {task.action.value} on {task.target_component}")
            
            # 작업 실행 (시뮬레이션)
            await asyncio.sleep(min(task.estimated_duration / 10, 5))  # 시뮬레이션용 단축
            
            # 성공 확률에 따른 결과 결정
            import random
            if random.random() < task.success_probability:
                task.status = "completed"
                logger.info(f"Maintenance task completed successfully: {task.task_id}")
            else:
                task.status = "failed"
                logger.warning(f"Maintenance task failed: {task.task_id}")
                # 롤백 실행
                await self._execute_rollback(task)
            
            # 활성 유지보수에서 제거
            if task.task_id in self.active_maintenance:
                del self.active_maintenance[task.task_id]
            
            # 히스토리에 추가
            self.maintenance_history.append(task)
            
        except Exception as e:
            logger.error(f"Maintenance task execution failed: {str(e)}", exc_info=True)
            task.status = "failed"
            if task.task_id in self.active_maintenance:
                del self.active_maintenance[task.task_id]
    
    async def _execute_rollback(self, task: MaintenanceTask):
        """롤백 실행"""
        try:
            logger.info(f"Executing rollback for task: {task.task_id}")
            logger.info(f"Rollback plan: {task.rollback_plan}")
            
            # 롤백 로직 (시뮬레이션)
            await asyncio.sleep(1)
            
            logger.info(f"Rollback completed for task: {task.task_id}")
            
        except Exception as e:
            logger.error(f"Rollback failed for task {task.task_id}: {str(e)}")
    
    async def generate_health_report(self) -> HealthReport:
        """시스템 건강 보고서 생성"""
        try:
            # 전체 시스템 상태 평가
            overall_status = self._assess_overall_health()
            
            # 컴포넌트별 상태
            component_status = self._assess_component_health()
            
            # 활성 이상 징후
            active_anomalies = [a for a in self.anomaly_history[-10:] if a.timestamp > datetime.now() - timedelta(hours=1)]
            
            # 유지보수 권장사항
            maintenance_recommendations = await self._generate_maintenance_recommendations()
            
            # 성능 트렌드
            performance_trends = self._analyze_performance_trends()
            
            # 용량 예측
            capacity_forecast = self._forecast_capacity_needs()
            
            # 위험 평가
            risk_assessment = self._assess_system_risks()
            
            return HealthReport(
                report_id=f"health_{uuid.uuid4().hex[:8]}",
                overall_status=overall_status,
                component_status=component_status,
                active_anomalies=active_anomalies,
                maintenance_recommendations=maintenance_recommendations,
                performance_trends=performance_trends,
                capacity_forecast=capacity_forecast,
                risk_assessment=risk_assessment
            )
            
        except Exception as e:
            logger.error(f"Health report generation failed: {str(e)}", exc_info=True)
            return HealthReport(
                report_id=f"health_error_{uuid.uuid4().hex[:8]}",
                overall_status=HealthStatus.FAILED,
                component_status={},
                active_anomalies=[],
                maintenance_recommendations=[],
                performance_trends={},
                capacity_forecast={},
                risk_assessment={"report_generation_error": 1.0}
            )
    
    def _assess_overall_health(self) -> HealthStatus:
        """전체 시스템 건강 상태 평가"""
        if not self.metrics_history:
            return HealthStatus.HEALTHY
        
        latest_metrics = self.metrics_history[-1]
        
        # 위험 요소 확인
        critical_issues = 0
        
        if latest_metrics.cpu_usage > 95:
            critical_issues += 1
        if latest_metrics.memory_usage > 95:
            critical_issues += 1
        if latest_metrics.error_rate > 0.1:
            critical_issues += 1
        if latest_metrics.response_time > 5000:
            critical_issues += 1
        
        # 활성 이상 징후 확인
        recent_anomalies = [a for a in self.anomaly_history[-5:] if a.severity in ["critical", "high"]]
        
        if critical_issues >= 2 or len(recent_anomalies) >= 3:
            return HealthStatus.CRITICAL
        elif critical_issues >= 1 or len(recent_anomalies) >= 2:
            return HealthStatus.WARNING
        elif latest_metrics.cpu_usage > 80 or latest_metrics.memory_usage > 80:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _assess_component_health(self) -> Dict[str, HealthStatus]:
        """컴포넌트별 건강 상태 평가"""
        component_status = {}
        
        if not self.metrics_history:
            return {comp: HealthStatus.HEALTHY for comp in self.component_health.keys()}
        
        latest_metrics = self.metrics_history[-1]
        
        # 오케스트레이터 상태
        if latest_metrics.agent_count == 0 or latest_metrics.execution_success_rate < 0.8:
            component_status["orchestrator"] = HealthStatus.CRITICAL
        elif latest_metrics.execution_success_rate < 0.9:
            component_status["orchestrator"] = HealthStatus.WARNING
        else:
            component_status["orchestrator"] = HealthStatus.HEALTHY
        
        # 데이터베이스 상태
        if latest_metrics.response_time > 2000:
            component_status["database"] = HealthStatus.DEGRADED
        elif latest_metrics.response_time > 1000:
            component_status["database"] = HealthStatus.WARNING
        else:
            component_status["database"] = HealthStatus.HEALTHY
        
        # 기타 컴포넌트는 기본 상태 유지
        for component in self.component_health.keys():
            if component not in component_status:
                component_status[component] = HealthStatus.HEALTHY
        
        return component_status
    
    async def _generate_maintenance_recommendations(self) -> List[MaintenanceTask]:
        """유지보수 권장사항 생성"""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        latest_metrics = self.metrics_history[-1]
        
        # 성능 기반 권장사항
        if latest_metrics.cpu_usage > 75:
            recommendations.append(MaintenanceTask(
                task_id=f"rec_scale_{uuid.uuid4().hex[:8]}",
                action=MaintenanceAction.SCALE_UP,
                target_component="orchestrator",
                priority="medium",
                estimated_duration=300,
                success_probability=0.9,
                rollback_plan="스케일 업 실패 시 원래 설정으로 복원",
                dependencies=[]
            ))
        
        if latest_metrics.memory_usage > 70:
            recommendations.append(MaintenanceTask(
                task_id=f"rec_memory_{uuid.uuid4().hex[:8]}",
                action=MaintenanceAction.OPTIMIZE_MEMORY,
                target_component="database",
                priority="low",
                estimated_duration=600,
                success_probability=0.85,
                rollback_plan="메모리 최적화 실패 시 서비스 재시작",
                dependencies=[]
            ))
        
        return recommendations
    
    def _analyze_performance_trends(self) -> Dict[str, List[float]]:
        """성능 트렌드 분석"""
        trends = {}
        
        if len(self.metrics_history) < 10:
            return trends
        
        recent_metrics = list(self.metrics_history)[-20:]
        
        trends["cpu_usage"] = [m.cpu_usage for m in recent_metrics]
        trends["memory_usage"] = [m.memory_usage for m in recent_metrics]
        trends["response_time"] = [m.response_time for m in recent_metrics]
        trends["throughput"] = [m.throughput for m in recent_metrics]
        trends["error_rate"] = [m.error_rate for m in recent_metrics]
        
        return trends
    
    def _forecast_capacity_needs(self) -> Dict[str, float]:
        """용량 필요량 예측"""
        forecast = {}
        
        if len(self.metrics_history) < 5:
            return {"cpu": 50.0, "memory": 60.0, "storage": 30.0}
        
        recent_metrics = list(self.metrics_history)[-10:]
        
        # 간단한 선형 예측
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_usage for m in recent_metrics]
        
        # 1시간 후 예상 사용률
        cpu_trend = np.mean(np.diff(cpu_values)) if len(cpu_values) > 1 else 0
        memory_trend = np.mean(np.diff(memory_values)) if len(memory_values) > 1 else 0
        
        forecast["cpu"] = min(100.0, max(0.0, cpu_values[-1] + cpu_trend * 6))  # 6 * 10분 = 1시간
        forecast["memory"] = min(100.0, max(0.0, memory_values[-1] + memory_trend * 6))
        forecast["storage"] = 30.0  # 기본값
        
        return forecast
    
    def _assess_system_risks(self) -> Dict[str, float]:
        """시스템 위험 평가"""
        risks = {}
        
        if not self.metrics_history:
            return {"no_data": 0.1}
        
        latest_metrics = self.metrics_history[-1]
        
        # 성능 위험
        risks["performance_degradation"] = min(1.0, latest_metrics.cpu_usage / 100 * 0.8 + latest_metrics.memory_usage / 100 * 0.2)
        
        # 가용성 위험
        risks["availability"] = latest_metrics.error_rate * 10  # 오류율 기반
        
        # 용량 위험
        risks["capacity_exhaustion"] = max(latest_metrics.cpu_usage, latest_metrics.memory_usage) / 100
        
        # 응답성 위험
        risks["responsiveness"] = min(1.0, latest_metrics.response_time / 5000)  # 5초 기준
        
        return risks

# 전역 인스턴스
_predictive_maintenance_instance = None

def get_predictive_maintenance_system() -> PredictiveMaintenanceSystem:
    """예측 유지보수 시스템 인스턴스 반환"""
    global _predictive_maintenance_instance
    if _predictive_maintenance_instance is None:
        from backend.services.multimodal.advanced_orchestrator import get_advanced_orchestrator
        from backend.services.multimodal.workflow_optimizer import get_workflow_optimizer
        
        orchestrator = get_advanced_orchestrator()
        optimizer = get_workflow_optimizer()
        _predictive_maintenance_instance = PredictiveMaintenanceSystem(orchestrator, optimizer)
    return _predictive_maintenance_instance