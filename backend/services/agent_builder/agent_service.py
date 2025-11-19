"""Agent Service for managing custom agents."""

import logging
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.models.agent_builder import (
    Agent,
    AgentVersion,
    AgentTool,
    AgentKnowledgebase,
    Tool
)
from backend.models.agent_builder import (
    AgentCreate,
    AgentUpdate,
    AgentResponse
)
from backend.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from backend.core.advanced_cache import MultiLevelCache, cache_key
from backend.core.enhanced_logging import get_logger, log_execution_time, log_error

logger = get_logger(__name__)


class AgentService:
    """Service for managing agents with Phase 1 Architecture improvements."""
    
    def __init__(
        self,
        db: Session,
        cache: Optional[MultiLevelCache] = None,
        db_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize Agent Service.
        
        Args:
            db: Database session
            cache: Multi-level cache (optional)
            db_breaker: Circuit breaker for database operations (optional)
        """
        self.db = db
        self.cache = cache
        self.db_breaker = db_breaker
    
    async def create_agent(
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
            ValueError: If validation fails or referenced resources don't exist
        """
        try:
            # Validate tools exist BEFORE starting transaction
            missing_tools = []
            if agent_data.tool_ids:
                for tool_id in agent_data.tool_ids:
                    tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
                    if not tool:
                        missing_tools.append(tool_id)
            
            if missing_tools:
                raise ValueError(f"Tools not found: {', '.join(missing_tools)}")
            
            # Validate knowledgebases exist
            missing_kbs = []
            if agent_data.knowledgebase_ids:
                from backend.db.models.agent_builder import Knowledgebase
                for kb_id in agent_data.knowledgebase_ids:
                    kb = self.db.query(Knowledgebase).filter(
                        Knowledgebase.id == kb_id
                    ).first()
                    if not kb:
                        missing_kbs.append(kb_id)
            
            if missing_kbs:
                raise ValueError(f"Knowledgebases not found: {', '.join(missing_kbs)}")
            
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
            
            # Store custom prompt template in configuration if provided
            if agent_data.prompt_template:
                agent.configuration["prompt_template"] = agent_data.prompt_template
            
            self.db.add(agent)
            self.db.flush()  # Flush to get agent ID
            
            # Attach tools
            for order, tool_id in enumerate(agent_data.tool_ids):
                agent_tool = AgentTool(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    tool_id=tool_id,
                    configuration={},
                    order=order
                )
                self.db.add(agent_tool)
            
            # Attach knowledgebases
            for priority, kb_id in enumerate(agent_data.knowledgebase_ids):
                agent_kb = AgentKnowledgebase(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    knowledgebase_id=kb_id,
                    priority=priority
                )
                self.db.add(agent_kb)
            
            # Create initial version
            self._create_version(
                agent=agent,
                version_number="1.0.0",
                change_description="Initial version",
                created_by=user_id
            )
            
            self.db.commit()
            self.db.refresh(agent)
            
            # Invalidate cache
            if self.cache:
                await self.cache.delete(cache_key("agent", agent.id))
                await self.cache.delete(cache_key("agents_list", user_id))
            
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
            
        except ValueError:
            # Re-raise validation errors
            self.db.rollback()
            raise
        except Exception as e:
            # Rollback on any error
            self.db.rollback()
            logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent by ID with caching and circuit breaker.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent model or None if not found
        """
        start_time = datetime.utcnow()
        
        try:
            # Try cache first
            if self.cache:
                key = cache_key("agent", agent_id)
                cached = await self.cache.get(key)
                if cached:
                    logger.debug(f"Cache hit for agent: {agent_id}")
                    return cached
            
            # Database query with circuit breaker
            async def _query():
                return self.db.query(Agent).filter(
                    Agent.id == agent_id,
                    Agent.deleted_at.is_(None)
                ).first()
            
            if self.db_breaker:
                agent = await self.db_breaker.call(_query)
            else:
                agent = await _query()
            
            # Cache result
            if agent and self.cache:
                key = cache_key("agent", agent_id)
                await self.cache.set(key, agent, ttl=3600)
            
            # Log execution time
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            log_execution_time("get_agent", duration_ms, agent_id=agent_id)
            
            return agent
            
        except CircuitBreakerOpenError:
            logger.warning(f"Circuit breaker open for get_agent: {agent_id}")
            # Try cache as fallback
            if self.cache:
                key = cache_key("agent", agent_id)
                return await self.cache.get(key)
            return None
        except Exception as e:
            log_error(e, context={"agent_id": agent_id, "operation": "get_agent"})
            raise
    
    async def update_agent(
        self,
        agent_id: str,
        agent_data: AgentUpdate,
        user_id: str
    ) -> Optional[Agent]:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            agent_data: Agent update data
            user_id: User ID performing update
            
        Returns:
            Updated Agent model or None if not found
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        # Track if significant changes were made
        significant_change = False
        
        # Update fields
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
            # Remove existing tools
            self.db.query(AgentTool).filter(
                AgentTool.agent_id == agent_id
            ).delete()
            
            # Add new tools
            for order, tool_id in enumerate(agent_data.tool_ids):
                tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
                if not tool:
                    logger.warning(f"Tool not found: {tool_id}, skipping")
                    continue
                
                agent_tool = AgentTool(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    tool_id=tool_id,
                    configuration={},
                    order=order
                )
                self.db.add(agent_tool)
            
            significant_change = True
        
        # Update knowledgebases if provided
        if agent_data.knowledgebase_ids is not None:
            # Remove existing knowledgebases
            self.db.query(AgentKnowledgebase).filter(
                AgentKnowledgebase.agent_id == agent_id
            ).delete()
            
            # Add new knowledgebases
            for priority, kb_id in enumerate(agent_data.knowledgebase_ids):
                agent_kb = AgentKnowledgebase(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    knowledgebase_id=kb_id,
                    priority=priority
                )
                self.db.add(agent_kb)
            
            significant_change = True
        
        # Update timestamp
        agent.updated_at = datetime.utcnow()
        
        # Create new version if significant changes
        if significant_change:
            # Get current version
            latest_version = self.db.query(AgentVersion).filter(
                AgentVersion.agent_id == agent_id
            ).order_by(AgentVersion.created_at.desc()).first()
            
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
        
        self.db.commit()
        self.db.refresh(agent)
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(cache_key("agent", agent_id))
            await self.cache.delete(cache_key("agents_list", agent.user_id))
        
        logger.info(
            "Agent updated",
            extra={
                "agent_id": agent_id,
                "user_id": user_id,
                "significant_change": significant_change
            }
        )
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Soft delete an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if deleted, False if not found
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.deleted_at = datetime.utcnow()
        self.db.commit()
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(cache_key("agent", agent_id))
            await self.cache.delete(cache_key("agents_list", agent.user_id))
        
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
        query = self.db.query(Agent).filter(Agent.deleted_at.is_(None))
        
        if user_id:
            query = query.filter(Agent.user_id == user_id)
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        
        if is_public is not None:
            query = query.filter(Agent.is_public == is_public)
        
        query = query.order_by(Agent.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def clone_agent(
        self,
        agent_id: str,
        user_id: str,
        new_name: Optional[str] = None
    ) -> Optional[Agent]:
        """
        Clone an agent.
        
        Args:
            agent_id: Agent ID to clone
            user_id: User ID for new agent
            new_name: New name for cloned agent (optional)
            
        Returns:
            Cloned Agent model or None if source not found
        """
        source_agent = self.get_agent(agent_id)
        if not source_agent:
            return None
        
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
        
        self.db.add(cloned_agent)
        self.db.flush()
        
        # Clone tools
        source_tools = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id
        ).all()
        
        for source_tool in source_tools:
            cloned_tool = AgentTool(
                id=str(uuid.uuid4()),
                agent_id=cloned_agent.id,
                tool_id=source_tool.tool_id,
                configuration=source_tool.configuration.copy() if source_tool.configuration else {},
                order=source_tool.order
            )
            self.db.add(cloned_tool)
        
        # Clone knowledgebases
        source_kbs = self.db.query(AgentKnowledgebase).filter(
            AgentKnowledgebase.agent_id == agent_id
        ).all()
        
        for source_kb in source_kbs:
            cloned_kb = AgentKnowledgebase(
                id=str(uuid.uuid4()),
                agent_id=cloned_agent.id,
                knowledgebase_id=source_kb.knowledgebase_id,
                priority=source_kb.priority
            )
            self.db.add(cloned_kb)
        
        # Create initial version
        self._create_version(
            agent=cloned_agent,
            version_number="1.0.0",
            change_description=f"Cloned from agent {agent_id}",
            created_by=user_id
        )
        
        self.db.commit()
        self.db.refresh(cloned_agent)
        
        logger.info(f"Cloned agent {agent_id} to {cloned_agent.id}")
        return cloned_agent
    
    def export_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Export agent as JSON.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent data as dictionary or None if not found
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        # Get tools
        tools = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id
        ).all()
        
        # Get knowledgebases
        kbs = self.db.query(AgentKnowledgebase).filter(
            AgentKnowledgebase.agent_id == agent_id
        ).all()
        
        # Get versions
        versions = self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.created_at.desc()).all()
        
        # Build export data
        export_data = {
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
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
            },
            "tools": [
                {
                    "tool_id": tool.tool_id,
                    "configuration": tool.configuration,
                    "order": tool.order
                }
                for tool in tools
            ],
            "knowledgebases": [
                {
                    "knowledgebase_id": kb.knowledgebase_id,
                    "priority": kb.priority
                }
                for kb in kbs
            ],
            "versions": [
                {
                    "version_number": version.version_number,
                    "change_description": version.change_description,
                    "created_at": version.created_at.isoformat() if version.created_at else None
                }
                for version in versions
            ]
        }
        
        logger.info(f"Exported agent: {agent_id}")
        return export_data
    
    def import_agent(
        self,
        user_id: str,
        agent_data: Dict[str, Any]
    ) -> Agent:
        """
        Import agent from JSON.
        
        Args:
            user_id: User ID for imported agent
            agent_data: Agent data dictionary
            
        Returns:
            Imported Agent model
        """
        agent_info = agent_data.get("agent", {})
        
        # Create agent
        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=agent_info.get("name", "Imported Agent"),
            description=agent_info.get("description"),
            agent_type=agent_info.get("agent_type", "custom"),
            template_id=agent_info.get("template_id"),
            llm_provider=agent_info.get("llm_provider", "ollama"),
            llm_model=agent_info.get("llm_model", "llama3.1"),
            prompt_template_id=agent_info.get("prompt_template_id"),
            configuration=agent_info.get("configuration", {}),
            is_public=False  # Imported agents are private by default
        )
        
        self.db.add(agent)
        self.db.flush()
        
        # Import tools
        for tool_data in agent_data.get("tools", []):
            tool_id = tool_data.get("tool_id")
            
            # Verify tool exists
            tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
            if not tool:
                logger.warning(f"Tool not found during import: {tool_id}, skipping")
                continue
            
            agent_tool = AgentTool(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                tool_id=tool_id,
                configuration=tool_data.get("configuration", {}),
                order=tool_data.get("order", 0)
            )
            self.db.add(agent_tool)
        
        # Import knowledgebases (skip if they don't exist)
        for kb_data in agent_data.get("knowledgebases", []):
            kb_id = kb_data.get("knowledgebase_id")
            
            agent_kb = AgentKnowledgebase(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                knowledgebase_id=kb_id,
                priority=kb_data.get("priority", 0)
            )
            self.db.add(agent_kb)
        
        # Create initial version
        self._create_version(
            agent=agent,
            version_number="1.0.0",
            change_description="Imported from JSON",
            created_by=user_id
        )
        
        self.db.commit()
        self.db.refresh(agent)
        
        logger.info(f"Imported agent: {agent.id}")
        return agent
    
    def get_agent_versions(self, agent_id: str) -> List[AgentVersion]:
        """
        Get version history for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of AgentVersion models
        """
        return self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.created_at.desc()).all()
    
    def _create_version(
        self,
        agent: Agent,
        version_number: str,
        change_description: str,
        created_by: str
    ) -> AgentVersion:
        """
        Create a version snapshot of an agent.
        
        Args:
            agent: Agent model
            version_number: Version number (semantic versioning)
            change_description: Description of changes
            created_by: User ID creating version
            
        Returns:
            Created AgentVersion model
        """
        # Capture current configuration
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
        
        self.db.add(version)
        return version
