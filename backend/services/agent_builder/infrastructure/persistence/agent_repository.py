"""
Agent Repository Implementation

Implements the AgentRepository interface using SQLAlchemy.
"""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.agent.repository import AgentRepositoryInterface
from backend.services.agent_builder.domain.agent.aggregate import AgentAggregate
from backend.services.agent_builder.domain.agent.entities import AgentEntity
from backend.services.agent_builder.domain.agent.value_objects import (
    AgentType, AgentStatus, ModelConfig, AgentConfig, ToolBinding, KnowledgebaseBinding
)

logger = logging.getLogger(__name__)


class AgentRepositoryImpl(AgentRepositoryInterface):
    """SQLAlchemy implementation of AgentRepository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, aggregate: AgentAggregate) -> None:
        """Save agent aggregate."""
        from backend.db.models.agent_builder import Agent, AgentTool
        
        agent = aggregate.agent
        
        db_agent = self.db.query(Agent).filter(Agent.id == agent.id).first()
        
        if db_agent:
            # Update existing
            db_agent.name = agent.name
            db_agent.description = agent.description
            db_agent.agent_type = agent.agent_type.value
            db_agent.llm_provider = agent.llm_provider if hasattr(agent, 'llm_provider') else agent.config.llm_settings.provider.value
            db_agent.llm_model = agent.llm_model if hasattr(agent, 'llm_model') else agent.config.llm_settings.model
            db_agent.configuration = agent.config.to_dict() if agent.config else {}
            db_agent.is_public = agent.is_public
            db_agent.updated_at = agent.updated_at
            db_agent.deleted_at = agent.deleted_at
            
            # Update tools - remove all existing and add new ones
            self.db.query(AgentTool).filter(AgentTool.agent_id == agent.id).delete()
            for tool in agent.tools:
                db_tool = AgentTool(
                    agent_id=agent.id,
                    tool_id=tool.tool_id,
                    configuration=tool.configuration,
                    order=tool.order
                )
                self.db.add(db_tool)
        else:
            # Create new - map domain entity fields to database model fields
            configuration = agent.config.to_dict() if agent.config else {}
            
            db_agent = Agent(
                id=agent.id,
                user_id=agent.user_id,
                name=agent.name,
                description=agent.description,
                agent_type=agent.agent_type.value,
                llm_provider=agent.llm_provider if hasattr(agent, 'llm_provider') else agent.config.llm_settings.provider.value,
                llm_model=agent.llm_model if hasattr(agent, 'llm_model') else agent.config.llm_settings.model,
                configuration=configuration,
                is_public=agent.is_public,
            )
            self.db.add(db_agent)
            
            # Add tools
            for tool in agent.tools:
                db_tool = AgentTool(
                    agent_id=agent.id,
                    tool_id=tool.tool_id,
                    configuration=tool.configuration,
                    order=tool.order
                )
                self.db.add(db_tool)
        
        self.db.commit()
        logger.debug(f"Saved agent: {agent.id}")
    
    def find_by_id(self, agent_id: UUID) -> Optional[AgentAggregate]:
        """Find agent by ID."""
        from backend.db.models.agent_builder import Agent
        
        db_agent = self.db.query(Agent).filter(
            Agent.id == str(agent_id),
            Agent.deleted_at.is_(None),
        ).first()
        
        if not db_agent:
            return None
        
        entity = self._to_entity(db_agent)
        return AgentAggregate(entity)
    
    def find_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AgentAggregate]:
        """Find agents by user."""
        from backend.db.models.agent_builder import Agent
        
        agents = self.db.query(Agent).filter(
            Agent.user_id == str(user_id),
            Agent.deleted_at.is_(None),
        ).order_by(Agent.created_at.desc()).limit(limit).offset(offset).all()
        
        return [AgentAggregate(self._to_entity(a)) for a in agents]
    
    def find_public(self, limit: int = 50, offset: int = 0) -> List[AgentAggregate]:
        """Find public agents."""
        from backend.db.models.agent_builder import Agent
        
        agents = self.db.query(Agent).filter(
            Agent.is_public == True,
            Agent.deleted_at.is_(None),
        ).order_by(Agent.created_at.desc()).limit(limit).offset(offset).all()
        
        return [AgentAggregate(self._to_entity(a)) for a in agents]
    
    def delete(self, agent_id: UUID) -> bool:
        """Hard delete agent."""
        from backend.db.models.agent_builder import Agent
        
        result = self.db.query(Agent).filter(Agent.id == str(agent_id)).delete()
        self.db.commit()
        
        return result > 0
    
    def exists(self, agent_id: UUID) -> bool:
        """Check if agent exists."""
        from backend.db.models.agent_builder import Agent
        
        return self.db.query(Agent).filter(
            Agent.id == str(agent_id),
            Agent.deleted_at.is_(None),
        ).count() > 0
    
    def _to_entity(self, db_agent) -> AgentEntity:
        """Convert DB model to domain entity."""
        # Build AgentConfig from database configuration
        config_dict = db_agent.configuration or {}
        config_dict["llm_provider"] = db_agent.llm_provider
        config_dict["llm_model"] = db_agent.llm_model
        config = AgentConfig.from_dict(config_dict)
        
        # Build tool bindings from database relationships
        tool_bindings = [
            ToolBinding(
                tool_id=str(at.tool_id),
                configuration=at.configuration or {},
                order=at.order if hasattr(at, 'order') else 0
            )
            for at in (db_agent.tools or [])
        ]
        
        # Build knowledgebase bindings from database relationships
        kb_bindings = [
            KnowledgebaseBinding(
                knowledgebase_id=str(ak.knowledgebase_id),
                priority=ak.order if hasattr(ak, 'order') else 0
            )
            for ak in (db_agent.knowledgebases or [])
        ]
        
        # Handle agent_type with fallback
        try:
            agent_type = AgentType(db_agent.agent_type) if db_agent.agent_type else AgentType.CUSTOM
        except ValueError:
            logger.warning(f"Unknown agent_type '{db_agent.agent_type}', defaulting to CUSTOM")
            agent_type = AgentType.CUSTOM
        
        return AgentEntity(
            id=db_agent.id,
            user_id=db_agent.user_id,
            name=db_agent.name,
            description=db_agent.description,
            agent_type=agent_type,
            config=config,
            template_id=str(db_agent.template_id) if db_agent.template_id else None,
            is_public=db_agent.is_public,
            is_active=db_agent.deleted_at is None,
            tools=tool_bindings,
            knowledgebases=kb_bindings,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
            deleted_at=db_agent.deleted_at,
            # Optional fields that may not exist in DB
            system_prompt=config_dict.get("system_prompt"),
            model_config=None,  # Not used in current implementation
            status=AgentStatus.ACTIVE if db_agent.deleted_at is None else AgentStatus.ARCHIVED,
        )
