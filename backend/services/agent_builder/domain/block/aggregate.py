"""Block Aggregate Root"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from backend.services.agent_builder.domain.block.entities import BlockEntity
from backend.services.agent_builder.domain.block.value_objects import (
    BlockType, BlockCategory, BlockConfig
)


class BlockAggregate:
    """Block Aggregate Root."""
    
    def __init__(self, block: BlockEntity):
        self._block = block
        self._events: List[Dict[str, Any]] = []
    
    @property
    def id(self) -> UUID:
        return self._block.id
    
    @property
    def block(self) -> BlockEntity:
        return self._block
    
    @property
    def events(self) -> List[Dict[str, Any]]:
        return self._events.copy()
    
    def clear_events(self) -> None:
        self._events.clear()
    
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
    ) -> "BlockAggregate":
        block = BlockEntity.create(
            user_id=user_id,
            name=name,
            block_type=block_type,
            category=category,
            description=description,
            config=config,
            code=code,
            is_public=is_public,
        )
        
        aggregate = cls(block)
        aggregate._events.append({
            "type": "BlockCreated",
            "block_id": str(block.id),
            "name": name,
            "block_type": block_type.value,
        })
        
        return aggregate
    
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> None:
        if name is not None:
            self._block.name = name
        if description is not None:
            self._block.description = description
        if config is not None:
            self._block.config = BlockConfig.from_dict(config)
        if code is not None:
            self._block.code = code
        if is_public is not None:
            self._block.is_public = is_public
        
        self._block.updated_at = datetime.utcnow()
        
        self._events.append({
            "type": "BlockUpdated",
            "block_id": str(self._block.id),
        })
    
    def delete(self, hard: bool = False) -> None:
        if not hard:
            self._block.soft_delete()
        
        self._events.append({
            "type": "BlockDeleted",
            "block_id": str(self._block.id),
            "hard": hard,
        })
    
    def clone(self, user_id: UUID, new_name: Optional[str] = None) -> "BlockAggregate":
        return BlockAggregate.create(
            user_id=user_id,
            name=new_name or f"{self._block.name} (Copy)",
            block_type=self._block.block_type,
            category=self._block.category,
            description=self._block.description,
            config=self._block.config.to_dict(),
            code=self._block.code,
            is_public=False,
        )
