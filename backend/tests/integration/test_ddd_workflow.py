"""
Integration Tests for DDD Workflow Implementation

Tests the complete workflow from API to Domain layer.
"""

import pytest
import asyncio
from uuid import uuid4
from sqlalchemy.orm import Session

from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.services.agent_builder.application import WorkflowApplicationService
from backend.services.agent_builder.domain.workflow.entities import WorkflowEntity, NodeEntity, EdgeEntity
from backend.services.agent_builder.domain.workflow.value_objects import NodeType, EdgeType
from backend.services.agent_builder.shared.errors import NotFoundError, ValidationError


class TestWorkflowFacade:
    """Test Workflow operations using Facade."""
    
    def test_create_workflow(self, db: Session):
        """Test workflow creation through facade."""
        facade = AgentBuilderFacade(db)
        user_id = str(uuid4())
        
        workflow = facade.create_workflow(
            user_id=user_id,
            name="Test Workflow",
            description="Test Description",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
                {
                    "id": "end",
                    "node_type": "end",
                    "config": {},
                },
            ],
            edges=[
                {
                    "id": "edge1",
                    "source_node_id": "start",
                    "target_node_id": "end",
                },
            ],
        )
        
        assert workflow is not None
        assert workflow.name == "Test Workflow"
        assert workflow.user_id == user_id
        assert len(workflow.nodes) == 2
        assert len(workflow.edges) == 1
    
    def test_get_workflow(self, db: Session):
        """Test getting a workflow."""
        facade = AgentBuilderFacade(db)
        user_id = str(uuid4())
        
        # Create workflow with at least one node
        created = facade.create_workflow(
            user_id=user_id,
            name="Test Workflow",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
            ],
        )
        
        # Get workflow
        retrieved = facade.get_workflow(str(created.id))
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
    
    def test_get_nonexistent_workflow(self, db: Session):
        """Test getting a non-existent workflow."""
        facade = AgentBuilderFacade(db)
        
        with pytest.raises(NotFoundError):
            facade.get_workflow(str(uuid4()))
    
    def test_update_workflow(self, db: Session):
        """Test updating a workflow."""
        facade = AgentBuilderFacade(db)
        user_id = str(uuid4())
        
        # Create workflow with at least one node
        created = facade.create_workflow(
            user_id=user_id,
            name="Original Name",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
            ],
        )
        
        # Update workflow
        updated = facade.workflows.update_workflow(
            workflow_id=str(created.id),
            name="Updated Name",
            description="Updated Description",
        )
        
        assert updated.name == "Updated Name"
        assert updated.description == "Updated Description"
    
    def test_delete_workflow(self, db: Session):
        """Test deleting a workflow."""
        facade = AgentBuilderFacade(db)
        user_id = str(uuid4())
        
        # Create workflow with at least one node
        created = facade.create_workflow(
            user_id=user_id,
            name="Test Workflow",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
            ],
        )
        
        # Delete workflow
        facade.workflows.delete_workflow(str(created.id))
        
        # Verify deletion
        with pytest.raises(NotFoundError):
            facade.get_workflow(str(created.id))
    
    def test_list_workflows(self, db: Session):
        """Test listing workflows."""
        facade = AgentBuilderFacade(db)
        user_id = str(uuid4())
        
        # Create multiple workflows with at least one node each
        for i in range(3):
            facade.create_workflow(
                user_id=user_id,
                name=f"Workflow {i}",
                nodes=[
                    {
                        "id": f"start_{i}",
                        "node_type": "start",
                        "config": {},
                    },
                ],
            )
        
        # List workflows
        workflows = facade.workflows.list_workflows(user_id=user_id)
        
        assert len(workflows) >= 3


class TestWorkflowApplicationService:
    """Test Workflow operations using Application Service."""
    
    def test_create_workflow(self, db: Session):
        """Test workflow creation through application service."""
        service = WorkflowApplicationService(db)
        user_id = str(uuid4())
        
        workflow = service.create_workflow(
            user_id=user_id,
            name="Test Workflow",
            description="Test Description",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
            ],
        )
        
        assert workflow is not None
        assert workflow.name == "Test Workflow"
    
    def test_validate_workflow(self, db: Session):
        """Test workflow validation."""
        service = WorkflowApplicationService(db)
        
        # Valid workflow - using dict format instead of entities
        nodes = [
            {
                "id": "start",
                "node_type": "start",
                "config": {},
            },
            {
                "id": "end",
                "node_type": "end",
                "config": {},
            },
        ]
        edges = [
            {
                "id": "edge1",
                "source_node_id": "start",
                "target_node_id": "end",
            },
        ]
        
        # Create workflow to test validation
        user_id = str(uuid4())
        workflow = service.create_workflow(
            user_id=user_id,
            name="Test Validation",
            nodes=nodes,
            edges=edges,
        )
        
        assert workflow is not None
        assert len(workflow.nodes) == 2
        assert len(workflow.edges) == 1
    
    def test_invalid_workflow(self, db: Session):
        """Test invalid workflow validation."""
        service = WorkflowApplicationService(db)
        
        # Invalid: empty workflow
        user_id = str(uuid4())
        
        with pytest.raises(ValueError) as exc_info:
            service.create_workflow(
                user_id=user_id,
                name="Invalid Workflow",
                nodes=[],  # No nodes
                edges=[],
            )
        
        assert "at least one node" in str(exc_info.value).lower()


class TestWorkflowExecution:
    """Test Workflow execution."""
    
    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, db: Session):
        """Test executing a simple workflow."""
        facade = AgentBuilderFacade(db)
        user_id = str(uuid4())
        
        # Create simple workflow
        workflow = facade.create_workflow(
            user_id=user_id,
            name="Simple Workflow",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
                {
                    "id": "end",
                    "node_type": "end",
                    "config": {},
                },
            ],
            edges=[
                {
                    "id": "edge1",
                    "source_node_id": "start",
                    "target_node_id": "end",
                },
            ],
        )
        
        # Execute workflow
        result = await facade.execute_workflow(
            workflow_id=str(workflow.id),
            input_data={"test": "data"},
            user_id=user_id,
        )
        
        assert result is not None
        assert result.status == "completed"
    
    @pytest.mark.asyncio
    async def test_execute_workflow_streaming(self, db: Session):
        """Test executing a workflow with streaming."""
        facade = AgentBuilderFacade(db)
        user_id = str(uuid4())
        
        # Create workflow
        workflow = facade.create_workflow(
            user_id=user_id,
            name="Streaming Workflow",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
                {
                    "id": "end",
                    "node_type": "end",
                    "config": {},
                },
            ],
            edges=[
                {
                    "id": "edge1",
                    "source_node_id": "start",
                    "target_node_id": "end",
                },
            ],
        )
        
        # Execute with streaming
        events = []
        async for event in facade.execute_workflow_streaming(
            workflow_id=str(workflow.id),
            input_data={"test": "data"},
            user_id=user_id,
        ):
            events.append(event)
        
        assert len(events) > 0
        assert events[0]["type"] == "execution_started"
        assert events[-1]["type"] == "execution_completed"


class TestWorkflowCQRS:
    """Test Workflow operations using CQRS."""
    
    def test_create_with_command(self, db: Session):
        """Test creating workflow with command handler."""
        from backend.services.agent_builder.application.commands import (
            WorkflowCommandHandler,
            CreateWorkflowCommand,
        )
        
        handler = WorkflowCommandHandler(db)
        user_id = str(uuid4())
        
        command = CreateWorkflowCommand(
            user_id=user_id,
            name="Test Workflow",
            description="Test Description",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
            ],
        )
        
        workflow = handler.handle_create(command)
        
        assert workflow is not None
        assert workflow.name == "Test Workflow"
    
    def test_get_with_query(self, db: Session):
        """Test getting workflow with query handler."""
        from backend.services.agent_builder.application.commands import (
            WorkflowCommandHandler,
            CreateWorkflowCommand,
        )
        from backend.services.agent_builder.application.queries import (
            WorkflowQueryHandler,
            GetWorkflowQuery,
        )
        
        # Create workflow with at least one node
        command_handler = WorkflowCommandHandler(db)
        user_id = str(uuid4())
        
        command = CreateWorkflowCommand(
            user_id=user_id,
            name="Test Workflow",
            nodes=[
                {
                    "id": "start",
                    "node_type": "start",
                    "config": {},
                },
            ],
        )
        created = command_handler.handle_create(command)
        
        # Query workflow
        query_handler = WorkflowQueryHandler(db)
        query = GetWorkflowQuery(workflow_id=str(created.id))
        retrieved = query_handler.handle_get(query)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_list_with_query(self, db: Session):
        """Test listing workflows with query handler."""
        from backend.services.agent_builder.application.commands import (
            WorkflowCommandHandler,
            CreateWorkflowCommand,
        )
        from backend.services.agent_builder.application.queries import (
            WorkflowQueryHandler,
            ListWorkflowsQuery,
        )
        
        # Create workflows with at least one node each
        command_handler = WorkflowCommandHandler(db)
        user_id = str(uuid4())
        
        for i in range(3):
            command = CreateWorkflowCommand(
                user_id=user_id,
                name=f"Workflow {i}",
                nodes=[
                    {
                        "id": f"start_{i}",
                        "node_type": "start",
                        "config": {},
                    },
                ],
            )
            command_handler.handle_create(command)
        
        # Query workflows
        query_handler = WorkflowQueryHandler(db)
        query = ListWorkflowsQuery(user_id=user_id)
        workflows = query_handler.handle_list(query)
        
        assert len(workflows) >= 3


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db():
    """Provide a database session for testing."""
    from backend.db.database import SessionLocal
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
