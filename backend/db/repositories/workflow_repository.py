"""Workflow Repository for data access layer."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models.agent_builder import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowExecution,
    AgentBlock,
    AgentEdge
)

logger = logging.getLogger(__name__)


class WorkflowRepository:
    """Repository for Workflow data access."""
    
    def __init__(self, db: Session):
        """
        Initialize Workflow Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, workflow: Workflow) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            workflow: Workflow model to create
            
        Returns:
            Created Workflow model
        """
        self.db.add(workflow)
        self.db.flush()
        return workflow
    
    def find_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """
        Find workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow model or None if not found
        """
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    def find_by_user(
        self,
        user_id: str,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Workflow]:
        """
        Find workflows by user ID with filters.
        
        Args:
            user_id: User ID
            is_public: Filter by public status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Workflow models
        """
        query = self.db.query(Workflow).filter(Workflow.user_id == user_id)
        
        if is_public is not None:
            query = query.filter(Workflow.is_public == is_public)
        
        query = query.order_by(Workflow.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def find_public(self, limit: int = 50, offset: int = 0) -> List[Workflow]:
        """
        Find public workflows.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of public Workflow models
        """
        return self.db.query(Workflow).filter(
            Workflow.is_public == True
        ).order_by(Workflow.created_at.desc()).limit(limit).offset(offset).all()
    
    def update(self, workflow: Workflow) -> Workflow:
        """
        Update a workflow.
        
        Args:
            workflow: Workflow model to update
            
        Returns:
            Updated Workflow model
        """
        workflow.updated_at = datetime.utcnow()
        self.db.flush()
        return workflow
    
    def delete(self, workflow: Workflow) -> None:
        """
        Delete a workflow.
        
        Args:
            workflow: Workflow model to delete
        """
        self.db.delete(workflow)
        self.db.flush()
    
    def exists(self, workflow_id: str) -> bool:
        """
        Check if workflow exists.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).count() > 0
    
    def count_by_user(self, user_id: str) -> int:
        """
        Count workflows by user.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of workflows
        """
        return self.db.query(Workflow).filter(Workflow.user_id == user_id).count()
    
    def search(
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
        search_filter = or_(
            Workflow.name.ilike(f"%{query}%"),
            Workflow.description.ilike(f"%{query}%")
        )
        
        db_query = self.db.query(Workflow).filter(search_filter)
        
        if user_id:
            db_query = db_query.filter(
                or_(
                    Workflow.user_id == user_id,
                    Workflow.is_public == True
                )
            )
        else:
            db_query = db_query.filter(Workflow.is_public == True)
        
        return db_query.order_by(Workflow.created_at.desc()).limit(limit).all()


class WorkflowNodeRepository:
    """Repository for WorkflowNode data access."""
    
    def __init__(self, db: Session):
        """
        Initialize WorkflowNode Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, node: WorkflowNode) -> WorkflowNode:
        """
        Create a new workflow node.
        
        Args:
            node: WorkflowNode model to create
            
        Returns:
            Created WorkflowNode model
        """
        self.db.add(node)
        self.db.flush()
        return node
    
    def find_by_workflow(self, workflow_id: str) -> List[WorkflowNode]:
        """
        Find nodes by workflow ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of WorkflowNode models
        """
        return self.db.query(WorkflowNode).filter(
            WorkflowNode.workflow_id == workflow_id
        ).all()
    
    def delete_by_workflow(self, workflow_id: str) -> int:
        """
        Delete all nodes for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Number of deleted records
        """
        count = self.db.query(WorkflowNode).filter(
            WorkflowNode.workflow_id == workflow_id
        ).delete()
        self.db.flush()
        return count


class WorkflowEdgeRepository:
    """Repository for WorkflowEdge data access."""
    
    def __init__(self, db: Session):
        """
        Initialize WorkflowEdge Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, edge: WorkflowEdge) -> WorkflowEdge:
        """
        Create a new workflow edge.
        
        Args:
            edge: WorkflowEdge model to create
            
        Returns:
            Created WorkflowEdge model
        """
        self.db.add(edge)
        self.db.flush()
        return edge
    
    def find_by_workflow(self, workflow_id: str) -> List[WorkflowEdge]:
        """
        Find edges by workflow ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of WorkflowEdge models
        """
        return self.db.query(WorkflowEdge).filter(
            WorkflowEdge.workflow_id == workflow_id
        ).all()
    
    def delete_by_workflow(self, workflow_id: str) -> int:
        """
        Delete all edges for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Number of deleted records
        """
        count = self.db.query(WorkflowEdge).filter(
            WorkflowEdge.workflow_id == workflow_id
        ).delete()
        self.db.flush()
        return count


class WorkflowExecutionRepository:
    """Repository for WorkflowExecution data access."""
    
    def __init__(self, db: Session):
        """
        Initialize WorkflowExecution Repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create(self, execution: WorkflowExecution) -> WorkflowExecution:
        """
        Create a new workflow execution.
        
        Args:
            execution: WorkflowExecution model to create
            
        Returns:
            Created WorkflowExecution model
        """
        self.db.add(execution)
        self.db.flush()
        return execution
    
    def find_by_id(self, execution_id: str) -> Optional[WorkflowExecution]:
        """
        Find execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            WorkflowExecution model or None if not found
        """
        return self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()
    
    def find_by_workflow(
        self,
        workflow_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """
        Find executions by workflow ID.
        
        Args:
            workflow_id: Workflow ID
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of WorkflowExecution models
        """
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        )
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        query = query.order_by(WorkflowExecution.started_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def find_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """
        Find executions by user ID.
        
        Args:
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of WorkflowExecution models
        """
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.user_id == user_id
        )
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        query = query.order_by(WorkflowExecution.started_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def update(self, execution: WorkflowExecution) -> WorkflowExecution:
        """
        Update a workflow execution.
        
        Args:
            execution: WorkflowExecution model to update
            
        Returns:
            Updated WorkflowExecution model
        """
        self.db.flush()
        return execution
    
    def count_by_workflow(
        self,
        workflow_id: str,
        status: Optional[str] = None
    ) -> int:
        """
        Count executions by workflow.
        
        Args:
            workflow_id: Workflow ID
            status: Filter by status (optional)
            
        Returns:
            Count of executions
        """
        query = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        )
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        return query.count()
    
    def find_running(self, limit: int = 100) -> List[WorkflowExecution]:
        """
        Find all running executions.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of running WorkflowExecution models
        """
        return self.db.query(WorkflowExecution).filter(
            WorkflowExecution.status == "running"
        ).order_by(WorkflowExecution.started_at).limit(limit).all()
