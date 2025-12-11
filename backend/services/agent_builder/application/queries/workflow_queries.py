"""
Workflow Queries

Query objects and handlers for workflow read operations.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.agent_builder.infrastructure.persistence import WorkflowRepositoryImpl


@dataclass
class GetWorkflowQuery:
    """Query to get a workflow by ID."""
    workflow_id: str


@dataclass
class ListWorkflowsQuery:
    """Query to list workflows."""
    user_id: Optional[str] = None
    is_public: Optional[bool] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetWorkflowStatsQuery:
    """Query to get workflow statistics."""
    workflow_id: str


class WorkflowQueryHandler:
    """Handles workflow queries."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = WorkflowRepositoryImpl(db)
    
    def handle_get(self, query: GetWorkflowQuery) -> Optional[Dict[str, Any]]:
        """Handle GetWorkflowQuery."""
        aggregate = self.repository.find_by_id(UUID(query.workflow_id))
        if not aggregate:
            return None
        
        workflow = aggregate.workflow
        return {
            "id": str(workflow.id),
            "user_id": str(workflow.user_id),
            "name": workflow.name,
            "description": workflow.description,
            "is_public": workflow.is_public,
            "node_count": len(workflow.nodes),
            "edge_count": len(workflow.edges),
            "entry_point": workflow.entry_point,
            "graph_definition": workflow.to_graph_definition(),
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    
    def handle_list(self, query: ListWorkflowsQuery) -> List[Dict[str, Any]]:
        """Handle ListWorkflowsQuery."""
        if query.user_id:
            aggregates = self.repository.find_by_user(
                UUID(query.user_id),
                limit=query.limit,
                offset=query.offset,
            )
        elif query.is_public:
            aggregates = self.repository.find_public(
                limit=query.limit,
                offset=query.offset,
            )
        else:
            aggregates = []
        
        return [
            {
                "id": str(a.workflow.id),
                "name": a.workflow.name,
                "description": a.workflow.description,
                "is_public": a.workflow.is_public,
                "node_count": len(a.workflow.nodes),
            }
            for a in aggregates
        ]
    
    def handle_stats(self, query: GetWorkflowStatsQuery) -> Optional[Dict[str, Any]]:
        """Handle GetWorkflowStatsQuery."""
        aggregate = self.repository.find_by_id(UUID(query.workflow_id))
        if not aggregate:
            return None
        
        workflow = aggregate.workflow
        
        # Count node types
        node_types = {}
        for node in workflow.nodes:
            node_type = node.node_type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        return {
            "workflow_id": str(workflow.id),
            "total_nodes": len(workflow.nodes),
            "total_edges": len(workflow.edges),
            "node_types": node_types,
            "has_entry_point": workflow.entry_point is not None,
            "has_exit_nodes": len(workflow.exit_nodes) > 0,
        }
