"""Block Entities"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from backend.services.agent_builder.domain.block.value_objects import (
    BlockType, BlockCategory, BlockConfig
)


@dataclass
class BlockEntity:
    """Block entity representing a reusable workflow component."""
    
    id: UUID
    user_id: UUID
    name: str
    block_type: BlockType
    category: BlockCategory = BlockCategory.UTILITY
    description: Optional[str] = None
    config: BlockConfig = field(default_factory=BlockConfig)
    code: Optional[str] = None
    is_public: bool = False
    is_system: bool = False
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        name: str,
        block_type: BlockType,
        category: BlockCategory = BlockCategory.UTILITY,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        is_public: bool = False,
    ) -> "BlockEntity":
        return cls(
            id=uuid4(),
            user_id=user_id,
            name=name,
            block_type=block_type,
            category=category,
            description=description,
            config=BlockConfig.from_dict(config or {}),
            code=code,
            is_public=is_public,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "block_type": self.block_type.value,
            "category": self.category.value,
            "description": self.description,
            "config": self.config.to_dict(),
            "code": self.code,
            "is_public": self.is_public,
            "is_system": self.is_system,
            "version": self.version,
            "tags": self.tags,
        }
    
    def soft_delete(self) -> None:
        self.deleted_at = datetime.utcnow()
