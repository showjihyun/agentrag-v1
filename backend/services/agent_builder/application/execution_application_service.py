"""
Execution Application Service

Orchestrates workflow execution operations.
"""

import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.execution.aggregate import ExecutionAggregate
from backend.services.agent_builder.domain.execution.entities import ExecutionEntity
from backend.services.agent_builder.domain.execution.value_objects import ExecutionStatus

logger = logging.getLogger(__name__)


class ExecutionApplicationService:
    """
    Application service for execution operations.
    
    Provides high-level use cases:
    - Query execution history
    - Get execution details
    - Cancel/Retry executions
    - Execution analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================================================
    # QUERY OPERATIONS
    # ========================================================================
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionAggregate]:
        """Get execution by ID."""
        entity = self._load_execution(execution_id)
        if not entity:
            return None
        return ExecutionAggregate(entity)
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ExecutionEntity]:
        """List executions with filters."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        query = self.db.query(WorkflowExecution)
        
        if workflow_id:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        if user_id:
            query = query.filter(WorkflowExecution.user_id == user_id)
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        executions = query.order_by(WorkflowExecution.started_at.desc()).limit(limit).offset(offset).all()
        return [self._db_to_entity(e) for e in executions]
    
    def get_execution_steps(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get execution steps."""
        aggregate = self.get_execution(execution_id)
        if not aggregate:
            return []
        
        return [step.to_dict() for step in aggregate.execution.steps]
    
    # ========================================================================
    # CONTROL OPERATIONS
    # ========================================================================
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        aggregate = self.get_execution(execution_id)
        if not aggregate:
            return False
        
        if aggregate.execution.status != ExecutionStatus.RUNNING:
            return False
        
        aggregate.cancel()
        self._save_execution(aggregate)
        
        logger.info(f"Cancelled execution: {execution_id}")
        return True
    
    def retry_execution(
        self,
        execution_id: str,
        user_id: str,
    ) -> Optional[ExecutionAggregate]:
        """Retry a failed execution."""
        original = self.get_execution(execution_id)
        if not original:
            return None
        
        if original.execution.status not in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]:
            raise ValueError("Can only retry failed or timed out executions")
        
        # Create new execution with same input
        new_execution = ExecutionAggregate.create(
            workflow_id=original.execution.workflow_id,
            user_id=UUID(user_id),
            input_data=original.execution.input_data,
            parent_execution_id=original.id,
            trigger_type="retry",
        )
        
        self._save_execution(new_execution)
        return new_execution
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_execution_stats(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get execution statistics."""
        from backend.db.models.agent_builder import WorkflowExecution
        from sqlalchemy import func
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.started_at >= since
        )
        
        if workflow_id:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        if user_id:
            query = query.filter(WorkflowExecution.user_id == user_id)
        
        executions = query.all()
        
        total = len(executions)
        completed = sum(1 for e in executions if e.status == "completed")
        failed = sum(1 for e in executions if e.status == "failed")
        
        durations = [
            (e.completed_at - e.started_at).total_seconds() * 1000
            for e in executions
            if e.completed_at and e.started_at
        ]
        
        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "period_days": days,
        }
    
    def get_recent_failures(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent failed executions."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.status == "failed"
        )
        
        if workflow_id:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        
        failures = query.order_by(WorkflowExecution.started_at.desc()).limit(limit).all()
        
        return [
            {
                "execution_id": str(e.id),
                "workflow_id": str(e.workflow_id),
                "error_message": e.error_message,
                "started_at": e.started_at.isoformat() if e.started_at else None,
            }
            for e in failures
        ]
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _save_execution(self, aggregate: ExecutionAggregate) -> None:
        """Save execution to database."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        execution = aggregate.execution
        
        db_execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution.id
        ).first()
        
        if db_execution:
            db_execution.status = execution.status.value
            db_execution.output_data = execution.output_data
            db_execution.error_message = execution.error_message
            db_execution.completed_at = execution.completed_at
        else:
            db_execution = WorkflowExecution(
                id=execution.id,
                workflow_id=execution.workflow_id,
                user_id=execution.user_id,
                input_data=execution.input_data,
                status=execution.status.value,
                started_at=execution.started_at,
            )
            self.db.add(db_execution)
        
        self.db.commit()
    
    def _load_execution(self, execution_id: str) -> Optional[ExecutionEntity]:
        """Load execution from database."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        db_execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
        
        if not db_execution:
            return None
        
        return self._db_to_entity(db_execution)
    
    def _db_to_entity(self, db_execution) -> ExecutionEntity:
        """Convert DB model to domain entity."""
        return ExecutionEntity(
            id=db_execution.id,
            workflow_id=db_execution.workflow_id,
            user_id=db_execution.user_id,
            input_data=db_execution.input_data or {},
            output_data=db_execution.output_data,
            status=ExecutionStatus(db_execution.status) if db_execution.status else ExecutionStatus.PENDING,
            error_message=db_execution.error_message,
            started_at=db_execution.started_at,
            completed_at=db_execution.completed_at,
        )
