"""
Enhanced Agent Plugin Manager

향상된 Agent Plugin 관리자 - 보안, 에러 처리, 성능 최적화가 강화된 버전
"""
from typing import Dict, List, Any, Optional, Type, Union
import asyncio
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from backend.services.plugins.agents.agent_plugin_registry import AgentPluginRegistry
from backend.services.plugins.agents.base_agent_plugin import IAgentPlugin, AgentExecutionContext
from backend.services.plugins.agents.plugin_lifecycle_manager import PluginLifecycleManager, EnhancedAgentPlugin
from backend.core.monitoring.plugin_performance_monitor import PluginPerformanceMonitor
from backend.services.plugins.agents.vector_search_agent_plugin import VectorSearchAgentPlugin
from backend.services.plugins.agents.web_search_agent_plugin import WebSearchAgentPlugin
from backend.services.plugins.agents.local_data_agent_plugin import LocalDataAgentPlugin
from backend.services.plugins.agents.aggregator_agent_plugin import AggregatorAgentPlugin
from backend.services.plugins.agents.custom_agent_factory import (
    get_custom_agent_plugin_manager, 
    CustomAgentPluginManager
)
from backend.services.optimization.optimization_service_manager import OptimizationServiceManager
from backend.core.event_bus import EventBus
from backend.core.dependencies import get_redis_client
from backend.services.plugins.enhanced_security_manager import (
    EnhancedPluginSecurityManager,
    SecurityContext,
    SecureAgentExecutionRequest,
    UserRole,
    PluginPermission
)
from backend.core.error_handling.plugin_errors import (
    enhanced_plugin_error_handler,
    PluginException,
    PluginErrorCode,
    PluginExecutionException,
    PluginTimeoutException,
    PluginResourceError,
    handle_plugin_errors,
    plugin_error_context
)
from backend.core.utils.circular_buffer import ExecutionHistoryBuffer
from backend.core.cache.plugin_cache import PluginCacheManager

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """실행 메트릭"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class AgentExecutionResult:
    """Agent 실행 결과"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metrics: Optional[ExecutionMetrics] = None
    trace_id: Optional[str] = None
    agent_type: Optional[str] = None
    user_id: Optional[str] = None


class EnhancedAgentPluginManager:
    """향상된 Agent Plugin 통합 관리자"""
    
    def __init__(self, event_bus: EventBus = None):
        self._event_bus = event_bus
        self._registry = None
        self._lifecycle_manager = None
        self._performance_monitor = None
        self.custom_agent_manager = get_custom_agent_plugin_manager()
        
        # 향상된 보안 및 에러 처리 매니저
        self.security_manager = EnhancedPluginSecurityManager()
        self.error_handler = enhanced_plugin_error_handler
    
    @property
    def event_bus(self) -> EventBus:
        """Lazy initialization of event bus"""
        if self._event_bus is None:
            self._event_bus = self._create_event_bus()
            # 여전히 None이면 기본 EventBus 생성 (Redis 없이)
            if self._event_bus is None:
                logger.warning("Creating EventBus without Redis connection")
                # 기본 EventBus 생성 (실제 구현에서는 메모리 기반 이벤트 버스 등을 사용)
                from backend.core.event_bus import EventBus
                self._event_bus = EventBus(None)  # None Redis client로 생성
        return self._event_bus
    
    @property
    def registry(self) -> AgentPluginRegistry:
        """Lazy initialization of registry"""
        if self._registry is None:
            self._registry = AgentPluginRegistry(self.event_bus)
        return self._registry
    
    @property
    def lifecycle_manager(self) -> PluginLifecycleManager:
        """Lazy initialization of lifecycle manager"""
        if self._lifecycle_manager is None:
            self._lifecycle_manager = PluginLifecycleManager(self.event_bus)
        return self._lifecycle_manager
    
    @property
    def performance_monitor(self) -> PluginPerformanceMonitor:
        """Lazy initialization of performance monitor"""
        if self._performance_monitor is None:
            self._performance_monitor = PluginPerformanceMonitor(self.event_bus)
        return self._performance_monitor
        
        # 캐시 매니저
        self.cache_manager = PluginCacheManager()
        
        # 메모리 관리를 위한 실행 이력 버퍼 (크기 증가)
        self.execution_history = ExecutionHistoryBuffer(max_size=2000, max_age_hours=48)
        
        # 최적화 서비스 매니저
        self.optimization_manager: Optional[OptimizationServiceManager] = None
        
        # 동시 실행 제한
        self.max_concurrent_executions = 50
        self.current_executions = 0
        self.execution_semaphore = asyncio.Semaphore(self.max_concurrent_executions)
        
        # 실행 큐 (우선순위 기반)
        self.execution_queue = asyncio.PriorityQueue()
        self.queue_processor_task: Optional[asyncio.Task] = None
        
        self._initialized = False
        self._shutdown = False
        
        # 기본 플러그인 정의
        self._default_plugins: Dict[str, Type[IAgentPlugin]] = {
            "vector_search": VectorSearchAgentPlugin,
            "web_search": WebSearchAgentPlugin,
            "local_data": LocalDataAgentPlugin,
            "aggregator": AggregatorAgentPlugin
        }
        
        # 성능 메트릭
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "peak_concurrent_executions": 0
        }
    
    def _create_event_bus(self) -> EventBus:
        """Event Bus 인스턴스 생성"""
        try:
            from backend.core.dependencies import get_container
            container = get_container()
            
            # 컨테이너가 초기화되지 않은 경우 기본 설정으로 초기화
            if not container._initialized:
                container.initialize()
                
            redis_client = container.get_redis_client()
            return EventBus(redis_client)
        except Exception as e:
            # 컨테이너 초기화 실패 시 None 반환하여 나중에 재시도
            logger.warning(f"Failed to create event bus: {e}")
            # 임시로 None을 반환하고 실제 사용 시점에 다시 시도
            return None
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """향상된 초기화"""
        try:
            config = config or {}
            
            logger.info("Initializing Enhanced Agent Plugin Manager...")
            
            # Event Bus 시작
            await self.event_bus.start_consuming()
            
            # 생명주기 관리자 시작
            await self.lifecycle_manager.start_health_monitoring()
            
            # 성능 모니터링 시작
            await self.performance_monitor.start_cleanup_task()
            
            # 캐시 매니저 초기화
            await self.cache_manager.initialize()
            
            # 최적화 서비스 매니저 초기화
            await self._initialize_optimization_services()
            
            # 기본 Agent Plugin들 등록
            await self._register_default_plugins(config)
            
            # Custom Agent Plugin들 등록
            await self._register_custom_agent_plugins(config)
            
            # 시스템 이벤트 핸들러 등록
            await self._setup_system_event_handlers()
            
            # 실행 큐 프로세서 시작
            await self._start_queue_processor()
            
            # 에러 콜백 등록
            self._setup_error_callbacks()
            
            self._initialized = True
            logger.info("Enhanced Agent Plugin Manager initialized successfully")
            
            # 초기화 완료 이벤트 발행
            await self.event_bus.publish(
                "enhanced_agent_plugin_manager_initialized",
                {
                    "timestamp": datetime.now().isoformat(),
                    "registered_agents": list(self._default_plugins.keys()),
                    "max_concurrent_executions": self.max_concurrent_executions,
                    "cache_enabled": True,
                    "security_enhanced": True
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Agent Plugin Manager: {str(e)}")
            await self.error_handler.handle_exception(
                e, context={"operation": "initialization", "config": config}
            )
            return False
    
    async def _initialize_optimization_services(self):
        """최적화 서비스 초기화"""
        try:
            self.optimization_manager = OptimizationServiceManager()
            await self.optimization_manager.initialize()
            logger.info("Optimization services initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize optimization services: {str(e)}")
    
    async def _register_default_plugins(self, config: Dict[str, Any]):
        """기본 플러그인 등록"""
        for agent_type, plugin_class in self._default_plugins.items():
            try:
                plugin_instance = plugin_class()
                enhanced_plugin = EnhancedAgentPlugin(
                    plugin=plugin_instance,
                    plugin_id=agent_type,
                    config=config.get(agent_type, {})
                )
                
                await self.registry.register_agent(agent_type, enhanced_plugin)
                await self.lifecycle_manager.register_plugin(enhanced_plugin)
                
                logger.info(f"Registered default plugin: {agent_type}")
                
            except Exception as e:
                logger.error(f"Failed to register default plugin {agent_type}: {str(e)}")
                await self.error_handler.handle_exception(
                    e, plugin_id=agent_type, context={"operation": "plugin_registration"}
                )
    
    async def _register_custom_agent_plugins(self, config: Dict[str, Any]):
        """사용자 정의 플러그인 등록"""
        try:
            custom_plugins = await self.custom_agent_manager.get_all_plugins()
            
            for plugin_id, plugin_instance in custom_plugins.items():
                enhanced_plugin = EnhancedAgentPlugin(
                    plugin=plugin_instance,
                    plugin_id=plugin_id,
                    config=config.get(plugin_id, {})
                )
                
                await self.registry.register_agent(plugin_id, enhanced_plugin)
                await self.lifecycle_manager.register_plugin(enhanced_plugin)
                
                logger.info(f"Registered custom plugin: {plugin_id}")
                
        except Exception as e:
            logger.error(f"Failed to register custom plugins: {str(e)}")
            await self.error_handler.handle_exception(
                e, context={"operation": "custom_plugin_registration"}
            )
    
    async def _setup_system_event_handlers(self):
        """시스템 이벤트 핸들러 설정"""
        
        async def handle_plugin_error(event_data: Dict[str, Any]):
            """플러그인 에러 이벤트 처리"""
            plugin_id = event_data.get("plugin_id")
            error_code = event_data.get("error_code")
            
            if plugin_id and error_code:
                # 에러 빈도가 높은 플러그인 비활성화
                error_count = await self._get_plugin_error_count(plugin_id)
                if error_count > 10:  # 10회 이상 에러 시
                    await self.lifecycle_manager.deactivate_plugin(plugin_id)
                    logger.warning(f"Plugin {plugin_id} deactivated due to high error rate")
        
        async def handle_performance_degradation(event_data: Dict[str, Any]):
            """성능 저하 이벤트 처리"""
            plugin_id = event_data.get("plugin_id")
            if plugin_id:
                # 성능 최적화 시도
                if self.optimization_manager:
                    await self.optimization_manager.optimize_plugin_performance(plugin_id)
        
        # 이벤트 핸들러 등록
        await self.event_bus.subscribe("plugin_error", handle_plugin_error)
        await self.event_bus.subscribe("performance_degradation", handle_performance_degradation)
    
    async def _start_queue_processor(self):
        """실행 큐 프로세서 시작"""
        self.queue_processor_task = asyncio.create_task(self._process_execution_queue())
    
    async def _process_execution_queue(self):
        """실행 큐 처리"""
        while not self._shutdown:
            try:
                # 큐에서 실행 요청 가져오기 (우선순위 순)
                priority, execution_request = await asyncio.wait_for(
                    self.execution_queue.get(), timeout=1.0
                )
                
                # 비동기 실행
                asyncio.create_task(self._execute_from_queue(execution_request))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in queue processor: {str(e)}")
                await asyncio.sleep(1)
    
    async def _execute_from_queue(self, execution_request: Dict[str, Any]):
        """큐에서 가져온 요청 실행"""
        try:
            agent_type = execution_request["agent_type"]
            input_data = execution_request["input_data"]
            security_context = execution_request["security_context"]
            
            result = await self._execute_single_agent_internal(
                agent_type, input_data, security_context
            )
            
            # 결과 콜백 호출 (있는 경우)
            callback = execution_request.get("callback")
            if callback:
                await callback(result)
                
        except Exception as e:
            logger.error(f"Error executing from queue: {str(e)}")
    
    def _setup_error_callbacks(self):
        """에러 콜백 설정"""
        
        async def log_security_violations(error: PluginException):
            """보안 위반 로깅"""
            if error.category.value == "security":
                await self.event_bus.publish("security_violation", {
                    "plugin_id": error.plugin_id,
                    "user_id": error.user_id,
                    "error_code": error.code.value,
                    "timestamp": error.timestamp.isoformat(),
                    "details": error.details
                })
        
        async def update_performance_metrics(error: PluginException):
            """성능 메트릭 업데이트"""
            self.performance_metrics["failed_executions"] += 1
            
            if error.plugin_id:
                await self.performance_monitor.record_error(error.plugin_id, error.code.value)
        
        # 콜백 등록
        self.error_handler.add_error_callback(log_security_violations)
        self.error_handler.add_error_callback(update_performance_metrics)
    
    async def create_security_context(
        self,
        user_id: str,
        user_role: UserRole,
        session_id: str,
        ip_address: Optional[str] = None
    ) -> SecurityContext:
        """보안 컨텍스트 생성"""
        return self.security_manager.create_security_context(
            user_id, user_role, session_id, ip_address
        )
    
    @handle_plugin_errors(attempt_recovery=True)
    async def execute_single_agent(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        security_context: SecurityContext,
        priority: int = 5,
        use_queue: bool = False
    ) -> AgentExecutionResult:
        """단일 Agent 실행 (향상된 버전)"""
        
        # 요청 검증
        request = SecureAgentExecutionRequest(
            agent_type=agent_type,
            input_data=input_data,
            priority=priority
        )
        
        validation_result = self.security_manager.validate_execution_request(
            request, security_context
        )
        
        if not validation_result.is_valid:
            raise PluginExecutionException(
                "Request validation failed",
                execution_context={
                    "agent_type": agent_type,
                    "validation_threats": [t.description for t in validation_result.threats]
                },
                plugin_id=agent_type,
                user_id=security_context.user_id
            )
        
        # 큐 사용 여부 결정
        if use_queue or self.current_executions >= self.max_concurrent_executions:
            return await self._queue_execution(request, security_context)
        
        # 직접 실행
        return await self._execute_single_agent_internal(agent_type, input_data, security_context)
    
    async def _queue_execution(
        self,
        request: SecureAgentExecutionRequest,
        security_context: SecurityContext
    ) -> AgentExecutionResult:
        """실행 요청을 큐에 추가"""
        
        # 결과를 받을 Future 생성
        result_future = asyncio.Future()
        
        async def callback(result):
            result_future.set_result(result)
        
        execution_request = {
            "agent_type": request.agent_type,
            "input_data": request.input_data,
            "security_context": security_context,
            "callback": callback
        }
        
        # 우선순위 큐에 추가 (낮은 숫자가 높은 우선순위)
        await self.execution_queue.put((request.priority, execution_request))
        
        # 결과 대기
        return await result_future
    
    async def _execute_single_agent_internal(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        security_context: SecurityContext
    ) -> AgentExecutionResult:
        """내부 Agent 실행 로직"""
        
        async with plugin_error_context(
            plugin_id=agent_type,
            user_id=security_context.user_id,
            operation="single_agent_execution"
        ) as trace_id:
            
            # 동시 실행 제한
            async with self.execution_semaphore:
                self.current_executions += 1
                self.performance_metrics["peak_concurrent_executions"] = max(
                    self.performance_metrics["peak_concurrent_executions"],
                    self.current_executions
                )
                
                try:
                    return await self._execute_with_monitoring(
                        agent_type, input_data, security_context, trace_id
                    )
                finally:
                    self.current_executions -= 1
    
    async def _execute_with_monitoring(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        security_context: SecurityContext,
        trace_id: str
    ) -> AgentExecutionResult:
        """모니터링과 함께 실행"""
        
        start_time = datetime.now()
        metrics = ExecutionMetrics(start_time=start_time)
        
        try:
            # 캐시 확인
            cache_key = self._generate_cache_key(agent_type, input_data, security_context.user_id)
            cached_result = await self.cache_manager.get("execution_results", cache_key)
            
            if cached_result:
                logger.info(f"Cache hit for {agent_type} execution: {trace_id}")
                return AgentExecutionResult(
                    success=True,
                    result=cached_result,
                    execution_time=0.0,
                    trace_id=trace_id,
                    agent_type=agent_type,
                    user_id=security_context.user_id
                )
            
            # Agent 가져오기
            agent = await self.registry.get_agent(agent_type)
            if not agent:
                raise PluginExecutionException(
                    f"Agent not found: {agent_type}",
                    execution_context={"available_agents": await self.registry.list_agents()},
                    plugin_id=agent_type,
                    user_id=security_context.user_id
                )
            
            # 실행 컨텍스트 생성
            execution_context = AgentExecutionContext(
                user_id=security_context.user_id,
                session_id=security_context.session_id,
                trace_id=trace_id,
                metadata={
                    "agent_type": agent_type,
                    "user_role": security_context.user_role.value,
                    "ip_address": security_context.ip_address
                }
            )
            
            # Agent 실행
            result = await asyncio.wait_for(
                agent.execute(input_data, execution_context),
                timeout=300  # 5분 타임아웃
            )
            
            # 실행 완료 메트릭
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            metrics.end_time = end_time
            metrics.duration_ms = execution_time * 1000
            metrics.success = True
            
            # 성능 메트릭 업데이트
            self.performance_metrics["total_executions"] += 1
            self.performance_metrics["successful_executions"] += 1
            self._update_average_execution_time(execution_time)
            
            # 결과 캐싱 (성공한 경우만)
            if result and isinstance(result, dict):
                await self.cache_manager.set(
                    "execution_results", 
                    cache_key, 
                    result, 
                    ttl=300  # 5분 캐시
                )
            
            # 실행 이력 저장
            self.execution_history.add({
                "timestamp": start_time.isoformat(),
                "agent_type": agent_type,
                "user_id": security_context.user_id,
                "execution_time": execution_time,
                "success": True,
                "trace_id": trace_id
            })
            
            return AgentExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metrics=metrics,
                trace_id=trace_id,
                agent_type=agent_type,
                user_id=security_context.user_id
            )
            
        except asyncio.TimeoutError:
            metrics.success = False
            metrics.error_message = "Execution timeout"
            
            self.performance_metrics["failed_executions"] += 1
            
            raise PluginTimeoutError(
                timeout_seconds=300,
                operation="agent_execution",
                plugin_id=agent_type,
                user_id=security_context.user_id,
                trace_id=trace_id
            )
            
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            
            self.performance_metrics["failed_executions"] += 1
            
            # 실행 이력 저장 (실패한 경우도)
            execution_time = (datetime.now() - start_time).total_seconds()
            self.execution_history.add({
                "timestamp": start_time.isoformat(),
                "agent_type": agent_type,
                "user_id": security_context.user_id,
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "trace_id": trace_id
            })
            
            raise
    
    def _generate_cache_key(self, agent_type: str, input_data: Dict[str, Any], user_id: str) -> str:
        """캐시 키 생성"""
        import hashlib
        import json
        
        # 입력 데이터를 정규화하여 해시 생성
        normalized_data = json.dumps(input_data, sort_keys=True, ensure_ascii=False)
        data_hash = hashlib.md5(normalized_data.encode()).hexdigest()
        
        return f"{agent_type}:{user_id}:{data_hash}"
    
    def _update_average_execution_time(self, execution_time: float):
        """평균 실행 시간 업데이트"""
        total = self.performance_metrics["total_executions"]
        current_avg = self.performance_metrics["average_execution_time"]
        
        # 이동 평균 계산
        new_avg = ((current_avg * (total - 1)) + execution_time) / total
        self.performance_metrics["average_execution_time"] = new_avg
    
    async def _get_plugin_error_count(self, plugin_id: str, hours: int = 1) -> int:
        """플러그인 에러 횟수 조회"""
        error_stats = self.error_handler.get_plugin_error_summary(plugin_id, hours)
        return error_stats.get("total_errors", 0)
    
    async def execute_orchestration(
        self,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        security_context: SecurityContext,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """오케스트레이션 실행 (향상된 버전)"""
        
        async with plugin_error_context(
            plugin_id="orchestration",
            user_id=security_context.user_id,
            operation=f"orchestration_{pattern}"
        ) as trace_id:
            
            # 권한 확인
            if not self.security_manager.permission_manager.has_permission(
                security_context.user_id,
                security_context.user_role,
                PluginPermission.EXECUTE
            ):
                raise PluginExecutionException(
                    "Insufficient permissions for orchestration",
                    execution_context={"pattern": pattern, "agents": agents},
                    user_id=security_context.user_id,
                    trace_id=trace_id
                )
            
            try:
                result = await self.registry.execute_orchestration(
                    pattern, agents, task, security_context.user_id, config
                )
                
                # 보안 이벤트 로깅
                self.security_manager.log_security_event(
                    "orchestration_executed",
                    security_context.user_id,
                    {
                        "pattern": pattern,
                        "agents": agents,
                        "trace_id": trace_id,
                        "success": True
                    }
                )
                
                return result
                
            except Exception as e:
                # 보안 이벤트 로깅
                self.security_manager.log_security_event(
                    "orchestration_failed",
                    security_context.user_id,
                    {
                        "pattern": pattern,
                        "agents": agents,
                        "trace_id": trace_id,
                        "error": str(e)
                    },
                    "error"
                )
                raise
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 정보"""
        return {
            "metrics": self.performance_metrics,
            "current_executions": self.current_executions,
            "queue_size": self.execution_queue.qsize(),
            "cache_stats": await self.cache_manager.get_cache_stats(),
            "error_stats": self.error_handler.get_error_statistics(),
            "uptime": (datetime.now() - datetime.now()).total_seconds() if self._initialized else 0
        }
    
    async def get_security_summary(self, user_id: str) -> Dict[str, Any]:
        """보안 요약 정보"""
        return self.security_manager.get_security_summary(user_id)
    
    async def shutdown(self):
        """매니저 종료"""
        logger.info("Shutting down Enhanced Agent Plugin Manager...")
        
        self._shutdown = True
        
        # 큐 프로세서 종료
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # 진행 중인 실행 완료 대기 (최대 30초)
        wait_time = 0
        while self.current_executions > 0 and wait_time < 30:
            await asyncio.sleep(1)
            wait_time += 1
        
        # 각 컴포넌트 종료
        if self.lifecycle_manager:
            await self.lifecycle_manager.stop_health_monitoring()
        
        if self.performance_monitor:
            await self.performance_monitor.stop_cleanup_task()
        
        if self.cache_manager:
            await self.cache_manager.shutdown()
        
        if self.event_bus:
            await self.event_bus.stop_consuming()
        
        logger.info("Enhanced Agent Plugin Manager shutdown complete")


# 전역 인스턴스
enhanced_agent_plugin_manager = EnhancedAgentPluginManager()