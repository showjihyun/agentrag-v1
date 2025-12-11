"""Block Value Objects"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class BlockType(str, Enum):
    """Types of blocks."""
    LLM = "llm"
    TOOL = "tool"
    CODE = "code"
    CONDITION = "condition"
    LOOP = "loop"
    HTTP = "http"
    DATABASE = "database"
    TRANSFORM = "transform"
    CUSTOM = "custom"


class BlockCategory(str, Enum):
    """Block categories."""
    AI = "ai"
    DATA = "data"
    INTEGRATION = "integration"
    LOGIC = "logic"
    UTILITY = "utility"


@dataclass(frozen=True)
class BlockConfig:
    """Block configuration."""
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockConfig":
        return cls(
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            settings=data.get("settings", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "inputs": self.inputs,
            "outputs": self.outputs,
            "settings": self.settings,
        }


@dataclass(frozen=True)
class BlockInput:
    """Block input definition."""
    name: str
    type: str
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass(frozen=True)
class BlockOutput:
    """Block output definition."""
    name: str
    type: str
    description: str = ""
