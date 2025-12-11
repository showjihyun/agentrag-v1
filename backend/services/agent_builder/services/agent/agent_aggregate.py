"""
Agent Aggregate for Event Sourcing

Implements Agent as an aggregate root with event sourcing.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.core.event_sourcing import Aggregate, DomainEvent
from backend.models.events import AgentEvent


logger = logging.getLogger(__name__)


class AgentAggregate(Aggregate):
    """
    Agent Aggregate Root.
    
    Manages agent state through domain events.
    """
    
    def __init__(self, aggregate_id: str):
        """
        Initialize Agent Aggregate.
        
        Args:
            aggregate_id: Agent ID
        """
        super().__init__(aggregate_id)
        
        # Agent state
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.agent_type: Optional[str] = None
        self.llm_provider: Optional[str] = None
        self.llm_model: Optional[str] = None
        self.configuration: Dict[str, Any] = {}
        self.tool_ids: List[str] = []
        self.knowledgebase_ids: List[str] = []
        self.is_public: bool = False
        self.is_deleted: bool = False
        
        # Metadata
        self.user_id: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None
    
    def create(
        self,
        name: str,
        user_id: str,
        agent_type: str = "custom",
        description: Optional[str] = None,
        llm_provider: str = "ollama",
        llm_model: str = "llama3.1",
        configuration: Optional[Dict[str, Any]] = None,
        tool_ids: Optional[List[str]] = None,
        knowledgebase_ids: Optional[List[str]] = None,
        is_public: bool = False
    ):
        """
        Create a new agent.
        
        Args:
            name: Agent name
            user_id: User ID
            agent_type: Agent type
            description: Agent description
            llm_provider: LLM provider
            llm_model: LLM model
            configuration: Agent configuration
            tool_ids: Tool IDs
            knowledgebase_ids: Knowledgebase IDs
            is_public: Public flag
        """
        self.raise_event(
            event_type=AgentEvent.CREATED,
            data={
                "name": name,
                "description": description,
                "agent_type": agent_type,
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "configuration": configuration or {},
                "tool_ids": tool_ids or [],
                "knowledgebase_ids": knowledgebase_ids or [],
                "is_public": is_public,
                "created_at": datetime.utcnow().isoformat()
            },
            user_id=user_id
        )
    
    def update(
        self,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        tool_ids: Optional[List[str]] = None,
        knowledgebase_ids: Optional[List[str]] = None,
        is_public: Optional[bool] = None
    ):
        """
        Update agent.
        
        Args:
            user_id: User ID
            name: New name
            description: New description
            llm_provider: New LLM provider
            llm_model: New LLM model
            configuration: New configuration
            tool_ids: New tool IDs
            knowledgebase_ids: New knowledgebase IDs
            is_public: New public flag
        """
        if self.is_deleted:
            raise ValueError("Cannot update deleted agent")
        
        changes = {}
        
        if name is not None and name != self.name:
            changes["name"] = name
        if description is not None and description != self.description:
            changes["description"] = description
        if llm_provider is not None and llm_provider != self.llm_provider:
            changes["llm_provider"] = llm_provider
        if llm_model is not None and llm_model != self.llm_model:
            changes["llm_model"] = llm_model
        if configuration is not None:
            changes["configuration"] = configuration
        if tool_ids is not None:
            changes["tool_ids"] = tool_ids
        if knowledgebase_ids is not None:
            changes["knowledgebase_ids"] = knowledgebase_ids
        if is_public is not None and is_public != self.is_public:
            changes["is_public"] = is_public
        
        if not changes:
            return  # No changes
        
        changes["updated_at"] = datetime.utcnow().isoformat()
        
        self.raise_event(
            event_type=AgentEvent.UPDATED,
            data=changes,
            user_id=user_id
        )
    
    def delete(self, user_id: str):
        """
        Delete agent (soft delete).
        
        Args:
            user_id: User ID
        """
        if self.is_deleted:
            raise ValueError("Agent already deleted")
        
        self.raise_event(
            event_type=AgentEvent.DELETED,
            data={"deleted_at": datetime.utcnow().isoformat()},
            user_id=user_id
        )
    
    def start_execution(
        self,
        user_id: str,
        input_data: Dict[str, Any],
        execution_id: str
    ):
        """
        Start agent execution.
        
        Args:
            user_id: User ID
            input_data: Input data
            execution_id: Execution ID
        """
        if self.is_deleted:
            raise ValueError("Cannot execute deleted agent")
        
        self.raise_event(
            event_type=AgentEvent.EXECUTION_STARTED,
            data={
                "execution_id": execution_id,
                "input_data": input_data,
                "started_at": datetime.utcnow().isoformat()
            },
            user_id=user_id,
            correlation_id=execution_id
        )
    
    def complete_execution(
        self,
        execution_id: str,
        output_data: Dict[str, Any],
        duration_ms: float
    ):
        """
        Complete agent execution.
        
        Args:
            execution_id: Execution ID
            output_data: Output data
            duration_ms: Execution duration in milliseconds
        """
        self.raise_event(
            event_type=AgentEvent.EXECUTION_COMPLETED,
            data={
                "execution_id": execution_id,
                "output_data": output_data,
                "duration_ms": duration_ms,
                "completed_at": datetime.utcnow().isoformat()
            },
            correlation_id=execution_id
        )
    
    def fail_execution(
        self,
        execution_id: str,
        error: str,
        duration_ms: float
    ):
        """
        Fail agent execution.
        
        Args:
            execution_id: Execution ID
            error: Error message
            duration_ms: Execution duration in milliseconds
        """
        self.raise_event(
            event_type=AgentEvent.EXECUTION_FAILED,
            data={
                "execution_id": execution_id,
                "error": error,
                "duration_ms": duration_ms,
                "failed_at": datetime.utcnow().isoformat()
            },
            correlation_id=execution_id
        )
    
    def apply_event(self, event: DomainEvent):
        """
        Apply event to update aggregate state.
        
        Args:
            event: Domain event
        """
        if event.event_type == AgentEvent.CREATED:
            self._apply_created(event)
        elif event.event_type == AgentEvent.UPDATED:
            self._apply_updated(event)
        elif event.event_type == AgentEvent.DELETED:
            self._apply_deleted(event)
        elif event.event_type == AgentEvent.EXECUTION_STARTED:
            self._apply_execution_started(event)
        elif event.event_type == AgentEvent.EXECUTION_COMPLETED:
            self._apply_execution_completed(event)
        elif event.event_type == AgentEvent.EXECUTION_FAILED:
            self._apply_execution_failed(event)
    
    def _apply_created(self, event: DomainEvent):
        """Apply agent created event."""
        data = event.data
        
        self.name = data["name"]
        self.description = data.get("description")
        self.agent_type = data["agent_type"]
        self.llm_provider = data["llm_provider"]
        self.llm_model = data["llm_model"]
        self.configuration = data.get("configuration", {})
        self.tool_ids = data.get("tool_ids", [])
        self.knowledgebase_ids = data.get("knowledgebase_ids", [])
        self.is_public = data.get("is_public", False)
        self.user_id = event.user_id
        self.created_at = datetime.fromisoformat(data["created_at"])
        self.updated_at = self.created_at
    
    def _apply_updated(self, event: DomainEvent):
        """Apply agent updated event."""
        data = event.data
        
        if "name" in data:
            self.name = data["name"]
        if "description" in data:
            self.description = data["description"]
        if "llm_provider" in data:
            self.llm_provider = data["llm_provider"]
        if "llm_model" in data:
            self.llm_model = data["llm_model"]
        if "configuration" in data:
            self.configuration = data["configuration"]
        if "tool_ids" in data:
            self.tool_ids = data["tool_ids"]
        if "knowledgebase_ids" in data:
            self.knowledgebase_ids = data["knowledgebase_ids"]
        if "is_public" in data:
            self.is_public = data["is_public"]
        
        self.updated_at = datetime.fromisoformat(data["updated_at"])
    
    def _apply_deleted(self, event: DomainEvent):
        """Apply agent deleted event."""
        self.is_deleted = True
        self.deleted_at = datetime.fromisoformat(event.data["deleted_at"])
    
    def _apply_execution_started(self, event: DomainEvent):
        """Apply execution started event."""
        # Update last execution time
        self.updated_at = datetime.fromisoformat(event.data["started_at"])
    
    def _apply_execution_completed(self, event: DomainEvent):
        """Apply execution completed event."""
        # Update last execution time
        self.updated_at = datetime.fromisoformat(event.data["completed_at"])
    
    def _apply_execution_failed(self, event: DomainEvent):
        """Apply execution failed event."""
        # Update last execution time
        self.updated_at = datetime.fromisoformat(event.data["failed_at"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "configuration": self.configuration,
            "tool_ids": self.tool_ids,
            "knowledgebase_ids": self.knowledgebase_ids,
            "is_public": self.is_public,
            "is_deleted": self.is_deleted,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "version": self.version
        }
