"""
Agent Domain Entities

Core domain entities for the Agent bounded context.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .value_objects import AgentType, AgentStatus, AgentConfig, ModelConfig, ToolBinding, KnowledgebaseBinding


@dataclass
class AgentEntity:
    """Agent domain entity."""
    id: UUID
    user_id: UUID
    name: str
    agent_type: AgentType
    config: Optional[AgentConfig] = None
    description: Optional[str] = None
    template_id: Optional[str] = None
    is_public: bool = False
    is_active: bool = True
    tools: List[ToolBinding] = field(default_factory=list)
    knowledgebases: List[KnowledgebaseBinding] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    # Additional fields for repository compatibility
    system_prompt: Optional[str] = None
    model_config: Optional["ModelConfig"] = None
    status: Optional["AgentStatus"] = None
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    @property
    def llm_provider(self) -> str:
        return self.config.llm_settings.provider.value
    
    @property
    def llm_model(self) -> str:
        return self.config.llm_settings.model
    
    def add_tool(self, tool: ToolBinding) -> None:
        """Add a tool binding."""
        self.tools.append(tool)
        self.updated_at = datetime.utcnow()
    
    def remove_tool(self, tool_id: str) -> None:
        """Remove a tool binding."""
        self.tools = [t for t in self.tools if t.tool_id != tool_id]
        self.updated_at = datetime.utcnow()
    
    def add_knowledgebase(self, kb: KnowledgebaseBinding) -> None:
        """Add a knowledgebase binding."""
        self.knowledgebases.append(kb)
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete the agent."""
        self.deleted_at = datetime.utcnow()
        self.is_active = False


@dataclass
class AgentVersionEntity:
    """Agent version for tracking changes."""
    id: UUID
    agent_id: UUID
    version_number: str
    configuration: Dict[str, Any]
    change_description: str
    created_by: UUID
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = False
    
    @classmethod
    def create_initial(cls, agent: AgentEntity, created_by: UUID) -> "AgentVersionEntity":
        """Create initial version for a new agent."""
        return cls(
            id=uuid4(),
            agent_id=agent.id,
            version_number="1.0.0",
            configuration=agent.config.to_dict(),
            change_description="Initial version",
            created_by=created_by,
            is_active=True,
        )
    
    def increment_minor(self) -> str:
        """Get next minor version number."""
        parts = self.version_number.split(".")
        return f"{parts[0]}.{int(parts[1]) + 1}.0"
    
    def increment_major(self) -> str:
        """Get next major version number."""
        parts = self.version_number.split(".")
        return f"{int(parts[0]) + 1}.0.0"


@dataclass
class AgentToolEntity:
    """Agent-Tool relationship entity."""
    id: UUID
    agent_id: UUID
    tool_id: UUID
    configuration: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    is_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
