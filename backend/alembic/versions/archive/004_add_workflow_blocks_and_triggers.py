"""add_workflow_blocks_and_triggers

Revision ID: 004_add_workflow_blocks_and_triggers
Revises: a462e291b8d9
Create Date: 2025-10-30 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_add_workflow_blocks_and_triggers"
down_revision: Union[str, None] = "a462e291b8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add workflow blocks, edges, schedules, webhooks, and subflows tables."""
    
    # ========================================================================
    # AGENT BLOCK TABLES (Visual Workflow Blocks)
    # ========================================================================
    
    # Create agent_blocks table
    op.create_table(
        "agent_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position_x", sa.Float(), nullable=False),
        sa.Column("position_y", sa.Float(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("sub_blocks", sa.JSON(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("outputs", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_blocks_workflow_id"), "agent_blocks", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_agent_blocks_type"), "agent_blocks", ["type"], unique=False)
    op.create_index("ix_agent_blocks_workflow_type", "agent_blocks", ["workflow_id", "type"], unique=False)
    op.create_index("ix_agent_blocks_workflow_enabled", "agent_blocks", ["workflow_id", "enabled"], unique=False)
    
    # Create agent_edges table
    op.create_table(
        "agent_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_handle", sa.String(length=50), nullable=True),
        sa.Column("target_handle", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_block_id"], ["agent_blocks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_block_id"], ["agent_blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_edges_workflow_id"), "agent_edges", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_agent_edges_source_block_id"), "agent_edges", ["source_block_id"], unique=False)
    op.create_index(op.f("ix_agent_edges_target_block_id"), "agent_edges", ["target_block_id"], unique=False)
    
    # ========================================================================
    # WORKFLOW TRIGGER TABLES
    # ========================================================================
    
    # Create workflow_schedules table
    op.create_table(
        "workflow_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cron_expression", sa.String(length=100), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_execution_at", sa.DateTime(), nullable=True),
        sa.Column("next_execution_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_schedules_workflow_id"), "workflow_schedules", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_workflow_schedules_is_active"), "workflow_schedules", ["is_active"], unique=False)
    op.create_index(op.f("ix_workflow_schedules_next_execution_at"), "workflow_schedules", ["next_execution_at"], unique=False)
    op.create_index("ix_workflow_schedules_workflow_active", "workflow_schedules", ["workflow_id", "is_active"], unique=False)
    op.create_index("ix_workflow_schedules_next_execution", "workflow_schedules", ["is_active", "next_execution_at"], unique=False)
    
    # Create workflow_webhooks table
    op.create_table(
        "workflow_webhooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("webhook_path", sa.String(length=255), nullable=False),
        sa.Column("webhook_secret", sa.String(length=255), nullable=True),
        sa.Column("http_method", sa.String(length=10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.Column("trigger_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')",
            name="check_webhook_method_valid",
        ),
        sa.CheckConstraint("trigger_count >= 0", name="check_trigger_count_positive"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_webhooks_workflow_id"), "workflow_webhooks", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_workflow_webhooks_webhook_path"), "workflow_webhooks", ["webhook_path"], unique=True)
    op.create_index(op.f("ix_workflow_webhooks_is_active"), "workflow_webhooks", ["is_active"], unique=False)
    op.create_index("ix_workflow_webhooks_workflow_active", "workflow_webhooks", ["workflow_id", "is_active"], unique=False)
    
    # ========================================================================
    # WORKFLOW SUBFLOW TABLES (Loops and Parallel)
    # ========================================================================
    
    # Create workflow_subflows table
    op.create_table(
        "workflow_subflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subflow_type", sa.String(length=50), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "subflow_type IN ('loop', 'parallel')",
            name="check_subflow_type_valid",
        ),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_block_id"], ["agent_blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_subflows_workflow_id"), "workflow_subflows", ["workflow_id"], unique=False)
    op.create_index(op.f("ix_workflow_subflows_parent_block_id"), "workflow_subflows", ["parent_block_id"], unique=False)
    op.create_index(op.f("ix_workflow_subflows_subflow_type"), "workflow_subflows", ["subflow_type"], unique=False)
    op.create_index("ix_workflow_subflows_workflow_type", "workflow_subflows", ["workflow_id", "subflow_type"], unique=False)


def downgrade() -> None:
    """Drop workflow blocks, edges, schedules, webhooks, and subflows tables."""
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table("workflow_subflows")
    op.drop_table("workflow_webhooks")
    op.drop_table("workflow_schedules")
    op.drop_table("agent_edges")
    op.drop_table("agent_blocks")
