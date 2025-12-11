"""
Legacy Executor Adapter

Provides backward compatibility with existing executor implementations.
Wraps legacy executors to work with the new DDD architecture.
"""

import logging
from typing import Dict, Any, Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.workflow.entities import WorkflowEntity
from backend.services.agent_builder.domain.execution.aggregate import ExecutionAggregate

logger = logging.getLogger(__name__)


class LegacyExecutorAdapter:
    """
    Adapter for legacy workflow executors.
    
    Allows gradual migration from:
    - workflow_executor.py (WorkflowExecutor)
    - workflow_executor_v2.py (execute_workflow_v2)
    - agentflow_executor.py (AgentflowExecutor)
    
    to the new UnifiedExecutor.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._unified_executor = None
        self._legacy_executor = None
        self._use_unified = True  # Feature flag
    
    @property
    def unified_executor(self):
        """Lazy load unified executor."""
        if self._unified_executor is None:
            from backend.services.agent_builder.infrastructure.execution.executor import UnifiedExecutor
            self._unified_executor = UnifiedExecutor(self.db)
        return self._unified_executor
    
    def get_legacy_executor(self, workflow):
        """Get legacy executor for a workflow."""
        from backend.services.agent_builder.workflow_executor import WorkflowExecutor
        return WorkflowExecutor(workflow, self.db)
    
    async def execute(
        self,
        workflow,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
        use_unified: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Execute workflow using appropriate executor.
        
        Args:
            workflow: Workflow DB model or WorkflowEntity
            input_data: Input data
            user_id: User ID
            execution_id: Optional execution ID
            use_unified: Override feature flag
        """
        should_use_unified = use_unified if use_unified is not None else self._use_unified
        
        if should_use_unified:
            return await self._execute_unified(workflow, input_data, user_id, execution_id)
        else:
            return await self._execute_legacy(workflow, input_data, user_id, execution_id)
    
    async def _execute_unified(
        self,
        workflow,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute using UnifiedExecutor."""
        # Convert to WorkflowEntity if needed
        if isinstance(workflow, WorkflowEntity):
            workflow_entity = workflow
        else:
            workflow_entity = self._convert_to_entity(workflow)
        
        try:
            result = await self.unified_executor.execute(
                workflow=workflow_entity,
                input_data=input_data,
                user_id=user_id,
                execution_id=execution_id,
            )
            
            return {
                "success": result.execution.status.value == "completed",
                "output": result.execution.output_data,
                "execution_id": str(result.id),
                "status": result.execution.status.value,
                "error": result.execution.error_message,
            }
        except Exception as e:
            logger.error(f"Unified executor failed: {e}", exc_info=True)
            # Fallback to legacy
            return await self._execute_legacy(workflow, input_data, user_id, execution_id)
    
    async def _execute_legacy(
        self,
        workflow,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute using legacy WorkflowExecutor."""
        executor = self.get_legacy_executor(workflow)
        if execution_id:
            executor.execution_id = execution_id
        
        return await executor.execute(input_data)
    
    def _convert_to_entity(self, workflow) -> WorkflowEntity:
        """Convert DB model to WorkflowEntity."""
        return WorkflowEntity.from_graph_definition(
            workflow_id=workflow.id,
            user_id=workflow.user_id,
            name=workflow.name,
            graph_def=workflow.graph_definition or {},
            description=workflow.description,
            is_public=workflow.is_public,
        )
    
    async def execute_streaming(
        self,
        workflow,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute with streaming updates."""
        workflow_entity = (
            workflow if isinstance(workflow, WorkflowEntity)
            else self._convert_to_entity(workflow)
        )
        
        async for update in self.unified_executor.execute_streaming(
            workflow=workflow_entity,
            input_data=input_data,
            user_id=user_id,
            execution_id=execution_id,
        ):
            yield update


# Factory function for easy migration
def get_executor(db: Session, use_unified: bool = True) -> LegacyExecutorAdapter:
    """
    Get an executor adapter.
    
    Usage:
        executor = get_executor(db)
        result = await executor.execute(workflow, input_data, user_id)
    """
    adapter = LegacyExecutorAdapter(db)
    adapter._use_unified = use_unified
    return adapter
