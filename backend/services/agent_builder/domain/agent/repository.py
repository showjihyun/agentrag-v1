"""
Agent Repository Interface

Defines the contract for agent persistence operations.
Implementation is in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from .entities import AgentEntity, AgentVersionEntity, AgentToolEntity
from .value_objects import AgentType


class AgentRepositoryInterface(ABC):
    """Abstract repository interface for Agent aggregate."""
    
    @abstractmethod
    def save(self, agent: AgentEntity) -> AgentEntity:
        """Save an agent (create or update)."""
        pass
    
    @abstractmethod
    def find_by_id(self, agent_id: UUID) -> Optional[AgentEntity]:
        """Find agent by ID."""
        pass
    
    @abstractmethod
    def find_by_user(
        self,
        user_id: UUID,
        agent_type: Optional[AgentType] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AgentEntity]:
        """Find agents by user ID with optional filters."""
        pass
    
    @abstractmethod
    def find_public(
        self,
        agent_type: Optional[AgentType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AgentEntity]:
        """Find public agents."""
        pass
    
    @abstractmethod
    def delete(self, agent_id: UUID, hard: bool = False) -> bool:
        """Delete an agent (soft or hard delete)."""
        pass
    
    @abstractmethod
    def exists(self, agent_id: UUID) -> bool:
        """Check if agent exists."""
        pass


class AgentVersionRepositoryInterface(ABC):
    """Abstract repository interface for Agent versions."""
    
    @abstractmethod
    def save(self, version: AgentVersionEntity) -> AgentVersionEntity:
        """Save a version."""
        pass
    
    @abstractmethod
    def find_by_agent(self, agent_id: UUID) -> List[AgentVersionEntity]:
        """Find all versions for an agent."""
        pass
    
    @abstractmethod
    def find_latest(self, agent_id: UUID) -> Optional[AgentVersionEntity]:
        """Find the latest version for an agent."""
        pass
    
    @abstractmethod
    def find_by_version_number(
        self, agent_id: UUID, version_number: str
    ) -> Optional[AgentVersionEntity]:
        """Find a specific version."""
        pass


class AgentToolRepositoryInterface(ABC):
    """Abstract repository interface for Agent-Tool relationships."""
    
    @abstractmethod
    def save(self, agent_tool: AgentToolEntity) -> AgentToolEntity:
        """Save an agent-tool relationship."""
        pass
    
    @abstractmethod
    def find_by_agent(self, agent_id: UUID) -> List[AgentToolEntity]:
        """Find all tools for an agent."""
        pass
    
    @abstractmethod
    def delete_by_agent(self, agent_id: UUID) -> int:
        """Delete all tools for an agent. Returns count deleted."""
        pass
    
    @abstractmethod
    def delete(self, agent_id: UUID, tool_id: UUID) -> bool:
        """Delete a specific agent-tool relationship."""
        pass
