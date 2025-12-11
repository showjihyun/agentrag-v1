"""
Agent Commands

Command objects and handlers for agent operations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.agent.aggregate import AgentAggregate
from backend.services.agent_builder.domain.agent.value_objects import AgentType
from backend.services.agent_builder.infrastructure.persistence import AgentRepositoryImpl


# ============================================================================
# COMMAND OBJECTS
# ============================================================================

@dataclass
class CreateAgentCommand:
    """Command to create a new agent."""
    user_id: str
    name: str
    agent_type: str = "assistant"
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Dict[str, Any] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    is_public: bool = False


@dataclass
class UpdateAgentCommand:
    """Command to update an agent."""
    agent_id: str
    user_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


@dataclass
class DeleteAgentCommand:
    """Command to delete an agent."""
    agent_id: str
    user_id: str
    hard: bool = False


@dataclass
class AddToolCommand:
    """Command to add a tool to an agent."""
    agent_id: str
    user_id: str
    tool_id: str


@dataclass
class RemoveToolCommand:
    """Command to remove a tool from an agent."""
    agent_id: str
    user_id: str
    tool_id: str


# ============================================================================
# COMMAND HANDLER
# ============================================================================

class AgentCommandHandler:
    """Handles agent commands."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AgentRepositoryImpl(db)
    
    def handle_create(self, command: CreateAgentCommand) -> AgentAggregate:
        """Handle CreateAgentCommand."""
        aggregate = AgentAggregate.create(
            user_id=UUID(command.user_id),
            name=command.name,
            agent_type=AgentType(command.agent_type),
            description=command.description,
            system_prompt=command.system_prompt,
            model_config=command.model_config,
            tools=command.tools,
            is_public=command.is_public,
        )
        
        self.repository.save(aggregate)
        return aggregate
    
    def handle_update(self, command: UpdateAgentCommand) -> Optional[AgentAggregate]:
        """Handle UpdateAgentCommand."""
        aggregate = self.repository.find_by_id(UUID(command.agent_id))
        if not aggregate:
            return None
        
        aggregate.update(
            user_id=UUID(command.user_id),
            name=command.name,
            description=command.description,
            system_prompt=command.system_prompt,
            model_config=command.model_config,
            is_public=command.is_public,
        )
        
        self.repository.save(aggregate)
        return aggregate
    
    def handle_delete(self, command: DeleteAgentCommand) -> bool:
        """Handle DeleteAgentCommand."""
        aggregate = self.repository.find_by_id(UUID(command.agent_id))
        if not aggregate:
            return False
        
        aggregate.delete(UUID(command.user_id), hard=command.hard)
        
        if command.hard:
            return self.repository.delete(UUID(command.agent_id))
        else:
            self.repository.save(aggregate)
            return True
    
    def handle_add_tool(self, command: AddToolCommand) -> Optional[AgentAggregate]:
        """Handle AddToolCommand."""
        aggregate = self.repository.find_by_id(UUID(command.agent_id))
        if not aggregate:
            return None
        
        aggregate.add_tool(command.tool_id)
        self.repository.save(aggregate)
        return aggregate
    
    def handle_remove_tool(self, command: RemoveToolCommand) -> Optional[AgentAggregate]:
        """Handle RemoveToolCommand."""
        aggregate = self.repository.find_by_id(UUID(command.agent_id))
        if not aggregate:
            return None
        
        aggregate.remove_tool(command.tool_id)
        self.repository.save(aggregate)
        return aggregate
