"""
Agent Domain Events

Events that occur within the Agent bounded context.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for domain events."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID = field(default=None)
    aggregate_type: str = "Agent"
    
    @property
    def event_type(self) -> str:
        return self.__class__.__name__


@dataclass
class AgentCreated(DomainEvent):
    """Event raised when an agent is created."""
    user_id: UUID = None
    agent_name: str = ""
    agent_type: str = "custom"
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1"
    tool_ids: List[str] = field(default_factory=list)
    knowledgebase_ids: List[str] = field(default_factory=list)
    is_public: bool = False


@dataclass
class AgentUpdated(DomainEvent):
    """Event raised when an agent is updated."""
    user_id: UUID = None
    updated_fields: List[str] = field(default_factory=list)
    previous_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)
    is_significant_change: bool = False
    new_version: Optional[str] = None


@dataclass
class AgentDeleted(DomainEvent):
    """Event raised when an agent is deleted."""
    user_id: UUID = None
    agent_name: str = ""
    deletion_type: str = "soft"  # soft or hard


@dataclass
class AgentExecuted(DomainEvent):
    """Event raised when an agent execution completes."""
    execution_id: UUID = None
    user_id: UUID = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "completed"  # completed, failed, timeout
    duration_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class AgentCloned(DomainEvent):
    """Event raised when an agent is cloned."""
    source_agent_id: UUID = None
    new_agent_id: UUID = None
    user_id: UUID = None
    new_agent_name: str = ""


@dataclass
class AgentToolAttached(DomainEvent):
    """Event raised when a tool is attached to an agent."""
    tool_id: str = None
    user_id: UUID = None
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentToolDetached(DomainEvent):
    """Event raised when a tool is detached from an agent."""
    tool_id: str = None
    user_id: UUID = None
