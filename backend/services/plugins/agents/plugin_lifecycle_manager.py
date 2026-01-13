"""
Plugin Lifecycle Manager

Plugin의 생명주기를 상태 기반으로 관리하는 시스템
"""
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass

from backend.services.plugins.agents.base_agent_plugin import IAgentPlugin
from backend.core.event_bus import EventBus


logger = logging.getLogger(__name__)


class PluginLifecycleState(Enum):
    """Plugin 생명주기 상태"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass
class HealthMetrics:
    """Plugin 건강 상태 메트릭"""
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    error_count: int = 0
    last_error_time: Optional[datetime] = None
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    def update_success(self, response_time: float):
        """성공 실행 시 메트릭 업데이트"""
        self.avg_response_time = (self.avg_response_time + response_time) / 2
        
    def update_error(self):
        """에러 발생 시 메트릭 업데이트"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        # 성공률 재계산 (간단한 예시)
        total_requests = max(1, self.error_count * 10)  # 추정값
        self.success_rate = max(0.0, 1.0 - (self.error_count / total_requests))


@dataclass
class StateTransitionRule:
    """상태 전환 규칙"""
    from_state: PluginLifecycleState
    to_state: PluginLifecycleState
    condition: Callable[['EnhancedAgentPlugin'], bool]
    action: Optional[Callable[['EnhancedAgentPlugin'], None]] = None


class EnhancedAgentPlugin:
    """생명주기 관리가 강화된 Agent Plugin"""
    
    def __init__(self, base_plugin: IAgentPlugin, event_bus: EventBus):
        self.base_plugin = base_plugin
        self.event_bus = event_bus
        self.state = PluginLifecycleState.INITIALIZING
        self.health_metrics = HealthMetrics()
        self.state_history: List[Dict[str, Any]] = []
        self.transition_rules = self._setup_transition_rules()
        self.last_health_check = datetime.now()
        
    def _setup_transition_rules(self) -> List[StateTransitionRule]:
        """상태 전환 규칙 설정"""
        return [
            # INITIALIZING → ACTIVE
            StateTransitionRule(
                from_state=PluginLifecycleState.INITIALIZING,
                to_state=PluginLifecycleState.ACTIVE,
                condition=lambda p: p.health_metrics.success_rate > 0.8,
                action=self._on_activation
            ),
            
            # ACTIVE → DEGRADED
            StateTransitionRule(
                from_state=PluginLifecycleState.ACTIVE,
                to_state=PluginLifecycleState.DEGRADED,
                condition=lambda p: p.health_metrics.success_rate < 0.7,
                action=self._on_degradation
            ),
            
            # DEGRADED → FAILED
            StateTransitionRule(
                from_state=PluginLifecycleState.DEGRADED,
                to_state=PluginLifecycleState.FAILED,
                condition=lambda p: p.health_metrics.success_rate < 0.3,
                action=self._on_failure
            ),
            
            # DEGRADED → ACTIVE (복구)
            StateTransitionRule(
                from_state=PluginLifecycleState.DEGRADED,
                to_state=PluginLifecycleState.ACTIVE,
                condition=lambda p: p.health_metrics.success_rate > 0.8,
                action=self._on_recovery
            ),
            
            # FAILED → MAINTENANCE
            StateTransitionRule(
                from_state=PluginLifecycleState.FAILED,
                to_state=PluginLifecycleState.MAINTENANCE,
                condition=lambda p: True,  # 수동 전환
                action=self._on_maintenance_start
            )
        ]
    
    async def transition_state(self, new_state: PluginLifecycleState, force: bool = False):
        """상태 전환"""
        if not force and not self._can_transition(self.state, new_state):
            logger.warning(f"Invalid state transition: {self.state} → {new_state}")
            return False
        
        old_state = self.state
        self.state = new_state
        
        # 상태 이력 기록
        self.state_history.append({
            'from_state': old_state.value,
            'to_state': new_state.value,
            'timestamp': datetime.now().isoformat(),
            'health_metrics': {
                'success_rate': self.health_metrics.success_rate,
                'error_count': self.health_metrics.error_count,
                'avg_response_time': self.health_metrics.avg_response_time
            }
        })
        
        # 상태 변경 이벤트 발행
        await self._emit_state_change_event(old_state, new_state)
        
        # 전환 액션 실행
        rule = self._find_transition_rule(old_state, new_state)
        if rule and rule.action:
            try:
                rule.action(self)
            except Exception as e:
                logger.error(f"State transition action failed: {e}")
        
        return True
    
    def _can_transition(self, from_state: PluginLifecycleState, to_state: PluginLifecycleState) -> bool:
        """상태 전환 가능 여부 확인"""
        return any(
            rule.from_state == from_state and rule.to_state == to_state
            for rule in self.transition_rules
        )
    
    def _find_transition_rule(
        self, 
        from_state: PluginLifecycleState, 
        to_state: PluginLifecycleState
    ) -> Optional[StateTransitionRule]:
        """상태 전환 규칙 찾기"""
        for rule in self.transition_rules:
            if rule.from_state == from_state and rule.to_state == to_state:
                return rule
        return None
    
    async def _emit_state_change_event(
        self, 
        old_state: PluginLifecycleState, 
        new_state: PluginLifecycleState
    ):
        """상태 변경 이벤트 발행"""
        await self.event_bus.publish(
            "plugin_state_changed",
            {
                "plugin_id": self.base_plugin.get_manifest().name,
                "plugin_type": self.base_plugin.get_agent_type(),
                "old_state": old_state.value,
                "new_state": new_state.value,
                "timestamp": datetime.now().isoformat(),
                "health_metrics": {
                    "success_rate": self.health_metrics.success_rate,
                    "error_count": self.health_metrics.error_count,
                    "avg_response_time": self.health_metrics.avg_response_time
                }
            }
        )
    
    async def check_health_and_transition(self):
        """건강 상태 확인 및 자동 상태 전환"""
        self.last_health_check = datetime.now()
        
        # 적용 가능한 전환 규칙 확인
        for rule in self.transition_rules:
            if rule.from_state == self.state and rule.condition(self):
                await self.transition_state(rule.to_state)
                break
    
    # 상태 전환 액션들
    def _on_activation(self):
        """활성화 시 액션"""
        logger.info(f"Plugin {self.base_plugin.get_agent_type()} activated")
    
    def _on_degradation(self):
        """성능 저하 시 액션"""
        logger.warning(f"Plugin {self.base_plugin.get_agent_type()} degraded")
    
    def _on_failure(self):
        """실패 시 액션"""
        logger.error(f"Plugin {self.base_plugin.get_agent_type()} failed")
    
    def _on_recovery(self):
        """복구 시 액션"""
        logger.info(f"Plugin {self.base_plugin.get_agent_type()} recovered")
    
    def _on_maintenance_start(self):
        """유지보수 시작 시 액션"""
        logger.info(f"Plugin {self.base_plugin.get_agent_type()} entering maintenance")
    
    # 기존 Plugin 인터페이스 위임
    def get_agent_type(self) -> str:
        return self.base_plugin.get_agent_type()
    
    def get_capabilities(self):
        return self.base_plugin.get_capabilities()
    
    def get_manifest(self):
        return self.base_plugin.get_manifest()
    
    async def execute_agent(self, input_data: Dict[str, Any], context):
        """Agent 실행 (메트릭 수집 포함)"""
        start_time = datetime.now()
        
        try:
            result = self.base_plugin.execute_agent(input_data, context)
            
            # 성공 메트릭 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            self.health_metrics.update_success(execution_time)
            
            return result
            
        except Exception as e:
            # 에러 메트릭 업데이트
            self.health_metrics.update_error()
            
            # 건강 상태 확인 및 상태 전환
            await self.check_health_and_transition()
            
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """확장된 건강 상태 정보"""
        base_status = self.base_plugin.get_health_status()
        
        return {
            **base_status,
            "lifecycle_state": self.state.value,
            "health_metrics": {
                "success_rate": self.health_metrics.success_rate,
                "avg_response_time": self.health_metrics.avg_response_time,
                "error_count": self.health_metrics.error_count,
                "last_error_time": self.health_metrics.last_error_time.isoformat() if self.health_metrics.last_error_time else None,
                "memory_usage": self.health_metrics.memory_usage,
                "cpu_usage": self.health_metrics.cpu_usage
            },
            "last_health_check": self.last_health_check.isoformat(),
            "state_history": self.state_history[-5:]  # 최근 5개 상태 변경 이력
        }


class PluginLifecycleManager:
    """Plugin 생명주기 관리자"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.enhanced_plugins: Dict[str, EnhancedAgentPlugin] = {}
        self.health_check_interval = 30  # 30초마다 건강 상태 확인
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def register_plugin(self, plugin: IAgentPlugin) -> EnhancedAgentPlugin:
        """Plugin을 생명주기 관리 시스템에 등록"""
        enhanced_plugin = EnhancedAgentPlugin(plugin, self.event_bus)
        plugin_id = plugin.get_manifest().name
        
        self.enhanced_plugins[plugin_id] = enhanced_plugin
        
        # 초기화 상태로 시작
        await enhanced_plugin.transition_state(PluginLifecycleState.INITIALIZING)
        
        return enhanced_plugin
    
    async def unregister_plugin(self, plugin_id: str):
        """Plugin 등록 해제"""
        if plugin_id in self.enhanced_plugins:
            plugin = self.enhanced_plugins[plugin_id]
            await plugin.transition_state(PluginLifecycleState.SHUTDOWN, force=True)
            del self.enhanced_plugins[plugin_id]
    
    async def start_health_monitoring(self):
        """건강 상태 모니터링 시작"""
        if self._health_check_task is None or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop_health_monitoring(self):
        """건강 상태 모니터링 중지"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    
    async def _health_check_loop(self):
        """건강 상태 확인 루프"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # 모든 Plugin의 건강 상태 확인
                for plugin in self.enhanced_plugins.values():
                    await plugin.check_health_and_transition()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    def get_plugin_status_summary(self) -> Dict[str, Any]:
        """전체 Plugin 상태 요약"""
        state_counts = {}
        total_plugins = len(self.enhanced_plugins)
        
        for plugin in self.enhanced_plugins.values():
            state = plugin.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "total_plugins": total_plugins,
            "state_distribution": state_counts,
            "healthy_plugins": state_counts.get("active", 0),
            "degraded_plugins": state_counts.get("degraded", 0),
            "failed_plugins": state_counts.get("failed", 0),
            "health_check_interval": self.health_check_interval,
            "last_check": datetime.now().isoformat()
        }
    
    def get_plugin(self, plugin_id: str) -> Optional[EnhancedAgentPlugin]:
        """Plugin 조회"""
        return self.enhanced_plugins.get(plugin_id)
    
    def list_plugins_by_state(self, state: PluginLifecycleState) -> List[EnhancedAgentPlugin]:
        """특정 상태의 Plugin 목록"""
        return [
            plugin for plugin in self.enhanced_plugins.values()
            if plugin.state == state
        ]