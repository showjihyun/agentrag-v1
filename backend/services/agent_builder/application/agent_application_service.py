"""
Agent Application Service

Orchestrates agent operations using domain aggregates.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.agent.aggregate import AgentAggregate
from backend.services.agent_builder.domain.agent.entities import AgentEntity
from backend.services.agent_builder.domain.agent.value_objects import AgentType, AgentStatus

logger = logging.getLogger(__name__)


class AgentApplicationService:
    """
    Application service for agent operations.
    
    Provides high-level use cases:
    - Create/Update/Delete agents
    - Configure agent capabilities
    - Manage agent tools
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def create_agent(
        self,
        user_id: str,
        name: str,
        agent_type: str = "assistant",
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None,
        is_public: bool = False,
    ) -> AgentAggregate:
        """Create a new agent."""
        aggregate = AgentAggregate.create(
            user_id=UUID(user_id),
            name=name,
            agent_type=AgentType(agent_type) if agent_type else AgentType.ASSISTANT,
            description=description,
            system_prompt=system_prompt,
            model_config=model_config or {},
            tools=tools or [],
            is_public=is_public,
        )
        
        self._save_agent(aggregate)
        logger.info(f"Created agent: {aggregate.id}")
        return aggregate
    
    def get_agent(self, agent_id: str) -> Optional[AgentAggregate]:
        """Get agent by ID."""
        entity = self._load_agent(agent_id)
        if not entity:
            return None
        return AgentAggregate(entity)
    
    def update_agent(
        self,
        agent_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        is_public: Optional[bool] = None,
    ) -> Optional[AgentAggregate]:
        """Update an agent."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return None
        
        aggregate.update(
            user_id=UUID(user_id),
            name=name,
            description=description,
            system_prompt=system_prompt,
            model_config=model_config,
            is_public=is_public,
        )
        
        self._save_agent(aggregate)
        logger.info(f"Updated agent: {agent_id}")
        return aggregate
    
    def delete_agent(self, agent_id: str, user_id: str, hard: bool = False) -> bool:
        """Delete an agent."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return False
        
        aggregate.delete(UUID(user_id), hard=hard)
        
        if hard:
            self._delete_agent(agent_id)
        else:
            self._save_agent(aggregate)
        
        logger.info(f"Deleted agent: {agent_id}")
        return True
    
    def list_agents(
        self,
        user_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AgentEntity]:
        """List agents with filters."""
        from backend.db.models.agent_builder import Agent
        
        query = self.db.query(Agent).filter(Agent.deleted_at.is_(None))
        
        if user_id:
            query = query.filter(Agent.user_id == user_id)
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        if is_public is not None:
            query = query.filter(Agent.is_public == is_public)
        
        agents = query.order_by(Agent.created_at.desc()).limit(limit).offset(offset).all()
        return [self._db_to_entity(a) for a in agents]
    
    # ========================================================================
    # TOOL MANAGEMENT
    # ========================================================================
    
    def add_tool(self, agent_id: str, user_id: str, tool_id: str) -> Optional[AgentAggregate]:
        """Add a tool to an agent."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return None
        
        aggregate.add_tool(tool_id)
        self._save_agent(aggregate)
        return aggregate
    
    def remove_tool(self, agent_id: str, user_id: str, tool_id: str) -> Optional[AgentAggregate]:
        """Remove a tool from an agent."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return None
        
        aggregate.remove_tool(tool_id)
        self._save_agent(aggregate)
        return aggregate
    
    # ========================================================================
    # STATUS MANAGEMENT
    # ========================================================================
    
    def activate_agent(self, agent_id: str, user_id: str) -> Optional[AgentAggregate]:
        """Activate an agent."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return None
        
        aggregate.activate(UUID(user_id))
        self._save_agent(aggregate)
        return aggregate
    
    def deactivate_agent(self, agent_id: str, user_id: str) -> Optional[AgentAggregate]:
        """Deactivate an agent."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return None
        
        aggregate.deactivate(UUID(user_id))
        self._save_agent(aggregate)
        return aggregate
    
    # ========================================================================
    # EXPORT/IMPORT
    # ========================================================================
    
    def export_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Export agent as JSON."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return None
        
        return {
            "agent": aggregate.agent.to_dict(),
            "version": "1.0",
        }
    
    def import_agent(self, user_id: str, data: Dict[str, Any]) -> AgentAggregate:
        """Import agent from JSON."""
        agent_data = data.get("agent", {})
        
        return self.create_agent(
            user_id=user_id,
            name=agent_data.get("name", "Imported Agent"),
            agent_type=agent_data.get("agent_type", "assistant"),
            description=agent_data.get("description"),
            system_prompt=agent_data.get("system_prompt"),
            model_config=agent_data.get("model_config", {}),
            tools=agent_data.get("tools", []),
            is_public=False,
        )
    
    def clone_agent(
        self,
        agent_id: str,
        user_id: str,
        new_name: Optional[str] = None,
    ) -> Optional[AgentAggregate]:
        """Clone an agent."""
        aggregate = self.get_agent(agent_id)
        if not aggregate:
            return None
        
        cloned = aggregate.clone(UUID(user_id), new_name)
        self._save_agent(cloned)
        return cloned
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _save_agent(self, aggregate: AgentAggregate) -> None:
        """Save agent to database."""
        from backend.db.models.agent_builder import Agent
        
        agent = aggregate.agent
        
        db_agent = self.db.query(Agent).filter(Agent.id == agent.id).first()
        
        if db_agent:
            db_agent.name = agent.name
            db_agent.description = agent.description
            db_agent.agent_type = agent.agent_type.value
            db_agent.system_prompt = agent.system_prompt
            db_agent.model_config = agent.model_config.to_dict() if agent.model_config else {}
            db_agent.tools = agent.tools
            db_agent.is_public = agent.is_public
            db_agent.status = agent.status.value
            db_agent.updated_at = agent.updated_at
            db_agent.deleted_at = agent.deleted_at
        else:
            db_agent = Agent(
                id=agent.id,
                user_id=agent.user_id,
                name=agent.name,
                description=agent.description,
                agent_type=agent.agent_type.value,
                system_prompt=agent.system_prompt,
                model_config=agent.model_config.to_dict() if agent.model_config else {},
                tools=agent.tools,
                is_public=agent.is_public,
                status=agent.status.value,
            )
            self.db.add(db_agent)
        
        self.db.commit()
    
    def _load_agent(self, agent_id: str) -> Optional[AgentEntity]:
        """Load agent from database."""
        from backend.db.models.agent_builder import Agent
        
        db_agent = self.db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.deleted_at.is_(None),
        ).first()
        
        if not db_agent:
            return None
        
        return self._db_to_entity(db_agent)
    
    def _db_to_entity(self, db_agent) -> AgentEntity:
        """Convert DB model to domain entity."""
        from backend.services.agent_builder.domain.agent.value_objects import ModelConfig
        
        return AgentEntity(
            id=db_agent.id,
            user_id=db_agent.user_id,
            name=db_agent.name,
            description=db_agent.description,
            agent_type=AgentType(db_agent.agent_type) if db_agent.agent_type else AgentType.ASSISTANT,
            system_prompt=db_agent.system_prompt,
            model_config=ModelConfig.from_dict(db_agent.model_config or {}),
            tools=db_agent.tools or [],
            is_public=db_agent.is_public,
            status=AgentStatus(db_agent.status) if db_agent.status else AgentStatus.DRAFT,
        )
    
    def _delete_agent(self, agent_id: str) -> None:
        """Hard delete agent from database."""
        from backend.db.models.agent_builder import Agent
        
        self.db.query(Agent).filter(Agent.id == agent_id).delete()
        self.db.commit()
