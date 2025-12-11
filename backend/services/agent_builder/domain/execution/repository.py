"""Execution Repository Interface"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from .entities import ExecutionEntity, ExecutionStepEntity
from .value_objects import ExecutionStatus


class ExecutionRepositoryInterface(ABC):
    """Abstract repository for Execution aggregate."""
    
    @abstractmethod
    def save(self, execution: ExecutionEntity) -> ExecutionEntity:
        """Save an execution."""
        pass
    
    @abstractmethod
    def find_by_id(self, execution_id: UUID) -> Optional[ExecutionEntity]:
        """Find execution by ID."""
        pass
    
    @abstractmethod
    def find_by_workflow(
        self,
        workflow_id: UUID,
        status: Optional[ExecutionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ExecutionEntity]:
        """Find executions by workflow."""
        pass
    
    @abstractmethod
    def find_by_user(
        self,
        user_id: UUID,
        status: Optional[ExecutionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ExecutionEntity]:
        """Find executions by user."""
        pass
    
    @abstractmethod
    def find_running(self, workflow_id: Optional[UUID] = None) -> List[ExecutionEntity]:
        """Find running executions."""
        pass
    
    @abstractmethod
    def update_status(
        self,
        execution_id: UUID,
        status: ExecutionStatus,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update execution status."""
        pass


class ExecutionStepRepositoryInterface(ABC):
    """Abstract repository for execution steps."""
    
    @abstractmethod
    def save(self, step: ExecutionStepEntity) -> ExecutionStepEntity:
        """Save a step."""
        pass
    
    @abstractmethod
    def find_by_execution(self, execution_id: UUID) -> List[ExecutionStepEntity]:
        """Find all steps for an execution."""
        pass
    
    @abstractmethod
    def find_latest(self, execution_id: UUID) -> Optional[ExecutionStepEntity]:
        """Find the latest step."""
        pass
