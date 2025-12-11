"""
Workflow Application Service

Orchestrates workflow operations using domain aggregates.
"""

import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.workflow.aggregate import WorkflowAggregate
from backend.services.agent_builder.domain.workflow.entities import WorkflowEntity
from backend.services.agent_builder.domain.workflow.value_objects import NodeType
from backend.services.agent_builder.domain.execution.aggregate import ExecutionAggregate
from backend.services.agent_builder.infrastructure.execution.executor import UnifiedExecutor

logger = logging.getLogger(__name__)


class WorkflowApplicationService:
    """
    Application service for workflow operations.
    
    Provides high-level use cases:
    - Create/Update/Delete workflows
    - Execute workflows
    - Validate workflows
    - Export/Import workflows
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._executor: Optional[UnifiedExecutor] = None
    
    @property
    def executor(self) -> UnifiedExecutor:
        """Lazy-load executor."""
        if self._executor is None:
            self._executor = UnifiedExecutor(self.db)
        return self._executor
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def create_workflow(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        entry_point: Optional[str] = None,
        is_public: bool = False,
    ) -> WorkflowAggregate:
        """Create a new workflow."""
        aggregate = WorkflowAggregate.create(
            user_id=UUID(user_id),
            name=name,
            description=description,
            nodes=nodes or [],
            edges=edges or [],
            entry_point=entry_point,
            is_public=is_public,
        )
        
        # Validate
        is_valid, errors, warnings = aggregate.validate()
        if not is_valid:
            raise ValueError(f"Invalid workflow: {'; '.join(errors)}")
        
        for warning in warnings:
            logger.warning(f"Workflow warning: {warning}")
        
        # Save to database
        self._save_workflow(aggregate)
        
        logger.info(f"Created workflow: {aggregate.id}")
        return aggregate
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowAggregate]:
        """Get workflow by ID."""
        workflow_entity = self._load_workflow(workflow_id)
        if not workflow_entity:
            return None
        return WorkflowAggregate(workflow_entity)
    
    def update_workflow(
        self,
        workflow_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        entry_point: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> Optional[WorkflowAggregate]:
        """Update a workflow."""
        aggregate = self.get_workflow(workflow_id)
        if not aggregate:
            return None
        
        # Update metadata
        aggregate.update(
            user_id=UUID(user_id),
            name=name,
            description=description,
            is_public=is_public,
        )
        
        # Update graph if provided
        if nodes is not None and edges is not None:
            aggregate.update_graph(
                user_id=UUID(user_id),
                nodes=nodes,
                edges=edges,
                entry_point=entry_point,
            )
            
            # Validate
            is_valid, errors, warnings = aggregate.validate()
            if not is_valid:
                raise ValueError(f"Invalid workflow: {'; '.join(errors)}")
        
        # Save
        self._save_workflow(aggregate)
        
        logger.info(f"Updated workflow: {workflow_id}")
        return aggregate
    
    def delete_workflow(self, workflow_id: str, user_id: str, hard: bool = False) -> bool:
        """Delete a workflow."""
        aggregate = self.get_workflow(workflow_id)
        if not aggregate:
            return False
        
        aggregate.delete(UUID(user_id), hard=hard)
        
        if hard:
            self._delete_workflow(workflow_id)
        else:
            self._save_workflow(aggregate)
        
        logger.info(f"Deleted workflow: {workflow_id}")
        return True
    
    def list_workflows(
        self,
        user_id: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowEntity]:
        """List workflows."""
        from backend.db.models.agent_builder import Workflow
        
        query = self.db.query(Workflow).filter(Workflow.deleted_at.is_(None))
        
        if user_id:
            query = query.filter(Workflow.user_id == user_id)
        if is_public is not None:
            query = query.filter(Workflow.is_public == is_public)
        
        workflows = query.order_by(Workflow.created_at.desc()).limit(limit).offset(offset).all()
        
        return [self._db_to_entity(w) for w in workflows]
    
    # ========================================================================
    # EXECUTION
    # ========================================================================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> ExecutionAggregate:
        """Execute a workflow."""
        aggregate = self.get_workflow(workflow_id)
        if not aggregate:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        return await self.executor.execute(
            workflow=aggregate.workflow,
            input_data=input_data,
            user_id=user_id,
            execution_id=execution_id,
            timeout=timeout,
        )
    
    async def execute_workflow_streaming(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with streaming updates."""
        aggregate = self.get_workflow(workflow_id)
        if not aggregate:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        async for update in self.executor.execute_streaming(
            workflow=aggregate.workflow,
            input_data=input_data,
            user_id=user_id,
            execution_id=execution_id,
        ):
            yield update
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Validate a workflow."""
        aggregate = self.get_workflow(workflow_id)
        if not aggregate:
            return {"is_valid": False, "errors": ["Workflow not found"], "warnings": []}
        
        is_valid, errors, warnings = aggregate.validate()
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
        }
    
    # ========================================================================
    # EXPORT/IMPORT
    # ========================================================================
    
    def export_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Export workflow as JSON."""
        aggregate = self.get_workflow(workflow_id)
        if not aggregate:
            return None
        
        return {
            "workflow": {
                "name": aggregate.workflow.name,
                "description": aggregate.workflow.description,
                "is_public": aggregate.workflow.is_public,
            },
            "graph_definition": aggregate.workflow.to_graph_definition(),
        }
    
    def import_workflow(
        self,
        user_id: str,
        data: Dict[str, Any],
    ) -> WorkflowAggregate:
        """Import workflow from JSON."""
        workflow_info = data.get("workflow", {})
        graph_def = data.get("graph_definition", {})
        
        return self.create_workflow(
            user_id=user_id,
            name=workflow_info.get("name", "Imported Workflow"),
            description=workflow_info.get("description"),
            nodes=graph_def.get("nodes", []),
            edges=graph_def.get("edges", []),
            entry_point=graph_def.get("entry_point"),
            is_public=False,
        )
    
    def clone_workflow(
        self,
        workflow_id: str,
        user_id: str,
        new_name: Optional[str] = None,
    ) -> Optional[WorkflowAggregate]:
        """Clone a workflow."""
        aggregate = self.get_workflow(workflow_id)
        if not aggregate:
            return None
        
        cloned = aggregate.clone(UUID(user_id), new_name)
        self._save_workflow(cloned)
        
        return cloned
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _save_workflow(self, aggregate: WorkflowAggregate) -> None:
        """Save workflow to database."""
        from backend.db.models.agent_builder import Workflow, WorkflowNode, WorkflowEdge
        
        workflow = aggregate.workflow
        
        # Upsert workflow
        db_workflow = self.db.query(Workflow).filter(Workflow.id == workflow.id).first()
        
        if db_workflow:
            db_workflow.name = workflow.name
            db_workflow.description = workflow.description
            db_workflow.graph_definition = workflow.to_graph_definition()
            db_workflow.is_public = workflow.is_public
            db_workflow.updated_at = workflow.updated_at
            db_workflow.deleted_at = workflow.deleted_at
        else:
            db_workflow = Workflow(
                id=workflow.id,
                user_id=workflow.user_id,
                name=workflow.name,
                description=workflow.description,
                graph_definition=workflow.to_graph_definition(),
                is_public=workflow.is_public,
            )
            self.db.add(db_workflow)
        
        # Update nodes
        self.db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow.id).delete()
        for node in workflow.nodes:
            db_node = WorkflowNode(
                id=node.id,
                workflow_id=workflow.id,
                node_type=node.node_type.value,
                node_ref_id=node.node_ref_id,
                position_x=node.position.x,
                position_y=node.position.y,
                configuration=node.config.to_dict(),
            )
            self.db.add(db_node)
        
        # Update edges
        self.db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow.id).delete()
        for edge in workflow.edges:
            db_edge = WorkflowEdge(
                id=edge.id,
                workflow_id=workflow.id,
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                edge_type=edge.edge_type.value,
                condition=edge.condition.expression if edge.condition else None,
            )
            self.db.add(db_edge)
        
        self.db.commit()
    
    def _load_workflow(self, workflow_id: str) -> Optional[WorkflowEntity]:
        """Load workflow from database."""
        from backend.db.models.agent_builder import Workflow
        
        db_workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.deleted_at.is_(None),
        ).first()
        
        if not db_workflow:
            return None
        
        return self._db_to_entity(db_workflow)
    
    def _db_to_entity(self, db_workflow) -> WorkflowEntity:
        """Convert DB model to domain entity."""
        return WorkflowEntity.from_graph_definition(
            workflow_id=db_workflow.id,
            user_id=db_workflow.user_id,
            name=db_workflow.name,
            graph_def=db_workflow.graph_definition or {},
            description=db_workflow.description,
            is_public=db_workflow.is_public,
        )
    
    def _delete_workflow(self, workflow_id: str) -> None:
        """Hard delete workflow from database."""
        from backend.db.models.agent_builder import Workflow, WorkflowNode, WorkflowEdge
        
        self.db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).delete()
        self.db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id).delete()
        self.db.query(Workflow).filter(Workflow.id == workflow_id).delete()
        self.db.commit()
