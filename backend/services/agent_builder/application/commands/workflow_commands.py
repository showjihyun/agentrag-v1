"""
Workflow Commands

Command objects and handlers for workflow operations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.workflow.aggregate import WorkflowAggregate
from backend.services.agent_builder.infrastructure.persistence import WorkflowRepositoryImpl
from backend.services.agent_builder.infrastructure.execution import UnifiedExecutor


# ============================================================================
# COMMAND OBJECTS
# ============================================================================

@dataclass
class CreateWorkflowCommand:
    """Command to create a new workflow."""
    user_id: str
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    entry_point: Optional[str] = None
    is_public: bool = False


@dataclass
class UpdateWorkflowCommand:
    """Command to update a workflow."""
    workflow_id: str
    user_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    entry_point: Optional[str] = None
    is_public: Optional[bool] = None


@dataclass
class DeleteWorkflowCommand:
    """Command to delete a workflow."""
    workflow_id: str
    user_id: str
    hard: bool = False


@dataclass
class ExecuteWorkflowCommand:
    """Command to execute a workflow."""
    workflow_id: str
    user_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    execution_id: Optional[str] = None
    timeout: Optional[int] = None


# ============================================================================
# COMMAND HANDLER
# ============================================================================

class WorkflowCommandHandler:
    """Handles workflow commands."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = WorkflowRepositoryImpl(db)
    
    def handle_create(self, command: CreateWorkflowCommand) -> WorkflowAggregate:
        """Handle CreateWorkflowCommand."""
        aggregate = WorkflowAggregate.create(
            user_id=UUID(command.user_id),
            name=command.name,
            description=command.description,
            nodes=command.nodes,
            edges=command.edges,
            entry_point=command.entry_point,
            is_public=command.is_public,
        )
        
        # Validate
        is_valid, errors, _ = aggregate.validate()
        if not is_valid:
            raise ValueError(f"Invalid workflow: {'; '.join(errors)}")
        
        # Save
        self.repository.save(aggregate)
        
        return aggregate
    
    def handle_update(self, command: UpdateWorkflowCommand) -> Optional[WorkflowAggregate]:
        """Handle UpdateWorkflowCommand."""
        aggregate = self.repository.find_by_id(UUID(command.workflow_id))
        if not aggregate:
            return None
        
        # Update metadata
        aggregate.update(
            user_id=UUID(command.user_id),
            name=command.name,
            description=command.description,
            is_public=command.is_public,
        )
        
        # Update graph if provided
        if command.nodes is not None and command.edges is not None:
            aggregate.update_graph(
                user_id=UUID(command.user_id),
                nodes=command.nodes,
                edges=command.edges,
                entry_point=command.entry_point,
            )
            
            is_valid, errors, _ = aggregate.validate()
            if not is_valid:
                raise ValueError(f"Invalid workflow: {'; '.join(errors)}")
        
        self.repository.save(aggregate)
        return aggregate
    
    def handle_delete(self, command: DeleteWorkflowCommand) -> bool:
        """Handle DeleteWorkflowCommand."""
        aggregate = self.repository.find_by_id(UUID(command.workflow_id))
        if not aggregate:
            return False
        
        aggregate.delete(UUID(command.user_id), hard=command.hard)
        
        if command.hard:
            return self.repository.delete(UUID(command.workflow_id))
        else:
            self.repository.save(aggregate)
            return True
    
    async def handle_execute(self, command: ExecuteWorkflowCommand):
        """Handle ExecuteWorkflowCommand."""
        aggregate = self.repository.find_by_id(UUID(command.workflow_id))
        if not aggregate:
            raise ValueError(f"Workflow not found: {command.workflow_id}")
        
        executor = UnifiedExecutor(self.db)
        return await executor.execute(
            workflow=aggregate.workflow,
            input_data=command.input_data,
            user_id=command.user_id,
            execution_id=command.execution_id,
            timeout=command.timeout,
        )
