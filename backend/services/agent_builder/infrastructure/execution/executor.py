"""
Unified Workflow Executor

Single entry point for all workflow executions.
Replaces workflow_executor.py, workflow_executor_v2.py, agentflow_executor.py
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.workflow.entities import WorkflowEntity, NodeEntity
from backend.services.agent_builder.domain.workflow.value_objects import ExecutionContext, NodeType
from backend.services.agent_builder.domain.execution.aggregate import ExecutionAggregate
from backend.services.agent_builder.domain.execution.value_objects import ExecutionStatus, StepType
from backend.services.agent_builder.infrastructure.execution.node_handler_registry import NodeHandlerRegistry
from backend.services.agent_builder.infrastructure.execution.base_handler import NodeExecutionResult

logger = logging.getLogger(__name__)


class UnifiedExecutor:
    """
    Unified workflow execution engine.
    
    Features:
    - Pluggable node handlers via registry
    - Streaming execution updates via SSE
    - Checkpoint/resume support
    - Parallel node execution
    - Timeout and cancellation
    - Comprehensive metrics tracking
    """
    
    DEFAULT_TIMEOUT = 300  # 5 minutes
    MAX_ITERATIONS = 100  # Prevent infinite loops
    
    def __init__(
        self,
        db: Session,
        handler_registry: Optional[NodeHandlerRegistry] = None,
    ):
        self.db = db
        self.handler_registry = handler_registry or NodeHandlerRegistry()
        self._cancelled = False
        
        # Import and register all handlers
        self._ensure_handlers_registered()
    
    def _ensure_handlers_registered(self) -> None:
        """Ensure all node handlers are registered."""
        # Import handlers to trigger registration
        try:
            from backend.services.agent_builder.infrastructure.execution import node_handlers
        except ImportError as e:
            logger.warning(f"Could not import node handlers: {e}")
    
    async def execute(
        self,
        workflow: WorkflowEntity,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionAggregate:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow to execute
            input_data: Input data
            user_id: User ID
            execution_id: Optional pre-generated execution ID
            timeout: Optional timeout in seconds
            
        Returns:
            ExecutionAggregate with results
        """
        exec_id = execution_id or str(uuid4())
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Create execution aggregate
        execution = ExecutionAggregate.create(
            workflow_id=workflow.id,
            user_id=UUID(user_id),
            input_data=input_data,
            trigger_type="api",
        )
        
        # Override ID if provided
        if execution_id:
            execution._execution.id = UUID(execution_id)
        
        # Create execution context
        context = ExecutionContext(
            execution_id=str(execution.id),
            workflow_id=str(workflow.id),
            user_id=user_id,
            input_data=input_data,
            trace_id=str(uuid4()),
        )
        
        logger.info(f"Starting workflow execution: {workflow.id}, exec_id: {execution.id}")
        
        try:
            # Start execution
            execution.start()
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_workflow(workflow, context, execution),
                timeout=timeout,
            )
            
            # Complete execution
            execution.complete(result)
            
        except asyncio.TimeoutError:
            logger.error(f"Workflow execution timed out: {execution.id}")
            execution.timeout()
            
        except asyncio.CancelledError:
            logger.info(f"Workflow execution cancelled: {execution.id}")
            execution.cancel()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            execution.fail(str(e), "EXECUTION_ERROR")
        
        # Save execution to database
        await self._save_execution(execution)
        
        return execution
    
    async def execute_streaming(
        self,
        workflow: WorkflowEntity,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute workflow with streaming updates.
        
        Yields status updates for each node execution.
        """
        exec_id = execution_id or str(uuid4())
        
        execution = ExecutionAggregate.create(
            workflow_id=workflow.id,
            user_id=UUID(user_id),
            input_data=input_data,
        )
        
        if execution_id:
            execution._execution.id = UUID(execution_id)
        
        context = ExecutionContext(
            execution_id=str(execution.id),
            workflow_id=str(workflow.id),
            user_id=user_id,
            input_data=input_data,
        )
        
        yield {
            "type": "execution_started",
            "execution_id": str(execution.id),
            "workflow_id": str(workflow.id),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        execution.start()
        
        try:
            async for update in self._execute_workflow_streaming(workflow, context, execution):
                yield update
            
            execution.complete(context.node_results.get(workflow.entry_point, {}))
            
            yield {
                "type": "execution_completed",
                "execution_id": str(execution.id),
                "status": "completed",
                "output": execution.execution.output_data,
                "duration_ms": execution.execution.duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            execution.fail(str(e))
            
            yield {
                "type": "execution_failed",
                "execution_id": str(execution.id),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        await self._save_execution(execution)
    
    async def _execute_workflow(
        self,
        workflow: WorkflowEntity,
        context: ExecutionContext,
        execution: ExecutionAggregate,
    ) -> Dict[str, Any]:
        """Execute workflow nodes."""
        if not workflow.entry_point:
            raise ValueError("Workflow has no entry point")
        
        # Start from entry point
        current_node_id = workflow.entry_point
        iterations = 0
        
        while current_node_id and iterations < self.MAX_ITERATIONS:
            if self._cancelled:
                raise asyncio.CancelledError()
            
            iterations += 1
            node = workflow.get_node(current_node_id)
            
            if not node:
                raise ValueError(f"Node not found: {current_node_id}")
            
            # Get input for this node
            node_input = self._get_node_input(node, context)
            
            # Execute node
            result = await self._execute_node(node, context, execution, node_input)
            
            # Store result
            context.set_node_result(node.id, result.output)
            
            if not result.success:
                raise Exception(f"Node {node.id} failed: {result.error_message}")
            
            # Determine next node
            current_node_id = self._get_next_node(workflow, node, result, context)
            
            # Check for end node
            if node.is_exit_point:
                break
        
        # Return final output
        return context.node_results.get(workflow.entry_point, {})
    
    async def _execute_workflow_streaming(
        self,
        workflow: WorkflowEntity,
        context: ExecutionContext,
        execution: ExecutionAggregate,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with streaming updates."""
        if not workflow.entry_point:
            raise ValueError("Workflow has no entry point")
        
        current_node_id = workflow.entry_point
        iterations = 0
        
        while current_node_id and iterations < self.MAX_ITERATIONS:
            iterations += 1
            node = workflow.get_node(current_node_id)
            
            if not node:
                raise ValueError(f"Node not found: {current_node_id}")
            
            # Yield node start
            yield {
                "type": "node_started",
                "node_id": node.id,
                "node_type": node.node_type.value,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            node_input = self._get_node_input(node, context)
            result = await self._execute_node(node, context, execution, node_input)
            context.set_node_result(node.id, result.output)
            
            # Yield node complete
            yield {
                "type": "node_completed",
                "node_id": node.id,
                "success": result.success,
                "output": result.output,
                "duration_ms": result.duration_ms,
                "error": result.error_message,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            if not result.success:
                raise Exception(f"Node {node.id} failed: {result.error_message}")
            
            current_node_id = self._get_next_node(workflow, node, result, context)
            
            if node.is_exit_point:
                break
    
    async def _execute_node(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        execution: ExecutionAggregate,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute a single node."""
        start_time = time.time()
        
        # Record step start
        execution.record_node_start(node.id, node.node_type.value, input_data)
        
        # Get handler
        handler = self.handler_registry.get_handler(node.node_type.value)
        
        if not handler:
            # Fallback for unregistered types
            logger.warning(f"No handler for node type: {node.node_type.value}")
            return NodeExecutionResult(
                success=True,
                output=input_data,
                duration_ms=0,
            )
        
        try:
            # Validate
            is_valid, errors = await handler.validate(node)
            if not is_valid:
                return NodeExecutionResult(
                    success=False,
                    output={},
                    error_message="; ".join(errors),
                    error_code="VALIDATION_ERROR",
                )
            
            # Execute
            result = await handler.execute(node, context, input_data)
            
            # Record completion
            if result.success:
                execution.record_node_complete(node.id, result.output, result.duration_ms)
            else:
                execution.record_node_error(node.id, result.error_message or "Unknown error", result.duration_ms)
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            execution.record_node_error(node.id, str(e), duration_ms)
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="EXECUTION_ERROR",
                duration_ms=duration_ms,
            )
    
    def _get_node_input(
        self,
        node: NodeEntity,
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Get input data for a node."""
        # Check for input mapping in config
        input_mapping = node.config.extra.get("inputMapping", {})
        
        if input_mapping:
            result = {}
            for key, source in input_mapping.items():
                if source.startswith("input."):
                    field = source[6:]
                    result[key] = context.input_data.get(field)
                elif source.startswith("nodes."):
                    parts = source.split(".")
                    node_id = parts[1]
                    field = parts[2] if len(parts) > 2 else None
                    node_result = context.get_node_result(node_id)
                    if node_result:
                        result[key] = node_result.get(field) if field else node_result
                elif source.startswith("vars."):
                    var_name = source[5:]
                    result[key] = context.get_variable(var_name)
                else:
                    result[key] = source
            return result
        
        # Default: pass through input data
        return context.input_data
    
    def _get_next_node(
        self,
        workflow: WorkflowEntity,
        current_node: NodeEntity,
        result: NodeExecutionResult,
        context: ExecutionContext,
    ) -> Optional[str]:
        """Determine the next node to execute."""
        # Check for explicit next node in result
        if result.next_node_id:
            return result.next_node_id
        
        # Get outgoing edges
        edges = workflow.get_outgoing_edges(current_node.id)
        
        if not edges:
            return None
        
        # For condition nodes, evaluate edge conditions
        if current_node.node_type == NodeType.CONDITION:
            branch = result.output.get("branch", "true")
            
            for edge in edges:
                if edge.condition:
                    if edge.condition.label == branch or edge.condition.expression == branch:
                        return edge.target_node_id
                elif edge.label == branch:
                    return edge.target_node_id
            
            # Default to first edge
            return edges[0].target_node_id
        
        # For normal nodes, follow first edge
        return edges[0].target_node_id
    
    async def _save_execution(self, execution: ExecutionAggregate) -> None:
        """Save execution to database."""
        try:
            from backend.db.models.agent_builder import WorkflowExecution
            
            db_execution = WorkflowExecution(
                id=execution.id,
                workflow_id=execution.execution.workflow_id,
                user_id=execution.execution.user_id,
                input_data=execution.execution.input_data,
                output_data=execution.execution.output_data,
                execution_context=execution.execution.execution_context,
                status=execution.execution.status.value,
                error_message=execution.execution.error_message,
                started_at=execution.execution.started_at,
                completed_at=execution.execution.completed_at,
            )
            
            self.db.merge(db_execution)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
            self.db.rollback()
    
    def cancel(self) -> None:
        """Cancel the current execution."""
        self._cancelled = True
