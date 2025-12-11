"""
Agent Aggregate Root

The aggregate root is the entry point for all operations on the Agent domain.
It ensures consistency and encapsulates business rules.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .entities import AgentEntity, AgentVersionEntity, AgentToolEntity
from .value_objects import AgentType, AgentConfig, LLMSettings, ToolBinding, KnowledgebaseBinding
from .events import (
    DomainEvent, AgentCreated, AgentUpdated, AgentDeleted, 
    AgentCloned, AgentToolAttached, AgentToolDetached
)


class AgentAggregate:
    """
    Agent Aggregate Root.
    
    Manages the Agent entity and its related entities (versions, tools, knowledgebases).
    All modifications to the aggregate go through this class.
    """
    
    def __init__(self, agent: AgentEntity):
        self._agent = agent
        self._events: List[DomainEvent] = []
        self._versions: List[AgentVersionEntity] = []
    
    @property
    def id(self) -> UUID:
        return self._agent.id
    
    @property
    def agent(self) -> AgentEntity:
        return self._agent
    
    @property
    def events(self) -> List[DomainEvent]:
        """Get uncommitted domain events."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear uncommitted events after persistence."""
        self._events.clear()
    
    # ========================================================================
    # FACTORY METHODS
    # ========================================================================
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        name: str,
        agent_type: AgentType,
        llm_provider: str,
        llm_model: str,
        description: Optional[str] = None,
        template_id: Optional[str] = None,
        prompt_template: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        tool_ids: Optional[List[str]] = None,
        knowledgebase_ids: Optional[List[str]] = None,
        is_public: bool = False,
    ) -> "AgentAggregate":
        """
        Factory method to create a new Agent aggregate.
        
        Args:
            user_id: Owner user ID
            name: Agent name
            agent_type: Type of agent
            llm_provider: LLM provider (ollama, openai, etc.)
            llm_model: LLM model name
            description: Optional description
            template_id: Optional template ID
            prompt_template: Optional custom prompt template
            configuration: Optional additional configuration
            tool_ids: Optional list of tool IDs to attach
            knowledgebase_ids: Optional list of knowledgebase IDs
            is_public: Whether agent is public
            
        Returns:
            New AgentAggregate instance
        """
        # Build configuration
        config_data = configuration or {}
        config_data["llm_provider"] = llm_provider
        config_data["llm_model"] = llm_model
        if prompt_template:
            config_data["prompt_template"] = prompt_template
        
        config = AgentConfig.from_dict(config_data)
        
        # Build tool bindings
        tools = [
            ToolBinding(tool_id=tid, order=i)
            for i, tid in enumerate(tool_ids or [])
        ]
        
        # Build knowledgebase bindings
        knowledgebases = [
            KnowledgebaseBinding(knowledgebase_id=kid, priority=i)
            for i, kid in enumerate(knowledgebase_ids or [])
        ]
        
        # Create entity
        agent = AgentEntity(
            id=uuid4(),
            user_id=user_id,
            name=name,
            agent_type=agent_type,
            config=config,
            description=description,
            template_id=template_id,
            is_public=is_public,
            tools=tools,
            knowledgebases=knowledgebases,
        )
        
        # Create aggregate
        aggregate = cls(agent)
        
        # Raise creation event
        aggregate._events.append(AgentCreated(
            aggregate_id=agent.id,
            user_id=user_id,
            agent_name=name,
            agent_type=agent_type.value,
            llm_provider=llm_provider,
            llm_model=llm_model,
            tool_ids=tool_ids or [],
            knowledgebase_ids=knowledgebase_ids or [],
            is_public=is_public,
        ))
        
        return aggregate
    
    # ========================================================================
    # COMMANDS
    # ========================================================================
    
    def update(
        self,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        prompt_template: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        is_public: Optional[bool] = None,
    ) -> None:
        """
        Update agent properties.
        
        Args:
            user_id: User performing the update
            name: New name (optional)
            description: New description (optional)
            llm_provider: New LLM provider (optional)
            llm_model: New LLM model (optional)
            prompt_template: New prompt template (optional)
            configuration: New configuration (optional)
            is_public: New public status (optional)
        """
        updated_fields = []
        previous_values = {}
        new_values = {}
        significant_change = False
        
        if name is not None and name != self._agent.name:
            previous_values["name"] = self._agent.name
            self._agent.name = name
            new_values["name"] = name
            updated_fields.append("name")
            significant_change = True
        
        if description is not None:
            previous_values["description"] = self._agent.description
            self._agent.description = description
            new_values["description"] = description
            updated_fields.append("description")
        
        if is_public is not None and is_public != self._agent.is_public:
            previous_values["is_public"] = self._agent.is_public
            self._agent.is_public = is_public
            new_values["is_public"] = is_public
            updated_fields.append("is_public")
        
        # Handle LLM settings changes
        if llm_provider or llm_model or prompt_template or configuration:
            config_dict = self._agent.config.to_dict()
            
            if llm_provider:
                config_dict["llm_settings"]["provider"] = llm_provider
                updated_fields.append("llm_provider")
                significant_change = True
            
            if llm_model:
                config_dict["llm_settings"]["model"] = llm_model
                updated_fields.append("llm_model")
                significant_change = True
            
            if prompt_template:
                config_dict["prompt_template"] = prompt_template
                updated_fields.append("prompt_template")
                significant_change = True
            
            if configuration:
                config_dict.update(configuration)
                updated_fields.append("configuration")
                significant_change = True
            
            # Rebuild config (immutable)
            self._agent.config = AgentConfig.from_dict(config_dict)
        
        self._agent.updated_at = datetime.utcnow()
        
        # Raise update event
        if updated_fields:
            self._events.append(AgentUpdated(
                aggregate_id=self._agent.id,
                user_id=user_id,
                updated_fields=updated_fields,
                previous_values=previous_values,
                new_values=new_values,
                is_significant_change=significant_change,
            ))
    
    def attach_tool(
        self,
        tool_id: str,
        user_id: UUID,
        configuration: Optional[Dict[str, Any]] = None,
        order: Optional[int] = None,
    ) -> None:
        """Attach a tool to the agent."""
        # Check if already attached
        existing = [t for t in self._agent.tools if t.tool_id == tool_id]
        if existing:
            return  # Already attached
        
        tool_order = order if order is not None else len(self._agent.tools)
        binding = ToolBinding(
            tool_id=tool_id,
            configuration=configuration or {},
            order=tool_order,
        )
        self._agent.add_tool(binding)
        
        self._events.append(AgentToolAttached(
            aggregate_id=self._agent.id,
            tool_id=UUID(tool_id) if isinstance(tool_id, str) else tool_id,
            user_id=user_id,
            configuration=configuration or {},
        ))
    
    def detach_tool(self, tool_id: str, user_id: UUID) -> None:
        """Detach a tool from the agent."""
        self._agent.remove_tool(tool_id)
        
        self._events.append(AgentToolDetached(
            aggregate_id=self._agent.id,
            tool_id=UUID(tool_id) if isinstance(tool_id, str) else tool_id,
            user_id=user_id,
        ))
    
    def delete(self, user_id: UUID, hard: bool = False) -> None:
        """
        Delete the agent.
        
        Args:
            user_id: User performing deletion
            hard: If True, mark for hard delete; otherwise soft delete
        """
        if not hard:
            self._agent.soft_delete()
        
        self._events.append(AgentDeleted(
            aggregate_id=self._agent.id,
            user_id=user_id,
            agent_name=self._agent.name,
            deletion_type="hard" if hard else "soft",
        ))
    
    def clone(self, user_id: UUID, new_name: Optional[str] = None) -> "AgentAggregate":
        """
        Clone this agent.
        
        Args:
            user_id: User creating the clone
            new_name: Name for the cloned agent
            
        Returns:
            New AgentAggregate instance
        """
        cloned = AgentAggregate.create(
            user_id=user_id,
            name=new_name or f"{self._agent.name} (Copy)",
            agent_type=self._agent.agent_type,
            llm_provider=self._agent.llm_provider,
            llm_model=self._agent.llm_model,
            description=self._agent.description,
            template_id=self._agent.template_id,
            prompt_template=self._agent.config.prompt_template,
            configuration=self._agent.config.to_dict(),
            tool_ids=[t.tool_id for t in self._agent.tools],
            knowledgebase_ids=[k.knowledgebase_id for k in self._agent.knowledgebases],
            is_public=False,  # Clones are private by default
        )
        
        # Add clone event to original
        self._events.append(AgentCloned(
            aggregate_id=self._agent.id,
            source_agent_id=self._agent.id,
            new_agent_id=cloned.id,
            user_id=user_id,
            new_agent_name=cloned.agent.name,
        ))
        
        return cloned
    
    # ========================================================================
    # VERSION MANAGEMENT
    # ========================================================================
    
    def create_version(
        self,
        created_by: UUID,
        change_description: str,
        is_major: bool = False,
    ) -> AgentVersionEntity:
        """
        Create a new version snapshot.
        
        Args:
            created_by: User creating the version
            change_description: Description of changes
            is_major: If True, increment major version
            
        Returns:
            New AgentVersionEntity
        """
        # Get latest version number
        if self._versions:
            latest = max(self._versions, key=lambda v: v.created_at)
            if is_major:
                version_number = latest.increment_major()
            else:
                version_number = latest.increment_minor()
        else:
            version_number = "1.0.0"
        
        version = AgentVersionEntity(
            id=uuid4(),
            agent_id=self._agent.id,
            version_number=version_number,
            configuration=self._agent.config.to_dict(),
            change_description=change_description,
            created_by=created_by,
            is_active=True,
        )
        
        # Deactivate previous versions
        for v in self._versions:
            v.is_active = False
        
        self._versions.append(version)
        return version
    
    def load_versions(self, versions: List[AgentVersionEntity]) -> None:
        """Load existing versions (for reconstitution from persistence)."""
        self._versions = versions
