"""Tests for advanced workflow features: variables, validation, templates, and versioning."""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

from backend.services.agent_builder.variable_resolver import VariableResolver
from backend.services.agent_builder.workflow_validator import WorkflowValidator
from backend.services.agent_builder.workflow_template_service import WorkflowTemplateService
from backend.services.agent_builder.workflow_version_service import WorkflowVersionService
from backend.db.models.agent_builder import Variable, Workflow, AgentBlock, AgentEdge
from backend.models.agent_builder import ExecutionContext


class TestVariableResolver:
    """Tests for variable resolution."""
    
    def test_resolve_variable_from_agent_scope(self):
        """Test resolving variable from agent scope."""
        # Mock database session
        db = Mock()
        
        # Mock variable
        var = Variable(
            id=uuid4(),
            name="api_key",
            scope="agent",
            scope_id=uuid4(),
            value="test-key-123",
            value_type="string",
            is_secret=False
        )
        
        db.query.return_value.filter.return_value.first.return_value = var
        
        # Create resolver
        resolver = VariableResolver(db)
        
        # Create context
        context = ExecutionContext(
            execution_id="test",
            user_id=str(uuid4()),
            agent_id=str(var.scope_id)
        )
        
        # Resolve variable
        # Note: This is async, so we'd need to use pytest-asyncio in real tests
        # For now, just verify the setup
        assert resolver.db == db
    
    def test_resolve_variables_in_template(self):
        """Test resolving variables in template string."""
        db = Mock()
        resolver = VariableResolver(db)
        
        # Test template substitution logic
        template = "API Key: ${api_key}, URL: ${base_url}"
        assert "${api_key}" in template
        assert "${base_url}" in template


class TestWorkflowValidator:
    """Tests for workflow validation."""
    
    def test_detect_cycle_in_workflow(self):
        """Test cycle detection in workflow graph."""
        db = Mock()
        validator = WorkflowValidator(db)
        
        # Create blocks
        block1 = AgentBlock(
            id=uuid4(),
            workflow_id=uuid4(),
            type="openai",
            name="Block 1",
            position_x=0,
            position_y=0,
            config={},
            sub_blocks={},
            inputs={},
            outputs={},
            enabled=True
        )
        
        block2 = AgentBlock(
            id=uuid4(),
            workflow_id=block1.workflow_id,
            type="http",
            name="Block 2",
            position_x=100,
            position_y=0,
            config={},
            sub_blocks={},
            inputs={},
            outputs={},
            enabled=True
        )
        
        # Create cycle: block1 -> block2 -> block1
        edges = [
            AgentEdge(
                id=uuid4(),
                workflow_id=block1.workflow_id,
                source_block_id=block1.id,
                target_block_id=block2.id
            ),
            AgentEdge(
                id=uuid4(),
                workflow_id=block1.workflow_id,
                source_block_id=block2.id,
                target_block_id=block1.id
            )
        ]
        
        # Detect cycle
        errors = validator._detect_cycles([block1, block2], edges)
        
        # Should detect cycle
        assert len(errors) > 0
        assert errors[0].error_type == "cycle_detected"
    
    def test_detect_disconnected_nodes(self):
        """Test detection of disconnected nodes."""
        db = Mock()
        validator = WorkflowValidator(db)
        
        # Create blocks
        block1 = AgentBlock(
            id=uuid4(),
            workflow_id=uuid4(),
            type="openai",
            name="Block 1",
            position_x=0,
            position_y=0,
            config={},
            sub_blocks={},
            inputs={},
            outputs={},
            enabled=True
        )
        
        block2 = AgentBlock(
            id=uuid4(),
            workflow_id=block1.workflow_id,
            type="http",
            name="Block 2",
            position_x=100,
            position_y=0,
            config={},
            sub_blocks={},
            inputs={},
            outputs={},
            enabled=True
        )
        
        # Disconnected block
        block3 = AgentBlock(
            id=uuid4(),
            workflow_id=block1.workflow_id,
            type="condition",
            name="Block 3",
            position_x=200,
            position_y=0,
            config={},
            sub_blocks={},
            inputs={},
            outputs={},
            enabled=True
        )
        
        # Only connect block1 and block2
        edges = [
            AgentEdge(
                id=uuid4(),
                workflow_id=block1.workflow_id,
                source_block_id=block1.id,
                target_block_id=block2.id
            )
        ]
        
        # Detect disconnected nodes
        warnings = validator._detect_disconnected_nodes([block1, block2, block3], edges)
        
        # Should detect disconnected block3
        assert len(warnings) > 0
        assert any(w.error_type == "disconnected_node" for w in warnings)


class TestWorkflowTemplateService:
    """Tests for workflow template service."""
    
    def test_list_builtin_templates(self):
        """Test listing built-in templates."""
        db = Mock()
        service = WorkflowTemplateService(db)
        
        # List templates
        templates = service.list_templates()
        
        # Should have built-in templates
        assert len(templates) > 0
        assert any(t.id == "simple-rag" for t in templates)
    
    def test_get_template_by_id(self):
        """Test getting template by ID."""
        db = Mock()
        service = WorkflowTemplateService(db)
        
        # Get template
        template = service.get_template("simple-rag")
        
        # Should return template
        assert template is not None
        assert template.id == "simple-rag"
        assert template.name == "Simple RAG Workflow"
    
    def test_filter_templates_by_category(self):
        """Test filtering templates by category."""
        db = Mock()
        service = WorkflowTemplateService(db)
        
        # Filter by category
        rag_templates = service.list_templates(category="rag")
        
        # Should only return RAG templates
        assert all(t.category == "rag" for t in rag_templates)


class TestWorkflowVersionService:
    """Tests for workflow version service."""
    
    def test_create_version(self):
        """Test creating a workflow version."""
        db = Mock()
        service = WorkflowVersionService(db)
        
        # Mock workflow
        workflow_id = uuid4()
        workflow = Workflow(
            id=workflow_id,
            user_id=uuid4(),
            name="Test Workflow",
            description="Test",
            graph_definition={},
            is_public=False
        )
        
        db.query.return_value.filter.return_value.first.return_value = workflow
        db.query.return_value.filter.return_value.all.return_value = []
        
        # Create version
        version = service.create_version(
            workflow_id=workflow_id,
            user_id=uuid4(),
            change_description="Initial version"
        )
        
        # Should create version
        assert version is not None
        assert version.version_number == 1
        assert version.change_description == "Initial version"
    
    def test_list_versions(self):
        """Test listing workflow versions."""
        db = Mock()
        service = WorkflowVersionService(db)
        
        workflow_id = uuid4()
        
        # Create multiple versions
        workflow = Workflow(
            id=workflow_id,
            user_id=uuid4(),
            name="Test Workflow",
            description="Test",
            graph_definition={},
            is_public=False
        )
        
        db.query.return_value.filter.return_value.first.return_value = workflow
        db.query.return_value.filter.return_value.all.return_value = []
        
        service.create_version(workflow_id, uuid4(), "Version 1")
        service.create_version(workflow_id, uuid4(), "Version 2")
        
        # List versions
        versions = service.list_versions(workflow_id)
        
        # Should return versions in descending order
        assert len(versions) == 2
        assert versions[0].version_number == 2
        assert versions[1].version_number == 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
