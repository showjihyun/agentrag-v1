"""
Workflow Repository Implementation

Implements the WorkflowRepository interface using SQLAlchemy.
"""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.domain.workflow.repository import WorkflowRepositoryInterface
from backend.services.agent_builder.domain.workflow.aggregate import WorkflowAggregate
from backend.services.agent_builder.domain.workflow.entities import WorkflowEntity

logger = logging.getLogger(__name__)


class WorkflowRepositoryImpl(WorkflowRepositoryInterface):
    """SQLAlchemy implementation of WorkflowRepository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, aggregate: WorkflowAggregate) -> None:
        """Save workflow aggregate."""
        from backend.db.models.agent_builder import Workflow, WorkflowNode, WorkflowEdge
        
        workflow = aggregate.workflow
        
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
        logger.debug(f"Saved workflow: {workflow.id}")
    
    def find_by_id(self, workflow_id: UUID) -> Optional[WorkflowAggregate]:
        """Find workflow by ID."""
        from backend.db.models.agent_builder import Workflow
        
        db_workflow = self.db.query(Workflow).filter(
            Workflow.id == str(workflow_id),
            Workflow.deleted_at.is_(None),
        ).first()
        
        if not db_workflow:
            return None
        
        entity = self._to_entity(db_workflow)
        return WorkflowAggregate(entity)
    
    def find_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowAggregate]:
        """Find workflows by user."""
        from backend.db.models.agent_builder import Workflow
        
        workflows = self.db.query(Workflow).filter(
            Workflow.user_id == str(user_id),
            Workflow.deleted_at.is_(None),
        ).order_by(Workflow.created_at.desc()).limit(limit).offset(offset).all()
        
        return [WorkflowAggregate(self._to_entity(w)) for w in workflows]
    
    def find_public(self, limit: int = 50, offset: int = 0) -> List[WorkflowAggregate]:
        """Find public workflows."""
        from backend.db.models.agent_builder import Workflow
        
        workflows = self.db.query(Workflow).filter(
            Workflow.is_public == True,
            Workflow.deleted_at.is_(None),
        ).order_by(Workflow.created_at.desc()).limit(limit).offset(offset).all()
        
        return [WorkflowAggregate(self._to_entity(w)) for w in workflows]
    
    def delete(self, workflow_id: UUID) -> bool:
        """Hard delete workflow."""
        from backend.db.models.agent_builder import Workflow, WorkflowNode, WorkflowEdge
        
        workflow_id_str = str(workflow_id)
        
        self.db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id_str).delete()
        self.db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id_str).delete()
        
        result = self.db.query(Workflow).filter(Workflow.id == workflow_id_str).delete()
        self.db.commit()
        
        return result > 0
    
    def exists(self, workflow_id: UUID) -> bool:
        """Check if workflow exists."""
        from backend.db.models.agent_builder import Workflow
        
        return self.db.query(Workflow).filter(
            Workflow.id == str(workflow_id),
            Workflow.deleted_at.is_(None),
        ).count() > 0
    
    def search(
        self,
        user_id: Optional[UUID] = None,
        name_pattern: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowAggregate]:
        """Search workflows with filters."""
        from backend.db.models.agent_builder import Workflow
        
        query = self.db.query(Workflow).filter(Workflow.deleted_at.is_(None))
        
        if user_id:
            query = query.filter(Workflow.user_id == str(user_id))
        
        if name_pattern:
            query = query.filter(Workflow.name.ilike(f"%{name_pattern}%"))
        
        if is_public is not None:
            query = query.filter(Workflow.is_public == is_public)
        
        workflows = query.order_by(Workflow.created_at.desc()).limit(limit).offset(offset).all()
        
        return [WorkflowAggregate(self._to_entity(w)) for w in workflows]
    
    def _to_entity(self, db_workflow) -> WorkflowEntity:
        """Convert DB model to domain entity."""
        return WorkflowEntity.from_graph_definition(
            workflow_id=db_workflow.id,
            user_id=db_workflow.user_id,
            name=db_workflow.name,
            graph_def=db_workflow.graph_definition or {},
            description=db_workflow.description,
            is_public=db_workflow.is_public,
        )
