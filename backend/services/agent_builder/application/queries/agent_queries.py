"""
Agent Queries

Query objects and handlers for agent read operations.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from backend.services.agent_builder.infrastructure.persistence import AgentRepositoryImpl

logger = logging.getLogger(__name__)


@dataclass
class GetAgentQuery:
    """Query to get an agent by ID."""
    agent_id: str


@dataclass
class ListAgentsQuery:
    """Query to list agents."""
    user_id: Optional[str] = None
    agent_type: Optional[str] = None
    is_public: Optional[bool] = None
    limit: int = 50
    offset: int = 0


class AgentQueryHandler:
    """Handles agent queries."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AgentRepositoryImpl(db)
    
    def handle_get(self, query: GetAgentQuery) -> Optional[Dict[str, Any]]:
        """Handle GetAgentQuery."""
        try:
            agent_uuid = UUID(query.agent_id)
        except ValueError as e:
            logger.error(f"Invalid UUID format for agent_id: {query.agent_id}")
            raise ValueError(f"Invalid agent ID format: {query.agent_id}") from e
            
        aggregate = self.repository.find_by_id(agent_uuid)
        if not aggregate:
            return None
        
        agent = aggregate.agent
        return {
            "id": str(agent.id),
            "user_id": str(agent.user_id),
            "name": agent.name,
            "description": agent.description,
            "agent_type": agent.agent_type.value,
            "system_prompt": agent.system_prompt,
            "model_config": agent.model_config.to_dict() if agent.model_config else {},
            "tools": agent.tools,
            "is_public": agent.is_public,
            "status": agent.status.value,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
        }
    
    def handle_list(self, query: ListAgentsQuery) -> List[Dict[str, Any]]:
        """Handle ListAgentsQuery."""
        if query.user_id:
            aggregates = self.repository.find_by_user(
                UUID(query.user_id),
                limit=query.limit,
                offset=query.offset,
            )
        elif query.is_public:
            aggregates = self.repository.find_public(
                limit=query.limit,
                offset=query.offset,
            )
        else:
            aggregates = []
        
        return [
            {
                "id": str(a.agent.id),
                "name": a.agent.name,
                "description": a.agent.description,
                "agent_type": a.agent.agent_type.value,
                "is_public": a.agent.is_public,
                "status": a.agent.status.value,
            }
            for a in aggregates
        ]
