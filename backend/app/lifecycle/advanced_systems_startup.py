"""
Advanced Systems Startup

고급 시스템 컴포넌트들의 초기화 및 생명주기 관리
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from backend.core.event_bus.validated_event_bus import ValidatedEventBus
from backend.core.monitoring.plugin_performance_monitor import PluginPerformanceMonitor
from backend.core.monitoring.advanced_metrics_collector import AdvancedMetricsCollector
from backend.core.security.runtime_security_monitor import RuntimeSecurityMonitor
from backend.core.scaling.auto_scaling_manager import AutoScalingManager, ScalingPolicy
from backend.services.plugins.agents.enhanced_agent_plugin_manager import EnhancedAgentPluginManager
from backend.core.dependencies import get_redis_client

logger = logging.getLogger(__name__)


class AdvancedSystemsManager:
    """고급 시스템 관리자"""
    
    def __init__(self):
        self.event_bus: Optional[ValidatedEventBus] = None
        self.performance_monitor: Optional[PluginPerformanceMonitor] = None
        self.advanced_metrics_collector: Optional[AdvancedMetricsCollector] = None
        self.runtime_security_monitor: Optional[RuntimeSecurityMonitor] = None
        self.auto_scaling_manager: Optional[AutoScalingManager] = None
        
        self.initialized = False
        self.startup_tasks: list = []
    
    async def initialize_all_systems(self, config: Dict[str, Any] = None) -> bool:
        """모든 고급 시스템 초기화"""
        
        if self.initialized:
            logger.warning("Advanced systems already initialized")
            return True
        
        config = config or {}
        
        try:
            logger.info("Starting advanced systems initialization...")
            
            # 1. Event Bus 초기화
            await self._initialize_event_bus()
            
            # 2. Performance Monitor 초기화
            await self._initialize_performance_monitor()
            
            # 3. Advanced Metrics Collector 초기화
            await self._initialize_advanced_metrics_collector()
            
            # 4. Runtime Security Monitor 초기화
            await self._initialize_runtime_security_monitor()
            
            # 5. Auto Scaling Manager 초기화
            await self._initialize_auto_scaling_manager()
            
            # 6. 시스템 간 연동 설정
            await self._setup_system_integrations()
            
            # 8. API 의존성 초기화
            await self._initialize_api_dependencies()
            
            # 9. 기본 정책 및 설정 적용
            await self._apply_default_configurations(config)
            
            # 10. 백그라운드 서비스 시작
            await self._start_background_services()
            
            self.initialized = True
            
            # 초기화 완료 이벤트 발행
            await self.event_bus.publish(
                'advanced_systems_initialized',
                {
                    'components': [
                        'event_bus',
                        'performance_monitor',
                        'advanced_metrics_collector',
                        'runtime_security_monitor',
                        'auto_scaling_manager'
                    ],
                    'initialization_time': 'completed',
                    'config_applied': bool(config)
                },
                source='advanced_systems_manager'
            )
            
            logger.info("Advanced systems initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize advanced systems: {str(e)}")
            await self._cleanup_partial_initialization()
            return False
    
    async def _initialize_event_bus(self):
        """Event Bus 초기화"""
        try:
            redis_client = get_redis_client()
            self.event_bus = ValidatedEventBus(redis_client)
            await self.event_bus.start_consuming()
            logger.info("Event Bus initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Event Bus: {str(e)}")
            raise
    
    async def _initialize_performance_monitor(self):
        """Performance Monitor 초기화"""
        try:
            self.performance_monitor = PluginPerformanceMonitor(
                event_bus=self.event_bus,
                retention_hours=48  # 48시간 데이터 보관
            )
            
            # 알림 임계값 설정
            self.performance_monitor.set_alert_thresholds({
                'max_execution_time': 30.0,
                'min_success_rate': 0.85,
                'max_memory_usage': 1000.0,  # 1GB
                'max_consecutive_failures': 3
            })
            
            await self.performance_monitor.start_cleanup_task()
            logger.info("Performance Monitor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Performance Monitor: {str(e)}")
            raise
    
    async def _initialize_advanced_metrics_collector(self):
        """Advanced Metrics Collector 초기화"""
        try:
            self.advanced_metrics_collector = AdvancedMetricsCollector(
                event_bus=self.event_bus,
                performance_monitor=self.performance_monitor
            )
            
            await self.advanced_metrics_collector.start_collection()
            logger.info("Advanced Metrics Collector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Advanced Metrics Collector: {str(e)}")
            raise
    
    async def _initialize_runtime_security_monitor(self):
        """Runtime Security Monitor 초기화"""
        try:
            self.runtime_security_monitor = RuntimeSecurityMonitor(
                event_bus=self.event_bus
            )
            
            # 보안 콜백 등록
            async def security_alert_callback(threat, context, action):
                logger.warning(
                    f"Security action taken: {action.value} for threat {threat.threat_type.value} "
                    f"in plugin {context.plugin_id}"
                )
            
            self.runtime_security_monitor.add_security_callback(security_alert_callback)
            logger.info("Runtime Security Monitor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Runtime Security Monitor: {str(e)}")
            raise
    
    async def _initialize_auto_scaling_manager(self):
        """Auto Scaling Manager 초기화"""
        try:
            self.auto_scaling_manager = AutoScalingManager(
                event_bus=self.event_bus,
                performance_monitor=self.performance_monitor,
                metrics_collector=self.advanced_metrics_collector
            )
            
            logger.info("Auto Scaling Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Auto Scaling Manager: {str(e)}")
            raise
    
    async def _setup_system_integrations(self):
        """시스템 간 연동 설정"""
        try:
            # Performance Monitor와 Security Monitor 연동
            async def performance_security_integration(event_data):
                """성능 이상시 보안 모니터링 강화"""
                if event_data.get('severity') == 'high':
                    plugin_id = event_data.get('plugin_type')
                    if plugin_id:
                        # 보안 모니터링 강화 로직
                        logger.info(f"Enhanced security monitoring for {plugin_id} due to performance issues")
            
            await self.event_bus.subscribe('performance_alert', performance_security_integration)
            
            # Security Monitor와 Scaling Manager 연동
            async def security_scaling_integration(event_data):
                """보안 위협시 스케일링 조정"""
                threat_level = event_data.get('severity')
                plugin_id = event_data.get('plugin_id')
                
                if threat_level == 'critical' and plugin_id:
                    # 해당 플러그인 스케일 다운 또는 격리
                    logger.warning(f"Security threat detected in {plugin_id}, considering scaling adjustments")
            
            await self.event_bus.subscribe('security_response_executed', security_scaling_integration)
            
            logger.info("System integrations configured")
        except Exception as e:
            logger.error(f"Failed to setup system integrations: {str(e)}")
            raise
    
    async def _initialize_api_dependencies(self):
        """API 의존성 초기화"""
        try:
            # Advanced Monitoring API 의존성 초기화
            from backend.api.agent_builder.advanced_monitoring import initialize_monitoring_dependencies
            
            initialize_monitoring_dependencies(
                self.advanced_metrics_collector,
                self.runtime_security_monitor,
                self.auto_scaling_manager
            )
            
            logger.info("API dependencies initialized")
        except Exception as e:
            logger.error(f"Failed to initialize API dependencies: {str(e)}")
            raise
    
    async def _apply_default_configurations(self, config: Dict[str, Any]):
        """기본 설정 적용"""
        try:
            # 기본 스케일링 정책 설정
            default_plugins = ['vector_search', 'web_search', 'local_data', 'aggregator']
            
            for plugin_type in default_plugins:
                policy = ScalingPolicy(
                    plugin_type=plugin_type,
                    min_instances=config.get(f'{plugin_type}_min_instances', 1),
                    max_instances=config.get(f'{plugin_type}_max_instances', 5),
                    target_cpu_utilization=config.get('target_cpu_utilization', 70.0),
                    target_memory_utilization=config.get('target_memory_utilization', 80.0),
                    target_response_time=config.get('target_response_time', 3.0),
                    scale_up_cooldown=config.get('scale_up_cooldown', 300),
                    scale_down_cooldown=config.get('scale_down_cooldown', 600)
                )
                
                self.auto_scaling_manager.set_scaling_policy(plugin_type, policy)
            
            # 자동 스케일링 활성화 여부
            if config.get('auto_scaling_enabled', True):
                await self.auto_scaling_manager.start_auto_scaling()
            
            logger.info("Default configurations applied")
        except Exception as e:
            logger.error(f"Failed to apply default configurations: {str(e)}")
            raise
    
    async def _start_background_services(self):
        """백그라운드 서비스 시작"""
        try:
            # 주기적 시스템 상태 체크
            async def system_health_check():
                while True:
                    try:
                        await asyncio.sleep(300)  # 5분마다
                        
                        # 시스템 상태 수집
                        health_data = {
                            'performance_monitor': self.performance_monitor is not None,
                            'security_monitor': self.runtime_security_monitor is not None,
                            'scaling_manager': self.auto_scaling_manager is not None,
                            'metrics_collector': self.advanced_metrics_collector is not None
                        }
                        
                        # 상태 이벤트 발행
                        await self.event_bus.publish(
                            'system_health_check',
                            health_data,
                            source='advanced_systems_manager'
                        )
                        
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"System health check error: {str(e)}")
            
            # 백그라운드 태스크 시작
            health_check_task = asyncio.create_task(system_health_check())
            self.startup_tasks.append(health_check_task)
            
            logger.info("Background services started")
        except Exception as e:
            logger.error(f"Failed to start background services: {str(e)}")
            raise
    
    async def _cleanup_partial_initialization(self):
        """부분 초기화 정리"""
        try:
            if self.auto_scaling_manager:
                await self.auto_scaling_manager.stop_auto_scaling()
            
            if self.advanced_metrics_collector:
                await self.advanced_metrics_collector.stop_collection()
            
            if self.performance_monitor:
                await self.performance_monitor.stop_cleanup_task()
            
            if self.event_bus:
                await self.event_bus.stop_consuming()
            
            # 백그라운드 태스크 정리
            for task in self.startup_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.startup_tasks.clear()
            
            logger.info("Partial initialization cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def shutdown_all_systems(self):
        """모든 시스템 종료"""
        if not self.initialized:
            return
        
        try:
            logger.info("Shutting down advanced systems...")
            
            # 1. 자동 스케일링 중지
            if self.auto_scaling_manager:
                await self.auto_scaling_manager.stop_auto_scaling()
            
            # 2. 메트릭 수집 중지
            if self.advanced_metrics_collector:
                await self.advanced_metrics_collector.stop_collection()
            
            # 3. 성능 모니터링 중지
            if self.performance_monitor:
                await self.performance_monitor.stop_cleanup_task()
            
            # 4. 백그라운드 태스크 정리
            for task in self.startup_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.startup_tasks.clear()
            
            # 5. Event Bus 중지
            if self.event_bus:
                await self.event_bus.stop_consuming()
            
            # 종료 완료 이벤트 (Event Bus 중지 전에)
            if self.event_bus:
                await self.event_bus.publish(
                    'advanced_systems_shutdown',
                    {'shutdown_time': 'completed'},
                    source='advanced_systems_manager'
                )
            
            self.initialized = False
            logger.info("Advanced systems shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during systems shutdown: {str(e)}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            'initialized': self.initialized,
            'components': {
                'event_bus': self.event_bus is not None,
                'performance_monitor': self.performance_monitor is not None,
                'advanced_metrics_collector': self.advanced_metrics_collector is not None,
                'runtime_security_monitor': self.runtime_security_monitor is not None,
                'auto_scaling_manager': self.auto_scaling_manager is not None
            },
            'background_tasks': len(self.startup_tasks),
            'active_tasks': sum(1 for task in self.startup_tasks if not task.done())
        }
    
    def get_components(self) -> Dict[str, Any]:
        """컴포넌트 인스턴스 반환 (의존성 주입용)"""
        return {
            'event_bus': self.event_bus,
            'performance_monitor': self.performance_monitor,
            'advanced_metrics_collector': self.advanced_metrics_collector,
            'runtime_security_monitor': self.runtime_security_monitor,
            'auto_scaling_manager': self.auto_scaling_manager
        }


# 전역 시스템 관리자 인스턴스
advanced_systems_manager = AdvancedSystemsManager()


async def initialize_advanced_systems(config: Dict[str, Any] = None) -> bool:
    """고급 시스템 초기화 (애플리케이션 시작시 호출)"""
    return await advanced_systems_manager.initialize_all_systems(config)


async def shutdown_advanced_systems():
    """고급 시스템 종료 (애플리케이션 종료시 호출)"""
    await advanced_systems_manager.shutdown_all_systems()


def get_advanced_systems_status() -> Dict[str, Any]:
    """고급 시스템 상태 조회"""
    return advanced_systems_manager.get_system_status()


def get_system_components() -> Dict[str, Any]:
    """시스템 컴포넌트 조회 (의존성 주입용)"""
    return advanced_systems_manager.get_components()