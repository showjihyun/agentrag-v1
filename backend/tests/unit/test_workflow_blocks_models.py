"""Tests for Workflow Blocks database models.

These tests verify the functionality of the new workflow blocks, edges,
schedules, webhooks, and subflows models added for Sim integration.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.db.database import Base
from backend.db.models.agent_builder import (
    Workflow,
    AgentBlock,
    AgentEdge,
    WorkflowSchedule,
    WorkflowWebhook,
    WorkflowSubflow,
)


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_workflow(db_session):
    """Create a sample workflow for testing."""
    workflow = Workflow(
        name="Test Workflow",
        description="Test workflow for blocks",
        graph_definition={"nodes": [], "edges": []},
        user_id="00000000-0000-0000-0000-000000000001",
    )
    db_session.add(workflow)
    db_session.commit()
    return workflow


# ============================================================================
# AgentBlock Tests
# ============================================================================

def test_agent_block_creation(db_session, sample_workflow):
    """Test AgentBlock model creation with required fields."""
    block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="openai",
        name="OpenAI Block",
        position_x=100.0,
        position_y=200.0,
        config={"model": "gpt-4"},
        sub_blocks={"prompt": "Hello"},
        inputs={"text": {"type": "string"}},
        outputs={"response": {"type": "string"}},
        enabled=True,
    )
    db_session.add(block)
    db_session.commit()
    
    assert block.id is not None
    assert block.workflow_id == sample_workflow.id
    assert block.type == "openai"
    assert block.name == "OpenAI Block"
    assert block.position_x == 100.0
    assert block.position_y == 200.0
    assert block.enabled is True
    assert block.created_at is not None
    assert block.updated_at is not None


def test_agent_block_workflow_relationship(db_session, sample_workflow):
    """Test AgentBlock relationship with Workflow."""
    block1 = AgentBlock(
        workflow_id=sample_workflow.id,
        type="openai",
        name="Block 1",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    block2 = AgentBlock(
        workflow_id=sample_workflow.id,
        type="http",
        name="Block 2",
        position_x=100.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add_all([block1, block2])
    db_session.commit()
    
    # Refresh workflow to load relationships
    db_session.refresh(sample_workflow)
    
    assert len(sample_workflow.blocks) == 2
    assert block1 in sample_workflow.blocks
    assert block2 in sample_workflow.blocks


def test_agent_block_cascade_delete(db_session, sample_workflow):
    """Test AgentBlock cascade delete when workflow is deleted."""
    block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="openai",
        name="Test Block",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add(block)
    db_session.commit()
    
    block_id = block.id
    
    # Delete workflow
    db_session.delete(sample_workflow)
    db_session.commit()
    
    # Block should be deleted
    deleted_block = db_session.query(AgentBlock).filter_by(id=block_id).first()
    assert deleted_block is None


# ============================================================================
# AgentEdge Tests
# ============================================================================

def test_agent_edge_creation(db_session, sample_workflow):
    """Test AgentEdge model creation with required fields."""
    # Create source and target blocks
    source_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="openai",
        name="Source Block",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    target_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="http",
        name="Target Block",
        position_x=100.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add_all([source_block, target_block])
    db_session.commit()
    
    # Create edge
    edge = AgentEdge(
        workflow_id=sample_workflow.id,
        source_block_id=source_block.id,
        target_block_id=target_block.id,
        source_handle="output",
        target_handle="input",
    )
    db_session.add(edge)
    db_session.commit()
    
    assert edge.id is not None
    assert edge.workflow_id == sample_workflow.id
    assert edge.source_block_id == source_block.id
    assert edge.target_block_id == target_block.id
    assert edge.source_handle == "output"
    assert edge.target_handle == "input"
    assert edge.created_at is not None


def test_agent_edge_relationships(db_session, sample_workflow):
    """Test AgentEdge relationships with blocks."""
    source_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="openai",
        name="Source",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    target_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="http",
        name="Target",
        position_x=100.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add_all([source_block, target_block])
    db_session.commit()
    
    edge = AgentEdge(
        workflow_id=sample_workflow.id,
        source_block_id=source_block.id,
        target_block_id=target_block.id,
    )
    db_session.add(edge)
    db_session.commit()
    
    # Refresh blocks to load relationships
    db_session.refresh(source_block)
    db_session.refresh(target_block)
    
    assert len(source_block.source_edges) == 1
    assert len(target_block.target_edges) == 1
    assert edge in source_block.source_edges
    assert edge in target_block.target_edges


def test_agent_edge_cascade_delete_on_block(db_session, sample_workflow):
    """Test AgentEdge cascade delete when block is deleted."""
    source_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="openai",
        name="Source",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    target_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="http",
        name="Target",
        position_x=100.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add_all([source_block, target_block])
    db_session.commit()
    
    edge = AgentEdge(
        workflow_id=sample_workflow.id,
        source_block_id=source_block.id,
        target_block_id=target_block.id,
    )
    db_session.add(edge)
    db_session.commit()
    
    edge_id = edge.id
    
    # Delete source block
    db_session.delete(source_block)
    db_session.commit()
    
    # Edge should be deleted
    deleted_edge = db_session.query(AgentEdge).filter_by(id=edge_id).first()
    assert deleted_edge is None


# ============================================================================
# WorkflowSchedule Tests
# ============================================================================

def test_workflow_schedule_creation(db_session, sample_workflow):
    """Test WorkflowSchedule model creation with required fields."""
    schedule = WorkflowSchedule(
        workflow_id=sample_workflow.id,
        cron_expression="0 0 * * *",
        timezone="UTC",
        input_data={"key": "value"},
        is_active=True,
    )
    db_session.add(schedule)
    db_session.commit()
    
    assert schedule.id is not None
    assert schedule.workflow_id == sample_workflow.id
    assert schedule.cron_expression == "0 0 * * *"
    assert schedule.timezone == "UTC"
    assert schedule.is_active is True
    assert schedule.created_at is not None
    assert schedule.updated_at is not None


def test_workflow_schedule_execution_tracking(db_session, sample_workflow):
    """Test WorkflowSchedule execution tracking fields."""
    schedule = WorkflowSchedule(
        workflow_id=sample_workflow.id,
        cron_expression="0 0 * * *",
        timezone="UTC",
        is_active=True,
    )
    db_session.add(schedule)
    db_session.commit()
    
    # Update execution tracking
    now = datetime.utcnow()
    schedule.last_execution_at = now
    schedule.next_execution_at = now
    db_session.commit()
    
    assert schedule.last_execution_at is not None
    assert schedule.next_execution_at is not None


def test_workflow_schedule_cascade_delete(db_session, sample_workflow):
    """Test WorkflowSchedule cascade delete when workflow is deleted."""
    schedule = WorkflowSchedule(
        workflow_id=sample_workflow.id,
        cron_expression="0 0 * * *",
        timezone="UTC",
        is_active=True,
    )
    db_session.add(schedule)
    db_session.commit()
    
    schedule_id = schedule.id
    
    # Delete workflow
    db_session.delete(sample_workflow)
    db_session.commit()
    
    # Schedule should be deleted
    deleted_schedule = db_session.query(WorkflowSchedule).filter_by(id=schedule_id).first()
    assert deleted_schedule is None


# ============================================================================
# WorkflowWebhook Tests
# ============================================================================

def test_workflow_webhook_creation(db_session, sample_workflow):
    """Test WorkflowWebhook model creation with required fields."""
    webhook = WorkflowWebhook(
        workflow_id=sample_workflow.id,
        webhook_path="/webhooks/test-workflow",
        webhook_secret="secret123",
        http_method="POST",
        is_active=True,
        trigger_count=0,
    )
    db_session.add(webhook)
    db_session.commit()
    
    assert webhook.id is not None
    assert webhook.workflow_id == sample_workflow.id
    assert webhook.webhook_path == "/webhooks/test-workflow"
    assert webhook.webhook_secret == "secret123"
    assert webhook.http_method == "POST"
    assert webhook.is_active is True
    assert webhook.trigger_count == 0
    assert webhook.created_at is not None
    assert webhook.updated_at is not None


def test_workflow_webhook_unique_path(db_session, sample_workflow):
    """Test WorkflowWebhook unique webhook_path constraint."""
    webhook1 = WorkflowWebhook(
        workflow_id=sample_workflow.id,
        webhook_path="/webhooks/unique-path",
        http_method="POST",
        is_active=True,
        trigger_count=0,
    )
    db_session.add(webhook1)
    db_session.commit()
    
    # Try to create another webhook with same path
    webhook2 = WorkflowWebhook(
        workflow_id=sample_workflow.id,
        webhook_path="/webhooks/unique-path",
        http_method="POST",
        is_active=True,
        trigger_count=0,
    )
    db_session.add(webhook2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_workflow_webhook_trigger_tracking(db_session, sample_workflow):
    """Test WorkflowWebhook trigger tracking fields."""
    webhook = WorkflowWebhook(
        workflow_id=sample_workflow.id,
        webhook_path="/webhooks/test",
        http_method="POST",
        is_active=True,
        trigger_count=0,
    )
    db_session.add(webhook)
    db_session.commit()
    
    # Simulate trigger
    webhook.trigger_count += 1
    webhook.last_triggered_at = datetime.utcnow()
    db_session.commit()
    
    assert webhook.trigger_count == 1
    assert webhook.last_triggered_at is not None


def test_workflow_webhook_cascade_delete(db_session, sample_workflow):
    """Test WorkflowWebhook cascade delete when workflow is deleted."""
    webhook = WorkflowWebhook(
        workflow_id=sample_workflow.id,
        webhook_path="/webhooks/test",
        http_method="POST",
        is_active=True,
        trigger_count=0,
    )
    db_session.add(webhook)
    db_session.commit()
    
    webhook_id = webhook.id
    
    # Delete workflow
    db_session.delete(sample_workflow)
    db_session.commit()
    
    # Webhook should be deleted
    deleted_webhook = db_session.query(WorkflowWebhook).filter_by(id=webhook_id).first()
    assert deleted_webhook is None


# ============================================================================
# WorkflowSubflow Tests
# ============================================================================

def test_workflow_subflow_creation(db_session, sample_workflow):
    """Test WorkflowSubflow model creation with required fields."""
    # Create parent block
    parent_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="loop",
        name="Loop Block",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add(parent_block)
    db_session.commit()
    
    # Create subflow
    subflow = WorkflowSubflow(
        workflow_id=sample_workflow.id,
        parent_block_id=parent_block.id,
        subflow_type="loop",
        configuration={"iterations": 5},
    )
    db_session.add(subflow)
    db_session.commit()
    
    assert subflow.id is not None
    assert subflow.workflow_id == sample_workflow.id
    assert subflow.parent_block_id == parent_block.id
    assert subflow.subflow_type == "loop"
    assert subflow.configuration == {"iterations": 5}
    assert subflow.created_at is not None
    assert subflow.updated_at is not None


def test_workflow_subflow_parallel_type(db_session, sample_workflow):
    """Test WorkflowSubflow with parallel type."""
    parent_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="parallel",
        name="Parallel Block",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add(parent_block)
    db_session.commit()
    
    subflow = WorkflowSubflow(
        workflow_id=sample_workflow.id,
        parent_block_id=parent_block.id,
        subflow_type="parallel",
        configuration={"branches": 3},
    )
    db_session.add(subflow)
    db_session.commit()
    
    assert subflow.subflow_type == "parallel"
    assert subflow.configuration == {"branches": 3}


def test_workflow_subflow_cascade_delete(db_session, sample_workflow):
    """Test WorkflowSubflow cascade delete when parent block is deleted."""
    parent_block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="loop",
        name="Loop Block",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add(parent_block)
    db_session.commit()
    
    subflow = WorkflowSubflow(
        workflow_id=sample_workflow.id,
        parent_block_id=parent_block.id,
        subflow_type="loop",
        configuration={},
    )
    db_session.add(subflow)
    db_session.commit()
    
    subflow_id = subflow.id
    
    # Delete parent block
    db_session.delete(parent_block)
    db_session.commit()
    
    # Subflow should be deleted
    deleted_subflow = db_session.query(WorkflowSubflow).filter_by(id=subflow_id).first()
    assert deleted_subflow is None


# ============================================================================
# Integration Tests
# ============================================================================

def test_complete_workflow_with_blocks_and_edges(db_session, sample_workflow):
    """Test creating a complete workflow with blocks and edges."""
    # Create blocks
    block1 = AgentBlock(
        workflow_id=sample_workflow.id,
        type="openai",
        name="Block 1",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    block2 = AgentBlock(
        workflow_id=sample_workflow.id,
        type="http",
        name="Block 2",
        position_x=100.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    block3 = AgentBlock(
        workflow_id=sample_workflow.id,
        type="condition",
        name="Block 3",
        position_x=200.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add_all([block1, block2, block3])
    db_session.commit()
    
    # Create edges
    edge1 = AgentEdge(
        workflow_id=sample_workflow.id,
        source_block_id=block1.id,
        target_block_id=block2.id,
    )
    edge2 = AgentEdge(
        workflow_id=sample_workflow.id,
        source_block_id=block2.id,
        target_block_id=block3.id,
    )
    db_session.add_all([edge1, edge2])
    db_session.commit()
    
    # Refresh workflow
    db_session.refresh(sample_workflow)
    
    assert len(sample_workflow.blocks) == 3
    assert len(sample_workflow.agent_edges) == 2


def test_workflow_with_all_components(db_session, sample_workflow):
    """Test workflow with blocks, edges, schedules, webhooks, and subflows."""
    # Create block
    block = AgentBlock(
        workflow_id=sample_workflow.id,
        type="loop",
        name="Loop Block",
        position_x=0.0,
        position_y=0.0,
        config={},
        sub_blocks={},
        inputs={},
        outputs={},
    )
    db_session.add(block)
    db_session.commit()
    
    # Create edge (self-loop for testing)
    edge = AgentEdge(
        workflow_id=sample_workflow.id,
        source_block_id=block.id,
        target_block_id=block.id,
    )
    db_session.add(edge)
    
    # Create schedule
    schedule = WorkflowSchedule(
        workflow_id=sample_workflow.id,
        cron_expression="0 0 * * *",
        timezone="UTC",
        is_active=True,
    )
    db_session.add(schedule)
    
    # Create webhook
    webhook = WorkflowWebhook(
        workflow_id=sample_workflow.id,
        webhook_path="/webhooks/complete-test",
        http_method="POST",
        is_active=True,
        trigger_count=0,
    )
    db_session.add(webhook)
    
    # Create subflow
    subflow = WorkflowSubflow(
        workflow_id=sample_workflow.id,
        parent_block_id=block.id,
        subflow_type="loop",
        configuration={},
    )
    db_session.add(subflow)
    
    db_session.commit()
    
    # Refresh workflow
    db_session.refresh(sample_workflow)
    
    assert len(sample_workflow.blocks) == 1
    assert len(sample_workflow.agent_edges) == 1
    assert len(sample_workflow.schedules) == 1
    assert len(sample_workflow.webhooks) == 1
    assert len(sample_workflow.subflows) == 1
