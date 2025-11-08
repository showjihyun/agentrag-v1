"""Refactored Agent Service using Repository Pattern."""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Agent, AgentVersion, AgentTool, AgentKnowledgebase, Tool
from backend.db.repositories.agent_repository import (
    AgentRepository,
    AgentVersionRepository,
    AgentToolRepository,
    AgentKnowledgebaseRepository
)
from backend.models.agent_builder import AgentCreate, AgentUpdate, AgentResponse
from backend.core.transaction import transaction, TransactionManager
from backend.core.advanced_cache import MultiLevelCache, cache_key
from backend.core.circuit_breaker import CircuitBreaker
from backend.core.enhanced_logging import get_logger, log_execution_time
from backend.core.event_bus import EventBus
from backend.models.agent_builder_events import (
    AgentCreatedEvent,
    AgentUpdatedEvent,
    AgentDeletedEvent,
    AgentClonedEvent,
    ToolAttachedEvent,
    ToolDetachedEvent,
    KnowledgebaseAttachedEvent,
    KnowledgebaseDetachedEvent
)
from backend.exceptions.agent_builder import (
    AgentNotFoundException,
    AgentValidationException,
    AgentToolNotFoundException,
    AgentKnowledgebaseNotFoundException
)

logger = get_logger(__name__)


class AgentServiceRefactored:
    """
    Refactored Agent Service with Repository Pattern.
    
    Improvements:
    - Repository pattern for data access
    - Proper transaction management
    - Standardized exception handling
    - Consistent sync methods (no fake async)
    - Better separation of concerns
    """
    
    def __init__(
        self,
        db: Session,
        cache: Optional[MultiLevelCache] = None,
        db_breaker: Optional[CircuitBreaker] = None,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize Agent Service.
        
        Args:
            db: Database session
            cache: Multi-level cache (optional)
            db_breaker: Circuit breaker for database operations (optional)
            event_bus: Event bus for event sourcing (optional)
        """
        self.db = db
        self.cache = cache
        self.db_breaker = db_breaker
        
        # Initialize EventBus with Redis client if not provided
        if event_bus:
            self.event_bus = event_bus
        else:
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
                self.event_bus = EventBus(redis_client=redis_client)
            except Exception as e:
                # Fallback: EventBus without Redis (in-memory only)
                import logging
                logging.warning(f"Failed to initialize EventBus with Redis: {e}. Using in-memory fallback.")
                self.event_bus = None
        
        # Initialize repositories
        self.agent_repo = AgentRepository(db)
        self.version_repo = AgentVersionRepository(db)
        self.tool_repo = AgentToolRepository(db)
        self.kb_repo = AgentKnowledgebaseRepository(db)
    
    def create_agent(
        self,
        user_id: str,
        agent_data: AgentCreate
    ) -> Agent:
        """
        Create a new agent with proper transaction management.
        
        Args:
            user_id: User ID creating the agent
            agent_data: Agent creation data
            
        Returns:
            Created Agent model
            
        Raises:
            AgentValidationException: If validation fails
            AgentToolNotFoundException: If tool not found
            AgentKnowledgebaseNotFoundException: If knowledgebase not found
        """
        # Validate before starting transaction
        validation_errors = self._validate_agent_create(agent_data)
        if validation_errors:
            raise AgentValidationException(validation_errors, agent_data.model_dump())
        
        # Verify tools exist
        if agent_data.tool_ids:
            missing_tools = self._verify_tools_exist(agent_data.tool_ids)
            if missing_tools:
                raise AgentToolNotFoundException(', '.join(missing_tools))
        
        # Verify knowledgebases exist
        if agent_data.knowledgebase_ids:
            missing_kbs = self._verify_knowledgebases_exist(agent_data.knowledgebase_ids)
            if missing_kbs:
                raise AgentKnowledgebaseNotFoundException(', '.join(missing_kbs))
        
        # Create agent with transaction management
        with transaction(self.db):
            # Create agent
            agent = Agent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=agent_data.name,
                description=agent_data.description,
                agent_type=agent_data.agent_type,
                template_id=agent_data.template_id,
                llm_provider=agent_data.llm_provider,
                llm_model=agent_data.llm_model,
                prompt_template_id=agent_data.prompt_template_id,
                configuration=agent_data.configuration or {},
                is_public=agent_data.is_public
            )
            
            # Store custom prompt template if provided
            if agent_data.prompt_template:
                agent.configuration["prompt_template"] = agent_data.prompt_template
            
            agent = self.agent_repo.create(agent)
            
            # Attach tools
            if agent_data.tool_ids:
                self._attach_tools(agent.id, agent_data.tool_ids)
            
            # Attach knowledgebases
            if agent_data.knowledgebase_ids:
                self._attach_knowledgebases(agent.id, agent_data.knowledgebase_ids)
            
            # Create initial version
            self._create_version(
                agent=agent,
                version_number="1.0.0",
                change_description="Initial version",
                created_by=user_id
            )
        
        # Invalidate cache after successful commit
        self._invalidate_agent_cache(agent.id, user_id)
        
        # Publish event
        self._publish_agent_created_event(agent, user_id, agent_data)
        
        logger.info(
            "Agent created",
            extra={
                "agent_id": agent.id,
                "agent_name": agent.name,
                "user_id": user_id,
                "agent_type": agent_data.agent_type
            }
        )
        
        return agent
    
    def get_agent(self, agent_id: str, use_cache: bool = True) -> Agent:
        """
        Get agent by ID with caching.
        
        Args:
            agent_id: Agent ID
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Agent model
            
        Raises:
            AgentNotFoundException: If agent not found
        """
        start_time = datetime.utcnow()
        
        # Try cache first
        if use_cache and self.cache:
            key = cache_key("agent", agent_id)
            cached = self.cache.get_sync(key)
            if cached:
                logger.debug(f"Cache hit for agent: {agent_id}")
                return cached
        
        # Query database
        agent = self.agent_repo.find_by_id(agent_id)
        
        if not agent:
            raise AgentNotFoundException(agent_id)
        
        # Cache result
        if use_cache and self.cache:
            key = cache_key("agent", agent_id)
            self.cache.set_sync(key, agent, ttl=3600)
        
        # Log execution time
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_execution_time("get_agent", duration_ms, agent_id=agent_id)
        
        return agent
    
    def update_agent(
        self,
        agent_id: str,
        agent_data: AgentUpdate,
        user_id: str
    ) -> Agent:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            agent_data: Agent update data
            user_id: User ID performing update
            
        Returns:
            Updated Agent model
            
        Raises:
            AgentNotFoundException: If agent not found
            AgentValidationException: If validation fails
        """
        agent = self.get_agent(agent_id, use_cache=False)
        
        # Track if significant changes were made
        significant_change = False
        
        with transaction(self.db):
            # Update basic fields
            if agent_data.name is not None:
                agent.name = agent_data.name
                significant_change = True
            
            if agent_data.description is not None:
                agent.description = agent_data.description
            
            if agent_data.llm_provider is not None:
                agent.llm_provider = agent_data.llm_provider
                significant_change = True
            
            if agent_data.llm_model is not None:
                agent.llm_model = agent_data.llm_model
                significant_change = True
            
            if agent_data.prompt_template_id is not None:
                agent.prompt_template_id = agent_data.prompt_template_id
                significant_change = True
            
            if agent_data.prompt_template is not None:
                if not agent.configuration:
                    agent.configuration = {}
                agent.configuration["prompt_template"] = agent_data.prompt_template
                significant_change = True
            
            if agent_data.configuration is not None:
                agent.configuration = agent_data.configuration
                significant_change = True
            
            if agent_data.is_public is not None:
                agent.is_public = agent_data.is_public
            
            # Update tools if provided
            if agent_data.tool_ids is not None:
                # Verify tools exist
                missing_tools = self._verify_tools_exist(agent_data.tool_ids)
                if missing_tools:
                    raise AgentToolNotFoundException(', '.join(missing_tools))
                
                # Remove existing tools
                self.tool_repo.delete_by_agent(agent_id)
                
                # Add new tools
                self._attach_tools(agent_id, agent_data.tool_ids)
                significant_change = True
            
            # Update knowledgebases if provided
            if agent_data.knowledgebase_ids is not None:
                # Verify knowledgebases exist
                missing_kbs = self._verify_knowledgebases_exist(agent_data.knowledgebase_ids)
                if missing_kbs:
                    raise AgentKnowledgebaseNotFoundException(', '.join(missing_kbs))
                
                # Remove existing knowledgebases
                self.kb_repo.delete_by_agent(agent_id)
                
                # Add new knowledgebases
                self._attach_knowledgebases(agent_id, agent_data.knowledgebase_ids)
                significant_change = True
            
            # Update agent
            agent = self.agent_repo.update(agent)
            
            # Create new version if significant changes
            if significant_change:
                latest_version = self.version_repo.find_latest(agent_id)
                
                # Increment version
                if latest_version:
                    major, minor, patch = latest_version.version_number.split(".")
                    new_version = f"{major}.{int(minor) + 1}.0"
                else:
                    new_version = "1.0.0"
                
                self._create_version(
                    agent=agent,
                    version_number=new_version,
                    change_description="Agent updated",
                    created_by=user_id
                )
        
        # Invalidate cache
        self._invalidate_agent_cache(agent_id, agent.user_id)
        
        # Publish event (track changes for event)
        updated_fields = []
        previous_values = {}
        new_values = {}
        
        if agent_data.name is not None:
            updated_fields.append("name")
            new_values["name"] = agent.name
        if agent_data.llm_provider is not None:
            updated_fields.append("llm_provider")
            new_values["llm_provider"] = agent.llm_provider
        if agent_data.llm_model is not None:
            updated_fields.append("llm_model")
            new_values["llm_model"] = agent.llm_model
        
        self._publish_agent_updated_event(
            agent, user_id, updated_fields, previous_values, new_values, significant_change
        )
        
        logger.info(
            "Agent updated",
            extra={
                "agent_id": agent_id,
                "user_id": user_id,
                "significant_change": significant_change
            }
        )
        
        return agent
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        Soft delete an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if deleted
            
        Raises:
            AgentNotFoundException: If agent not found
        """
        agent = self.get_agent(agent_id, use_cache=False)
        
        with transaction(self.db):
            self.agent_repo.soft_delete(agent)
        
        # Invalidate cache
        self._invalidate_agent_cache(agent_id, agent.user_id)
        
        # Publish event
        self._publish_agent_deleted_event(agent, deletion_type="soft")
        
        logger.info(
            "Agent deleted",
            extra={"agent_id": agent_id, "user_id": agent.user_id}
        )
        
        return True
    
    def list_agents(
        self,
        user_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Agent]:
        """
        List agents with filters.
        
        Args:
            user_id: Filter by user ID (optional)
            agent_type: Filter by agent type (optional)
            is_public: Filter by public status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Agent models
        """
        if user_id:
            return self.agent_repo.find_by_user(
                user_id=user_id,
                agent_type=agent_type,
                is_public=is_public,
                limit=limit,
                offset=offset
            )
        elif is_public:
            return self.agent_repo.find_public(
                agent_type=agent_type,
                limit=limit,
                offset=offset
            )
        else:
            # Default to public agents if no user specified
            return self.agent_repo.find_public(
                agent_type=agent_type,
                limit=limit,
                offset=offset
            )
    
    def clone_agent(
        self,
        agent_id: str,
        user_id: str,
        new_name: Optional[str] = None
    ) -> Agent:
        """
        Clone an agent.
        
        Args:
            agent_id: Agent ID to clone
            user_id: User ID for new agent
            new_name: New name for cloned agent (optional)
            
        Returns:
            Cloned Agent model
            
        Raises:
            AgentNotFoundException: If source agent not found
        """
        source_agent = self.get_agent(agent_id)
        
        with transaction(self.db):
            # Create cloned agent
            cloned_agent = Agent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=new_name or f"{source_agent.name} (Copy)",
                description=source_agent.description,
                agent_type=source_agent.agent_type,
                template_id=source_agent.template_id,
                llm_provider=source_agent.llm_provider,
                llm_model=source_agent.llm_model,
                prompt_template_id=source_agent.prompt_template_id,
                configuration=source_agent.configuration.copy() if source_agent.configuration else {},
                is_public=False  # Cloned agents are private by default
            )
            
            cloned_agent = self.agent_repo.create(cloned_agent)
            
            # Clone tools
            source_tools = self.tool_repo.find_by_agent(agent_id)
            for source_tool in source_tools:
                cloned_tool = AgentTool(
                    id=str(uuid.uuid4()),
                    agent_id=cloned_agent.id,
                    tool_id=source_tool.tool_id,
                    configuration=source_tool.configuration.copy() if source_tool.configuration else {},
                    order=source_tool.order
                )
                self.tool_repo.create(cloned_tool)
            
            # Clone knowledgebases
            source_kbs = self.kb_repo.find_by_agent(agent_id)
            for source_kb in source_kbs:
                cloned_kb = AgentKnowledgebase(
                    id=str(uuid.uuid4()),
                    agent_id=cloned_agent.id,
                    knowledgebase_id=source_kb.knowledgebase_id,
                    priority=source_kb.priority
                )
                self.kb_repo.create(cloned_kb)
            
            # Create initial version
            self._create_version(
                agent=cloned_agent,
                version_number="1.0.0",
                change_description=f"Cloned from agent {agent_id}",
                created_by=user_id
            )
        
        # Publish event
        self._publish_agent_cloned_event(agent_id, cloned_agent, user_id)
        
        logger.info(f"Cloned agent {agent_id} to {cloned_agent.id}")
        return cloned_agent
    
    def get_agent_versions(self, agent_id: str) -> List[AgentVersion]:
        """
        Get version history for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of AgentVersion models
        """
        return self.version_repo.find_by_agent(agent_id)
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _validate_agent_create(self, agent_data: AgentCreate) -> List[str]:
        """Validate agent creation data."""
        errors = []
        
        if not agent_data.name or len(agent_data.name) < 3:
            errors.append("Name must be at least 3 characters")
        
        if agent_data.agent_type not in ["custom", "template_based"]:
            errors.append(f"Invalid agent type: {agent_data.agent_type}")
        
        if not agent_data.llm_provider:
            errors.append("LLM provider is required")
        
        if not agent_data.llm_model:
            errors.append("LLM model is required")
        
        return errors
    
    def _verify_tools_exist(self, tool_ids: List[str]) -> List[str]:
        """Verify tools exist, return list of missing tool IDs."""
        logger.info(f"🔍 Verifying tools exist: {tool_ids}")
        
        # Get all available tools from database
        all_tools = self.db.query(Tool).all()
        available_tool_ids = [tool.id for tool in all_tools]
        
        logger.info(f"📋 Available tools in database ({len(all_tools)} total):")
        for tool in all_tools[:10]:  # Show first 10
            logger.info(f"  - {tool.id}: {tool.name}")
        if len(all_tools) > 10:
            logger.info(f"  ... and {len(all_tools) - 10} more tools")
        
        missing_tools = []
        for tool_id in tool_ids:
            tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
            if not tool:
                logger.warning(f"❌ Tool NOT FOUND: {tool_id}")
                logger.info(f"   Available tool IDs: {available_tool_ids[:20]}")
                missing_tools.append(tool_id)
            else:
                logger.info(f"✅ Tool found: {tool_id} ({tool.name})")
        
        if missing_tools:
            logger.error(f"🚫 Missing tools: {missing_tools}")
        else:
            logger.info(f"✅ All tools verified successfully")
            
        return missing_tools
    
    def _verify_knowledgebases_exist(self, kb_ids: List[str]) -> List[str]:
        """Verify knowledgebases exist, return list of missing KB IDs."""
        from backend.db.models.agent_builder import Knowledgebase
        missing_kbs = []
        for kb_id in kb_ids:
            kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
            if not kb:
                missing_kbs.append(kb_id)
        return missing_kbs
    
    def _attach_tools(self, agent_id: str, tool_ids: List[str]) -> None:
        """Attach tools to agent."""
        for order, tool_id in enumerate(tool_ids):
            agent_tool = AgentTool(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                tool_id=tool_id,
                configuration={},
                order=order
            )
            self.tool_repo.create(agent_tool)
    
    def _attach_knowledgebases(self, agent_id: str, kb_ids: List[str]) -> None:
        """Attach knowledgebases to agent."""
        for priority, kb_id in enumerate(kb_ids):
            agent_kb = AgentKnowledgebase(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                knowledgebase_id=kb_id,
                priority=priority
            )
            self.kb_repo.create(agent_kb)
    
    def _create_version(
        self,
        agent: Agent,
        version_number: str,
        change_description: str,
        created_by: str
    ) -> AgentVersion:
        """Create a version snapshot of an agent."""
        configuration = {
            "name": agent.name,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "template_id": agent.template_id,
            "llm_provider": agent.llm_provider,
            "llm_model": agent.llm_model,
            "prompt_template_id": agent.prompt_template_id,
            "configuration": agent.configuration,
            "is_public": agent.is_public
        }
        
        version = AgentVersion(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            version_number=version_number,
            configuration=configuration,
            change_description=change_description,
            created_by=created_by
        )
        
        return self.version_repo.create(version)
    
    def _invalidate_agent_cache(self, agent_id: str, user_id: str) -> None:
        """Invalidate agent cache."""
        if self.cache:
            self.cache.delete_sync(cache_key("agent", agent_id))
            self.cache.delete_sync(cache_key("agents_list", user_id))
    
    # ========================================================================
    # EVENT PUBLISHING METHODS
    # ========================================================================
    
    def _publish_agent_created_event(
        self,
        agent: Agent,
        user_id: str,
        agent_data: AgentCreate
    ) -> None:
        """Publish AgentCreatedEvent."""
        try:
            event = AgentCreatedEvent(
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
                metadata={
                    "template_id": agent.template_id,
                    "prompt_template_id": agent.prompt_template_id
                }
            )
            if self.event_bus:
                self.event_bus.publish(event)
                logger.debug(f"Published AgentCreatedEvent for agent {agent.id}")
        except Exception as e:
            logger.error(f"Failed to publish AgentCreatedEvent: {e}", exc_info=True)
    
    def _publish_agent_updated_event(
        self,
        agent: Agent,
        user_id: str,
        updated_fields: List[str],
        previous_values: Dict[str, Any],
        new_values: Dict[str, Any],
        significant_change: bool
    ) -> None:
        """Publish AgentUpdatedEvent."""
        try:
            event = AgentUpdatedEvent(
                aggregate_id=agent.id,
                agent_id=agent.id,
                user_id=user_id,
                updated_fields=updated_fields,
                previous_values=previous_values,
                new_values=new_values,
                significant_change=significant_change
            )
            if self.event_bus:
                self.event_bus.publish(event)
                logger.debug(f"Published AgentUpdatedEvent for agent {agent.id}")
        except Exception as e:
            logger.error(f"Failed to publish AgentUpdatedEvent: {e}", exc_info=True)
    
    def _publish_agent_deleted_event(
        self,
        agent: Agent,
        deletion_type: str = "soft"
    ) -> None:
        """Publish AgentDeletedEvent."""
        try:
            event = AgentDeletedEvent(
                aggregate_id=agent.id,
                agent_id=agent.id,
                user_id=agent.user_id,
                agent_name=agent.name,
                deletion_type=deletion_type
            )
            if self.event_bus:
                self.event_bus.publish(event)
                logger.debug(f"Published AgentDeletedEvent for agent {agent.id}")
        except Exception as e:
            logger.error(f"Failed to publish AgentDeletedEvent: {e}", exc_info=True)
    
    def _publish_agent_cloned_event(
        self,
        source_agent_id: str,
        new_agent: Agent,
        user_id: str
    ) -> None:
        """Publish AgentClonedEvent."""
        try:
            event = AgentClonedEvent(
                aggregate_id=new_agent.id,
                source_agent_id=source_agent_id,
                new_agent_id=new_agent.id,
                user_id=user_id,
                new_agent_name=new_agent.name
            )
            if self.event_bus:
                self.event_bus.publish(event)
                logger.debug(f"Published AgentClonedEvent for agent {new_agent.id}")
        except Exception as e:
            logger.error(f"Failed to publish AgentClonedEvent: {e}", exc_info=True)
