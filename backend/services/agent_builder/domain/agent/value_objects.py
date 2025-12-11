"""
Agent Value Objects

Immutable objects that describe characteristics of domain entities.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class AgentType(str, Enum):
    """Agent type enumeration."""
    CUSTOM = "custom"
    TEMPLATE_BASED = "template_based"
    CHATFLOW = "chatflow"
    AGENTFLOW = "agentflow"
    ASSISTANT = "assistant"


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class LLMProvider(str, Enum):
    """LLM provider enumeration."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"


@dataclass(frozen=True)
class LLMSettings:
    """LLM configuration value object."""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMSettings":
        return cls(
            provider=LLMProvider(data.get("provider", "ollama")),
            model=data.get("model", "llama3.1"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            top_p=data.get("top_p", 1.0),
            frequency_penalty=data.get("frequency_penalty", 0.0),
            presence_penalty=data.get("presence_penalty", 0.0),
        )


@dataclass(frozen=True)
class AgentConfig:
    """Agent configuration value object."""
    llm_settings: LLMSettings
    prompt_template: Optional[str] = None
    system_prompt: Optional[str] = None
    memory_enabled: bool = True
    memory_window: int = 10
    tools_enabled: bool = True
    streaming_enabled: bool = True
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_seconds: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm_settings": self.llm_settings.to_dict(),
            "prompt_template": self.prompt_template,
            "system_prompt": self.system_prompt,
            "memory_enabled": self.memory_enabled,
            "memory_window": self.memory_window,
            "tools_enabled": self.tools_enabled,
            "streaming_enabled": self.streaming_enabled,
            "retry_on_failure": self.retry_on_failure,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        llm_data = data.get("llm_settings", {})
        if not llm_data:
            llm_data = {
                "provider": data.get("llm_provider", "ollama"),
                "model": data.get("llm_model", "llama3.1"),
            }
        
        return cls(
            llm_settings=LLMSettings.from_dict(llm_data),
            prompt_template=data.get("prompt_template"),
            system_prompt=data.get("system_prompt"),
            memory_enabled=data.get("memory_enabled", True),
            memory_window=data.get("memory_window", 10),
            tools_enabled=data.get("tools_enabled", True),
            streaming_enabled=data.get("streaming_enabled", True),
            retry_on_failure=data.get("retry_on_failure", True),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 60),
        )


@dataclass(frozen=True)
class ToolBinding:
    """Tool binding to an agent."""
    tool_id: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    enabled: bool = True


@dataclass(frozen=True)
class KnowledgebaseBinding:
    """Knowledgebase binding to an agent."""
    knowledgebase_id: str
    priority: int = 0
    search_top_k: int = 5
    similarity_threshold: float = 0.7


@dataclass(frozen=True)
class ModelConfig:
    """Model configuration value object for agent repository compatibility."""
    provider: str = "ollama"
    model: str = "llama3.1"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        return cls(
            provider=data.get("provider", "ollama"),
            model=data.get("model", "llama3.1"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            top_p=data.get("top_p", 1.0),
            frequency_penalty=data.get("frequency_penalty", 0.0),
            presence_penalty=data.get("presence_penalty", 0.0),
        )
