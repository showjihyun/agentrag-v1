"""Workflow executor for executing visual workflows.

This module provides the WorkflowExecutor class that orchestrates the execution
of workflows by processing blocks in topological order.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.core.execution.context import ExecutionContext, BlockState
from backend.core.execution.errors import (
    ExecutionError,
    WorkflowNotFoundError,
    BlockExecutionError,
    CyclicDependencyError,
    ExecutionTimeoutError,
)
from backend.core.blocks.registry import BlockRegistry
from backend.db.models.agent_builder import (
    Workflow,
    AgentBlock,
    AgentEdge,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Executes workflows by processing blocks in topological order.
    
    The executor:
    1. Loads workflow definition from database
    2. Creates execution context
    3. Performs topological sort to determine execution order
    4. Executes blocks sequentially
    5. Handles control flow (conditions, loops, parallel)
    6. Logs execution results
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize WorkflowExecutor.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.block_registry = BlockRegistry
    
    async def execute(
        self,
        workflow_id: str,
        user_id: str,
        trigger: str = "manual",
        input_data: Dict[str, Any] = None
    ) -> ExecutionContext:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow identifier
            user_id: User identifier
            trigger: Trigger type (manual, webhook, schedule, api, chat)
            input_data: Input data for workflow
            
        Returns:
            ExecutionContext with execution results
            
        Raises:
            WorkflowNotFoundError: If workflow not found
            ExecutionError: If execution fails
        """
        execution_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting workflow execution: workflow_id={workflow_id}, "
            f"execution_id={execution_id}, trigger={trigger}"
        )
        
        try:
            # 1. Load workflow definition
            workflow = await self.load_workflow(workflow_id)
            
            # 2. Create execution context
            context = ExecutionContext(
                workflow_id=workflow_id,
                execution_id=execution_id,
                user_id=user_id,
                trigger=trigger,
                started_at=datetime.utcnow(),
            )
            
            # Load environment variables
            context.environment_variables = await self.load_env_vars(user_id)
            
            # Load workflow variables
            context.workflow_variables = input_data or {}
            
            # Initialize block states
            blocks = await self.load_blocks(workflow_id)
            for block in blocks:
                context.block_states[str(block.id)] = BlockState(
                    block_id=str(block.id),
                    block_type=block.type,
                )
            
            # 3. Find start blocks (blocks with no incoming edges)
            start_blocks = await self.find_start_blocks(workflow_id, blocks)
            
            if not start_blocks:
                raise ExecutionError(
                    "No start blocks found in workflow",
                    execution_id=execution_id,
                    workflow_id=workflow_id,
                )
            
            logger.info(f"Found {len(start_blocks)} start blocks")
            
            # 4. Get execution order using topological sort
            execution_order = await self.topological_sort(workflow_id, blocks)
            
            logger.info(f"Execution order: {[str(b.id) for b in execution_order]}")
            
            # 5. Execute blocks in order
            for block in execution_order:
                await self.execute_block(block, context)
                
                # Check if execution should stop (e.g., error occurred)
                if context.status == "failed":
                    break
            
            # 6. Mark execution as completed
            context.completed_at = datetime.utcnow()
            if context.status == "running":
                context.status = "completed"
            
            duration_ms = int(
                (context.completed_at - context.started_at).total_seconds() * 1000
            )
            
            logger.info(
                f"Workflow execution completed: execution_id={execution_id}, "
                f"status={context.status}, duration_ms={duration_ms}"
            )
            
            # 7. Save execution log
            await self.save_execution_log(context)
            
            return context
            
        except Exception as e:
            logger.error(
                f"Workflow execution failed: execution_id={execution_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            
            # Create error context if not already created
            if 'context' not in locals():
                context = ExecutionContext(
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    user_id=user_id,
                    trigger=trigger,
                    started_at=datetime.utcnow(),
                )
            
            context.status = "failed"
            context.error_message = str(e)
            context.completed_at = datetime.utcnow()
            
            # Save error log
            await self.save_execution_log(context)
            
            raise ExecutionError(
                f"Workflow execution failed: {str(e)}",
                execution_id=execution_id,
                workflow_id=workflow_id,
                original_error=e
            )
    
    async def load_workflow(self, workflow_id: str) -> Workflow:
        """
        Load workflow from database.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow model
            
        Raises:
            WorkflowNotFoundError: If workflow not found
        """
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        
        if not workflow:
            raise WorkflowNotFoundError(
                f"Workflow not found: {workflow_id}",
                workflow_id=workflow_id
            )
        
        return workflow
    
    async def load_blocks(self, workflow_id: str) -> List[AgentBlock]:
        """
        Load blocks for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of AgentBlock models
        """
        blocks = self.db.query(AgentBlock).filter(
            AgentBlock.workflow_id == workflow_id,
            AgentBlock.enabled == True
        ).all()
        
        return blocks
    
    async def load_edges(self, workflow_id: str) -> List[AgentEdge]:
        """
        Load edges for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of AgentEdge models
        """
        edges = self.db.query(AgentEdge).filter(
            AgentEdge.workflow_id == workflow_id
        ).all()
        
        return edges
    
    async def load_env_vars(self, user_id: str) -> Dict[str, Any]:
        """
        Load environment variables for user from Variable model.
        
        Loads variables in order of precedence:
        1. Global variables
        2. User-specific variables (override global)
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of environment variables
        """
        from backend.db.models.agent_builder import Variable
        from backend.utils.encryption import encryption_service
        import json
        
        env_vars = {}
        
        try:
            # Load global variables first
            global_vars = self.db_session.query(Variable).filter(
                Variable.scope == "global",
                Variable.deleted_at.is_(None)
            ).all()
            
            for var in global_vars:
                env_vars[var.name] = self._parse_variable_value(var)
            
            # Load user-specific variables (override global)
            if user_id:
                user_vars = self.db_session.query(Variable).filter(
                    Variable.scope == "user",
                    Variable.scope_id == user_id,
                    Variable.deleted_at.is_(None)
                ).all()
                
                for var in user_vars:
                    env_vars[var.name] = self._parse_variable_value(var)
            
            logger.debug(f"Loaded {len(env_vars)} environment variables for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to load environment variables: {e}")
        
        return env_vars
    
    def _parse_variable_value(self, var) -> Any:
        """Parse variable value based on its type."""
        from backend.utils.encryption import encryption_service
        import json
        
        value = var.value
        
        # Decrypt if secret
        if var.is_secret and var.secret:
            try:
                value = encryption_service.decrypt(var.secret.encrypted_value)
            except Exception as e:
                logger.warning(f"Failed to decrypt secret variable {var.name}: {e}")
                return None
        
        # Parse based on type
        if var.value_type == "number":
            try:
                return float(value) if "." in str(value) else int(value)
            except (ValueError, TypeError):
                return value
        elif var.value_type == "boolean":
            return str(value).lower() in ("true", "1", "yes")
        elif var.value_type == "json":
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        else:
            return value
    
    async def find_start_blocks(
        self,
        workflow_id: str,
        blocks: List[AgentBlock]
    ) -> List[AgentBlock]:
        """
        Find start blocks (blocks with no incoming edges).
        
        Args:
            workflow_id: Workflow identifier
            blocks: List of blocks
            
        Returns:
            List of start blocks
        """
        edges = await self.load_edges(workflow_id)
        
        # Get all block IDs that have incoming edges
        blocks_with_incoming = {str(edge.target_block_id) for edge in edges}
        
        # Start blocks are those without incoming edges
        start_blocks = [
            block for block in blocks
            if str(block.id) not in blocks_with_incoming
        ]
        
        return start_blocks
    
    async def topological_sort(
        self,
        workflow_id: str,
        blocks: List[AgentBlock]
    ) -> List[AgentBlock]:
        """
        Perform topological sort to determine block execution order.
        
        Uses Kahn's algorithm for topological sorting.
        
        Args:
            workflow_id: Workflow identifier
            blocks: List of blocks
            
        Returns:
            List of blocks in execution order
            
        Raises:
            CyclicDependencyError: If workflow has cycles
        """
        edges = await self.load_edges(workflow_id)
        
        # Build adjacency list and in-degree map
        adjacency: Dict[str, List[str]] = {str(block.id): [] for block in blocks}
        in_degree: Dict[str, int] = {str(block.id): 0 for block in blocks}
        block_map: Dict[str, AgentBlock] = {str(block.id): block for block in blocks}
        
        for edge in edges:
            source_id = str(edge.source_block_id)
            target_id = str(edge.target_block_id)
            adjacency[source_id].append(target_id)
            in_degree[target_id] += 1
        
        # Find blocks with no incoming edges
        queue = [block_id for block_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Process block with no dependencies
            current_id = queue.pop(0)
            result.append(block_map[current_id])
            
            # Reduce in-degree for neighbors
            for neighbor_id in adjacency[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
        
        # Check if all blocks were processed
        if len(result) != len(blocks):
            raise CyclicDependencyError(
                "Workflow contains cyclic dependencies",
                workflow_id=workflow_id
            )
        
        return result
    
    async def execute_block(
        self,
        block: AgentBlock,
        context: ExecutionContext
    ):
        """
        Execute a single block.
        
        Args:
            block: AgentBlock model
            context: Execution context
        """
        block_id = str(block.id)
        
        logger.info(f"Executing block: {block_id} ({block.type})")
        
        # Get block state
        block_state = context.block_states[block_id]
        block_state.started_at = datetime.utcnow()
        
        try:
            # Create block instance
            block_instance = self.block_registry.create_block_instance(
                block_type=block.type,
                block_id=block_id,
                config=block.config,
                sub_blocks=block.sub_blocks
            )
            
            # Prepare inputs by resolving references to previous block outputs
            inputs = await self.prepare_block_inputs(block, context)
            
            # Execute block with error handling
            result = await block_instance.execute_with_error_handling(
                inputs=inputs,
                context={
                    "execution_id": context.execution_id,
                    "workflow_id": context.workflow_id,
                    "user_id": context.user_id,
                    "variables": context.workflow_variables,
                    "previous_outputs": {
                        bid: state.outputs
                        for bid, state in context.block_states.items()
                        if state.executed
                    },
                }
            )
            
            # Update block state
            block_state.completed_at = datetime.utcnow()
            block_state.duration_ms = result.get("duration_ms", 0)
            block_state.executed = True
            block_state.success = result.get("success", False)
            
            if result.get("success"):
                block_state.outputs = result.get("outputs", {})
                
                # Add log entry
                context.add_log(
                    block_id=block_id,
                    block_type=block.type,
                    block_name=block.name,
                    success=True,
                    inputs=inputs,
                    outputs=block_state.outputs,
                    duration_ms=block_state.duration_ms,
                    metadata=result.get("metadata", {}),
                )
                
                logger.info(
                    f"Block executed successfully: {block_id}, "
                    f"duration_ms={block_state.duration_ms}"
                )
            else:
                block_state.error = result.get("error", "Unknown error")
                
                # Add error log entry
                context.add_log(
                    block_id=block_id,
                    block_type=block.type,
                    block_name=block.name,
                    success=False,
                    inputs=inputs,
                    error=block_state.error,
                    error_type=result.get("error_type", "execution"),
                    duration_ms=block_state.duration_ms,
                    metadata=result.get("metadata", {}),
                )
                
                # Mark execution as failed
                context.status = "failed"
                context.error_message = f"Block {block_id} failed: {block_state.error}"
                
                logger.error(
                    f"Block execution failed: {block_id}, error={block_state.error}"
                )
            
        except Exception as e:
            block_state.completed_at = datetime.utcnow()
            block_state.executed = True
            block_state.success = False
            block_state.error = str(e)
            
            if block_state.started_at:
                duration_ms = int(
                    (block_state.completed_at - block_state.started_at).total_seconds() * 1000
                )
                block_state.duration_ms = duration_ms
            
            # Add error log entry
            context.add_log(
                block_id=block_id,
                block_type=block.type,
                block_name=block.name,
                success=False,
                error=str(e),
                error_type="unexpected",
                duration_ms=block_state.duration_ms,
            )
            
            # Mark execution as failed
            context.status = "failed"
            context.error_message = f"Block {block_id} failed: {str(e)}"
            
            logger.error(
                f"Block execution error: {block_id}, error={str(e)}",
                exc_info=True
            )
    
    async def prepare_block_inputs(
        self,
        block: AgentBlock,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Prepare inputs for block execution.
        
        Resolves references to previous block outputs and variables.
        
        Args:
            block: AgentBlock model
            context: Execution context
            
        Returns:
            Dictionary of resolved inputs
        """
        inputs = {}
        
        # Get input configuration from block
        input_config = block.inputs or {}
        
        # Resolve each input
        for input_name, input_spec in input_config.items():
            # Check if input is a reference to another block's output
            if isinstance(input_spec, dict) and "block_id" in input_spec:
                # Reference format: {"block_id": "block_123", "output_key": "result"}
                ref_block_id = input_spec["block_id"]
                output_key = input_spec.get("output_key")
                
                value = context.get_block_output(ref_block_id, output_key)
                inputs[input_name] = value
            
            # Check if input is a variable reference
            elif isinstance(input_spec, str) and input_spec.startswith("{{"):
                # Variable format: "{{variable_name}}"
                resolved = context.resolve_template(input_spec)
                inputs[input_name] = resolved
            
            # Direct value
            else:
                inputs[input_name] = input_spec
        
        # Also include SubBlock values as inputs
        for sub_block_id, sub_block_value in block.sub_blocks.items():
            if isinstance(sub_block_value, str) and sub_block_value.startswith("{{"):
                inputs[sub_block_id] = context.resolve_template(sub_block_value)
            else:
                inputs[sub_block_id] = sub_block_value
        
        return inputs
    
    async def save_execution_log(self, context: ExecutionContext):
        """
        Save execution log to database.
        
        Args:
            context: Execution context
        """
        from backend.db.models.agent_builder import WorkflowExecution
        
        try:
            # Calculate duration
            duration_ms = None
            if context.started_at and context.completed_at:
                duration_ms = int(
                    (context.completed_at - context.started_at).total_seconds() * 1000
                )
            
            # Create execution record
            execution = WorkflowExecution(
                id=uuid.UUID(context.execution_id),
                workflow_id=uuid.UUID(context.workflow_id),
                user_id=uuid.UUID(context.user_id),
                input_data=context.workflow_variables,
                output_data=self.get_final_output(context),
                execution_context=context.to_dict(),
                status=context.status,
                error_message=context.error_message,
                started_at=context.started_at,
                completed_at=context.completed_at,
                duration_ms=duration_ms,
            )
            
            self.db.add(execution)
            self.db.commit()
            
            logger.info(f"Saved execution log: {context.execution_id}")
            
        except Exception as e:
            logger.error(
                f"Failed to save execution log: {context.execution_id}, error={str(e)}",
                exc_info=True
            )
            self.db.rollback()
    
    def get_final_output(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Get final output from execution context.
        
        Returns outputs from all executed blocks.
        
        Args:
            context: Execution context
            
        Returns:
            Dictionary of final outputs
        """
        final_output = {}
        
        for block_id, block_state in context.block_states.items():
            if block_state.executed and block_state.success:
                final_output[block_id] = block_state.outputs
        
        return final_output
