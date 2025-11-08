"""Refactored Block Service using Repository Pattern."""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Block, BlockVersion, BlockTestCase
from backend.db.repositories.block_repository import (
    BlockRepository,
    BlockVersionRepository,
    BlockTestCaseRepository
)
from backend.models.agent_builder import BlockCreate, BlockUpdate, BlockTestInput, BlockTestResult
from backend.validators.block_validator import BlockValidator
from backend.core.transaction import transaction
from backend.core.event_bus import EventBus
from backend.models.agent_builder_events import (
    BlockCreatedEvent,
    BlockUpdatedEvent,
    BlockDeletedEvent,
    BlockTestedEvent,
    BlockVersionCreatedEvent
)
from backend.exceptions.agent_builder import (
    BlockNotFoundException,
    BlockValidationException,
    BlockExecutionException
)

logger = logging.getLogger(__name__)


class BlockServiceRefactored:
    """Refactored Block Service with Repository Pattern."""
    
    def __init__(self, db: Session, event_bus: Optional[EventBus] = None):
        self.db = db
        self.event_bus = event_bus or EventBus()
        
        # Initialize repositories
        self.block_repo = BlockRepository(db)
        self.version_repo = BlockVersionRepository(db)
        self.test_repo = BlockTestCaseRepository(db)
    
    def create_block(self, user_id: str, block_data: BlockCreate) -> Block:
        """Create a new block."""
        # Validate
        errors = BlockValidator.validate_create(block_data)
        if errors:
            raise BlockValidationException(errors, block_data.model_dump())
        
        with transaction(self.db):
            block = Block(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=block_data.name,
                description=block_data.description,
                block_type=block_data.block_type,
                input_schema=block_data.input_schema,
                output_schema=block_data.output_schema,
                configuration=block_data.configuration or {},
                implementation=block_data.implementation,
                is_public=block_data.is_public
            )
            
            block = self.block_repo.create(block)
            self._create_version(block, "1.0.0", False)
        
        # Publish event
        self._publish_block_created_event(block, user_id)
        
        logger.info(f"Block created: {block.id}")
        return block
    
    def get_block(self, block_id: str) -> Block:
        """Get block by ID."""
        block = self.block_repo.find_by_id(block_id)
        if not block:
            raise BlockNotFoundException(block_id)
        return block
    
    def update_block(self, block_id: str, block_data: BlockUpdate) -> Block:
        """Update a block."""
        block = self.get_block(block_id)
        
        # Validate
        errors = BlockValidator.validate_update(block_data)
        if errors:
            raise BlockValidationException(errors)
        
        is_breaking = False
        
        with transaction(self.db):
            if block_data.name:
                block.name = block_data.name
            if block_data.description is not None:
                block.description = block_data.description
            if block_data.input_schema:
                is_breaking = True
                block.input_schema = block_data.input_schema
            if block_data.output_schema:
                is_breaking = True
                block.output_schema = block_data.output_schema
            if block_data.configuration:
                block.configuration = block_data.configuration
            if block_data.implementation:
                is_breaking = True
                block.implementation = block_data.implementation
            
            block = self.block_repo.update(block)
            
            # Create new version
            latest = self.version_repo.find_latest(block_id)
            if latest:
                major, minor, patch = latest.version_number.split(".")
                new_version = f"{int(major) + 1}.0.0" if is_breaking else f"{major}.{int(minor) + 1}.0"
            else:
                new_version = "1.0.0"
            
            self._create_version(block, new_version, is_breaking)
        
        # Publish event
        self._publish_block_updated_event(block, is_breaking, new_version)
        
        return block
    
    def delete_block(self, block_id: str) -> bool:
        """Delete a block."""
        block = self.get_block(block_id)
        
        with transaction(self.db):
            self.block_repo.delete(block)
        
        # Publish event
        self._publish_block_deleted_event(block)
        
        return True
    
    def _create_version(self, block: Block, version_number: str, is_breaking: bool):
        """Create block version."""
        version = BlockVersion(
            id=str(uuid.uuid4()),
            block_id=block.id,
            version_number=version_number,
            configuration=block.configuration,
            implementation=block.implementation,
            is_breaking_change=is_breaking
        )
        self.version_repo.create(version)
    
    def _publish_block_created_event(self, block: Block, user_id: str):
        """Publish BlockCreatedEvent."""
        try:
            event = BlockCreatedEvent(
                aggregate_id=block.id,
                block_id=block.id,
                user_id=user_id,
                block_name=block.name,
                block_type=block.block_type,
                is_public=block.is_public
            )
            self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish BlockCreatedEvent: {e}")
    
    def _publish_block_updated_event(self, block: Block, is_breaking: bool, new_version: str):
        """Publish BlockUpdatedEvent."""
        try:
            event = BlockUpdatedEvent(
                aggregate_id=block.id,
                block_id=block.id,
                user_id=block.user_id,
                updated_fields=["configuration"],
                is_breaking_change=is_breaking,
                new_version=new_version
            )
            self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish BlockUpdatedEvent: {e}")
    
    def _publish_block_deleted_event(self, block: Block):
        """Publish BlockDeletedEvent."""
        try:
            event = BlockDeletedEvent(
                aggregate_id=block.id,
                block_id=block.id,
                user_id=block.user_id,
                block_name=block.name
            )
            self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish BlockDeletedEvent: {e}")
