"""
A2A Agent Registry.

외부 A2A 에이전트 설정을 관리하는 레지스트리.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid

from models.a2a import (
    A2AAgentConfig,
    A2AAgentConfigCreate,
    A2AAgentConfigUpdate,
    A2AAgentConfigResponse,
    A2AServerConfig,
    A2AServerConfigCreate,
    A2AServerConfigUpdate,
    A2AServerConfigResponse,
    AgentCard,
    ProtocolBinding,
)
from .client import A2AClient, A2AClientError

logger = logging.getLogger(__name__)


class A2AAgentRegistry:
    """
    A2A Agent Registry.
    
    외부 A2A 에이전트 연결 설정과 로컬 에이전트의 A2A 서버 설정을 관리합니다.
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize registry.
        
        Args:
            redis_client: Optional Redis client for persistent storage
        """
        self._redis = redis_client
        
        # In-memory storage (fallback)
        self._agent_configs: Dict[str, A2AAgentConfig] = {}
        self._server_configs: Dict[str, A2AServerConfig] = {}
        
        # Connection status cache
        self._connection_status: Dict[str, Dict[str, Any]] = {}
        
    # =========================================================================
    # External Agent Configuration (Client)
    # =========================================================================
    
    async def create_agent_config(
        self,
        user_id: str,
        config: A2AAgentConfigCreate,
    ) -> A2AAgentConfigResponse:
        """
        Create a new external A2A agent configuration.
        
        Args:
            user_id: Owner user ID
            config: Configuration to create
            
        Returns:
            Created configuration with status
        """
        config_id = str(uuid.uuid4())
        
        agent_config = A2AAgentConfig(
            id=config_id,
            name=config.name,
            description=config.description,
            agent_card_url=config.agent_card_url,
            base_url=config.base_url,
            protocol_binding=config.protocol_binding,
            auth_type=config.auth_type,
            auth_config=config.auth_config,
            headers=config.headers,
            timeout_seconds=config.timeout_seconds,
            retry_count=config.retry_count,
            enabled=config.enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Try to fetch agent card
        agent_card = None
        status = "disconnected"
        last_error = None
        
        if config.enabled:
            try:
                async with A2AClient(agent_config) as client:
                    agent_card = await client.fetch_agent_card()
                    agent_config.cached_agent_card = agent_card
                    status = "connected"
            except A2AClientError as e:
                last_error = str(e)
                status = "error"
            except Exception as e:
                last_error = str(e)
                status = "error"
                
        # Store configuration
        await self._store_agent_config(user_id, agent_config)
        
        # Update status cache
        self._connection_status[config_id] = {
            "status": status,
            "last_error": last_error,
            "last_check": datetime.utcnow().isoformat(),
        }
        
        return A2AAgentConfigResponse(
            config=agent_config,
            agent_card=agent_card,
            status=status,
            last_error=last_error,
        )
        
    async def get_agent_config(
        self,
        user_id: str,
        config_id: str,
    ) -> Optional[A2AAgentConfigResponse]:
        """
        Get agent configuration by ID.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            
        Returns:
            Configuration with status or None
        """
        agent_config = await self._load_agent_config(user_id, config_id)
        if not agent_config:
            return None
            
        status_info = self._connection_status.get(config_id, {})
        
        return A2AAgentConfigResponse(
            config=agent_config,
            agent_card=agent_config.cached_agent_card,
            status=status_info.get("status", "disconnected"),
            last_error=status_info.get("last_error"),
        )
        
    async def list_agent_configs(
        self,
        user_id: str,
        enabled_only: bool = False,
    ) -> List[A2AAgentConfigResponse]:
        """
        List all agent configurations for a user.
        
        Args:
            user_id: Owner user ID
            enabled_only: Only return enabled configs
            
        Returns:
            List of configurations with status
        """
        configs = await self._load_all_agent_configs(user_id)
        
        if enabled_only:
            configs = [c for c in configs if c.enabled]
            
        results = []
        for config in configs:
            status_info = self._connection_status.get(config.id, {})
            results.append(A2AAgentConfigResponse(
                config=config,
                agent_card=config.cached_agent_card,
                status=status_info.get("status", "disconnected"),
                last_error=status_info.get("last_error"),
            ))
            
        return results
        
    async def update_agent_config(
        self,
        user_id: str,
        config_id: str,
        update: A2AAgentConfigUpdate,
    ) -> Optional[A2AAgentConfigResponse]:
        """
        Update agent configuration.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            update: Update data
            
        Returns:
            Updated configuration or None
        """
        agent_config = await self._load_agent_config(user_id, config_id)
        if not agent_config:
            return None
            
        # Apply updates
        update_data = update.model_dump(exclude_unset=True, by_alias=False)
        for key, value in update_data.items():
            if hasattr(agent_config, key):
                setattr(agent_config, key, value)
                
        agent_config.updated_at = datetime.utcnow()
        
        # Re-fetch agent card if URL changed or re-enabled
        if update.agent_card_url or (update.enabled and not agent_config.cached_agent_card):
            try:
                async with A2AClient(agent_config) as client:
                    agent_card = await client.fetch_agent_card()
                    agent_config.cached_agent_card = agent_card
                    self._connection_status[config_id] = {
                        "status": "connected",
                        "last_error": None,
                        "last_check": datetime.utcnow().isoformat(),
                    }
            except Exception as e:
                self._connection_status[config_id] = {
                    "status": "error",
                    "last_error": str(e),
                    "last_check": datetime.utcnow().isoformat(),
                }
                
        await self._store_agent_config(user_id, agent_config)
        
        status_info = self._connection_status.get(config_id, {})
        return A2AAgentConfigResponse(
            config=agent_config,
            agent_card=agent_config.cached_agent_card,
            status=status_info.get("status", "disconnected"),
            last_error=status_info.get("last_error"),
        )
        
    async def delete_agent_config(
        self,
        user_id: str,
        config_id: str,
    ) -> bool:
        """
        Delete agent configuration.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            
        Returns:
            True if deleted
        """
        return await self._delete_agent_config(user_id, config_id)
        
    async def test_agent_connection(
        self,
        user_id: str,
        config_id: str,
    ) -> A2AAgentConfigResponse:
        """
        Test connection to external agent.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            
        Returns:
            Configuration with updated status
        """
        agent_config = await self._load_agent_config(user_id, config_id)
        if not agent_config:
            raise ValueError(f"Configuration not found: {config_id}")
            
        status = "disconnected"
        last_error = None
        agent_card = None
        
        try:
            async with A2AClient(agent_config) as client:
                agent_card = await client.fetch_agent_card()
                agent_config.cached_agent_card = agent_card
                status = "connected"
        except A2AClientError as e:
            last_error = str(e)
            status = "error"
        except Exception as e:
            last_error = str(e)
            status = "error"
            
        # Update status cache
        self._connection_status[config_id] = {
            "status": status,
            "last_error": last_error,
            "last_check": datetime.utcnow().isoformat(),
        }
        
        # Save updated agent card
        await self._store_agent_config(user_id, agent_config)
        
        return A2AAgentConfigResponse(
            config=agent_config,
            agent_card=agent_card,
            status=status,
            last_error=last_error,
        )
        
    async def get_client(
        self,
        user_id: str,
        config_id: str,
    ) -> A2AClient:
        """
        Get A2A client for a configuration.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            
        Returns:
            A2AClient instance
        """
        agent_config = await self._load_agent_config(user_id, config_id)
        if not agent_config:
            raise ValueError(f"Configuration not found: {config_id}")
            
        if not agent_config.enabled:
            raise ValueError(f"Agent is disabled: {config_id}")
            
        return A2AClient(agent_config)
        
    # =========================================================================
    # Local Agent A2A Server Configuration
    # =========================================================================
    
    async def create_server_config(
        self,
        user_id: str,
        config: A2AServerConfigCreate,
    ) -> A2AServerConfigResponse:
        """
        Create A2A server configuration for local agent.
        
        Args:
            user_id: Owner user ID
            config: Configuration to create
            
        Returns:
            Created configuration
        """
        config_id = str(uuid.uuid4())
        
        server_config = A2AServerConfig(
            id=config_id,
            agent_id=config.agent_id,
            workflow_id=config.workflow_id,
            name=config.name,
            description=config.description,
            version=config.version,
            skills=config.skills,
            streaming_enabled=config.streaming_enabled,
            push_notifications_enabled=config.push_notifications_enabled,
            require_auth=config.require_auth,
            allowed_auth_schemes=config.allowed_auth_schemes,
            rate_limit_per_minute=config.rate_limit_per_minute,
            enabled=config.enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        await self._store_server_config(user_id, server_config)
        
        # Generate URLs
        base_url = f"/api/a2a/servers/{config_id}"
        
        return A2AServerConfigResponse(
            config=server_config,
            agent_card_url=f"{base_url}/.well-known/agent-card.json",
            endpoint_url=f"{base_url}/v1",
        )
        
    async def get_server_config(
        self,
        user_id: str,
        config_id: str,
    ) -> Optional[A2AServerConfigResponse]:
        """
        Get server configuration by ID.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            
        Returns:
            Configuration or None
        """
        server_config = await self._load_server_config(user_id, config_id)
        if not server_config:
            return None
            
        base_url = f"/api/a2a/servers/{config_id}"
        
        return A2AServerConfigResponse(
            config=server_config,
            agent_card_url=f"{base_url}/.well-known/agent-card.json",
            endpoint_url=f"{base_url}/v1",
        )
        
    async def get_server_config_by_id(
        self,
        config_id: str,
    ) -> Optional[A2AServerConfig]:
        """
        Get server configuration by ID (without user check).
        Used for public A2A endpoints.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Configuration or None
        """
        # Search in all configs
        for key, config in self._server_configs.items():
            if config.id == config_id:
                return config
        return None
        
    async def list_server_configs(
        self,
        user_id: str,
        enabled_only: bool = False,
    ) -> List[A2AServerConfigResponse]:
        """
        List all server configurations for a user.
        
        Args:
            user_id: Owner user ID
            enabled_only: Only return enabled configs
            
        Returns:
            List of configurations
        """
        configs = await self._load_all_server_configs(user_id)
        
        if enabled_only:
            configs = [c for c in configs if c.enabled]
            
        results = []
        for config in configs:
            base_url = f"/api/a2a/servers/{config.id}"
            results.append(A2AServerConfigResponse(
                config=config,
                agent_card_url=f"{base_url}/.well-known/agent-card.json",
                endpoint_url=f"{base_url}/v1",
            ))
            
        return results
        
    async def update_server_config(
        self,
        user_id: str,
        config_id: str,
        update: A2AServerConfigUpdate,
    ) -> Optional[A2AServerConfigResponse]:
        """
        Update server configuration.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            update: Update data
            
        Returns:
            Updated configuration or None
        """
        server_config = await self._load_server_config(user_id, config_id)
        if not server_config:
            return None
            
        # Apply updates
        update_data = update.model_dump(exclude_unset=True, by_alias=False)
        for key, value in update_data.items():
            if hasattr(server_config, key):
                setattr(server_config, key, value)
                
        server_config.updated_at = datetime.utcnow()
        
        await self._store_server_config(user_id, server_config)
        
        base_url = f"/api/a2a/servers/{config_id}"
        
        return A2AServerConfigResponse(
            config=server_config,
            agent_card_url=f"{base_url}/.well-known/agent-card.json",
            endpoint_url=f"{base_url}/v1",
        )
        
    async def delete_server_config(
        self,
        user_id: str,
        config_id: str,
    ) -> bool:
        """
        Delete server configuration.
        
        Args:
            user_id: Owner user ID
            config_id: Configuration ID
            
        Returns:
            True if deleted
        """
        return await self._delete_server_config(user_id, config_id)
        
    # =========================================================================
    # Storage Methods (In-memory with Redis fallback)
    # =========================================================================
    
    async def _store_agent_config(self, user_id: str, config: A2AAgentConfig):
        """Store agent configuration."""
        key = f"{user_id}:{config.id}"
        self._agent_configs[key] = config
        
        if self._redis:
            try:
                redis_key = f"a2a:agent_configs:{key}"
                await self._redis.set(
                    redis_key,
                    config.model_dump_json(by_alias=True),
                    ex=86400 * 30  # 30 days
                )
            except Exception as e:
                logger.warning(f"Failed to store in Redis: {e}")
                
    async def _load_agent_config(
        self, 
        user_id: str, 
        config_id: str
    ) -> Optional[A2AAgentConfig]:
        """Load agent configuration."""
        key = f"{user_id}:{config_id}"
        
        # Check memory first
        if key in self._agent_configs:
            return self._agent_configs[key]
            
        # Try Redis
        if self._redis:
            try:
                redis_key = f"a2a:agent_configs:{key}"
                data = await self._redis.get(redis_key)
                if data:
                    config = A2AAgentConfig.model_validate_json(data)
                    self._agent_configs[key] = config
                    return config
            except Exception as e:
                logger.warning(f"Failed to load from Redis: {e}")
                
        return None
        
    async def _load_all_agent_configs(self, user_id: str) -> List[A2AAgentConfig]:
        """Load all agent configurations for user."""
        configs = []
        prefix = f"{user_id}:"
        
        for key, config in self._agent_configs.items():
            if key.startswith(prefix):
                configs.append(config)
                
        return configs
        
    async def _delete_agent_config(self, user_id: str, config_id: str) -> bool:
        """Delete agent configuration."""
        key = f"{user_id}:{config_id}"
        
        if key in self._agent_configs:
            del self._agent_configs[key]
            
        if config_id in self._connection_status:
            del self._connection_status[config_id]
            
        if self._redis:
            try:
                redis_key = f"a2a:agent_configs:{key}"
                await self._redis.delete(redis_key)
            except Exception as e:
                logger.warning(f"Failed to delete from Redis: {e}")
                
        return True
        
    async def _store_server_config(self, user_id: str, config: A2AServerConfig):
        """Store server configuration."""
        key = f"{user_id}:{config.id}"
        self._server_configs[key] = config
        
        if self._redis:
            try:
                redis_key = f"a2a:server_configs:{key}"
                await self._redis.set(
                    redis_key,
                    config.model_dump_json(by_alias=True),
                    ex=86400 * 30
                )
            except Exception as e:
                logger.warning(f"Failed to store in Redis: {e}")
                
    async def _load_server_config(
        self, 
        user_id: str, 
        config_id: str
    ) -> Optional[A2AServerConfig]:
        """Load server configuration."""
        key = f"{user_id}:{config_id}"
        
        if key in self._server_configs:
            return self._server_configs[key]
            
        if self._redis:
            try:
                redis_key = f"a2a:server_configs:{key}"
                data = await self._redis.get(redis_key)
                if data:
                    config = A2AServerConfig.model_validate_json(data)
                    self._server_configs[key] = config
                    return config
            except Exception as e:
                logger.warning(f"Failed to load from Redis: {e}")
                
        return None
        
    async def _load_all_server_configs(self, user_id: str) -> List[A2AServerConfig]:
        """Load all server configurations for user."""
        configs = []
        prefix = f"{user_id}:"
        
        for key, config in self._server_configs.items():
            if key.startswith(prefix):
                configs.append(config)
                
        return configs
        
    async def _delete_server_config(self, user_id: str, config_id: str) -> bool:
        """Delete server configuration."""
        key = f"{user_id}:{config_id}"
        
        if key in self._server_configs:
            del self._server_configs[key]
            
        if self._redis:
            try:
                redis_key = f"a2a:server_configs:{key}"
                await self._redis.delete(redis_key)
            except Exception as e:
                logger.warning(f"Failed to delete from Redis: {e}")
                
        return True


# Global registry instance
_registry: Optional[A2AAgentRegistry] = None


def get_a2a_registry() -> A2AAgentRegistry:
    """Get global A2A registry instance."""
    global _registry
    if _registry is None:
        _registry = A2AAgentRegistry()
    return _registry


def set_a2a_registry(registry: A2AAgentRegistry):
    """Set global A2A registry instance."""
    global _registry
    _registry = registry
