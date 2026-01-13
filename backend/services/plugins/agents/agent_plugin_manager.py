"""
Agent Plugin Manager

Agent Plugin들의 생명주기를 관리하고 이벤트 기반 통신을 조정하는 통합 관리자
"""
from typing import Dict, List, Any, Optional, Type
import asyncio
import logging
from datetime import datetime

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
from backend.core.security.plugin_security import plugin_security_manager, PluginPermission
from backend.core.error_handling.plugin_errors import plugin_error_handler, PluginException, PluginErrorCode
from backend.core.utils.circular_buffer import ExecutionHistoryBuffer

logger = logging.getLogger(__name__)


class AgentPluginManager:
    """Agent Plugin 통합 관리자"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus or self._create_event_bus()
        self.registry = AgentPluginRegistry(self.event_bus)
        self.lifecycle_manager = PluginLifecycleManager(self.event_bus)
        self.performance_monitor = PluginPerformanceMonitor(self.event_bus)
        self.custom_agent_manager = get_custom_agent_plugin_manager()
        
        # 보안 및 에러 처리 매니저
        self.security_manager = plugin_security_manager
        self.error_handler = plugin_error_handler
        
        # 메모리 관리를 위한 실행 이력 버퍼
        self.execution_history = ExecutionHistoryBuffer(max_size=1000, max_age_hours=24)
        
        # 최적화 서비스 매니저 초기화
        self.optimization_manager: Optional[OptimizationServiceManager] = None
        
        self._initialized = False
        self._default_plugins: Dict[str, Type[IAgentPlugin]] = {
            "vector_search": VectorSearchAgentPlugin,
            "web_search": WebSearchAgentPlugin,
            "local_data": LocalDataAgentPlugin,
            "aggregator": AggregatorAgentPlugin
        }
        
    def _create_event_bus(self) -> EventBus:
        """Event Bus 인스턴스 생성"""
        redis_client = get_redis_client()
        return EventBus(redis_client)
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Agent Plugin Manager 초기화"""
        try:
            config = config or {}
            
            # Event Bus 시작
            await self.event_bus.start_consuming()
            
            # 생명주기 관리자 시작
            await self.lifecycle_manager.start_health_monitoring()
            
            # 성능 모니터링 시작
            await self.performance_monitor.start_cleanup_task()
            
            # 최적화 서비스 매니저 초기화
            await self._initialize_optimization_services()
            
            # 기본 Agent Plugin들 등록
            await self._register_default_plugins(config)
            
            # Custom Agent Plugin들 등록 (사용자별)
            await self._register_custom_agent_plugins(config)
            
            # 시스템 이벤트 핸들러 등록
            await self._setup_system_event_handlers()
            
            self._initialized = True
            logger.info("Agent Plugin Manager initialized successfully")
            
            # 초기화 완료 이벤트 발행
            await self.event_bus.publish(
                "agent_plugin_manager_initialized",
                {
                    "timestamp": datetime.now().isoformat(),
                    "registered_agents": list(self._default_plugins.keys()),
                    "event_bus_active": True,
                    "optimization_services_enabled": self.optimization_manager is not None
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Agent Plugin Manager: {e}")
            return False
    
    async def _register_default_plugins(self, config: Dict[str, Any]):
        """기본 Agent Plugin들 등록"""
        for agent_type, plugin_class in self._default_plugins.items():
            try:
                # Agent별 설정 추출
                agent_config = config.get(f"{agent_type}_config", {})
                
                # Plugin 인스턴스 생성
                plugin = plugin_class(agent_config)
                
                # 생명주기 관리자에 등록
                enhanced_plugin = await self.lifecycle_manager.register_plugin(plugin)
                
                # Plugin 등록
                success = await self.registry.register_agent_plugin(enhanced_plugin, agent_config)
                if success:
                    logger.info(f"Registered agent plugin: {agent_type}")
                else:
                    logger.error(f"Failed to register agent plugin: {agent_type}")
                    
            except Exception as e:
                logger.error(f"Error registering {agent_type} plugin: {e}")
    
    async def _register_custom_agent_plugins(self, config: Dict[str, Any]):
        """Custom Agent Plugin들 등록"""
        try:
            # 설정에서 사용자 목록 가져오기 (실제로는 활성 사용자 조회)
            users_to_register = config.get("custom_agent_users", [])
            
            if not users_to_register:
                # 기본적으로는 모든 활성 사용자의 Agent를 등록하지 않음
                # 필요시 개별적으로 등록
                logger.info("No custom agent users specified in config")
                return
            
            for user_id in users_to_register:
                try:
                    registered_ids = await self.custom_agent_manager.register_user_agents_as_plugins(
                        user_id, include_public=True
                    )
                    logger.info(f"Registered {len(registered_ids)} custom agents for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to register custom agents for user {user_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error registering custom agent plugins: {e}")
    
    async def _setup_system_event_handlers(self):
        """시스템 레벨 이벤트 핸들러 설정"""
        # Agent 생명주기 이벤트
        self.event_bus.subscribe("agent_plugin_install_request", self._handle_plugin_install)
        self.event_bus.subscribe("agent_plugin_uninstall_request", self._handle_plugin_uninstall)
        self.event_bus.subscribe("agent_plugin_update_request", self._handle_plugin_update)
        
        # 오케스트레이션 관리 이벤트
        self.event_bus.subscribe("orchestration_pattern_request", self._handle_orchestration_pattern_request)
        self.event_bus.subscribe("agent_health_check_request", self._handle_health_check_request)
        
        # Custom Agent 관리 이벤트
        self.event_bus.subscribe("custom_agent_created", self._handle_custom_agent_created)
        self.event_bus.subscribe("custom_agent_updated", self._handle_custom_agent_updated)
        self.event_bus.subscribe("custom_agent_deleted", self._handle_custom_agent_deleted)
        self.event_bus.subscribe("custom_agent_register_request", self._handle_custom_agent_register_request)
    
    async def execute_single_agent(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """단일 Agent 실행 (보안 및 에러 처리 강화)"""
        if not self._initialized:
            raise PluginException(
                code=PluginErrorCode.CONFIGURATION_ERROR,
                message="Agent Plugin Manager not initialized",
                plugin_id=agent_type,
                user_id=user_id
            )
        
        start_time = datetime.now()
        trace_id = f"{agent_type}_{start_time.timestamp()}"
        
        try:
            # 보안 검증
            if user_id:
                self.security_manager.validate_user_permissions(
                    user_id, PluginPermission.EXECUTE, agent_type
                )
                self.security_manager.check_rate_limit(user_id)
            
            # 입력 데이터 검증 및 정화
            validated_input = self.security_manager.validate_input_data(input_data)
            
            # 실행 컨텍스트 생성
            context = AgentExecutionContext(
                user_id=user_id,
                session_id=session_id,
                workflow_id=workflow_id,
                execution_metadata={
                    "execution_type": "single_agent",
                    "timestamp": start_time.isoformat(),
                    "trace_id": trace_id
                }
            )
            
            # Agent 실행
            result = await self.registry.execute_agent_with_communication(
                agent_type, validated_input, context
            )
            
            # 실행 이력 기록
            execution_data = {
                "agent_type": agent_type,
                "user_id": user_id,
                "success": True,
                "duration": (datetime.now() - start_time).total_seconds(),
                "timestamp": start_time.isoformat(),
                "trace_id": trace_id,
                "input_size": len(str(validated_input)),
                "output_size": len(str(result))
            }
            self.execution_history.add_execution(execution_data)
            
            return result
            
        except Exception as e:
            # 에러 처리
            plugin_exception = self.error_handler.handle_exception(
                e, agent_type, user_id, trace_id, 
                {"input_data": input_data, "context": context.__dict__ if 'context' in locals() else {}}
            )
            
            # 실행 이력 기록 (실패)
            execution_data = {
                "agent_type": agent_type,
                "user_id": user_id,
                "success": False,
                "duration": (datetime.now() - start_time).total_seconds(),
                "timestamp": start_time.isoformat(),
                "trace_id": trace_id,
                "error": str(plugin_exception),
                "error_code": plugin_exception.code.value
            }
            self.execution_history.add_execution(execution_data)
            
            raise plugin_exception
    
    async def execute_orchestration(
        self,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """다중 Agent 오케스트레이션 실행"""
        if not self._initialized:
            raise RuntimeError("Agent Plugin Manager not initialized")
        
        # 실행 컨텍스트 생성
        context = AgentExecutionContext(
            user_id=user_id,
            session_id=session_id,
            workflow_id=workflow_id,
            orchestration_pattern=pattern,
            execution_metadata={
                "execution_type": "orchestration",
                "pattern": pattern,
                "agent_count": len(agents),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 오케스트레이션 실행
        return await self.registry.orchestrate_agents(pattern, agents, task, context)
    
    async def install_agent_plugin(
        self,
        plugin_source: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """새로운 Agent Plugin 설치"""
        try:
            # 설치 요청 이벤트 발행
            install_id = f"install_{datetime.now().timestamp()}"
            await self.event_bus.publish(
                "agent_plugin_install_started",
                {
                    "install_id": install_id,
                    "plugin_source": plugin_source,
                    "config": config or {}
                }
            )
            
            # 실제 설치 로직 (여기서는 간단한 예시)
            # 실제 구현에서는 plugin_source에서 플러그인을 다운로드하고 검증
            
            # 설치 완료 이벤트 발행
            await self.event_bus.publish(
                "agent_plugin_install_completed",
                {
                    "install_id": install_id,
                    "success": True,
                    "plugin_info": {
                        "source": plugin_source,
                        "installed_at": datetime.now().isoformat()
                    }
                }
            )
            
            return {
                "success": True,
                "install_id": install_id,
                "message": "Plugin installed successfully"
            }
            
        except Exception as e:
            await self.event_bus.publish(
                "agent_plugin_install_failed",
                {
                    "install_id": install_id,
                    "error": str(e)
                }
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_agent_status(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Agent 상태 조회"""
        if agent_type:
            # 특정 Agent 상태
            agents = self.registry.get_available_agents()
            
            # 기본 Agent 검색
            for agent in agents:
                if agent["agent_type"] == agent_type:
                    return agent
            
            # Custom Agent 검색
            if agent_type.startswith("custom_"):
                agent_id = agent_type.replace("custom_", "")
                custom_plugin = self.custom_agent_manager.get_plugin_by_agent_id(agent_id)
                if custom_plugin:
                    return {
                        "agent_type": custom_plugin.get_agent_type(),
                        "agent_id": custom_plugin.agent_data.id,
                        "capabilities": [cap.dict() for cap in custom_plugin.get_capabilities()],
                        "health_status": custom_plugin.get_health_status(),
                        "communication_channel": f"custom_agent_{custom_plugin.agent_data.id}",
                        "is_custom": True,
                        "user_id": custom_plugin.agent_data.user_id
                    }
            
            return {"error": f"Agent not found: {agent_type}"}
        else:
            # 모든 Agent 상태
            base_agents = self.registry.get_available_agents()
            
            # Custom Agent들 추가
            custom_agents = []
            for plugin in self.custom_agent_manager.get_all_plugins().values():
                custom_agents.append({
                    "agent_type": plugin.get_agent_type(),
                    "agent_id": plugin.agent_data.id,
                    "capabilities": [cap.dict() for cap in plugin.get_capabilities()],
                    "health_status": plugin.get_health_status(),
                    "communication_channel": f"custom_agent_{plugin.agent_data.id}",
                    "is_custom": True,
                    "user_id": plugin.agent_data.user_id
                })
            
            all_agents = base_agents + custom_agents
            
            return {
                "agents": all_agents,
                "orchestration_patterns": self.registry.get_orchestration_patterns(),
                "manager_status": {
                    "initialized": self._initialized,
                    "event_bus_active": True,
                    "registered_plugins": len(self._default_plugins),
                    "custom_agents": len(custom_agents)
                }
            }
    
    async def execute_workflow(
        self,
        workflow_definition: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """워크플로우 실행 (복합 Agent 작업)"""
        workflow_id = f"workflow_{datetime.now().timestamp()}"
        
        try:
            # 워크플로우 시작 이벤트
            await self.event_bus.publish(
                "workflow_started",
                {
                    "workflow_id": workflow_id,
                    "definition": workflow_definition,
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
            
            steps = workflow_definition.get("steps", [])
            results = {}
            
            for step in steps:
                step_type = step.get("type")
                step_config = step.get("config", {})
                
                if step_type == "single_agent":
                    # 단일 Agent 실행
                    result = await self.execute_single_agent(
                        step_config["agent_type"],
                        step_config["input_data"],
                        user_id,
                        session_id,
                        workflow_id
                    )
                elif step_type == "orchestration":
                    # 오케스트레이션 실행
                    result = await self.execute_orchestration(
                        step_config["pattern"],
                        step_config["agents"],
                        step_config["task"],
                        user_id,
                        session_id,
                        workflow_id
                    )
                else:
                    result = {"error": f"Unknown step type: {step_type}"}
                
                results[step.get("name", f"step_{len(results)}")] = result
            
            # 워크플로우 완료 이벤트
            await self.event_bus.publish(
                "workflow_completed",
                {
                    "workflow_id": workflow_id,
                    "results": results,
                    "success": True
                }
            )
            
            return {
                "workflow_id": workflow_id,
                "success": True,
                "results": results
            }
            
        except Exception as e:
            # 워크플로우 실패 이벤트
            await self.event_bus.publish(
                "workflow_failed",
                {
                    "workflow_id": workflow_id,
                    "error": str(e)
                }
            )
            
            return {
                "workflow_id": workflow_id,
                "success": False,
                "error": str(e)
            }
    
    # Custom Agent 관리 메서드들
    async def register_custom_agent_as_plugin(
        self,
        agent_id: str,
        user_id: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Custom Agent를 Plugin으로 등록"""
        try:
            plugin_id = await self.custom_agent_manager.register_agent_as_plugin(
                agent_id, user_id, config
            )
            
            if plugin_id:
                return {
                    "success": True,
                    "plugin_id": plugin_id,
                    "agent_id": agent_id,
                    "message": "Custom agent registered as plugin successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to register custom agent as plugin"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def unregister_custom_agent_plugin(
        self,
        agent_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Custom Agent Plugin 등록 해제"""
        try:
            plugin_id = f"custom_agent_{agent_id}"
            success = self.custom_agent_manager.unregister_plugin(plugin_id)
            
            return {
                "success": success,
                "plugin_id": plugin_id if success else None,
                "message": "Custom agent plugin unregistered successfully" if success else "Plugin not found"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_custom_agent_plugin(
        self,
        agent_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Custom Agent Plugin 갱신"""
        try:
            success = await self.custom_agent_manager.refresh_plugin(agent_id, user_id)
            
            return {
                "success": success,
                "agent_id": agent_id,
                "message": "Custom agent plugin refreshed successfully" if success else "Failed to refresh plugin"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_custom_agents(self, user_id: str) -> Dict[str, Any]:
        """사용자의 Custom Agent 목록"""
        try:
            plugins = self.custom_agent_manager.list_plugins_by_user(user_id)
            
            agent_list = []
            for plugin in plugins:
                agent_list.append({
                    "agent_id": plugin.agent_data.id,
                    "agent_name": plugin.agent_data.name,
                    "agent_type": plugin.get_agent_type(),
                    "description": plugin.agent_data.description,
                    "capabilities": [cap.name for cap in plugin.get_capabilities()],
                    "health_status": plugin.get_health_status(),
                    "is_registered": True
                })
            
            return {
                "success": True,
                "agents": agent_list,
                "total": len(agent_list)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agents": [],
                "total": 0
            }
    
    async def execute_custom_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Custom Agent 실행"""
        try:
            # Custom Agent Plugin 찾기
            plugin = self.custom_agent_manager.get_plugin_by_agent_id(agent_id)
            if not plugin:
                return {
                    "success": False,
                    "error": f"Custom agent plugin not found: {agent_id}"
                }
            
            # 권한 확인 (사용자가 해당 Agent의 소유자인지)
            if user_id and plugin.agent_data.user_id != user_id and not plugin.agent_data.is_public:
                return {
                    "success": False,
                    "error": "Permission denied: You don't have access to this agent"
                }
            
            # 실행 컨텍스트 생성
            context = AgentExecutionContext(
                user_id=user_id,
                session_id=session_id,
                workflow_id=workflow_id,
                execution_metadata={
                    "execution_type": "custom_agent",
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Agent 실행
            result = plugin.execute_agent(input_data, context)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }
    
    # 이벤트 핸들러들
    async def _handle_plugin_install(self, event_data: Dict[str, Any]):
        """Plugin 설치 요청 처리"""
        plugin_source = event_data.get("plugin_source")
        config = event_data.get("config", {})
        
        result = await self.install_agent_plugin(plugin_source, config)
        
        # 결과 이벤트 발행
        await self.event_bus.publish(
            "agent_plugin_install_response",
            {
                "request_id": event_data.get("request_id"),
                "result": result
            }
        )
    
    async def _handle_plugin_uninstall(self, event_data: Dict[str, Any]):
        """Plugin 제거 요청 처리"""
        # 제거 로직 구현
        pass
    
    async def _handle_plugin_update(self, event_data: Dict[str, Any]):
        """Plugin 업데이트 요청 처리"""
        # 업데이트 로직 구현
        pass
    
    async def _handle_orchestration_pattern_request(self, event_data: Dict[str, Any]):
        """오케스트레이션 패턴 요청 처리"""
        patterns = self.registry.get_orchestration_patterns()
        
        await self.event_bus.publish(
            "orchestration_pattern_response",
            {
                "request_id": event_data.get("request_id"),
                "patterns": patterns
            }
        )
    
    async def _handle_health_check_request(self, event_data: Dict[str, Any]):
        """Agent 상태 확인 요청 처리"""
        agent_type = event_data.get("agent_type")
        status = await self.get_agent_status(agent_type)
        
        await self.event_bus.publish(
            "agent_health_check_response",
            {
                "request_id": event_data.get("request_id"),
                "agent_type": agent_type,
                "status": status
            }
        )
    
    async def _handle_communication_protocol_change(self, event_data: Dict[str, Any]):
        """통신 프로토콜 변경 처리"""
        # 프로토콜 변경 로직 구현
        pass
    
    async def _handle_agent_discovery_request(self, event_data: Dict[str, Any]):
        """Agent 발견 요청 처리"""
        agents = self.registry.get_available_agents()
        
        # Custom Agent들도 포함
        custom_agents = []
        for plugin in self.custom_agent_manager.get_all_plugins().values():
            custom_agents.append({
                "agent_type": plugin.get_agent_type(),
                "agent_id": plugin.agent_data.id,
                "capabilities": [cap.name for cap in plugin.get_capabilities()],
                "health_status": plugin.get_health_status(),
                "communication_channel": f"custom_agent_{plugin.agent_data.id}",
                "is_custom": True,
                "user_id": plugin.agent_data.user_id
            })
        
        all_agents = agents + custom_agents
        
        await self.event_bus.publish(
            "agent_discovery_response",
            {
                "request_id": event_data.get("request_id"),
                "agents": all_agents
            }
        )
    
    # Custom Agent 이벤트 핸들러들
    async def _handle_custom_agent_created(self, event_data: Dict[str, Any]):
        """Custom Agent 생성 이벤트 처리"""
        try:
            agent_id = event_data.get("agent_id")
            user_id = event_data.get("user_id")
            
            if agent_id and user_id:
                # 새로 생성된 Agent를 Plugin으로 등록
                plugin_id = await self.custom_agent_manager.register_agent_as_plugin(agent_id, user_id)
                if plugin_id:
                    logger.info(f"Registered new custom agent as plugin: {plugin_id}")
                    
                    # 등록 완료 이벤트 발행
                    await self.event_bus.publish(
                        "custom_agent_plugin_registered",
                        {
                            "agent_id": agent_id,
                            "plugin_id": plugin_id,
                            "user_id": user_id
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to handle custom agent created event: {e}")
    
    async def _handle_custom_agent_updated(self, event_data: Dict[str, Any]):
        """Custom Agent 업데이트 이벤트 처리"""
        try:
            agent_id = event_data.get("agent_id")
            user_id = event_data.get("user_id")
            
            if agent_id and user_id:
                # Plugin 갱신
                success = await self.custom_agent_manager.refresh_plugin(agent_id, user_id)
                if success:
                    logger.info(f"Refreshed custom agent plugin: {agent_id}")
                    
                    # 갱신 완료 이벤트 발행
                    await self.event_bus.publish(
                        "custom_agent_plugin_refreshed",
                        {
                            "agent_id": agent_id,
                            "user_id": user_id
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to handle custom agent updated event: {e}")
    
    async def _handle_custom_agent_deleted(self, event_data: Dict[str, Any]):
        """Custom Agent 삭제 이벤트 처리"""
        try:
            agent_id = event_data.get("agent_id")
            user_id = event_data.get("user_id")
            
            if agent_id and user_id:
                # Plugin 등록 해제
                plugin_id = f"custom_agent_{agent_id}"
                success = self.custom_agent_manager.unregister_plugin(plugin_id)
                if success:
                    logger.info(f"Unregistered custom agent plugin: {plugin_id}")
                    
                    # 등록 해제 완료 이벤트 발행
                    await self.event_bus.publish(
                        "custom_agent_plugin_unregistered",
                        {
                            "agent_id": agent_id,
                            "plugin_id": plugin_id,
                            "user_id": user_id
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to handle custom agent deleted event: {e}")
    
    async def _handle_custom_agent_register_request(self, event_data: Dict[str, Any]):
        """Custom Agent Plugin 등록 요청 처리"""
        try:
            agent_id = event_data.get("agent_id")
            user_id = event_data.get("user_id")
            config = event_data.get("config", {})
            
            if agent_id and user_id:
                plugin_id = await self.custom_agent_manager.register_agent_as_plugin(
                    agent_id, user_id, config
                )
                
                # 응답 이벤트 발행
                await self.event_bus.publish(
                    "custom_agent_register_response",
                    {
                        "request_id": event_data.get("request_id"),
                        "success": plugin_id is not None,
                        "plugin_id": plugin_id,
                        "agent_id": agent_id,
                        "user_id": user_id
                    }
                )
        except Exception as e:
            logger.error(f"Failed to handle custom agent register request: {e}")
            
            # 에러 응답 이벤트 발행
            await self.event_bus.publish(
                "custom_agent_register_response",
                {
                    "request_id": event_data.get("request_id"),
                    "success": False,
                    "error": str(e)
                }
            )
    
    # AI 기반 최적화 관련 메서드들
    
    async def _initialize_optimization_services(self):
        """최적화 서비스 초기화"""
        try:
            # ValidatedEventBus로 변환 (실제 구현에서는 적절한 변환 로직 필요)
            from backend.core.event_bus.validated_event_bus import ValidatedEventBus
            
            # 임시로 기본 이벤트 버스를 사용 (실제로는 ValidatedEventBus 인스턴스 필요)
            validated_event_bus = self.event_bus  # 실제 구현에서는 적절한 변환 필요
            
            self.optimization_manager = OptimizationServiceManager(
                performance_monitor=self.performance_monitor,
                event_bus=validated_event_bus
            )
            
            await self.optimization_manager.initialize_services()
            logger.info("Optimization services initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize optimization services: {e}")
            # 최적화 서비스 실패는 전체 시스템을 중단시키지 않음
            self.optimization_manager = None
    
    async def get_workflow_optimization_analysis(
        self,
        workflow_id: str,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        recent_executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """워크플로우 최적화 분석"""
        if not self.optimization_manager:
            return {
                'status': 'optimization_services_unavailable',
                'message': '최적화 서비스가 사용할 수 없습니다.'
            }
        
        try:
            return await self.optimization_manager.get_comprehensive_optimization_analysis(
                workflow_id, pattern, agents, task, recent_executions
            )
        except Exception as e:
            logger.error(f"Workflow optimization analysis failed: {e}")
            return {
                'status': 'analysis_failed',
                'error': str(e)
            }
    
    async def apply_optimization_recommendations(
        self,
        workflow_id: str,
        recommendations: List[str],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """최적화 추천사항 적용"""
        if not self.optimization_manager:
            return {
                'success': False,
                'error': 'Optimization services not available'
            }
        
        try:
            return await self.optimization_manager.apply_optimization_recommendations(
                workflow_id, recommendations, auto_apply
            )
        except Exception as e:
            logger.error(f"Failed to apply optimization recommendations: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def start_continuous_optimization(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """지속적인 최적화 시작"""
        if not self.optimization_manager:
            return {
                'success': False,
                'error': 'Optimization services not available'
            }
        
        try:
            from backend.services.optimization.auto_tuning_service import TuningConfiguration, TuningStrategy
            
            tuning_config = None
            if config:
                tuning_config = TuningConfiguration(
                    strategy=TuningStrategy(config.get('strategy', 'balanced')),
                    auto_apply=config.get('auto_apply', False),
                    tuning_interval_hours=config.get('interval_hours', 24),
                    min_improvement_threshold=config.get('min_improvement', 5.0)
                )
            
            return await self.optimization_manager.start_continuous_optimization(tuning_config)
            
        except Exception as e:
            logger.error(f"Failed to start continuous optimization: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def stop_continuous_optimization(self) -> Dict[str, Any]:
        """지속적인 최적화 중지"""
        if not self.optimization_manager:
            return {
                'success': False,
                'error': 'Optimization services not available'
            }
        
        try:
            return await self.optimization_manager.stop_continuous_optimization()
        except Exception as e:
            logger.error(f"Failed to stop continuous optimization: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_optimization_dashboard_data(self) -> Dict[str, Any]:
        """최적화 대시보드 데이터 조회"""
        if not self.optimization_manager:
            return {
                'status': 'optimization_services_unavailable',
                'message': '최적화 서비스가 사용할 수 없습니다.'
            }
        
        try:
            return await self.optimization_manager.get_optimization_dashboard_data()
        except Exception as e:
            logger.error(f"Failed to get optimization dashboard data: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # 기존 메서드들과의 호환성을 위한 속성 접근자들
    
    @property
    def optimizer(self):
        """ML 최적화기 접근자 (API 호환성용)"""
        if self.optimization_manager:
            return self.optimization_manager.ml_optimizer
        return None
    
    @property
    def auto_tuning_service(self):
        """자동 튜닝 서비스 접근자 (API 호환성용)"""
        if self.optimization_manager:
            return self.optimization_manager.auto_tuning_service
        return None
    
    @property
    def cost_optimization_engine(self):
        """비용 최적화 엔진 접근자 (API 호환성용)"""
        if self.optimization_manager:
            return self.optimization_manager.cost_optimization_engine
        return None
    
    async def shutdown(self):
        """Agent Plugin Manager 종료"""
        try:
            # 최적화 서비스 정리
            if self.optimization_manager:
                await self.optimization_manager.cleanup()
            
            # 종료 이벤트 발행
            await self.event_bus.publish(
                "agent_plugin_manager_shutdown",
                {
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Event Bus 정리
            if hasattr(self.event_bus, 'stop_consuming'):
                await self.event_bus.stop_consuming()
            
            self._initialized = False
            logger.info("Agent Plugin Manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# 전역 인스턴스 (싱글톤 패턴)
_agent_plugin_manager: Optional[AgentPluginManager] = None


async def get_agent_plugin_manager() -> AgentPluginManager:
    """Agent Plugin Manager 인스턴스 반환"""
    global _agent_plugin_manager
    
    if _agent_plugin_manager is None:
        _agent_plugin_manager = AgentPluginManager()
        await _agent_plugin_manager.initialize()
    
    return _agent_plugin_manager


async def initialize_agent_plugin_system(config: Dict[str, Any] = None) -> AgentPluginManager:
    """Agent Plugin 시스템 초기화"""
    manager = await get_agent_plugin_manager()
    
    if config:
        # 추가 설정이 있으면 재초기화
        await manager.initialize(config)
    
    return manager