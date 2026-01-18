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
        config_dict = agent.config.to_dict() if agent.config else {}
        
        return {
            "id": str(agent.id),
            "user_id": str(agent.user_id),
            "name": agent.name,
            "description": agent.description,
            "agent_type": agent.agent_type.value,
            "template_id": agent.template_id,
            "llm_provider": agent.llm_provider,
            "llm_model": agent.llm_model,
            "configuration": config_dict,
            "tools": [
                {
                    "tool_id": tool.tool_id,
                    "order": tool.order,
                    "configuration": tool.configuration,
                    "enabled": tool.enabled
                }
                for tool in agent.tools
            ],
            "knowledgebases": [
                {
                    "knowledgebase_id": kb.knowledgebase_id,
                    "priority": kb.priority,
                    "search_top_k": kb.search_top_k,
                    "similarity_threshold": kb.similarity_threshold
                }
                for kb in agent.knowledgebases
            ],
            "is_public": agent.is_public,
            "status": agent.status.value if agent.status else "active",
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
        
        result = []
        for aggregate in aggregates:
            agent = aggregate.agent
            config_dict = agent.config.to_dict() if agent.config else {}
            
            result.append({
                "id": str(agent.id),
                "user_id": str(agent.user_id),
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type.value,
                "template_id": agent.template_id,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model,
                "configuration": config_dict,
                "tools": [
                    {
                        "tool_id": tool.tool_id,
                        "order": tool.order,
                        "configuration": tool.configuration,
                        "enabled": tool.enabled
                    }
                    for tool in agent.tools
                ],
                "knowledgebases": [
                    {
                        "knowledgebase_id": kb.knowledgebase_id,
                        "priority": kb.priority,
                        "search_top_k": kb.search_top_k,
                        "similarity_threshold": kb.similarity_threshold
                    }
                    for kb in agent.knowledgebases
                ],
                "is_public": agent.is_public,
                "status": agent.status.value if agent.status else "active",
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            })
        
        return result
