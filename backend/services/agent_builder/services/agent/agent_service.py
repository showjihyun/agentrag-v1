"""
Agent Service - Unified Implementation
Combines best practices from original and refactored versions.

Uses:
- Repository Pattern for data access
- Transaction management
- Event sourcing
- Circuit breaker pattern
- Multi-level caching
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import (
    Agent, AgentVersion, AgentTool, AgentKnowledgebase, Tool
)
from backend.db.repositories.agent_repository import (
    AgentRepository,
    AgentVersionRepository,
    AgentToolRepository,
    AgentKnowledgebaseRepository
)
from backend.models.agent_builder import AgentCreate, AgentUpdate, AgentResponse
from backend.core.transaction import transaction
from backend.core.advanced_cache import MultiLevelCache, cache_key
from backend.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from backend.core.enhanced_logging import get_logger, log_execution_time, log_error
from backend.core.event_bus import EventBus
from backend.models.agent_builder_events import (
    AgentCreatedEvent, AgentUpdatedEvent, AgentDeletedEvent, AgentClonedEvent
)
from backend.exceptions.agent_builder import (
    AgentNotFoundException,
    AgentValidationException,
    AgentToolNotFoundException,
    AgentKnowledgebaseNotFoundException
)

logger = get_logger(__name__)


class AgentService:
    """
    Unified Agent Service with DDD patterns.
    
    Features:
    - Repository pattern for clean data access
    - Transaction management for data integrity
    - Event sourcing for audit trail
    - Circuit breaker for resilience
    - Multi-level caching for performance
    """
    
    def __init__(
        self,
        db: Session,
        cache: Optional[MultiLevelCache] = None,
        db_breaker: Optional[CircuitBreaker] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.db = db
        self.cache = cache
        self.db_breaker = db_breaker
        self.event_bus = self._init_event_bus(event_bus)
        
        # Initialize repositories
        self.agent_repo = AgentRepository(db)
        self.version_repo = AgentVersionRepository(db)
        self.tool_repo = AgentToolRepository(db)
        self.kb_repo = AgentKnowledgebaseRepository(db)
    
    def _init_event_bus(self, event_bus: Optional[EventBus]) -> Optional[EventBus]:
        """Initialize EventBus with Redis if not provided."""
        if event_bus:
            return event_bus
        try:
            from backend.core.connection_pool import get_redis_pool
            from backend.config import settings
            redis_pool = get_redis_pool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD
            )
            redis_client = redis_pool.get_connection()
            return EventBus(redis_client=redis_client)
        except Exception as e:
            logger.warning(f"EventBus init failed: {e}. Using in-memory fallback.")
            return None
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def create_agent(self, user_id: str, agent_data: AgentCreate) -> Agent:
        """Create a new agent with validation and event publishing."""
        # Validate
        self._validate_agent_create(agent_data)
        self._verify_resources_exist(agent_data)
        
        with transaction(self.db):
            agent = self._build_agent(user_id, agent_data)
            agent = self.agent_repo.create(agent)
            
            self._attach_tools(agent.id, agent_data)
            self._attach_knowledgebases(agent.id, agent_data.knowledgebase_ids or [])
            self._create_version(agent, "1.0.0", "Initial version", user_id)
        
        self._invalidate_cache(agent.id, user_id)
        self._publish_event(AgentCreatedEvent(
            aggregate_id=agent.id,
            agent_id=agent.id,
            user_id=user_id,
            agent_name=agent.name,
            agent_type=agent.agent_type,
            llm_provider=agent.llm_provider,
            llm_model=agent.llm_model,
            tool_ids=agent_data.tool_ids or [],
            knowledgebase_ids=agent_data.knowledgebase_ids or [],
            is_public=agent.is_public,
            metadata={"template_id": agent.template_id}
        ))
        
        logger.info("Agent created", extra={
            "agent_id": agent.id, "agent_name": agent.name, "user_id": user_id
        })
        return agent
    
    async def get_agent(self, agent_id: str, use_cache: bool = True) -> Agent:
        """Get agent by ID with caching and circuit breaker."""
        start_time = datetime.utcnow()
        
        # Try cache
        if use_cache and self.cache:
            cached = await self.cache.get(cache_key("agent", agent_id))
            if cached:
                return cached
        
        # Query with circuit breaker
        try:
            if self.db_breaker:
                agent = await self.db_breaker.call(
                    lambda: self.agent_repo.find_by_id(agent_id)
                )
            else:
                agent = self.agent_repo.find_by_id(agent_id)
        except CircuitBreakerOpenError:
            if self.cache:
                return await self.cache.get(cache_key("agent", agent_id))
            raise
        
        if not agent:
            raise AgentNotFoundException(agent_id)
        
        # Cache result
        if use_cache and self.cache:
            await self.cache.set(cache_key("agent", agent_id), agent, ttl=3600)
        
        log_execution_time("get_agent", 
            (datetime.utcnow() - start_time).total_seconds() * 1000, 
            agent_id=agent_id)
        return agent
    
    async def update_agent(
        self, agent_id: str, agent_data: AgentUpdate, user_id: str
    ) -> Agent:
        """Update an agent with version tracking."""
        agent = await self.get_agent(agent_id, use_cache=False)
        significant_change = False
        
        with transaction(self.db):
            significant_change = self._apply_updates(agent, agent_data)
            
            if agent_data.tool_ids is not None:
                self._verify_tools_exist(agent_data.tool_ids)
                self.tool_repo.delete_by_agent(agent_id)
                self._attach_tools_simple(agent_id, agent_data.tool_ids)
                significant_change = True
            
            if agent_data.knowledgebase_ids is not None:
                self._verify_knowledgebases_exist(agent_data.knowledgebase_ids)
                self.kb_repo.delete_by_agent(agent_id)
                self._attach_knowledgebases(agent_id, agent_data.knowledgebase_ids)
                significant_change = True
            
            agent = self.agent_repo.update(agent)
            
            if significant_change:
                new_version = self._increment_version(agent_id)
                self._create_version(agent, new_version, "Agent updated", user_id)
        
        self._invalidate_cache(agent_id, agent.user_id)
        self._publish_event(AgentUpdatedEvent(
            aggregate_id=agent.id,
            agent_id=agent.id,
            user_id=user_id,
            updated_fields=[],
            previous_values={},
            new_values={},
            significant_change=significant_change
        ))
        
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Soft delete an agent."""
        agent = await self.get_agent(agent_id, use_cache=False)
        
        with transaction(self.db):
            self.agent_repo.soft_delete(agent)
        
        self._invalidate_cache(agent_id, agent.user_id)
        self._publish_event(AgentDeletedEvent(
            aggregate_id=agent.id,
            agent_id=agent.id,
            user_id=agent.user_id,
            agent_name=agent.name,
            deletion_type="soft"
        ))
        
        return True
    
    def list_agents(
        self,
        user_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Agent]:
        """List agents with filters."""
        if user_id:
            return self.agent_repo.find_by_user(
                user_id, agent_type, is_public, limit, offset
            )
        return self.agent_repo.find_public(agent_type, limit, offset)
    
    async def clone_agent(
        self, agent_id: str, user_id: str, new_name: Optional[str] = None
    ) -> Agent:
        """Clone an agent."""
        source = await self.get_agent(agent_id)
        
        with transaction(self.db):
            cloned = Agent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=new_name or f"{source.name} (Copy)",
                description=source.description,
                agent_type=source.agent_type,
                template_id=source.template_id,
                llm_provider=source.llm_provider,
                llm_model=source.llm_model,
                prompt_template_id=source.prompt_template_id,
                configuration=source.configuration.copy() if source.configuration else {},
                is_public=False
            )
            cloned = self.agent_repo.create(cloned)
            
            # Clone tools and knowledgebases
            for tool in self.tool_repo.find_by_agent(agent_id):
                self.tool_repo.create(AgentTool(
                    id=str(uuid.uuid4()),
                    agent_id=cloned.id,
                    tool_id=tool.tool_id,
                    configuration=tool.configuration.copy() if tool.configuration else {},
                    order=tool.order
                ))
            
            for kb in self.kb_repo.find_by_agent(agent_id):
                self.kb_repo.create(AgentKnowledgebase(
                    id=str(uuid.uuid4()),
                    agent_id=cloned.id,
                    knowledgebase_id=kb.knowledgebase_id,
                    priority=kb.priority
                ))
            
            self._create_version(cloned, "1.0.0", f"Cloned from {agent_id}", user_id)
        
        self._publish_event(AgentClonedEvent(
            aggregate_id=cloned.id,
            source_agent_id=agent_id,
            new_agent_id=cloned.id,
            user_id=user_id,
            new_agent_name=cloned.name
        ))
        
        return cloned
    
    def get_agent_versions(self, agent_id: str) -> List[AgentVersion]:
        """Get version history for an agent."""
        return self.version_repo.find_by_agent(agent_id)
    
    def export_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Export agent as JSON."""
        agent = self.agent_repo.find_by_id(agent_id)
        if not agent:
            return None
        
        return {
            "agent": {
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "template_id": agent.template_id,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
                "prompt_template_id": agent.prompt_template_id,
                "configuration": agent.configuration,
                "is_public": agent.is_public,
            },
            "tools": [
                {"tool_id": t.tool_id, "configuration": t.configuration, "order": t.order}
                for t in self.tool_repo.find_by_agent(agent_id)
            ],
            "knowledgebases": [
                {"knowledgebase_id": kb.knowledgebase_id, "priority": kb.priority}
                for kb in self.kb_repo.find_by_agent(agent_id)
            ],
            "versions": [
                {"version_number": v.version_number, "change_description": v.change_description}
                for v in self.version_repo.find_by_agent(agent_id)
            ]
        }
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _validate_agent_create(self, data: AgentCreate) -> None:
        """Validate agent creation data."""
        errors = []
        if not data.name or len(data.name) < 3:
            errors.append("Name must be at least 3 characters")
        if data.agent_type not in ["custom", "template_based"]:
            errors.append(f"Invalid agent type: {data.agent_type}")
        if not data.llm_provider:
            errors.append("LLM provider is required")
        if not data.llm_model:
            errors.append("LLM model is required")
        if errors:
            raise AgentValidationException(errors, data.model_dump())
    
    def _verify_resources_exist(self, data: AgentCreate) -> None:
        """Verify tools and knowledgebases exist."""
        if data.tool_ids:
            self._verify_tools_exist(data.tool_ids)
        if data.knowledgebase_ids:
            self._verify_knowledgebases_exist(data.knowledgebase_ids)
    
    def _verify_tools_exist(self, tool_ids: List[str]) -> None:
        """Verify tools exist."""
        missing = [tid for tid in tool_ids 
                   if not self.db.query(Tool).filter(Tool.id == tid).first()]
        if missing:
            raise AgentToolNotFoundException(', '.join(missing))
    
    def _verify_knowledgebases_exist(self, kb_ids: List[str]) -> None:
        """Verify knowledgebases exist."""
        from backend.db.models.agent_builder import Knowledgebase
        missing = [kid for kid in kb_ids 
                   if not self.db.query(Knowledgebase).filter(Knowledgebase.id == kid).first()]
        if missing:
            raise AgentKnowledgebaseNotFoundException(', '.join(missing))
    
    def _build_agent(self, user_id: str, data: AgentCreate) -> Agent:
        """Build Agent model from create data."""
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.name,
            description=data.description,
            agent_type=data.agent_type,
            template_id=data.template_id,
            llm_provider=data.llm_provider,
            llm_model=data.llm_model,
            prompt_template_id=data.prompt_template_id,
            configuration=data.configuration or {},
            is_public=data.is_public
        )
        if data.prompt_template:
            agent.configuration["prompt_template"] = data.prompt_template
        return agent
    
    def _attach_tools(self, agent_id: str, data: AgentCreate) -> None:
        """Attach tools to agent."""
        if data.tools:
            for tc in data.tools:
                self.tool_repo.create(AgentTool(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    tool_id=tc.tool_id,
                    configuration=tc.configuration or {},
                    order=tc.order
                ))
        elif data.tool_ids:
            self._attach_tools_simple(agent_id, data.tool_ids)
    
    def _attach_tools_simple(self, agent_id: str, tool_ids: List[str]) -> None:
        """Attach tools by ID list."""
        for order, tool_id in enumerate(tool_ids):
            self.tool_repo.create(AgentTool(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                tool_id=tool_id,
                configuration={},
                order=order
            ))
    
    def _attach_knowledgebases(self, agent_id: str, kb_ids: List[str]) -> None:
        """Attach knowledgebases to agent."""
        for priority, kb_id in enumerate(kb_ids):
            self.kb_repo.create(AgentKnowledgebase(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                knowledgebase_id=kb_id,
                priority=priority
            ))
    
    def _apply_updates(self, agent: Agent, data: AgentUpdate) -> bool:
        """Apply updates to agent, return True if significant change."""
        significant = False
        
        if data.name is not None:
            agent.name = data.name
            significant = True
        if data.description is not None:
            agent.description = data.description
        if data.llm_provider is not None:
            agent.llm_provider = data.llm_provider
            significant = True
        if data.llm_model is not None:
            agent.llm_model = data.llm_model
            significant = True
        if data.prompt_template_id is not None:
            agent.prompt_template_id = data.prompt_template_id
            significant = True
        if data.prompt_template is not None:
            agent.configuration = agent.configuration or {}
            agent.configuration["prompt_template"] = data.prompt_template
            significant = True
        if data.configuration is not None:
            agent.configuration = data.configuration
            significant = True
        if data.is_public is not None:
            agent.is_public = data.is_public
        
        agent.updated_at = datetime.utcnow()
        return significant
    
    def _create_version(
        self, agent: Agent, version: str, description: str, user_id: str
    ) -> AgentVersion:
        """Create version snapshot."""
        return self.version_repo.create(AgentVersion(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            version_number=version,
            configuration={
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
                "configuration": agent.configuration,
                "is_public": agent.is_public
            },
            change_description=description,
            created_by=user_id
        ))
    
    def _increment_version(self, agent_id: str) -> str:
        """Get next version number."""
        latest = self.version_repo.find_latest(agent_id)
        if latest:
            major, minor, patch = latest.version_number.split(".")
            return f"{major}.{int(minor) + 1}.0"
        return "1.0.0"
    
    def _invalidate_cache(self, agent_id: str, user_id: str) -> None:
        """Invalidate agent cache."""
        if self.cache:
            self.cache.delete_sync(cache_key("agent", agent_id))
            self.cache.delete_sync(cache_key("agents_list", user_id))
    
    def _publish_event(self, event) -> None:
        """Publish event to event bus."""
        if self.event_bus:
            try:
                self.event_bus.publish(event)
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")


# Backward compatibility alias
AgentServiceRefactored = AgentService
