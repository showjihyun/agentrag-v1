"""
Workflow Repository Interface

Defines the contract for workflow persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from .entities import WorkflowEntity, NodeEntity, EdgeEntity


class WorkflowRepositoryInterface(ABC):
    """Abstract repository interface for Workflow aggregate."""
    
    @abstractmethod
    def save(self, workflow: WorkflowEntity) -> WorkflowEntity:
        """Save a workflow (create or update)."""
        pass
    
    @abstractmethod
    def find_by_id(self, workflow_id: UUID) -> Optional[WorkflowEntity]:
        """Find workflow by ID with all nodes and edges."""
        pass
    
    @abstractmethod
    def find_by_user(
        self,
        user_id: UUID,
        is_public: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowEntity]:
        """Find workflows by user ID."""
        pass
    
    @abstractmethod
    def find_public(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowEntity]:
        """Find public workflows."""
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[WorkflowEntity]:
        """Search workflows by name or description."""
        pass
    
    @abstractmethod
    def delete(self, workflow_id: UUID, hard: bool = False) -> bool:
        """Delete a workflow."""
        pass
    
    @abstractmethod
    def exists(self, workflow_id: UUID) -> bool:
        """Check if workflow exists."""
        pass


class NodeRepositoryInterface(ABC):
    """Abstract repository interface for workflow nodes."""
    
    @abstractmethod
    def save(self, node: NodeEntity) -> NodeEntity:
        """Save a node."""
        pass
    
    @abstractmethod
    def save_batch(self, nodes: List[NodeEntity]) -> List[NodeEntity]:
        """Save multiple nodes."""
        pass
    
    @abstractmethod
    def find_by_workflow(self, workflow_id: UUID) -> List[NodeEntity]:
        """Find all nodes for a workflow."""
        pass
    
    @abstractmethod
    def delete_by_workflow(self, workflow_id: UUID) -> int:
        """Delete all nodes for a workflow."""
        pass


class EdgeRepositoryInterface(ABC):
    """Abstract repository interface for workflow edges."""
    
    @abstractmethod
    def save(self, edge: EdgeEntity) -> EdgeEntity:
        """Save an edge."""
        pass
    
    @abstractmethod
    def save_batch(self, edges: List[EdgeEntity]) -> List[EdgeEntity]:
        """Save multiple edges."""
        pass
    
    @abstractmethod
    def find_by_workflow(self, workflow_id: UUID) -> List[EdgeEntity]:
        """Find all edges for a workflow."""
        pass
    
    @abstractmethod
    def delete_by_workflow(self, workflow_id: UUID) -> int:
        """Delete all edges for a workflow."""
        pass
