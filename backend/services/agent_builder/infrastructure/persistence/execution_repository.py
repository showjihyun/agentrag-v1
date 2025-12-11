"""
Execution Repository Implementation

Implements the ExecutionRepository interface using SQLAlchemy.
"""

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.execution.repository import ExecutionRepositoryInterface
from backend.services.agent_builder.domain.execution.aggregate import ExecutionAggregate
from backend.services.agent_builder.domain.execution.entities import ExecutionEntity
from backend.services.agent_builder.domain.execution.value_objects import ExecutionStatus

logger = logging.getLogger(__name__)


class ExecutionRepositoryImpl(ExecutionRepositoryInterface):
    """SQLAlchemy implementation of ExecutionRepository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, aggregate: ExecutionAggregate) -> None:
        """Save execution aggregate."""
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
            db_execution.execution_context = execution.execution_context
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
        logger.debug(f"Saved execution: {execution.id}")
    
    def find_by_id(self, execution_id: UUID) -> Optional[ExecutionAggregate]:
        """Find execution by ID."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        db_execution = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == str(execution_id)
        ).first()
        
        if not db_execution:
            return None
        
        entity = self._to_entity(db_execution)
        return ExecutionAggregate(entity)
    
    def find_by_workflow(
        self,
        workflow_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ExecutionAggregate]:
        """Find executions by workflow."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        executions = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == str(workflow_id)
        ).order_by(WorkflowExecution.started_at.desc()).limit(limit).offset(offset).all()
        
        return [ExecutionAggregate(self._to_entity(e)) for e in executions]
    
    def find_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ExecutionAggregate]:
        """Find executions by user."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        executions = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.user_id == str(user_id)
        ).order_by(WorkflowExecution.started_at.desc()).limit(limit).offset(offset).all()
        
        return [ExecutionAggregate(self._to_entity(e)) for e in executions]
    
    def find_by_status(
        self,
        status: ExecutionStatus,
        limit: int = 50,
    ) -> List[ExecutionAggregate]:
        """Find executions by status."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        executions = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.status == status.value
        ).order_by(WorkflowExecution.started_at.desc()).limit(limit).all()
        
        return [ExecutionAggregate(self._to_entity(e)) for e in executions]
    
    def find_recent(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[ExecutionAggregate]:
        """Find recent executions."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        executions = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.started_at >= since
        ).order_by(WorkflowExecution.started_at.desc()).limit(limit).all()
        
        return [ExecutionAggregate(self._to_entity(e)) for e in executions]
    
    def delete(self, execution_id: UUID) -> bool:
        """Delete execution."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        result = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == str(execution_id)
        ).delete()
        self.db.commit()
        
        return result > 0
    
    def delete_old(self, days: int = 30) -> int:
        """Delete executions older than specified days."""
        from backend.db.models.agent_builder import WorkflowExecution
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.started_at < cutoff
        ).delete()
        self.db.commit()
        
        logger.info(f"Deleted {result} old executions")
        return result
    
    def _to_entity(self, db_execution) -> ExecutionEntity:
        """Convert DB model to domain entity."""
        return ExecutionEntity(
            id=db_execution.id,
            workflow_id=db_execution.workflow_id,
            user_id=db_execution.user_id,
            input_data=db_execution.input_data or {},
            output_data=db_execution.output_data,
            execution_context=db_execution.execution_context or {},
            status=ExecutionStatus(db_execution.status) if db_execution.status else ExecutionStatus.PENDING,
            error_message=db_execution.error_message,
            started_at=db_execution.started_at,
            completed_at=db_execution.completed_at,
        )
