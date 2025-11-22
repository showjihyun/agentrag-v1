"""Agent Repository for data access layer."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models.agent_builder import Agent, AgentVersion, AgentTool, AgentKnowledgebase
from backend.core.query_optimizer import QueryOptimizer

logger = logging.getLogger(__name__)


class AgentRepository:
    """Repository for Agent data access."""
    
    def __init__(self, db: Session):
        """
        Initialize Agent Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, agent: Agent) -> Agent:
        """
        Create a new agent.
        
        Args:
            agent: Agent model to create
            
        Returns:
            Created Agent model
        """
        self.db.add(agent)
        self.db.flush()
        return agent
    
    def find_by_id(self, agent_id: str, include_deleted: bool = False) -> Optional[Agent]:
        """
        Find agent by ID.
        
        Args:
            agent_id: Agent ID
            include_deleted: Include soft-deleted agents
            
        Returns:
            Agent model or None if not found
        """
        query = self.db.query(Agent).filter(Agent.id == agent_id)
        
        if not include_deleted:
            query = query.filter(Agent.deleted_at.is_(None))
        
        return query.first()
    
    def find_by_user(
        self,
        user_id: str,
        agent_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Agent]:
        """
        Find agents by user ID with filters.
        
        Optimized with eager loading to prevent N+1 queries.
        
        Args:
            user_id: User ID
            agent_type: Filter by agent type (optional)
            is_public: Filter by public status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Agent models
        """
        # Build base query
        query = self.db.query(Agent).filter(
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        )
        
        # Apply eager loading to prevent N+1 queries
        query = QueryOptimizer.apply_eager_loading(
            query,
            Agent,
            ['tools', 'knowledgebases'],
            strategy='joined'
        )
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        
        if is_public is not None:
            query = query.filter(Agent.is_public == is_public)
        
        query = query.order_by(Agent.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def find_public(
        self,
        agent_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Agent]:
        """
        Find public agents.
        
        Args:
            agent_type: Filter by agent type (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of public Agent models
        """
        query = self.db.query(Agent).filter(
            Agent.is_public == True,
            Agent.deleted_at.is_(None)
        )
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        
        query = query.order_by(Agent.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def update(self, agent: Agent) -> Agent:
        """
        Update an agent.
        
        Args:
            agent: Agent model to update
            
        Returns:
            Updated Agent model
        """
        agent.updated_at = datetime.utcnow()
        self.db.flush()
        return agent
    
    def soft_delete(self, agent: Agent) -> Agent:
        """
        Soft delete an agent.
        
        Args:
            agent: Agent model to delete
            
        Returns:
            Deleted Agent model
        """
        agent.deleted_at = datetime.utcnow()
        self.db.flush()
        return agent
    
    def hard_delete(self, agent: Agent) -> None:
        """
        Hard delete an agent.
        
        Args:
            agent: Agent model to delete
        """
        self.db.delete(agent)
        self.db.flush()
    
    def count_by_user(self, user_id: str, agent_type: Optional[str] = None) -> int:
        """
        Count agents by user.
        
        Args:
            user_id: User ID
            agent_type: Filter by agent type (optional)
            
        Returns:
            Count of agents
        """
        query = self.db.query(Agent).filter(
            Agent.user_id == user_id,
            Agent.deleted_at.is_(None)
        )
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        
        return QueryOptimizer.optimize_count_query(query)
    
    def exists(self, agent_id: str) -> bool:
        """
        Check if agent exists.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if exists, False otherwise
        """
        return QueryOptimizer.optimize_exists_check(
            self.db,
            Agent,
            {'id': agent_id, 'deleted_at': None}
        )
    
    def find_by_template(self, template_id: str, limit: int = 50) -> List[Agent]:
        """
        Find agents by template ID.
        
        Args:
            template_id: Template ID
            limit: Maximum number of results
            
        Returns:
            List of Agent models
        """
        return self.db.query(Agent).filter(
            Agent.template_id == template_id,
            Agent.deleted_at.is_(None)
        ).order_by(Agent.created_at.desc()).limit(limit).all()
    
    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Agent]:
        """
        Search agents by name or description.
        
        Args:
            query: Search query
            user_id: Filter by user ID (optional)
            limit: Maximum number of results
            
        Returns:
            List of Agent models
        """
        search_filter = or_(
            Agent.name.ilike(f"%{query}%"),
            Agent.description.ilike(f"%{query}%")
        )
        
        db_query = self.db.query(Agent).filter(
            search_filter,
            Agent.deleted_at.is_(None)
        )
        
        if user_id:
            db_query = db_query.filter(
                or_(
                    Agent.user_id == user_id,
                    Agent.is_public == True
                )
            )
        else:
            db_query = db_query.filter(Agent.is_public == True)
        
        return db_query.order_by(Agent.created_at.desc()).limit(limit).all()


class AgentVersionRepository:
    """Repository for AgentVersion data access."""
    
    def __init__(self, db: Session):
        """
        Initialize AgentVersion Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, version: AgentVersion) -> AgentVersion:
        """
        Create a new agent version.
        
        Args:
            version: AgentVersion model to create
            
        Returns:
            Created AgentVersion model
        """
        self.db.add(version)
        self.db.flush()
        return version
    
    def find_by_agent(self, agent_id: str) -> List[AgentVersion]:
        """
        Find versions by agent ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of AgentVersion models
        """
        return self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.created_at.desc()).all()
    
    def find_latest(self, agent_id: str) -> Optional[AgentVersion]:
        """
        Find latest version for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Latest AgentVersion model or None
        """
        return self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id
        ).order_by(AgentVersion.created_at.desc()).first()
    
    def find_by_version_number(
        self,
        agent_id: str,
        version_number: str
    ) -> Optional[AgentVersion]:
        """
        Find version by version number.
        
        Args:
            agent_id: Agent ID
            version_number: Version number
            
        Returns:
            AgentVersion model or None
        """
        return self.db.query(AgentVersion).filter(
            AgentVersion.agent_id == agent_id,
            AgentVersion.version_number == version_number
        ).first()


class AgentToolRepository:
    """Repository for AgentTool data access."""
    
    def __init__(self, db: Session):
        """
        Initialize AgentTool Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, agent_tool: AgentTool) -> AgentTool:
        """
        Create a new agent-tool association.
        
        Args:
            agent_tool: AgentTool model to create
            
        Returns:
            Created AgentTool model
        """
        self.db.add(agent_tool)
        self.db.flush()
        return agent_tool
    
    def find_by_agent(self, agent_id: str) -> List[AgentTool]:
        """
        Find tools by agent ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of AgentTool models
        """
        return self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id
        ).order_by(AgentTool.order).all()
    
    def delete_by_agent(self, agent_id: str) -> int:
        """
        Delete all tools for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Number of deleted records
        """
        count = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id
        ).delete()
        self.db.flush()
        return count
    
    def exists(self, agent_id: str, tool_id: str) -> bool:
        """
        Check if agent-tool association exists.
        
        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id,
            AgentTool.tool_id == tool_id
        ).count() > 0


class AgentKnowledgebaseRepository:
    """Repository for AgentKnowledgebase data access."""
    
    def __init__(self, db: Session):
        """
        Initialize AgentKnowledgebase Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, agent_kb: AgentKnowledgebase) -> AgentKnowledgebase:
        """
        Create a new agent-knowledgebase association.
        
        Args:
            agent_kb: AgentKnowledgebase model to create
            
        Returns:
            Created AgentKnowledgebase model
        """
        self.db.add(agent_kb)
        self.db.flush()
        return agent_kb
    
    def find_by_agent(self, agent_id: str) -> List[AgentKnowledgebase]:
        """
        Find knowledgebases by agent ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of AgentKnowledgebase models
        """
        return self.db.query(AgentKnowledgebase).filter(
            AgentKnowledgebase.agent_id == agent_id
        ).order_by(AgentKnowledgebase.priority).all()
    
    def delete_by_agent(self, agent_id: str) -> int:
        """
        Delete all knowledgebases for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Number of deleted records
        """
        count = self.db.query(AgentKnowledgebase).filter(
            AgentKnowledgebase.agent_id == agent_id
        ).delete()
        self.db.flush()
        return count
    
    def exists(self, agent_id: str, knowledgebase_id: str) -> bool:
        """
        Check if agent-knowledgebase association exists.
        
        Args:
            agent_id: Agent ID
            knowledgebase_id: Knowledgebase ID
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(AgentKnowledgebase).filter(
            AgentKnowledgebase.agent_id == agent_id,
            AgentKnowledgebase.knowledgebase_id == knowledgebase_id
        ).count() > 0
