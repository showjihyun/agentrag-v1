"""
Execution Queries

Query objects and handlers for execution read operations.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.services.agent_builder.infrastructure.persistence import ExecutionRepositoryImpl


@dataclass
class GetExecutionQuery:
    """Query to get an execution by ID."""
    execution_id: str


@dataclass
class ListExecutionsQuery:
    """Query to list executions."""
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetExecutionStatsQuery:
    """Query to get execution statistics."""
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    days: int = 7


class ExecutionQueryHandler:
    """Handles execution queries."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = ExecutionRepositoryImpl(db)
    
    def handle_get(self, query: GetExecutionQuery) -> Optional[Dict[str, Any]]:
        """Handle GetExecutionQuery."""
        aggregate = self.repository.find_by_id(UUID(query.execution_id))
        if not aggregate:
            return None
        
        execution = aggregate.execution
        return {
            "id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "user_id": str(execution.user_id),
            "status": execution.status.value,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "error_message": execution.error_message,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_ms": execution.duration_ms,
            "steps": [s.to_dict() for s in execution.steps],
        }
    
    def handle_list(self, query: ListExecutionsQuery) -> List[Dict[str, Any]]:
        """Handle ListExecutionsQuery."""
        if query.workflow_id:
            aggregates = self.repository.find_by_workflow(
                UUID(query.workflow_id),
                limit=query.limit,
                offset=query.offset,
            )
        elif query.user_id:
            aggregates = self.repository.find_by_user(
                UUID(query.user_id),
                limit=query.limit,
                offset=query.offset,
            )
        else:
            aggregates = self.repository.find_recent(limit=query.limit)
        
        return [
            {
                "id": str(a.execution.id),
                "workflow_id": str(a.execution.workflow_id),
                "status": a.execution.status.value,
                "started_at": a.execution.started_at.isoformat() if a.execution.started_at else None,
                "duration_ms": a.execution.duration_ms,
            }
            for a in aggregates
        ]
    
    def handle_stats(self, query: GetExecutionStatsQuery) -> Dict[str, Any]:
        """Handle GetExecutionStatsQuery."""
        from backend.db.models.agent_builder import WorkflowExecution
        from sqlalchemy import func
        
        since = datetime.utcnow() - timedelta(days=query.days)
        
        db_query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.started_at >= since
        )
        
        if query.workflow_id:
            db_query = db_query.filter(WorkflowExecution.workflow_id == query.workflow_id)
        if query.user_id:
            db_query = db_query.filter(WorkflowExecution.user_id == query.user_id)
        
        executions = db_query.all()
        
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
            "period_days": query.days,
        }
