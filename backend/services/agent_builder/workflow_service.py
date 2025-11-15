"""Workflow Service for managing workflows."""

import logging
import uuid
import json
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Workflow, WorkflowNode, WorkflowEdge
from backend.models.agent_builder import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowValidationResult
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflows."""
    
    def __init__(self, db: Session):
        """
        Initialize Workflow Service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_workflow(
        self,
        user_id: str,
        workflow_data: WorkflowCreate
    ) -> Workflow:
        """
        Create a new workflow with proper transaction management.
        
        Args:
            user_id: User ID creating the workflow
            workflow_data: Workflow creation data
            
        Returns:
            Created Workflow model
            
        Raises:
            ValueError: If workflow validation fails
        """
        try:
            # Allow empty workflows during creation (nodes can be added later)
            # Only validate if nodes are provided
            if workflow_data.nodes and len(workflow_data.nodes) > 0:
                validation = self.validate_workflow_definition(
                    nodes=workflow_data.nodes,
                    edges=workflow_data.edges,
                    entry_point=workflow_data.entry_point
                )
                
                if not validation.is_valid:
                    raise ValueError(f"Workflow validation failed: {', '.join(validation.errors)}")
            
            # Build graph definition
            graph_definition = {
                "nodes": [node.model_dump() for node in workflow_data.nodes] if workflow_data.nodes else [],
                "edges": [edge.model_dump() for edge in workflow_data.edges] if workflow_data.edges else [],
                "entry_point": workflow_data.entry_point if workflow_data.entry_point else None
            }
            
            # Create workflow
            workflow = Workflow(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=workflow_data.name,
                description=workflow_data.description,
                graph_definition=graph_definition,
                is_public=workflow_data.is_public
            )
            
            self.db.add(workflow)
            self.db.flush()
            
            # Create nodes (if any)
            if workflow_data.nodes:
                for node_data in workflow_data.nodes:
                    node = WorkflowNode(
                        id=node_data.id,
                        workflow_id=workflow.id,
                        node_type=node_data.node_type,
                        node_ref_id=node_data.node_ref_id,
                        position_x=node_data.position_x,
                        position_y=node_data.position_y,
                        configuration=node_data.configuration
                    )
                    self.db.add(node)
            
            # Create edges (if any)
            if workflow_data.edges:
                for edge_data in workflow_data.edges:
                    edge = WorkflowEdge(
                        id=edge_data.id,
                        workflow_id=workflow.id,
                        source_node_id=edge_data.source_node_id,
                        target_node_id=edge_data.target_node_id,
                        edge_type=edge_data.edge_type,
                        condition=edge_data.condition
                    )
                    self.db.add(edge)
            
            self.db.commit()
            self.db.refresh(workflow)
            
            logger.info(f"Created workflow: {workflow.id} ({workflow.name})")
            return workflow
            
        except ValueError:
            # Re-raise validation errors
            self.db.rollback()
            raise
        except Exception as e:
            # Rollback on any error
            self.db.rollback()
            logger.error(f"Failed to create workflow: {e}", exc_info=True)
            raise
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get workflow by ID with all relations (prevents N+1 queries).
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow model or None if not found
        """
        from backend.db.query_helpers import get_workflow_with_relations
        return get_workflow_with_relations(self.db, workflow_id)
    
    def update_workflow(
        self,
        workflow_id: str,
        workflow_data: WorkflowUpdate
    ) -> Optional[Workflow]:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            workflow_data: Workflow update data
            
        Returns:
            Updated Workflow model or None if not found
            
        Raises:
            ValueError: If workflow validation fails
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # Update basic fields
        if workflow_data.name is not None:
            workflow.name = workflow_data.name
        
        if workflow_data.description is not None:
            workflow.description = workflow_data.description
        
        if workflow_data.is_public is not None:
            workflow.is_public = workflow_data.is_public
        
        # Update graph definition if nodes/edges/entry_point provided
        if (workflow_data.nodes is not None or 
            workflow_data.edges is not None or 
            workflow_data.entry_point is not None):
            
            # Use existing values if not provided
            nodes = workflow_data.nodes or [
                WorkflowNodeCreate(**node) 
                for node in workflow.graph_definition.get("nodes", [])
            ]
            edges = workflow_data.edges or [
                WorkflowEdgeCreate(**edge) 
                for edge in workflow.graph_definition.get("edges", [])
            ]
            entry_point = workflow_data.entry_point or workflow.graph_definition.get("entry_point")
            
            # Validate new workflow
            validation = self.validate_workflow_definition(
                nodes=nodes,
                edges=edges,
                entry_point=entry_point
            )
            
            if not validation.is_valid:
                raise ValueError(f"Workflow validation failed: {', '.join(validation.errors)}")
            
            # Update graph definition
            workflow.graph_definition = {
                "nodes": [node.model_dump() for node in nodes],
                "edges": [edge.model_dump() for edge in edges],
                "entry_point": entry_point
            }
            
            # Delete existing nodes and edges
            self.db.query(WorkflowNode).filter(
                WorkflowNode.workflow_id == workflow_id
            ).delete()
            self.db.query(WorkflowEdge).filter(
                WorkflowEdge.workflow_id == workflow_id
            ).delete()
            
            # Create new nodes
            for node_data in nodes:
                node = WorkflowNode(
                    id=node_data.id,
                    workflow_id=workflow.id,
                    node_type=node_data.node_type,
                    node_ref_id=node_data.node_ref_id,
                    position_x=node_data.position_x,
                    position_y=node_data.position_y,
                    configuration=node_data.configuration
                )
                self.db.add(node)
            
            # Create new edges
            for edge_data in edges:
                edge = WorkflowEdge(
                    id=edge_data.id,
                    workflow_id=workflow.id,
                    source_node_id=edge_data.source_node_id,
                    target_node_id=edge_data.target_node_id,
                    edge_type=edge_data.edge_type,
                    condition=edge_data.condition
                )
                self.db.add(edge)
        
        # Update timestamp
        workflow.updated_at = datetime.utcnow()
        
        # Clear compiled graph cache
        workflow.compiled_graph = None
        
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(f"Updated workflow: {workflow_id}")
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted, False if not found
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        # Delete nodes and edges
        self.db.query(WorkflowNode).filter(
            WorkflowNode.workflow_id == workflow_id
        ).delete()
        self.db.query(WorkflowEdge).filter(
            WorkflowEdge.workflow_id == workflow_id
        ).delete()
        
        # Delete workflow
        self.db.delete(workflow)
        self.db.commit()
        
        logger.info(f"Deleted workflow: {workflow_id}")
        return True
    
    def list_workflows(
        self,
        user_id: Optional[str] = None,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Workflow]:
        """
        List workflows with filters.
        
        Args:
            user_id: Filter by user ID (optional)
            is_public: Filter by public status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Workflow models
        """
        query = self.db.query(Workflow)
        
        if user_id:
            query = query.filter(Workflow.user_id == user_id)
        
        if is_public is not None:
            query = query.filter(Workflow.is_public == is_public)
        
        query = query.order_by(Workflow.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def validate_workflow_definition(
        self,
        nodes: List[Any],
        edges: List[Any],
        entry_point: str
    ) -> WorkflowValidationResult:
        """
        Validate workflow definition.
        
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            entry_point: Entry node ID
            
        Returns:
            WorkflowValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Check if nodes exist
        if not nodes:
            errors.append("Workflow must have at least one node")
            return WorkflowValidationResult(is_valid=False, errors=errors)
        
        # Build node ID set
        node_ids = {node.id for node in nodes}
        
        # Validate entry point
        if entry_point not in node_ids:
            errors.append(f"Entry point '{entry_point}' not found in nodes")
        
        # Validate edges
        for edge in edges:
            if edge.source_node_id not in node_ids:
                errors.append(f"Edge source '{edge.source_node_id}' not found in nodes")
            
            if edge.target_node_id not in node_ids:
                errors.append(f"Edge target '{edge.target_node_id}' not found in nodes")
            
            # Validate conditional edges have conditions
            if edge.edge_type == "conditional" and not edge.condition:
                errors.append(f"Conditional edge '{edge.id}' missing condition")
        
        # Check for cycles
        has_cycle, cycle_path = self._detect_cycle(nodes, edges)
        if has_cycle:
            errors.append(f"Workflow contains cycle: {' -> '.join(cycle_path)}")
        
        # Check for disconnected nodes
        disconnected = self._find_disconnected_nodes(nodes, edges, entry_point)
        if disconnected:
            warnings.append(f"Disconnected nodes found: {', '.join(disconnected)}")
        
        is_valid = len(errors) == 0
        
        return WorkflowValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def export_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Export workflow as JSON.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data as dictionary or None if not found
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        export_data = {
            "workflow": {
                "name": workflow.name,
                "description": workflow.description,
                "is_public": workflow.is_public,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            },
            "graph_definition": workflow.graph_definition
        }
        
        logger.info(f"Exported workflow: {workflow_id}")
        return export_data
    
    def import_workflow(
        self,
        user_id: str,
        workflow_data: Dict[str, Any]
    ) -> Workflow:
        """
        Import workflow from JSON.
        
        Args:
            user_id: User ID for imported workflow
            workflow_data: Workflow data dictionary
            
        Returns:
            Imported Workflow model
        """
        workflow_info = workflow_data.get("workflow", {})
        graph_def = workflow_data.get("graph_definition", {})
        
        # Create workflow
        workflow = Workflow(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=workflow_info.get("name", "Imported Workflow"),
            description=workflow_info.get("description"),
            graph_definition=graph_def,
            is_public=False  # Imported workflows are private by default
        )
        
        self.db.add(workflow)
        self.db.flush()
        
        # Create nodes
        for node_data in graph_def.get("nodes", []):
            node = WorkflowNode(
                id=node_data.get("id"),
                workflow_id=workflow.id,
                node_type=node_data.get("node_type"),
                node_ref_id=node_data.get("node_ref_id"),
                position_x=node_data.get("position_x", 0),
                position_y=node_data.get("position_y", 0),
                configuration=node_data.get("configuration", {})
            )
            self.db.add(node)
        
        # Create edges
        for edge_data in graph_def.get("edges", []):
            edge = WorkflowEdge(
                id=edge_data.get("id"),
                workflow_id=workflow.id,
                source_node_id=edge_data.get("source_node_id"),
                target_node_id=edge_data.get("target_node_id"),
                edge_type=edge_data.get("edge_type", "normal"),
                condition=edge_data.get("condition")
            )
            self.db.add(edge)
        
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(f"Imported workflow: {workflow.id}")
        return workflow
    
    def _detect_cycle(
        self,
        nodes: List[Any],
        edges: List[Any]
    ) -> Tuple[bool, List[str]]:
        """
        Detect cycles in workflow graph using DFS.
        
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            
        Returns:
            Tuple of (has_cycle, cycle_path)
        """
        # Build adjacency list
        graph = {node.id: [] for node in nodes}
        for edge in edges:
            graph[edge.source_node_id].append(edge.target_node_id)
        
        # DFS to detect cycle
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    path.append(neighbor)
                    return True
            
            rec_stack.remove(node_id)
            path.pop()
            return False
        
        for node in nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True, path
        
        return False, []
    
    def _find_disconnected_nodes(
        self,
        nodes: List[Any],
        edges: List[Any],
        entry_point: str
    ) -> List[str]:
        """
        Find nodes that are not reachable from entry point.
        
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            entry_point: Entry node ID
            
        Returns:
            List of disconnected node IDs
        """
        # Build adjacency list
        graph = {node.id: [] for node in nodes}
        for edge in edges:
            graph[edge.source_node_id].append(edge.target_node_id)
        
        # BFS from entry point
        visited = set()
        queue = [entry_point]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            
            visited.add(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        # Find disconnected nodes
        all_nodes = {node.id for node in nodes}
        disconnected = all_nodes - visited
        
        return list(disconnected)


# Import WorkflowNodeCreate and WorkflowEdgeCreate for type hints
from backend.models.agent_builder import WorkflowNodeCreate, WorkflowEdgeCreate
