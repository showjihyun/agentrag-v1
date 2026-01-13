"""
Custom Agent Plugin Factory

기존 Agent Builder에서 생성된 Agent들을 Plugin으로 변환하는 팩토리
"""
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy.orm import Session

from backend.services.plugins.agents.custom_agent_plugin import CustomAgentPlugin
from backend.services.plugins.agents.base_agent_plugin import IAgentPlugin
from backend.models.agent_builder import AgentResponse
from backend.db.models.agent_builder import Agent as AgentModel
from backend.services.agent_builder.agent_service import AgentService
from backend.db.database import get_db


logger = logging.getLogger(__name__)


class CustomAgentPluginFactory:
    """Custom Agent를 Plugin으로 변환하는 팩토리"""
    
    def __init__(self, agent_service: AgentService = None):
        if agent_service is None:
            # 기본 DB 세션 생성
            from backend.db.database import get_db
            db_session = next(get_db())
            agent_service = AgentService(db_session)
            
        self.agent_service = agent_service
        self._plugin_cache: Dict[str, CustomAgentPlugin] = {}
    
    async def create_plugin_from_agent_id(
        self, 
        agent_id: str, 
        user_id: str,
        config: Dict[str, Any] = None
    ) -> Optional[CustomAgentPlugin]:
        """Agent ID로부터 Plugin 생성"""
        try:
            # 캐시 확인
            cache_key = f"{agent_id}_{user_id}"
            if cache_key in self._plugin_cache:
                logger.info(f"Returning cached plugin for agent {agent_id}")
                return self._plugin_cache[cache_key]
            
            # Agent 데이터 조회
            agent_data = await self._get_agent_data(agent_id, user_id)
            if not agent_data:
                logger.error(f"Agent not found: {agent_id}")
                return None
            
            # Plugin 생성
            plugin = CustomAgentPlugin(agent_data, config or {})
            
            # 초기화
            success = plugin.initialize(config or {})
            if not success:
                logger.error(f"Failed to initialize plugin for agent {agent_id}")
                return None
            
            # 캐시에 저장
            self._plugin_cache[cache_key] = plugin
            
            logger.info(f"Created custom agent plugin for agent {agent_id}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to create plugin for agent {agent_id}: {e}")
            return None
    
    async def create_plugin_from_agent_data(
        self, 
        agent_data: AgentResponse,
        config: Dict[str, Any] = None
    ) -> Optional[CustomAgentPlugin]:
        """Agent 데이터로부터 직접 Plugin 생성"""
        try:
            # Plugin 생성
            plugin = CustomAgentPlugin(agent_data, config or {})
            
            # 초기화
            success = plugin.initialize(config or {})
            if not success:
                logger.error(f"Failed to initialize plugin for agent {agent_data.id}")
                return None
            
            # 캐시에 저장
            cache_key = f"{agent_data.id}_{agent_data.user_id}"
            self._plugin_cache[cache_key] = plugin
            
            logger.info(f"Created custom agent plugin for agent {agent_data.id}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to create plugin for agent {agent_data.id}: {e}")
            return None
    
    async def get_user_agent_plugins(
        self, 
        user_id: str,
        include_public: bool = True
    ) -> List[CustomAgentPlugin]:
        """사용자의 모든 Agent를 Plugin으로 변환"""
        plugins = []
        
        try:
            # 사용자 Agent 목록 조회
            agents = await self._get_user_agents(user_id, include_public)
            
            # 각 Agent를 Plugin으로 변환
            for agent_data in agents:
                plugin = await self.create_plugin_from_agent_data(agent_data)
                if plugin:
                    plugins.append(plugin)
            
            logger.info(f"Created {len(plugins)} custom agent plugins for user {user_id}")
            return plugins
            
        except Exception as e:
            logger.error(f"Failed to get user agent plugins for {user_id}: {e}")
            return []
    
    async def refresh_plugin(self, agent_id: str, user_id: str) -> Optional[CustomAgentPlugin]:
        """Plugin 캐시 갱신"""
        try:
            # 캐시에서 제거
            cache_key = f"{agent_id}_{user_id}"
            if cache_key in self._plugin_cache:
                del self._plugin_cache[cache_key]
            
            # 새로 생성
            return await self.create_plugin_from_agent_id(agent_id, user_id)
            
        except Exception as e:
            logger.error(f"Failed to refresh plugin for agent {agent_id}: {e}")
            return None
    
    def remove_plugin_from_cache(self, agent_id: str, user_id: str):
        """캐시에서 Plugin 제거"""
        cache_key = f"{agent_id}_{user_id}"
        if cache_key in self._plugin_cache:
            del self._plugin_cache[cache_key]
            logger.info(f"Removed plugin from cache: {agent_id}")
    
    def get_cached_plugin(self, agent_id: str, user_id: str) -> Optional[CustomAgentPlugin]:
        """캐시된 Plugin 반환"""
        cache_key = f"{agent_id}_{user_id}"
        return self._plugin_cache.get(cache_key)
    
    def clear_cache(self):
        """전체 캐시 클리어"""
        self._plugin_cache.clear()
        logger.info("Cleared all custom agent plugin cache")
    
    async def _get_agent_data(self, agent_id: str, user_id: str) -> Optional[AgentResponse]:
        """Agent 데이터 조회"""
        try:
            # Agent Service를 통한 조회
            agent = await self.agent_service.get_agent(agent_id, user_id)
            if not agent:
                return None
            
            # AgentResponse로 변환
            return AgentResponse(
                id=agent.id,
                user_id=agent.user_id,
                name=agent.name,
                description=agent.description,
                agent_type=agent.agent_type,
                template_id=agent.template_id,
                llm_provider=agent.llm_provider,
                llm_model=agent.llm_model,
                prompt_template_id=agent.prompt_template_id,
                configuration=agent.configuration,
                is_public=agent.is_public,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
                deleted_at=agent.deleted_at,
                tools=agent.tools or [],
                knowledgebases=agent.knowledgebases or [],
                version_count=getattr(agent, 'version_count', 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get agent data for {agent_id}: {e}")
            return None
    
    async def _get_user_agents(
        self, 
        user_id: str, 
        include_public: bool = True
    ) -> List[AgentResponse]:
        """사용자 Agent 목록 조회"""
        try:
            # Agent Service를 통한 조회
            agents = await self.agent_service.list_agents(
                user_id=user_id,
                include_public=include_public,
                limit=100  # 적절한 제한
            )
            
            # AgentResponse 리스트로 변환
            agent_responses = []
            for agent in agents:
                agent_response = AgentResponse(
                    id=agent.id,
                    user_id=agent.user_id,
                    name=agent.name,
                    description=agent.description,
                    agent_type=agent.agent_type,
                    template_id=agent.template_id,
                    llm_provider=agent.llm_provider,
                    llm_model=agent.llm_model,
                    prompt_template_id=agent.prompt_template_id,
                    configuration=agent.configuration,
                    is_public=agent.is_public,
                    created_at=agent.created_at,
                    updated_at=agent.updated_at,
                    deleted_at=agent.deleted_at,
                    tools=agent.tools or [],
                    knowledgebases=agent.knowledgebases or [],
                    version_count=getattr(agent, 'version_count', 0)
                )
                agent_responses.append(agent_response)
            
            return agent_responses
            
        except Exception as e:
            logger.error(f"Failed to get user agents for {user_id}: {e}")
            return []


class CustomAgentPluginManager:
    """Custom Agent Plugin 관리자"""
    
    def __init__(self):
        self.factory = CustomAgentPluginFactory()
        self._registered_plugins: Dict[str, CustomAgentPlugin] = {}
    
    async def register_user_agents_as_plugins(
        self, 
        user_id: str,
        include_public: bool = True
    ) -> List[str]:
        """사용자의 모든 Agent를 Plugin으로 등록"""
        registered_ids = []
        
        try:
            # 사용자 Agent Plugin들 생성
            plugins = await self.factory.get_user_agent_plugins(user_id, include_public)
            
            # Plugin Registry에 등록
            for plugin in plugins:
                plugin_id = f"custom_agent_{plugin.agent_data.id}"
                self._registered_plugins[plugin_id] = plugin
                registered_ids.append(plugin_id)
            
            logger.info(f"Registered {len(registered_ids)} custom agent plugins for user {user_id}")
            return registered_ids
            
        except Exception as e:
            logger.error(f"Failed to register user agent plugins for {user_id}: {e}")
            return []
    
    async def register_agent_as_plugin(
        self, 
        agent_id: str, 
        user_id: str,
        config: Dict[str, Any] = None
    ) -> Optional[str]:
        """특정 Agent를 Plugin으로 등록"""
        try:
            plugin = await self.factory.create_plugin_from_agent_id(agent_id, user_id, config)
            if not plugin:
                return None
            
            plugin_id = f"custom_agent_{agent_id}"
            self._registered_plugins[plugin_id] = plugin
            
            logger.info(f"Registered custom agent plugin: {plugin_id}")
            return plugin_id
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id} as plugin: {e}")
            return None
    
    def get_plugin(self, plugin_id: str) -> Optional[CustomAgentPlugin]:
        """등록된 Plugin 반환"""
        return self._registered_plugins.get(plugin_id)
    
    def get_all_plugins(self) -> Dict[str, CustomAgentPlugin]:
        """모든 등록된 Plugin 반환"""
        return self._registered_plugins.copy()
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """Plugin 등록 해제"""
        if plugin_id in self._registered_plugins:
            del self._registered_plugins[plugin_id]
            logger.info(f"Unregistered custom agent plugin: {plugin_id}")
            return True
        return False
    
    async def refresh_plugin(self, agent_id: str, user_id: str) -> bool:
        """Plugin 갱신"""
        try:
            plugin_id = f"custom_agent_{agent_id}"
            
            # 기존 Plugin 제거
            self.unregister_plugin(plugin_id)
            
            # 새로 등록
            new_plugin_id = await self.register_agent_as_plugin(agent_id, user_id)
            return new_plugin_id is not None
            
        except Exception as e:
            logger.error(f"Failed to refresh plugin for agent {agent_id}: {e}")
            return False
    
    def get_plugin_by_agent_id(self, agent_id: str) -> Optional[CustomAgentPlugin]:
        """Agent ID로 Plugin 찾기"""
        plugin_id = f"custom_agent_{agent_id}"
        return self.get_plugin(plugin_id)
    
    def list_plugins_by_user(self, user_id: str) -> List[CustomAgentPlugin]:
        """특정 사용자의 Plugin 목록"""
        user_plugins = []
        for plugin in self._registered_plugins.values():
            if plugin.agent_data.user_id == user_id:
                user_plugins.append(plugin)
        return user_plugins
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Plugin 통계"""
        total_plugins = len(self._registered_plugins)
        user_counts = {}
        
        for plugin in self._registered_plugins.values():
            user_id = plugin.agent_data.user_id
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        return {
            "total_plugins": total_plugins,
            "unique_users": len(user_counts),
            "plugins_per_user": user_counts,
            "average_plugins_per_user": total_plugins / len(user_counts) if user_counts else 0
        }


# 전역 인스턴스
_custom_agent_plugin_manager: Optional[CustomAgentPluginManager] = None


def get_custom_agent_plugin_manager() -> CustomAgentPluginManager:
    """Custom Agent Plugin Manager 싱글톤 인스턴스 반환"""
    global _custom_agent_plugin_manager
    
    if _custom_agent_plugin_manager is None:
        _custom_agent_plugin_manager = CustomAgentPluginManager()
    
    return _custom_agent_plugin_manager