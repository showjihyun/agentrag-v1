"""Refactored Workflow Service using Repository Pattern."""

import logging
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Workflow, WorkflowNode, WorkflowEdge
from backend.db.repositories.workflow_repository import (
    WorkflowRepository,
    WorkflowNodeRepository,
    WorkflowEdgeRepository,
    WorkflowExecutionRepository
)
from backend.models.agent_builder import WorkflowCreate, WorkflowUpdate
from backend.validators.workflow_validator import WorkflowValidator
from backend.core.transaction import transaction
from backend.exceptions.agent_builder import (
    WorkflowNotFoundException,
    WorkflowValidationException,
    WorkflowCycleException
)

logger = logging.getLogger(__name__)


class WorkflowServiceRefactored:
    """
    Refactored Workflow Service with Repository Pattern.
    
    Improvements:
    - Repository pattern for data access
    - Proper transaction management
    - Standardized exception handling
    - Validation layer separation
    """
    
    def __init__(self, db: Session):
        """
        Initialize Workflow Service.
        
        Args:
            db: Database session
        """
        self.db = db
        
        # Initialize repositories
        self.workflow_repo = WorkflowRepository(db)
        self.node_repo = WorkflowNodeRepository(db)
        self.edge_repo = WorkflowEdgeRepository(db)
        self.execution_repo = WorkflowExecutionRepository(db)
    
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
            WorkflowValidationException: If validation fails
            WorkflowCycleException: If workflow contains cycle
        """
        # Validate before starting transaction
        errors, warnings = WorkflowValidator.validate_create(workflow_data)
        if errors:
            raise WorkflowValidationException(errors, warnings)
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Workflow validation warning: {warning}")
        
        # Create workflow with transaction management
        with transaction(self.db):
            # Build graph definition
            graph_definition = {
                "nodes": [node.model_dump() for node in workflow_data.nodes],
                "edges": [edge.model_dump() for edge in workflow_data.edges],
                "entry_point": workflow_data.entry_point
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
            
            workflow = self.workflow_repo.create(workflow)
            
            # Create nodes
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
                self.node_repo.create(node)
            
            # Create edges
            for edge_data in workflow_data.edges:
                edge = WorkflowEdge(
                    id=edge_data.id,
                    workflow_id=workflow.id,
                    source_node_id=edge_data.source_node_id,
                    target_node_id=edge_data.target_node_id,
                    edge_type=edge_data.edge_type,
                    condition=edge_data.condition
                )
                self.edge_repo.create(edge)
        
        logger.info(
            "Workflow created",
            extra={
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "user_id": user_id,
                "node_count": len(workflow_data.nodes),
                "edge_count": len(workflow_data.edges)
            }
        )
        
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Workflow:
        """
        Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow model
            
        Raises:
            WorkflowNotFoundException: If workflow not found
        """
        workflow = self.workflow_repo.find_by_id(workflow_id)
        
        if not workflow:
            raise WorkflowNotFoundException(workflow_id)
        
        return workflow
    
    def update_workflow(
        self,
        workflow_id: str,
        workflow_data: WorkflowUpdate
    ) -> Workflow:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            workflow_data: Workflow update data
            
        Returns:
            Updated Workflow model
            
        Raises:
            WorkflowNotFoundException: If workflow not found
            WorkflowValidationException: If validation fails
        """
        workflow = self.get_workflow(workflow_id)
        
        # Validate update data
        errors, warnings = WorkflowValidator.validate_update(workflow_data)
        if errors:
            raise WorkflowValidationException(errors, warnings)
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Workflow validation warning: {warning}")
        
        with transaction(self.db):
            # Update basic fields
            if workflow_data.name is not None:
                workflow.name = workflow_data.name
            
            if workflow_data.description is not None:
                workflow.description = workflow_data.description
            
            if workflow_data.is_public is not None:
                workflow.is_public = workflow_data.is_public
            
            # Update graph definition if nodes/edges/entry_point provided
            if (workflow_data.nodes is not None and 
                workflow_data.edges is not None and 
                workflow_data.entry_point is not None):
                
                # Update graph definition
                workflow.graph_definition = {
                    "nodes": [node.model_dump() for node in workflow_data.nodes],
                    "edges": [edge.model_dump() for edge in workflow_data.edges],
                    "entry_point": workflow_data.entry_point
                }
                
                # Delete existing nodes and edges
                self.node_repo.delete_by_workflow(workflow_id)
                self.edge_repo.delete_by_workflow(workflow_id)
                
                # Create new nodes
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
                    self.node_repo.create(node)
                
                # Create new edges
                for edge_data in workflow_data.edges:
                    edge = WorkflowEdge(
                        id=edge_data.id,
                        workflow_id=workflow.id,
                        source_node_id=edge_data.source_node_id,
                        target_node_id=edge_data.target_node_id,
                        edge_type=edge_data.edge_type,
                        condition=edge_data.condition
                    )
                    self.edge_repo.create(edge)
            
            # Clear compiled graph cache
            workflow.compiled_graph = None
            
            # Update workflow
            workflow = self.workflow_repo.update(workflow)
        
        logger.info(
            "Workflow updated",
            extra={"workflow_id": workflow_id}
        )
        
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted
            
        Raises:
            WorkflowNotFoundException: If workflow not found
        """
        workflow = self.get_workflow(workflow_id)
        
        with transaction(self.db):
            # Delete nodes and edges (cascade)
            self.node_repo.delete_by_workflow(workflow_id)
            self.edge_repo.delete_by_workflow(workflow_id)
            
            # Delete workflow
            self.workflow_repo.delete(workflow)
        
        logger.info(
            "Workflow deleted",
            extra={"workflow_id": workflow_id}
        )
        
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
        if user_id:
            return self.workflow_repo.find_by_user(
                user_id=user_id,
                is_public=is_public,
                limit=limit,
                offset=offset
            )
        elif is_public:
            return self.workflow_repo.find_public(
                limit=limit,
                offset=offset
            )
        else:
            # Default to public workflows if no user specified
            return self.workflow_repo.find_public(
                limit=limit,
                offset=offset
            )
    
    def export_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Export workflow as JSON.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data as dictionary
            
        Raises:
            WorkflowNotFoundException: If workflow not found
        """
        workflow = self.get_workflow(workflow_id)
        
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
        
        with transaction(self.db):
            # Create workflow
            workflow = Workflow(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=workflow_info.get("name", "Imported Workflow"),
                description=workflow_info.get("description"),
                graph_definition=graph_def,
                is_public=False  # Imported workflows are private by default
            )
            
            workflow = self.workflow_repo.create(workflow)
            
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
                self.node_repo.create(node)
            
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
                self.edge_repo.create(edge)
        
        logger.info(f"Imported workflow: {workflow.id}")
        return workflow
    
    def search_workflows(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Workflow]:
        """
        Search workflows by name or description.
        
        Args:
            query: Search query
            user_id: Filter by user ID (optional)
            limit: Maximum number of results
            
        Returns:
            List of Workflow models
        """
        return self.workflow_repo.search(
            query=query,
            user_id=user_id,
            limit=limit
        )
