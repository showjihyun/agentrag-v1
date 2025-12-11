"""
Workflow Executor V2

Enhanced workflow execution engine with:
- Distributed state management
- Idempotency support
- Dead letter queue integration
- Distributed locking
- Event-driven architecture support
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from backend.services.agent_builder.workflow_state_manager import (
    WorkflowStateManager,
    WorkflowState,
    get_state_manager,
)
from backend.services.agent_builder.distributed_lock import (
    DistributedLockManager,
    get_lock_manager,
    LockAcquisitionError,
)
from backend.services.agent_builder.idempotency_manager import (
    IdempotencyManager,
    get_idempotency_manager,
)
from backend.services.agent_builder.dead_letter_queue import (
    DeadLetterQueue,
    get_dead_letter_queue,
)
from backend.services.agent_builder.workflow_errors import (
    WorkflowError,
    WorkflowErrorCode,
    create_error_response,
)
from backend.services.agent_builder.workflow_logger import (
    WorkflowLogger,
    generate_trace_id,
    set_trace_context,
    clear_trace_context,
)

logger = logging.getLogger(__name__)
wf_logger = WorkflowLogger("executor_v2")


class WorkflowExecutorV2:
    """
    Enhanced workflow executor with enterprise features.
    
    Improvements over V1:
    - Centralized state management with Redis
    - Idempotent execution support
    - Automatic DLQ for failed executions
    - Distributed locking for multi-instance
    - Checkpoint/restore for long workflows
    """
    
    def __init__(
        self,
        workflow: Any,
        db: Session,
        redis_client=None,
        execution_id: Optional[str] = None,
    ):
        """
        Initialize executor.
        
        Args:
            workflow: Workflow model instance
            db: Database session
            redis_client: Optional Redis client for distributed features
            execution_id: Optional pre-generated execution ID
        """
        self.workflow = workflow
        self.db = db
        self.redis = redis_client
        self.execution_id = execution_id or str(uuid.uuid4())
        
        # Initialize managers
        self.state_manager = get_state_manager(redis_client)
        self.lock_manager = get_lock_manager(redis_client)
        self.idempotency_manager = get_idempotency_manager(redis_client)
        self.dlq = get_dead_letter_queue(redis_client, db)
        
        # Execution settings
        self.workflow_timeout = 300  # 5 minutes default
        self.enable_checkpoints = True
        self.checkpoint_interval = 5  # Checkpoint every 5 nodes
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute workflow with full enterprise features.
        
        Args:
            input_data: Input data for workflow
            idempotency_key: Optional idempotency key for deduplication
            
        Returns:
            Execution result
        """
        workflow_id = str(self.workflow.id)
        trace_id = generate_trace_id()
        
        # Set trace context
        set_trace_context(
            trace_id=trace_id,
            workflow_id=workflow_id,
            execution_id=self.execution_id,
        )
        
        try:
            # Check idempotency
            if idempotency_key:
                existing = await self.idempotency_manager.check_and_set(
                    idempotency_key,
                    self.execution_id,
                )
                if existing:
                    logger.info(f"Returning cached response for idempotent request")
                    return existing.get("response", {
                        "execution_id": existing["execution_id"],
                        "status": existing["status"],
                        "message": "Duplicate request - returning cached result",
                    })
            
            # Acquire workflow lock
            try:
                async with self.lock_manager.workflow_lock(workflow_id, timeout=60):
                    result = await self._execute_with_state_management(input_data)
            except LockAcquisitionError:
                logger.warning(f"Could not acquire lock for workflow {workflow_id}")
                return {
                    "success": False,
                    "error": "Workflow is currently being executed. Please try again.",
                    "error_code": WorkflowErrorCode.CONCURRENCY_LIMIT.value,
                }
            
            # Complete idempotency record
            if idempotency_key:
                await self.idempotency_manager.complete(
                    idempotency_key,
                    result,
                    success=result.get("success", False),
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            
            # Add to DLQ
            await self.dlq.enqueue(
                execution_id=self.execution_id,
                workflow_id=workflow_id,
                error=e,
                input_data=input_data,
            )
            
            # Complete idempotency as failed
            if idempotency_key:
                await self.idempotency_manager.complete(
                    idempotency_key,
                    create_error_response(e),
                    success=False,
                )
            
            return create_error_response(e)
            
        finally:
            clear_trace_context()
    
    async def _execute_with_state_management(
        self,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute workflow with state management.
        
        Args:
            input_data: Input data
            
        Returns:
            Execution result
        """
        workflow_id = str(self.workflow.id)
        
        # Initialize state
        state = await self.state_manager.initialize_execution(
            execution_id=self.execution_id,
            workflow_id=workflow_id,
            input_data=input_data,
            metadata={
                "workflow_name": self.workflow.name,
                "started_by": input_data.pop("_user_id", None),
            },
        )
        
        # Transition to queued
        await self.state_manager.transition_state(
            self.execution_id,
            WorkflowState.QUEUED,
            "Execution queued",
        )
        
        try:
            # Transition to running
            await self.state_manager.transition_state(
                self.execution_id,
                WorkflowState.RUNNING,
                "Execution started",
            )
            
            wf_logger.workflow_start(workflow_id, self.execution_id, input_data)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_nodes(input_data),
                timeout=self.workflow_timeout,
            )
            
            # Transition to completed
            await self.state_manager.transition_state(
                self.execution_id,
                WorkflowState.COMPLETED,
                "Execution completed successfully",
            )
            
            return {
                "success": True,
                "execution_id": self.execution_id,
                "output": result,
                "state": (await self.state_manager.get_state(self.execution_id)),
            }
            
        except asyncio.TimeoutError:
            await self.state_manager.transition_state(
                self.execution_id,
                WorkflowState.TIMEOUT,
                f"Execution timed out after {self.workflow_timeout}s",
            )
            
            return {
                "success": False,
                "execution_id": self.execution_id,
                "error": f"Workflow timed out after {self.workflow_timeout} seconds",
                "error_code": WorkflowErrorCode.TIMEOUT.value,
            }
            
        except Exception as e:
            await self.state_manager.transition_state(
                self.execution_id,
                WorkflowState.FAILED,
                str(e),
                error=str(e),
            )
            raise
    
    async def _execute_nodes(self, input_data: Dict[str, Any]) -> Any:
        """
        Execute workflow nodes.
        
        This is a simplified version - the full implementation would
        delegate to the existing node execution logic.
        
        Args:
            input_data: Input data
            
        Returns:
            Final output
        """
        # Import the original executor for node execution
        from backend.services.agent_builder.workflow_executor import WorkflowExecutor
        
        # Create original executor for node processing
        original_executor = WorkflowExecutor(
            workflow=self.workflow,
            db=self.db,
            execution_id=self.execution_id,
        )
        
        # Get graph definition
        graph = self.workflow.graph_definition or {}
        nodes = graph.get("nodes", [])
        
        # Track node count for checkpointing
        node_count = 0
        
        # Hook into node execution for state updates
        original_execute_from_node = original_executor._execute_from_node
        
        async def wrapped_execute_from_node(current_node, nodes, edges, data):
            nonlocal node_count
            node_id = current_node["id"]
            
            # Update state with current node
            await self.state_manager.update_node_result(
                self.execution_id,
                node_id,
                {"status": "running"},
                status="running",
            )
            
            # Execute node
            result = await original_execute_from_node(current_node, nodes, edges, data)
            
            # Update state with result
            await self.state_manager.update_node_result(
                self.execution_id,
                node_id,
                result,
                status="success",
            )
            
            # Checkpoint periodically
            node_count += 1
            if self.enable_checkpoints and node_count % self.checkpoint_interval == 0:
                await self.state_manager.create_checkpoint(
                    self.execution_id,
                    f"auto_checkpoint_{node_count}",
                )
            
            return result
        
        # Replace method
        original_executor._execute_from_node = wrapped_execute_from_node
        
        # Execute
        result = await original_executor._execute_internal(input_data)
        
        return result.get("output", result)
    
    async def pause(self, reason: str = "Manual pause") -> Dict[str, Any]:
        """
        Pause workflow execution.
        
        Args:
            reason: Reason for pause
            
        Returns:
            Updated state
        """
        state = await self.state_manager.transition_state(
            self.execution_id,
            WorkflowState.PAUSED,
            reason,
        )
        
        # Create checkpoint
        await self.state_manager.create_checkpoint(
            self.execution_id,
            f"pause_{datetime.utcnow().isoformat()}",
        )
        
        return state
    
    async def resume(self, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Resume paused workflow.
        
        Args:
            checkpoint_id: Optional checkpoint to resume from
            
        Returns:
            Execution result
        """
        if checkpoint_id:
            await self.state_manager.restore_checkpoint(
                self.execution_id,
                checkpoint_id,
            )
        
        await self.state_manager.transition_state(
            self.execution_id,
            WorkflowState.RUNNING,
            "Execution resumed",
        )
        
        # Continue execution from current state
        state = await self.state_manager.get_state(self.execution_id)
        return await self._execute_nodes(state.get("input_data", {}))
    
    async def cancel(self, reason: str = "Manual cancellation") -> Dict[str, Any]:
        """
        Cancel workflow execution.
        
        Args:
            reason: Cancellation reason
            
        Returns:
            Final state
        """
        return await self.state_manager.transition_state(
            self.execution_id,
            WorkflowState.CANCELLED,
            reason,
        )


async def execute_workflow_v2(
    workflow: Any,
    db: Session,
    input_data: Dict[str, Any],
    redis_client=None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute workflow using V2 executor.
    
    Args:
        workflow: Workflow model
        db: Database session
        input_data: Input data
        redis_client: Optional Redis client
        idempotency_key: Optional idempotency key
        
    Returns:
        Execution result
    """
    executor = WorkflowExecutorV2(
        workflow=workflow,
        db=db,
        redis_client=redis_client,
    )
    
    return await executor.execute(input_data, idempotency_key)
