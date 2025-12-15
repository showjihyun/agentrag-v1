"""
Multi-Tenant Manager
멀티테넌트 관리자 - Phase 6 구현
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from collections import defaultdict

from backend.services.enterprise.security_manager import get_security_manager, SecurityLevel, AccessLevel
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class TenantStatus(Enum):
    """테넌트 상태"""
    ACTIVE = "active"           # 활성
    SUSPENDED = "suspended"     # 일시 중단
    INACTIVE = "inactive"       # 비활성
    TRIAL = "trial"            # 체험판
    ENTERPRISE = "enterprise"   
    STARTER = "starter"           # 스타터 플랜
    PROFESSIONAL = "professional" # 프로페셔널 플랜
    ENTERPRISE = "enterprise"     # 엔터프라이즈 플랜
    CUSTOM = "custom"            # 커스텀 플랜

class TenantStatus(Enum):
    """테넌트 상태"""
    ACTIVE = "active"             # 활성
    SUSPENDED = "suspended"       # 일시 정지
    TERMINATED = "terminated"     # 종료
    PROVISIONING = "provisioning" # 프로비저닝 중
    MIGRATING = "migrating"       # 마이그레이션 중

class IsolationLevel(Enum):
    """격리 수준"""
    SHARED = "shared"             # 공유 리소스
    DEDICATED = "dedicated"       # 전용 리소스
    HYBRID = "hybrid"            # 하이브리드

@dataclass
class TenantConfiguration:
    """테넌트 설정"""
    tenant_id: str
    name: str
    tier: TenantTier
    status: TenantStatus
    isolation_level: IsolationLevel
    
    # 리소스 제한
    max_workflows: int
    max_agents: int
    max_executions_per_hour: int
    max_storage_gb: int
    max_api_calls_per_minute: int
    
    # 기능 제한
    enabled_features: Set[str]
    custom_integrations: bool
    advanced_analytics: bool
    priority_support: bool
    
    # 보안 설정
    sso_enabled: bool
    mfa_required: bool
    ip_whitelist: List[str]
    data_retention_days: int
    
    # 네트워크 설정
    custom_domain: Optional[str]
    vpc_id: Optional[str]
    subnet_ids: List[str]
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    billing_contact: Optional[str] = None
    technical_contact: Optional[str] = None

@dataclass
class TenantMetrics:
    """테넌트 메트릭"""
    tenant_id: str
    timestamp: datetime
    
    # 사용량 메트릭
    active_workflows: int
    total_executions: int
    storage_used_gb: float
    api_calls_count: int
    active_users: int
    
    # 성능 메트릭
    avg_execution_time: float
    success_rate: float
    error_rate: float
    uptime_percentage: float
    
    # 비용 메트릭
    compute_cost: float
    storage_cost: float
    network_cost: float
    total_cost: float

@dataclass
class TenantAlert:
    """테넌트 알림"""
    alert_id: str
    tenant_id: str
    alert_type: str  # quota_exceeded, performance_degraded, security_incident
    severity: str    # low, medium, high, critical
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

class MultiTenantManager:
    """멀티 테넌트 관리자"""
    
    def __init__(self):
        # 테넌트 저장소
        self.tenants: Dict[str, TenantConfiguration] = {}
        self.tenant_metrics: Dict[str, List[TenantMetrics]] = defaultdict(list)
        self.tenant_alerts: Dict[str, List[TenantAlert]] = defaultdict(list)
        
        # 리소스 풀
        self.resource_pools: Dict[str, Dict[str, Any]] = {
            "shared": {
                "max_capacity": 1000,
                "current_usage": 0,
                "tenants": set()
            },
            "dedicated": {},
            "hybrid": {}
        }
        
        # 격리 관리자
        self.isolation_manager = TenantIsolationManager()
        
        # 모니터링 설정
        self.monitoring_config = {
            "metrics_collection_interval": 60,  # 초
            "alert_check_interval": 30,
            "quota_check_interval": 300,
            "cleanup_interval": 3600
        }
        
        # 백그라운드 작업 시작
        asyncio.create_task(self._start_monitoring_loop())
        
        logger.info("Multi-Tenant Manager initialized")
    
    async def create_tenant(
        self,
        name: str,
        tier: TenantTier,
        isolation_level: IsolationLevel,
        admin_email: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> TenantConfiguration:
        """새 테넌트 생성"""
        try:
            tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
            
            # 기본 설정 생성
            config = self._create_default_config(tenant_id, name, tier, isolation_level)
            
            # 커스텀 설정 적용
            if custom_config:
                config = self._apply_custom_config(config, custom_config)
            
            # 리소스 프로비저닝
            await self._provision_tenant_resources(config)
            
            # 데이터베이스 스키마 생성
            await self._create_tenant_schema(tenant_id)
            
            # 보안 설정 초기화
            await self._initialize_tenant_security(config)
            
            # 모니터링 설정
            await self._setup_tenant_monitoring(tenant_id)
            
            # 테넌트 등록
            self.tenants[tenant_id] = config
            
            logger.info(f"Tenant created successfully: {tenant_id}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create tenant: {str(e)}", exc_info=True)
            raise
    
    def _create_default_config(
        self,
        tenant_id: str,
        name: str,
        tier: TenantTier,
        isolation_level: IsolationLevel
    ) -> TenantConfiguration:
        """기본 테넌트 설정 생성"""
        
        # 티어별 기본 제한
        tier_limits = {
            TenantTier.STARTER: {
                "max_workflows": 10,
                "max_agents": 5,
                "max_executions_per_hour": 100,
                "max_storage_gb": 1,
                "max_api_calls_per_minute": 60,
                "enabled_features": {"basic_workflows", "simple_agents"},
                "custom_integrations": False,
                "advanced_analytics": False,
                "priority_support": False
            },
            TenantTier.PROFESSIONAL: {
                "max_workflows": 100,
                "max_agents": 50,
                "max_executions_per_hour": 1000,
                "max_storage_gb": 10,
                "max_api_calls_per_minute": 300,
                "enabled_features": {"basic_workflows", "simple_agents", "advanced_orchestration", "optimization"},
                "custom_integrations": True,
                "advanced_analytics": True,
                "priority_support": False
            },
            TenantTier.ENTERPRISE: {
                "max_workflows": 1000,
                "max_agents": 500,
                "max_executions_per_hour": 10000,
                "max_storage_gb": 100,
                "max_api_calls_per_minute": 1000,
                "enabled_features": {"all_features"},
                "custom_integrations": True,
                "advanced_analytics": True,
                "priority_support": True
            }
        }
        
        limits = tier_limits.get(tier, tier_limits[TenantTier.STARTER])
        
        return TenantConfiguration(
            tenant_id=tenant_id,
            name=name,
            tier=tier,
            status=TenantStatus.PROVISIONING,
            isolation_level=isolation_level,
            **limits,
            sso_enabled=tier in [TenantTier.ENTERPRISE],
            mfa_required=tier in [TenantTier.PROFESSIONAL, TenantTier.ENTERPRISE],
            ip_whitelist=[],
            data_retention_days=90 if tier == TenantTier.STARTER else 365,
            custom_domain=None,
            vpc_id=None,
            subnet_ids=[]
        )
    
    def _apply_custom_config(
        self,
        config: TenantConfiguration,
        custom_config: Dict[str, Any]
    ) -> TenantConfiguration:
        """커스텀 설정 적용"""
        
        # 안전한 설정만 적용
        safe_fields = {
            'name', 'custom_domain', 'ip_whitelist', 'data_retention_days',
            'billing_contact', 'technical_contact'
        }
        
        for field, value in custom_config.items():
            if field in safe_fields and hasattr(config, field):
                setattr(config, field, value)
        
        return config
    
    async def _provision_tenant_resources(self, config: TenantConfiguration):
        """테넌트 리소스 프로비저닝"""
        try:
            if config.isolation_level == IsolationLevel.DEDICATED:
                # 전용 리소스 할당
                await self._allocate_dedicated_resources(config)
            elif config.isolation_level == IsolationLevel.HYBRID:
                # 하이브리드 리소스 할당
                await self._allocate_hybrid_resources(config)
            else:
                # 공유 리소스 할당
                await self._allocate_shared_resources(config)
            
            logger.info(f"Resources provisioned for tenant: {config.tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to provision resources: {str(e)}")
            raise
    
    async def _allocate_dedicated_resources(self, config: TenantConfiguration):
        """전용 리소스 할당"""
        # 전용 데이터베이스 인스턴스
        db_instance = await self._create_dedicated_database(config.tenant_id)
        
        # 전용 Redis 인스턴스
        redis_instance = await self._create_dedicated_redis(config.tenant_id)
        
        # 전용 Milvus 컬렉션
        milvus_collection = await self._create_dedicated_milvus(config.tenant_id)
        
        # 전용 컴퓨팅 리소스
        compute_resources = await self._allocate_dedicated_compute(config)
        
        # 리소스 정보 저장
        self.resource_pools["dedicated"][config.tenant_id] = {
            "database": db_instance,
            "redis": redis_instance,
            "milvus": milvus_collection,
            "compute": compute_resources,
            "allocated_at": datetime.now()
        }
    
    async def _allocate_shared_resources(self, config: TenantConfiguration):
        """공유 리소스 할당"""
        # 공유 풀에 테넌트 추가
        self.resource_pools["shared"]["tenants"].add(config.tenant_id)
        self.resource_pools["shared"]["current_usage"] += 1
        
        # 네임스페이스 생성
        await self._create_tenant_namespace(config.tenant_id)
    
    async def _create_dedicated_database(self, tenant_id: str) -> Dict[str, Any]:
        """전용 데이터베이스 생성"""
        # 실제 구현에서는 클라우드 프로바이더 API 호출
        return {
            "instance_id": f"db_{tenant_id}",
            "connection_string": f"postgresql://user:pass@db-{tenant_id}.internal:5432/{tenant_id}",
            "type": "dedicated",
            "size": "medium"
        }
    
    async def _create_dedicated_redis(self, tenant_id: str) -> Dict[str, Any]:
        """전용 Redis 인스턴스 생성"""
        return {
            "instance_id": f"redis_{tenant_id}",
            "connection_string": f"redis://redis-{tenant_id}.internal:6379",
            "type": "dedicated",
            "memory_gb": 4
        }
    
    async def _create_dedicated_milvus(self, tenant_id: str) -> Dict[str, Any]:
        """전용 Milvus 컬렉션 생성"""
        return {
            "collection_name": f"vectors_{tenant_id}",
            "connection_params": {
                "host": f"milvus-{tenant_id}.internal",
                "port": 19530
            },
            "type": "dedicated"
        }
    
    async def _create_tenant_schema(self, tenant_id: str):
        """테넌트 데이터베이스 스키마 생성"""
        try:
            # 테넌트별 스키마 생성 SQL
            schema_sql = f"""
            CREATE SCHEMA IF NOT EXISTS tenant_{tenant_id};
            
            -- 워크플로우 테이블
            CREATE TABLE IF NOT EXISTS tenant_{tenant_id}.workflows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                definition JSONB NOT NULL,
                status VARCHAR(50) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            -- 에이전트 테이블
            CREATE TABLE IF NOT EXISTS tenant_{tenant_id}.agents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                configuration JSONB NOT NULL,
                status VARCHAR(50) DEFAULT 'inactive',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            -- 실행 기록 테이블
            CREATE TABLE IF NOT EXISTS tenant_{tenant_id}.executions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_id UUID NOT NULL,
                status VARCHAR(50) NOT NULL,
                input_data JSONB,
                output_data JSONB,
                error_message TEXT,
                started_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                duration_ms INTEGER
            );
            
            -- 메트릭 테이블
            CREATE TABLE IF NOT EXISTS tenant_{tenant_id}.metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_type VARCHAR(100) NOT NULL,
                metric_name VARCHAR(255) NOT NULL,
                metric_value NUMERIC NOT NULL,
                labels JSONB,
                timestamp TIMESTAMP DEFAULT NOW()
            );
            
            -- 인덱스 생성
            CREATE INDEX IF NOT EXISTS idx_workflows_status ON tenant_{tenant_id}.workflows(status);
            CREATE INDEX IF NOT EXISTS idx_agents_type ON tenant_{tenant_id}.agents(type);
            CREATE INDEX IF NOT EXISTS idx_executions_workflow ON tenant_{tenant_id}.executions(workflow_id);
            CREATE INDEX IF NOT EXISTS idx_executions_status ON tenant_{tenant_id}.executions(status);
            CREATE INDEX IF NOT EXISTS idx_metrics_type_name ON tenant_{tenant_id}.metrics(metric_type, metric_name);
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON tenant_{tenant_id}.metrics(timestamp);
            """
            
            # 실제 구현에서는 데이터베이스 연결을 통해 실행
            logger.info(f"Database schema created for tenant: {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to create tenant schema: {str(e)}")
            raise
    
    async def _initialize_tenant_security(self, config: TenantConfiguration):
        """테넌트 보안 설정 초기화"""
        try:
            # API 키 생성
            api_key = self._generate_tenant_api_key(config.tenant_id)
            
            # 암호화 키 생성
            encryption_key = self._generate_encryption_key(config.tenant_id)
            
            # 접근 제어 정책 설정
            await self._setup_access_control(config)
            
            # 감사 로그 설정
            await self._setup_audit_logging(config.tenant_id)
            
            logger.info(f"Security initialized for tenant: {config.tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize security: {str(e)}")
            raise
    
    def _generate_tenant_api_key(self, tenant_id: str) -> str:
        """테넌트 API 키 생성"""
        timestamp = str(int(datetime.now().timestamp()))
        raw_key = f"{tenant_id}:{timestamp}:{uuid.uuid4().hex}"
        return hashlib.sha256(raw_key.encode()).hexdigest()
    
    def _generate_encryption_key(self, tenant_id: str) -> str:
        """암호화 키 생성"""
        return hashlib.sha256(f"encryption_{tenant_id}_{uuid.uuid4().hex}".encode()).hexdigest()
    
    async def _setup_tenant_monitoring(self, tenant_id: str):
        """테넌트 모니터링 설정"""
        try:
            # 메트릭 수집 설정
            await self._configure_metrics_collection(tenant_id)
            
            # 알림 규칙 설정
            await self._configure_alert_rules(tenant_id)
            
            # 대시보드 생성
            await self._create_tenant_dashboard(tenant_id)
            
            logger.info(f"Monitoring configured for tenant: {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring: {str(e)}")
            raise
    
    async def get_tenant_metrics(self, tenant_id: str, time_range_hours: int = 24) -> List[TenantMetrics]:
        """테넌트 메트릭 조회"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            
            metrics = [
                m for m in self.tenant_metrics[tenant_id]
                if m.timestamp >= cutoff_time
            ]
            
            return sorted(metrics, key=lambda x: x.timestamp)
            
        except Exception as e:
            logger.error(f"Failed to get tenant metrics: {str(e)}")
            return []
    
    async def check_tenant_quotas(self, tenant_id: str) -> Dict[str, Any]:
        """테넌트 할당량 확인"""
        try:
            config = self.tenants.get(tenant_id)
            if not config:
                raise ValueError(f"Tenant not found: {tenant_id}")
            
            # 현재 사용량 조회
            current_usage = await self._get_current_usage(tenant_id)
            
            # 할당량 대비 사용률 계산
            quota_status = {
                "workflows": {
                    "current": current_usage.get("workflows", 0),
                    "limit": config.max_workflows,
                    "usage_percentage": (current_usage.get("workflows", 0) / config.max_workflows) * 100
                },
                "agents": {
                    "current": current_usage.get("agents", 0),
                    "limit": config.max_agents,
                    "usage_percentage": (current_usage.get("agents", 0) / config.max_agents) * 100
                },
                "storage": {
                    "current_gb": current_usage.get("storage_gb", 0),
                    "limit_gb": config.max_storage_gb,
                    "usage_percentage": (current_usage.get("storage_gb", 0) / config.max_storage_gb) * 100
                },
                "api_calls": {
                    "current_per_minute": current_usage.get("api_calls_per_minute", 0),
                    "limit_per_minute": config.max_api_calls_per_minute,
                    "usage_percentage": (current_usage.get("api_calls_per_minute", 0) / config.max_api_calls_per_minute) * 100
                }
            }
            
            # 위험 수준 평가
            risk_level = "low"
            for resource, stats in quota_status.items():
                if stats["usage_percentage"] > 90:
                    risk_level = "critical"
                    break
                elif stats["usage_percentage"] > 80:
                    risk_level = "high"
                elif stats["usage_percentage"] > 70:
                    risk_level = "medium"
            
            return {
                "tenant_id": tenant_id,
                "quota_status": quota_status,
                "risk_level": risk_level,
                "checked_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to check tenant quotas: {str(e)}")
            return {}
    
    async def _get_current_usage(self, tenant_id: str) -> Dict[str, Any]:
        """현재 사용량 조회"""
        # 실제 구현에서는 데이터베이스에서 조회
        return {
            "workflows": 5,
            "agents": 12,
            "storage_gb": 2.5,
            "api_calls_per_minute": 45,
            "executions_per_hour": 150
        }
    
    async def _start_monitoring_loop(self):
        """모니터링 루프 시작"""
        while True:
            try:
                # 메트릭 수집
                await self._collect_tenant_metrics()
                
                # 할당량 확인
                await self._check_all_tenant_quotas()
                
                # 알림 확인
                await self._check_tenant_alerts()
                
                # 정리 작업
                await self._cleanup_old_data()
                
                # 대기
                await asyncio.sleep(self.monitoring_config["metrics_collection_interval"])
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _collect_tenant_metrics(self):
        """모든 테넌트 메트릭 수집"""
        for tenant_id in self.tenants.keys():
            try:
                metrics = await self._collect_single_tenant_metrics(tenant_id)
                self.tenant_metrics[tenant_id].append(metrics)
                
                # 메트릭 히스토리 제한 (최근 1000개)
                if len(self.tenant_metrics[tenant_id]) > 1000:
                    self.tenant_metrics[tenant_id] = self.tenant_metrics[tenant_id][-1000:]
                    
            except Exception as e:
                logger.error(f"Failed to collect metrics for tenant {tenant_id}: {str(e)}")
    
    async def _collect_single_tenant_metrics(self, tenant_id: str) -> TenantMetrics:
        """단일 테넌트 메트릭 수집"""
        # 실제 구현에서는 각 테넌트의 실제 메트릭을 수집
        import random
        
        return TenantMetrics(
            tenant_id=tenant_id,
            timestamp=datetime.now(),
            active_workflows=random.randint(1, 10),
            total_executions=random.randint(50, 500),
            storage_used_gb=random.uniform(0.5, 5.0),
            api_calls_count=random.randint(100, 1000),
            active_users=random.randint(1, 20),
            avg_execution_time=random.uniform(1.0, 10.0),
            success_rate=random.uniform(0.9, 1.0),
            error_rate=random.uniform(0.0, 0.1),
            uptime_percentage=random.uniform(99.0, 100.0),
            compute_cost=random.uniform(10.0, 100.0),
            storage_cost=random.uniform(5.0, 50.0),
            network_cost=random.uniform(2.0, 20.0),
            total_cost=random.uniform(20.0, 200.0)
        )

class TenantIsolationManager:
    """테넌트 격리 관리자"""
    
    def __init__(self):
        self.isolation_policies: Dict[str, Dict[str, Any]] = {}
        self.resource_boundaries: Dict[str, Dict[str, Any]] = {}
    
    async def enforce_isolation(self, tenant_id: str, resource_type: str, operation: str) -> bool:
        """격리 정책 강제 적용"""
        try:
            policy = self.isolation_policies.get(tenant_id, {})
            
            # 리소스 접근 권한 확인
            if not self._check_resource_access(tenant_id, resource_type):
                logger.warning(f"Resource access denied for tenant {tenant_id}: {resource_type}")
                return False
            
            # 작업 권한 확인
            if not self._check_operation_permission(tenant_id, operation):
                logger.warning(f"Operation denied for tenant {tenant_id}: {operation}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enforce isolation: {str(e)}")
            return False
    
    def _check_resource_access(self, tenant_id: str, resource_type: str) -> bool:
        """리소스 접근 권한 확인"""
        # 실제 구현에서는 세밀한 권한 확인
        return True
    
    def _check_operation_permission(self, tenant_id: str, operation: str) -> bool:
        """작업 권한 확인"""
        # 실제 구현에서는 작업별 권한 확인
        return True

# 전역 인스턴스
_multi_tenant_manager_instance = None

def get_multi_tenant_manager() -> MultiTenantManager:
    """멀티 테넌트 관리자 인스턴스 반환"""
    global _multi_tenant_manager_instance
    if _multi_tenant_manager_instance is None:
        _multi_tenant_manager_instance = MultiTenantManager()
    return _multi_tenant_manager_instance