"""
Block Service - Unified Implementation
Combines best practices from original and refactored versions.

Uses:
- Repository Pattern for data access
- Transaction management
- Event sourcing
- Semantic versioning
"""

import logging
import uuid
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Block, BlockVersion, BlockTestCase
from backend.db.repositories.block_repository import (
    BlockRepository,
    BlockVersionRepository,
    BlockTestCaseRepository
)
from backend.models.agent_builder import (
    BlockCreate, BlockUpdate, BlockTestInput, BlockTestResult
)
from backend.validators.block_validator import BlockValidator
from backend.core.transaction import transaction
from backend.core.event_bus import EventBus
from backend.models.agent_builder_events import (
    BlockCreatedEvent, BlockUpdatedEvent, BlockDeletedEvent, BlockTestedEvent
)
from backend.exceptions.agent_builder import (
    BlockNotFoundException,
    BlockValidationException,
    BlockExecutionException
)

logger = logging.getLogger(__name__)


class BlockService:
    """
    Unified Block Service with DDD patterns.
    
    Features:
    - Repository pattern for clean data access
    - Transaction management for data integrity
    - Event sourcing for audit trail
    - Semantic versioning for breaking changes
    """
    
    VALID_BLOCK_TYPES = ["llm", "tool", "logic", "composite"]
    
    def __init__(self, db: Session, event_bus: Optional[EventBus] = None):
        self.db = db
        
        # Use provided event_bus or create a no-op one if Redis is not available
        if event_bus is not None:
            self.event_bus = event_bus
        else:
            # Create a no-op EventBus for when Redis is not available
            self.event_bus = self._create_noop_event_bus()
        
        # Initialize repositories
        self.block_repo = BlockRepository(db)
        self.version_repo = BlockVersionRepository(db)
        self.test_repo = BlockTestCaseRepository(db)
    
    def _create_noop_event_bus(self):
        """Create a no-op EventBus for when Redis is not available."""
        class NoOpEventBus:
            async def publish(self, event_type: str, data: dict, **kwargs):
                """No-op publish method."""
                pass
            
            def subscribe(self, event_type: str, handler):
                """No-op subscribe method."""
                pass
        
        return NoOpEventBus()
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def create_block(self, user_id: str, block_data: BlockCreate) -> Block:
        """Create a new block with validation."""
        self._validate_block_type(block_data.block_type)
        
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
        
        self._publish_event(BlockCreatedEvent(
            aggregate_id=str(block.id),
            aggregate_type="block",
            block_id=str(block.id),
            user_id=str(user_id),
            block_name=block.name,
            block_type=block.block_type,
            is_public=block.is_public
        ))
        
        logger.info(f"Block created: {block.id} ({block.name})")
        return block
    
    def get_block(self, block_id: str) -> Block:
        """Get block by ID."""
        block = self.block_repo.find_by_id(block_id)
        if not block:
            raise BlockNotFoundException(block_id)
        return block
    
    def update_block(self, block_id: str, block_data: BlockUpdate) -> Block:
        """Update a block with version tracking."""
        block = self.get_block(block_id)
        
        errors = BlockValidator.validate_update(block_data)
        if errors:
            raise BlockValidationException(errors)
        
        is_breaking = False
        
        with transaction(self.db):
            if block_data.name is not None:
                block.name = block_data.name
            if block_data.description is not None:
                block.description = block_data.description
            if block_data.input_schema is not None:
                is_breaking = self._is_schema_breaking(block.input_schema, block_data.input_schema)
                block.input_schema = block_data.input_schema
            if block_data.output_schema is not None:
                is_breaking = is_breaking or self._is_schema_breaking(
                    block.output_schema, block_data.output_schema
                )
                block.output_schema = block_data.output_schema
            if block_data.configuration is not None:
                block.configuration = block_data.configuration
            if block_data.implementation is not None:
                block.implementation = block_data.implementation
                is_breaking = True
            if block_data.is_public is not None:
                block.is_public = block_data.is_public
            
            block.updated_at = datetime.utcnow()
            block = self.block_repo.update(block)
            
            new_version = self._get_next_version(block_id, is_breaking)
            self._create_version(block, new_version, is_breaking)
        
        self._publish_event(BlockUpdatedEvent(
            aggregate_id=str(block.id),
            aggregate_type="block",
            block_id=str(block.id),
            user_id=str(block.user_id),
            updated_fields=["configuration"],
            is_breaking_change=is_breaking,
            new_version=new_version
        ))
        
        logger.info(f"Block updated: {block_id} (version: {new_version})")
        return block
    
    def delete_block(self, block_id: str) -> bool:
        """Delete a block."""
        block = self.get_block(block_id)
        
        with transaction(self.db):
            self.block_repo.delete(block)
        
        self._publish_event(BlockDeletedEvent(
            aggregate_id=str(block.id),
            aggregate_type="block",
            block_id=str(block.id),
            user_id=str(block.user_id),
            block_name=block.name
        ))
        
        logger.info(f"Block deleted: {block_id}")
        return True
    
    def list_blocks(
        self,
        user_id: Optional[str] = None,
        block_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Block]:
        """List blocks with filters."""
        query = self.db.query(Block)
        
        if user_id:
            query = query.filter(Block.user_id == user_id)
        if block_type:
            query = query.filter(Block.block_type == block_type)
        if is_public is not None:
            query = query.filter(Block.is_public == is_public)
        
        return query.order_by(Block.created_at.desc()).limit(limit).offset(offset).all()
    
    # ========================================================================
    # BLOCK EXECUTION
    # ========================================================================
    
    async def test_block(
        self,
        block_id: str,
        test_input: BlockTestInput,
        user_id: Optional[str] = None,
        save_execution: bool = True
    ) -> BlockTestResult:
        """Test a block with given input."""
        try:
            block = self.get_block(block_id)
        except BlockNotFoundException:
            return BlockTestResult(success=False, error="Block not found", duration_ms=0)
        
        if not self._validate_input(test_input.input_data, block.input_schema):
            return BlockTestResult(success=False, error="Input validation failed", duration_ms=0)
        
        start_time = time.time()
        
        try:
            output = await self._execute_block(block, test_input)
            duration_ms = int((time.time() - start_time) * 1000)
            
            if save_execution and user_id:
                self._save_execution(block_id, user_id, test_input.input_data, 
                                    output, "success", duration_ms)
            
            self._publish_event(BlockTestedEvent(
                aggregate_id=block_id,
                block_id=block_id,
                user_id=user_id or "anonymous",
                success=True,
                duration_ms=duration_ms
            ))
            
            return BlockTestResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
                metadata={"block_type": block.block_type}
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            if save_execution and user_id:
                self._save_execution(block_id, user_id, test_input.input_data,
                                    None, "failed", duration_ms, error_msg)
            
            logger.error(f"Block execution failed: {e}")
            return BlockTestResult(success=False, error=error_msg, duration_ms=duration_ms)
    
    async def _execute_block(self, block: Block, test_input: BlockTestInput) -> Dict[str, Any]:
        """Execute block based on type."""
        executors = {
            "llm": self._execute_llm_block,
            "tool": self._execute_tool_block,
            "logic": self._execute_logic_block,
            "composite": self._execute_composite_block
        }
        
        executor = executors.get(block.block_type)
        if not executor:
            raise ValueError(f"Unknown block type: {block.block_type}")
        
        return await executor(block, test_input)
    
    async def _execute_llm_block(self, block: Block, test_input: BlockTestInput) -> Dict[str, Any]:
        """Execute LLM block."""
        from backend.services.llm_manager import LLMManager
        
        config = block.configuration or {}
        llm_manager = LLMManager()
        
        prompt = config.get("prompt_template", "{input}").format(**test_input.input_data)
        messages = [{"role": "user", "content": prompt}]
        
        response = await llm_manager.generate(
            messages=messages,
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000)
        )
        
        return {
            "output": response if isinstance(response, str) else str(response),
            "model": config.get("llm_model", "llama3.1"),
            "provider": config.get("llm_provider", "ollama")
        }
    
    async def _execute_tool_block(self, block: Block, test_input: BlockTestInput) -> Dict[str, Any]:
        """Execute tool block."""
        from backend.services.agent_builder.tool_registry import ToolRegistry
        
        config = block.configuration or {}
        tool_id = config.get("tool_id")
        
        if not tool_id:
            raise ValueError("Tool block missing tool_id")
        
        registry = ToolRegistry()
        tool = registry.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")
        
        result = await registry.execute_tool(tool_id, test_input.input_data, test_input.context)
        return {"output": result.get("output"), "tool_id": tool_id, "tool_name": tool.name}
    
    async def _execute_logic_block(self, block: Block, test_input: BlockTestInput) -> Dict[str, Any]:
        """Execute logic block securely."""
        if not block.implementation:
            raise ValueError("Logic block has no implementation")
        
        from backend.services.agent_builder.block_executor_secure import get_block_executor
        executor = get_block_executor(use_docker=False)
        return executor.execute_logic_block(
            block.implementation, test_input.input_data, test_input.context
        )
    
    async def _execute_composite_block(self, block: Block, test_input: BlockTestInput) -> Dict[str, Any]:
        """Execute composite block."""
        return {"output": "Composite block execution not yet implemented"}
    
    # ========================================================================
    # VERSION MANAGEMENT
    # ========================================================================
    
    def get_block_versions(self, block_id: str) -> List[BlockVersion]:
        """Get version history for a block."""
        return self.version_repo.find_by_block(block_id)
    
    def create_composite_block(
        self,
        user_id: str,
        name: str,
        description: str,
        workflow_definition: Dict[str, Any]
    ) -> Block:
        """Create a composite block from workflow definition."""
        with transaction(self.db):
            block = Block(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=name,
                description=description,
                block_type="composite",
                input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"output": {"type": "string"}}},
                configuration={"workflow": workflow_definition},
                implementation=None,
                is_public=False
            )
            block = self.block_repo.create(block)
            self._create_version(block, "1.0.0", False)
        
        logger.info(f"Composite block created: {block.id}")
        return block
    
    def create_test_case(
        self,
        block_id: str,
        name: str,
        input_data: Dict[str, Any],
        expected_output: Dict[str, Any],
        assertions: Optional[List[str]] = None
    ) -> BlockTestCase:
        """Create a test case for a block."""
        test_case = BlockTestCase(
            id=str(uuid.uuid4()),
            block_id=block_id,
            name=name,
            input_data=input_data,
            expected_output=expected_output,
            assertions=assertions or []
        )
        
        self.db.add(test_case)
        self.db.commit()
        self.db.refresh(test_case)
        
        logger.info(f"Test case created for block {block_id}: {name}")
        return test_case
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _validate_block_type(self, block_type: str) -> None:
        """Validate block type."""
        if block_type not in self.VALID_BLOCK_TYPES:
            raise ValueError(f"Invalid block type: {block_type}. Must be one of: {self.VALID_BLOCK_TYPES}")
    
    def _validate_input(self, input_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate input against schema."""
        required = schema.get("required", [])
        return all(field in input_data for field in required)
    
    def _is_schema_breaking(self, old: Dict[str, Any], new: Dict[str, Any]) -> bool:
        """Check if schema change is breaking."""
        old_required = set(old.get("required", []))
        new_required = set(new.get("required", []))
        
        if new_required - old_required:
            return True
        
        old_props = set(old.get("properties", {}).keys())
        new_props = set(new.get("properties", {}).keys())
        
        if old_props - new_props:
            return True
        
        return False
    
    def _create_version(self, block: Block, version: str, is_breaking: bool) -> BlockVersion:
        """Create block version."""
        version_obj = BlockVersion(
            id=str(uuid.uuid4()),
            block_id=block.id,
            version_number=version,
            configuration=block.configuration,
            implementation=block.implementation,
            is_breaking_change=is_breaking
        )
        return self.version_repo.create(version_obj)
    
    def _get_next_version(self, block_id: str, is_breaking: bool) -> str:
        """Get next version number."""
        latest = self.version_repo.find_latest(block_id)
        if latest:
            major, minor, patch = latest.version_number.split(".")
            if is_breaking:
                return f"{int(major) + 1}.0.0"
            return f"{major}.{int(minor) + 1}.0"
        return "1.0.0"
    
    def _save_execution(
        self,
        block_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]],
        status: str,
        duration_ms: int,
        error_message: Optional[str] = None
    ) -> None:
        """Save block execution history."""
        try:
            from backend.db.models.agent_builder import BlockExecution
            
            execution = BlockExecution(
                block_id=block_id,
                user_id=user_id,
                input_data=input_data,
                output_data=output_data,
                status=status,
                duration_ms=duration_ms,
                error_message=error_message,
                execution_metadata={"block_type": "test"}
            )
            self.db.add(execution)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
            self.db.rollback()
    
    def _publish_event(self, event) -> None:
        """Publish event to event bus."""
        try:
            self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")


# Backward compatibility alias
BlockServiceRefactored = BlockService
