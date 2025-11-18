"""Block Service for managing reusable blocks."""

import logging
import uuid
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Block, BlockVersion, BlockTestCase
from backend.models.agent_builder import (
    BlockCreate,
    BlockUpdate,
    BlockTestInput,
    BlockTestResult
)

logger = logging.getLogger(__name__)


class BlockService:
    """Service for managing blocks."""
    
    def __init__(self, db: Session):
        """
        Initialize Block Service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_block(
        self,
        user_id: str,
        block_data: BlockCreate
    ) -> Block:
        """
        Create a new block.
        
        Args:
            user_id: User ID creating the block
            block_data: Block creation data
            
        Returns:
            Created Block model
            
        Raises:
            ValueError: If block type is invalid
        """
        # Validate block type
        valid_types = ["llm", "tool", "logic", "composite"]
        if block_data.block_type not in valid_types:
            raise ValueError(
                f"Invalid block type: {block_data.block_type}. "
                f"Must be one of: {valid_types}"
            )
        
        # Create block
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
        
        self.db.add(block)
        self.db.flush()
        
        # Create initial version
        self._create_version(
            block=block,
            version_number="1.0.0",
            is_breaking_change=False
        )
        
        self.db.commit()
        self.db.refresh(block)
        
        logger.info(f"Created block: {block.id} ({block.name})")
        return block
    
    def get_block(self, block_id: str) -> Optional[Block]:
        """
        Get block by ID.
        
        Args:
            block_id: Block ID
            
        Returns:
            Block model or None if not found
        """
        return self.db.query(Block).filter(Block.id == block_id).first()
    
    def update_block(
        self,
        block_id: str,
        block_data: BlockUpdate
    ) -> Optional[Block]:
        """
        Update a block.
        
        Args:
            block_id: Block ID
            block_data: Block update data
            
        Returns:
            Updated Block model or None if not found
        """
        block = self.get_block(block_id)
        if not block:
            return None
        
        # Track if breaking changes were made
        is_breaking_change = False
        
        # Update fields
        if block_data.name is not None:
            block.name = block_data.name
        
        if block_data.description is not None:
            block.description = block_data.description
        
        if block_data.input_schema is not None:
            # Check if schema change is breaking
            if self._is_schema_breaking_change(
                block.input_schema,
                block_data.input_schema
            ):
                is_breaking_change = True
            block.input_schema = block_data.input_schema
        
        if block_data.output_schema is not None:
            # Check if schema change is breaking
            if self._is_schema_breaking_change(
                block.output_schema,
                block_data.output_schema
            ):
                is_breaking_change = True
            block.output_schema = block_data.output_schema
        
        if block_data.configuration is not None:
            block.configuration = block_data.configuration
        
        if block_data.implementation is not None:
            block.implementation = block_data.implementation
            is_breaking_change = True  # Implementation changes are breaking
        
        if block_data.is_public is not None:
            block.is_public = block_data.is_public
        
        # Update timestamp
        block.updated_at = datetime.utcnow()
        
        # Create new version
        latest_version = self.db.query(BlockVersion).filter(
            BlockVersion.block_id == block_id
        ).order_by(BlockVersion.created_at.desc()).first()
        
        if latest_version:
            major, minor, patch = latest_version.version_number.split(".")
            if is_breaking_change:
                new_version = f"{int(major) + 1}.0.0"
            else:
                new_version = f"{major}.{int(minor) + 1}.0"
        else:
            new_version = "1.0.0"
        
        self._create_version(
            block=block,
            version_number=new_version,
            is_breaking_change=is_breaking_change
        )
        
        self.db.commit()
        self.db.refresh(block)
        
        logger.info(f"Updated block: {block_id} (version: {new_version})")
        return block
    
    def delete_block(self, block_id: str) -> bool:
        """
        Delete a block.
        
        Args:
            block_id: Block ID
            
        Returns:
            True if deleted, False if not found
        """
        block = self.get_block(block_id)
        if not block:
            return False
        
        self.db.delete(block)
        self.db.commit()
        
        logger.info(f"Deleted block: {block_id}")
        return True
    
    def list_blocks(
        self,
        user_id: Optional[str] = None,
        block_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Block]:
        """
        List blocks with filters.
        
        Args:
            user_id: Filter by user ID (optional)
            block_type: Filter by block type (optional)
            is_public: Filter by public status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Block models
        """
        query = self.db.query(Block)
        
        if user_id:
            query = query.filter(Block.user_id == user_id)
        
        if block_type:
            query = query.filter(Block.block_type == block_type)
        
        if is_public is not None:
            query = query.filter(Block.is_public == is_public)
        
        query = query.order_by(Block.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    async def test_block(
        self,
        block_id: str,
        test_input: BlockTestInput,
        user_id: Optional[str] = None,
        save_execution: bool = True
    ) -> BlockTestResult:
        """
        Test a block with given input.
        
        Args:
            block_id: Block ID
            test_input: Test input data
            user_id: User ID (for execution history)
            save_execution: Whether to save execution history
            
        Returns:
            BlockTestResult with output or error
        """
        block = self.get_block(block_id)
        if not block:
            return BlockTestResult(
                success=False,
                error="Block not found",
                duration_ms=0
            )
        
        # Validate input against schema
        if not self._validate_input(test_input.input_data, block.input_schema):
            return BlockTestResult(
                success=False,
                error="Input validation failed",
                duration_ms=0
            )
        
        # Execute block based on type
        start_time = time.time()
        execution_status = "success"
        error_message = None
        output = None
        
        try:
            if block.block_type == "llm":
                output = await self._execute_llm_block(block, test_input)
            elif block.block_type == "tool":
                output = await self._execute_tool_block(block, test_input)
            elif block.block_type == "logic":
                output = await self._execute_logic_block(block, test_input)
            elif block.block_type == "composite":
                output = await self._execute_composite_block(block, test_input)
            else:
                execution_status = "failed"
                error_message = f"Unknown block type: {block.block_type}"
                return BlockTestResult(
                    success=False,
                    error=error_message,
                    duration_ms=0
                )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Save execution history
            if save_execution and user_id:
                self._save_block_execution(
                    block_id=block_id,
                    user_id=user_id,
                    input_data=test_input.input_data,
                    output_data=output,
                    status=execution_status,
                    duration_ms=duration_ms,
                    error_message=error_message
                )
            
            return BlockTestResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
                metadata={"block_type": block.block_type}
            )
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            execution_status = "failed"
            error_message = str(e)
            logger.error(f"Block execution failed: {e}")
            
            # Save failed execution history
            if save_execution and user_id:
                self._save_block_execution(
                    block_id=block_id,
                    user_id=user_id,
                    input_data=test_input.input_data,
                    output_data=None,
                    status=execution_status,
                    duration_ms=duration_ms,
                    error_message=error_message
                )
            
            return BlockTestResult(
                success=False,
                error=error_message,
                duration_ms=duration_ms
            )
    
    def _save_block_execution(
        self,
        block_id: str,
        user_id: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]],
        status: str,
        duration_ms: int,
        error_message: Optional[str] = None
    ):
        """Save block execution history to database."""
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
            logger.info(f"Saved block execution: {execution.id}")
        except Exception as e:
            logger.error(f"Failed to save block execution: {e}")
            self.db.rollback()
    
    def create_composite_block(
        self,
        user_id: str,
        name: str,
        description: str,
        workflow_definition: Dict[str, Any]
    ) -> Block:
        """
        Create a composite block from a workflow definition.
        
        Args:
            user_id: User ID
            name: Block name
            description: Block description
            workflow_definition: Workflow definition (nodes and edges)
            
        Returns:
            Created Block model
        """
        # Infer input/output schemas from workflow
        input_schema = self._infer_input_schema(workflow_definition)
        output_schema = self._infer_output_schema(workflow_definition)
        
        # Create block
        block = Block(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            block_type="composite",
            input_schema=input_schema,
            output_schema=output_schema,
            configuration={"workflow": workflow_definition},
            implementation=None,  # Composite blocks use workflow definition
            is_public=False
        )
        
        self.db.add(block)
        self.db.flush()
        
        # Create initial version
        self._create_version(
            block=block,
            version_number="1.0.0",
            is_breaking_change=False
        )
        
        self.db.commit()
        self.db.refresh(block)
        
        logger.info(f"Created composite block: {block.id}")
        return block
    
    def get_block_versions(self, block_id: str) -> List[BlockVersion]:
        """
        Get version history for a block.
        
        Args:
            block_id: Block ID
            
        Returns:
            List of BlockVersion models
        """
        return self.db.query(BlockVersion).filter(
            BlockVersion.block_id == block_id
        ).order_by(BlockVersion.created_at.desc()).all()
    
    def create_test_case(
        self,
        block_id: str,
        name: str,
        input_data: Dict[str, Any],
        expected_output: Dict[str, Any],
        assertions: Optional[List[str]] = None
    ) -> BlockTestCase:
        """
        Create a test case for a block.
        
        Args:
            block_id: Block ID
            name: Test case name
            input_data: Input data
            expected_output: Expected output
            assertions: List of assertions (optional)
            
        Returns:
            Created BlockTestCase model
        """
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
        
        logger.info(f"Created test case for block {block_id}: {name}")
        return test_case
    
    def _create_version(
        self,
        block: Block,
        version_number: str,
        is_breaking_change: bool
    ) -> BlockVersion:
        """
        Create a version snapshot of a block.
        
        Args:
            block: Block model
            version_number: Version number (semantic versioning)
            is_breaking_change: Whether this is a breaking change
            
        Returns:
            Created BlockVersion model
        """
        version = BlockVersion(
            id=str(uuid.uuid4()),
            block_id=block.id,
            version_number=version_number,
            configuration=block.configuration,
            implementation=block.implementation,
            is_breaking_change=is_breaking_change
        )
        
        self.db.add(version)
        return version
    
    def _is_schema_breaking_change(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> bool:
        """
        Check if schema change is breaking.
        
        A breaking change occurs when:
        - Required fields are added
        - Existing fields are removed
        - Field types are changed
        
        Args:
            old_schema: Old schema
            new_schema: New schema
            
        Returns:
            True if breaking change, False otherwise
        """
        # Check for added required fields
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))
        
        if new_required - old_required:
            return True
        
        # Check for removed fields
        old_properties = set(old_schema.get("properties", {}).keys())
        new_properties = set(new_schema.get("properties", {}).keys())
        
        if old_properties - new_properties:
            return True
        
        # Check for type changes
        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})
        
        for prop in old_properties & new_properties:
            old_type = old_props[prop].get("type")
            new_type = new_props[prop].get("type")
            
            if old_type != new_type:
                return True
        
        return False
    
    def _validate_input(
        self,
        input_data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> bool:
        """
        Validate input data against schema.
        
        Args:
            input_data: Input data
            schema: JSON Schema
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in input_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    async def _execute_llm_block(
        self,
        block: Block,
        test_input: BlockTestInput
    ) -> Dict[str, Any]:
        """Execute LLM block with LLM Manager."""
        try:
            from backend.services.llm_manager import LLMManager
            
            # Get LLM configuration from block
            config = block.configuration or {}
            llm_provider = config.get("llm_provider", "ollama")
            llm_model = config.get("llm_model", "llama3.1")
            prompt_template = config.get("prompt_template", "{input}")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 2000)
            
            # Initialize LLM Manager
            llm_manager = LLMManager()
            
            # Format prompt with input data
            prompt = prompt_template.format(**test_input.input_data)
            
            # Convert prompt to messages format
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Call LLM
            response = await llm_manager.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Response is a string, not a dict
            return {
                "output": response if isinstance(response, str) else str(response),
                "tokens_used": 0,  # Token counting would need to be implemented separately
                "model": llm_model,
                "provider": llm_provider
            }
            
        except Exception as e:
            logger.error(f"LLM block execution failed: {e}", exc_info=True)
            return {"output": f"Error: {str(e)}", "error": True}
    
    async def _execute_tool_block(
        self,
        block: Block,
        test_input: BlockTestInput
    ) -> Dict[str, Any]:
        """Execute tool block with Tool Registry."""
        try:
            from backend.services.agent_builder.tool_registry import ToolRegistry
            
            # Get tool configuration from block
            config = block.configuration or {}
            tool_id = config.get("tool_id")
            
            if not tool_id:
                raise ValueError("Tool block missing tool_id in configuration")
            
            # Initialize Tool Registry
            tool_registry = ToolRegistry()
            
            # Get tool
            tool = tool_registry.get_tool(tool_id)
            if not tool:
                raise ValueError(f"Tool {tool_id} not found")
            
            # Execute tool
            result = await tool_registry.execute_tool(
                tool_id=tool_id,
                input_data=test_input.input_data,
                context=test_input.context
            )
            
            return {
                "output": result.get("output"),
                "tool_id": tool_id,
                "tool_name": tool.name,
                "execution_time_ms": result.get("execution_time_ms", 0)
            }
            
        except Exception as e:
            logger.error(f"Tool block execution failed: {e}", exc_info=True)
            return {"output": f"Error: {str(e)}", "error": True}
    
    async def _execute_logic_block(
        self,
        block: Block,
        test_input: BlockTestInput
    ) -> Dict[str, Any]:
        """Execute logic block with custom Python code using secure executor."""
        if not block.implementation:
            raise ValueError("Logic block has no implementation")
        
        # Import secure executor
        from backend.services.agent_builder.block_executor_secure import get_block_executor
        
        # Get executor (use Docker if available, otherwise RestrictedPython)
        executor = get_block_executor(use_docker=False)
        
        # Execute code securely
        try:
            result = executor.execute_logic_block(
                code=block.implementation,
                input_data=test_input.input_data,
                context=test_input.context
            )
            return result
        except Exception as e:
            logger.error(f"Secure logic block execution failed: {e}", exc_info=True)
            raise ValueError(f"Logic block execution failed: {str(e)}")
    
    async def _execute_composite_block(
        self,
        block: Block,
        test_input: BlockTestInput
    ) -> Dict[str, Any]:
        """Execute composite block (placeholder)."""
        # This will be implemented when integrated with Workflow Executor
        return {"output": "Composite block execution not yet implemented"}
    
    def _infer_input_schema(
        self,
        workflow_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Infer input schema from workflow entry points.
        
        Args:
            workflow_definition: Workflow definition
            
        Returns:
            Inferred input schema
        """
        # Placeholder - basic schema
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }
    
    def _infer_output_schema(
        self,
        workflow_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Infer output schema from workflow exit points.
        
        Args:
            workflow_definition: Workflow definition
            
        Returns:
            Inferred output schema
        """
        # Placeholder - basic schema
        return {
            "type": "object",
            "properties": {
                "output": {"type": "string"}
            }
        }
