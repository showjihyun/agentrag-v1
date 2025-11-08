"""add_agent_builder_tables

Revision ID: a462e291b8d9
Revises: 3cf740d85320
Create Date: 2025-10-25 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a462e291b8d9"
down_revision: Union[str, None] = "3cf740d85320"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Agent Builder tables."""
    
    # ========================================================================
    # AGENT TABLES
    # ========================================================================
    
    # Create agent_templates table
    op.create_table(
        "agent_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("required_tools", sa.JSON(), nullable=True),
        sa.Column("use_case_examples", sa.JSON(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("rating >= 0.0 AND rating <= 5.0", name="check_rating_range"),
        sa.CheckConstraint("usage_count >= 0", name="check_usage_count_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_templates_category"), "agent_templates", ["category"], unique=False)
    op.create_index(op.f("ix_agent_templates_is_published"), "agent_templates", ["is_published"], unique=False)

    
    # Create prompt_templates table
    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prompt_templates_category"), "prompt_templates", ["category"], unique=False)
    op.create_index(op.f("ix_prompt_templates_is_system"), "prompt_templates", ["is_system"], unique=False)
    
    # Create agents table
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prompt_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("llm_provider", sa.String(length=100), nullable=False),
        sa.Column("llm_model", sa.String(length=100), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("agent_type IN ('custom', 'template_based')", name="check_agent_type_valid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["agent_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["prompt_template_id"], ["prompt_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agents_agent_type"), "agents", ["agent_type"], unique=False)
    op.create_index(op.f("ix_agents_created_at"), "agents", ["created_at"], unique=False)
    op.create_index(op.f("ix_agents_deleted_at"), "agents", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_agents_is_public"), "agents", ["is_public"], unique=False)
    op.create_index(op.f("ix_agents_user_id"), "agents", ["user_id"], unique=False)
    op.create_index("ix_agents_user_type", "agents", ["user_id", "agent_type"], unique=False)
    op.create_index("ix_agents_user_created", "agents", ["user_id", "created_at"], unique=False)

    
    # Create agent_versions table
    op.create_table(
        "agent_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version_number", sa.String(length=50), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("change_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_versions_agent_id"), "agent_versions", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_versions_created_at"), "agent_versions", ["created_at"], unique=False)
    op.create_index("ix_agent_versions_agent_created", "agent_versions", ["agent_id", "created_at"], unique=False)
    
    # Create prompt_template_versions table
    op.create_table(
        "prompt_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.String(length=50), nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("change_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["prompt_template_id"], ["prompt_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prompt_template_versions_prompt_template_id"), "prompt_template_versions", ["prompt_template_id"], unique=False)
    
    # Create tools table
    op.create_table(
        "tools",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("input_schema", sa.JSON(), nullable=False),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("implementation_type", sa.String(length=50), nullable=False),
        sa.Column("implementation_ref", sa.String(length=500), nullable=True),
        sa.Column("requires_auth", sa.Boolean(), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("implementation_type IN ('langchain', 'custom', 'builtin')", name="check_tool_implementation_type_valid"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tools_category"), "tools", ["category"], unique=False)
    op.create_index(op.f("ix_tools_is_builtin"), "tools", ["is_builtin"], unique=False)
    
    # Create agent_tools table
    op.create_table(
        "agent_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_id", sa.String(length=100), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool"),
    )
    op.create_index(op.f("ix_agent_tools_agent_id"), "agent_tools", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_tools_tool_id"), "agent_tools", ["tool_id"], unique=False)
    op.create_index("ix_agent_tools_agent_order", "agent_tools", ["agent_id", "order"], unique=False)

    
    # ========================================================================
    # BLOCK TABLES
    # ========================================================================
    
    # Create blocks table
    op.create_table(
        "blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("block_type", sa.String(length=50), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=False),
        sa.Column("output_schema", sa.JSON(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("implementation", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("block_type IN ('llm', 'tool', 'logic', 'composite')", name="check_block_type_valid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_block_name_per_user"),
    )
    op.create_index(op.f("ix_blocks_block_type"), "blocks", ["block_type"], unique=False)
    op.create_index(op.f("ix_blocks_is_public"), "blocks", ["is_public"], unique=False)
    op.create_index(op.f("ix_blocks_user_id"), "blocks", ["user_id"], unique=False)
    op.create_index("ix_blocks_user_type", "blocks", ["user_id", "block_type"], unique=False)
    op.create_index("ix_blocks_user_public", "blocks", ["user_id", "is_public"], unique=False)
    
    # Create block_versions table
    op.create_table(
        "block_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.String(length=50), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("implementation", sa.Text(), nullable=True),
        sa.Column("is_breaking_change", sa.Boolean(), nullable=True),
        sa.Column("change_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_block_versions_block_id"), "block_versions", ["block_id"], unique=False)
    op.create_index(op.f("ix_block_versions_created_at"), "block_versions", ["created_at"], unique=False)
    op.create_index("ix_block_versions_block_created", "block_versions", ["block_id", "created_at"], unique=False)
    
    # Create block_dependencies table
    op.create_table(
        "block_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_constraint", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["parent_block_id"], ["blocks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_block_id"], ["blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_block_id", "child_block_id", name="uq_block_dependency"),
    )
    op.create_index(op.f("ix_block_dependencies_child_block_id"), "block_dependencies", ["child_block_id"], unique=False)
    op.create_index(op.f("ix_block_dependencies_parent_block_id"), "block_dependencies", ["parent_block_id"], unique=False)
    
    # Create block_test_cases table
    op.create_table(
        "block_test_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("expected_output", sa.JSON(), nullable=False),
        sa.Column("assertions", sa.JSON(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_status", sa.String(length=50), nullable=True),
        sa.Column("last_run_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("last_run_status IS NULL OR last_run_status IN ('passed', 'failed', 'error')", name="check_test_status_valid"),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_block_test_cases_block_id"), "block_test_cases", ["block_id"], unique=False)

    
    # ========================================================================
    # WORKFLOW TABLES
    # ========================================================================
    
    # Create workflows table
    op.create_table(
        "workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("graph_definition", sa.JSON(), nullable=False),
        sa.Column("compiled_graph", sa.LargeBinary(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflows_user_id"), "workflows", ["user_id"], unique=False)
    op.create_index("ix_workflows_user_public", "workflows", ["user_id", "is_public"], unique=False)
    
    # Create workflow_nodes table
    op.create_table(
        "workflow_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_type", sa.String(length=50), nullable=False),
        sa.Column("node_ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("position_x", sa.Float(), nullable=True),
        sa.Column("position_y", sa.Float(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.CheckConstraint("node_type IN ('agent', 'block', 'control')", name="check_node_type_valid"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_nodes_workflow_id"), "workflow_nodes", ["workflow_id"], unique=False)
    
    # Create workflow_edges table
    op.create_table(
        "workflow_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edge_type", sa.String(length=50), nullable=True),
        sa.Column("condition", sa.Text(), nullable=True),
        sa.CheckConstraint("edge_type IN ('normal', 'conditional')", name="check_edge_type_valid"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_node_id"], ["workflow_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_node_id"], ["workflow_nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_edges_source_node_id"), "workflow_edges", ["source_node_id"], unique=False)
    op.create_index(op.f("ix_workflow_edges_target_node_id"), "workflow_edges", ["target_node_id"], unique=False)
    op.create_index(op.f("ix_workflow_edges_workflow_id"), "workflow_edges", ["workflow_id"], unique=False)
    
    # Create workflow_executions table
    op.create_table(
        "workflow_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("execution_context", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.CheckConstraint("status IN ('running', 'completed', 'failed', 'timeout', 'cancelled')", name="check_workflow_execution_status_valid"),
        sa.CheckConstraint("duration_ms >= 0", name="check_workflow_duration_positive"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_executions_session_id"), "workflow_executions", ["session_id"], unique=False)
    op.create_index(op.f("ix_workflow_executions_started_at"), "workflow_executions", ["started_at"], unique=False)
    op.create_index(op.f("ix_workflow_executions_status"), "workflow_executions", ["status"], unique=False)
    op.create_index(op.f("ix_workflow_executions_user_id"), "workflow_executions", ["user_id"], unique=False)
    op.create_index(op.f("ix_workflow_executions_workflow_id"), "workflow_executions", ["workflow_id"], unique=False)
    op.create_index("ix_workflow_executions_user_status", "workflow_executions", ["user_id", "status"], unique=False)
    op.create_index("ix_workflow_executions_workflow_started", "workflow_executions", ["workflow_id", "started_at"], unique=False)

    
    # ========================================================================
    # KNOWLEDGEBASE TABLES
    # ========================================================================
    
    # Create knowledgebases table
    op.create_table(
        "knowledgebases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("milvus_collection_name", sa.String(length=255), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=True),
        sa.Column("chunk_overlap", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("chunk_size > 0", name="check_chunk_size_positive"),
        sa.CheckConstraint("chunk_overlap >= 0", name="check_chunk_overlap_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledgebases_created_at"), "knowledgebases", ["created_at"], unique=False)
    op.create_index(op.f("ix_knowledgebases_milvus_collection_name"), "knowledgebases", ["milvus_collection_name"], unique=True)
    op.create_index(op.f("ix_knowledgebases_user_id"), "knowledgebases", ["user_id"], unique=False)
    
    # Create knowledgebase_documents table
    op.create_table(
        "knowledgebase_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledgebase_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("removed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["knowledgebase_id"], ["knowledgebases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("knowledgebase_id", "document_id", name="uq_kb_document"),
    )
    op.create_index(op.f("ix_knowledgebase_documents_document_id"), "knowledgebase_documents", ["document_id"], unique=False)
    op.create_index(op.f("ix_knowledgebase_documents_knowledgebase_id"), "knowledgebase_documents", ["knowledgebase_id"], unique=False)
    
    # Create knowledgebase_versions table
    op.create_table(
        "knowledgebase_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledgebase_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("document_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("version_number > 0", name="check_kb_version_positive"),
        sa.ForeignKeyConstraint(["knowledgebase_id"], ["knowledgebases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledgebase_versions_created_at"), "knowledgebase_versions", ["created_at"], unique=False)
    op.create_index(op.f("ix_knowledgebase_versions_knowledgebase_id"), "knowledgebase_versions", ["knowledgebase_id"], unique=False)
    op.create_index("ix_kb_versions_kb_created", "knowledgebase_versions", ["knowledgebase_id", "created_at"], unique=False)
    
    # Create agent_knowledgebases table
    op.create_table(
        "agent_knowledgebases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledgebase_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledgebase_id"], ["knowledgebases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "knowledgebase_id", name="uq_agent_kb"),
    )
    op.create_index(op.f("ix_agent_knowledgebases_agent_id"), "agent_knowledgebases", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_knowledgebases_knowledgebase_id"), "agent_knowledgebases", ["knowledgebase_id"], unique=False)
    op.create_index("ix_agent_kb_agent_priority", "agent_knowledgebases", ["agent_id", "priority"], unique=False)

    
    # ========================================================================
    # VARIABLE AND SECRET TABLES
    # ========================================================================
    
    # Create variables table
    op.create_table(
        "variables",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.String(length=50), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("value_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("scope IN ('global', 'workspace', 'user', 'agent')", name="check_variable_scope_valid"),
        sa.CheckConstraint("value_type IN ('string', 'number', 'boolean', 'json')", name="check_variable_type_valid"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "scope", "scope_id", name="uq_variable_scope"),
    )
    op.create_index(op.f("ix_variables_deleted_at"), "variables", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_variables_is_secret"), "variables", ["is_secret"], unique=False)
    op.create_index(op.f("ix_variables_name"), "variables", ["name"], unique=False)
    op.create_index(op.f("ix_variables_scope"), "variables", ["scope"], unique=False)
    op.create_index(op.f("ix_variables_scope_id"), "variables", ["scope_id"], unique=False)
    op.create_index("ix_variables_scope_id", "variables", ["scope", "scope_id"], unique=False)
    
    # Create secrets table
    op.create_table(
        "secrets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variable_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("encryption_key_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["variable_id"], ["variables.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_secrets_variable_id"), "secrets", ["variable_id"], unique=True)

    
    # ========================================================================
    # EXECUTION TABLES
    # ========================================================================
    
    # Create agent_executions table
    op.create_table(
        "agent_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("execution_context", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.CheckConstraint("status IN ('running', 'completed', 'failed', 'timeout', 'cancelled')", name="check_agent_execution_status_valid"),
        sa.CheckConstraint("duration_ms >= 0", name="check_agent_duration_positive"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_executions_agent_id"), "agent_executions", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_executions_session_id"), "agent_executions", ["session_id"], unique=False)
    op.create_index(op.f("ix_agent_executions_started_at"), "agent_executions", ["started_at"], unique=False)
    op.create_index(op.f("ix_agent_executions_status"), "agent_executions", ["status"], unique=False)
    op.create_index(op.f("ix_agent_executions_user_id"), "agent_executions", ["user_id"], unique=False)
    op.create_index("ix_agent_executions_agent_started", "agent_executions", ["agent_id", "started_at"], unique=False)
    op.create_index("ix_agent_executions_user_status", "agent_executions", ["user_id", "status"], unique=False)
    op.create_index("ix_agent_executions_status_started", "agent_executions", ["status", "started_at"], unique=False)
    
    # Create execution_steps table
    op.create_table(
        "execution_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("step_metadata", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.CheckConstraint("step_number >= 0", name="check_step_number_positive"),
        sa.ForeignKeyConstraint(["execution_id"], ["agent_executions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_steps_execution_id"), "execution_steps", ["execution_id"], unique=False)
    op.create_index(op.f("ix_execution_steps_timestamp"), "execution_steps", ["timestamp"], unique=False)
    op.create_index("ix_execution_steps_execution_number", "execution_steps", ["execution_id", "step_number"], unique=False)
    op.create_index("ix_execution_steps_execution_timestamp", "execution_steps", ["execution_id", "timestamp"], unique=False)
    
    # Create execution_metrics table
    op.create_table(
        "execution_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("llm_call_count", sa.Integer(), nullable=True),
        sa.Column("llm_total_tokens", sa.Integer(), nullable=True),
        sa.Column("llm_prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("llm_completion_tokens", sa.Integer(), nullable=True),
        sa.Column("tool_call_count", sa.Integer(), nullable=True),
        sa.Column("tool_total_duration_ms", sa.Integer(), nullable=True),
        sa.Column("cache_hit_count", sa.Integer(), nullable=True),
        sa.Column("cache_miss_count", sa.Integer(), nullable=True),
        sa.CheckConstraint("llm_call_count >= 0", name="check_llm_call_count_positive"),
        sa.CheckConstraint("llm_total_tokens >= 0", name="check_llm_tokens_positive"),
        sa.CheckConstraint("tool_call_count >= 0", name="check_tool_call_count_positive"),
        sa.CheckConstraint("tool_total_duration_ms >= 0", name="check_tool_duration_positive"),
        sa.CheckConstraint("cache_hit_count >= 0", name="check_cache_hit_positive"),
        sa.CheckConstraint("cache_miss_count >= 0", name="check_cache_miss_positive"),
        sa.ForeignKeyConstraint(["execution_id"], ["agent_executions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_metrics_execution_id"), "execution_metrics", ["execution_id"], unique=True)
    
    # Create execution_schedules table
    op.create_table(
        "execution_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cron_expression", sa.String(length=100), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("last_execution_at", sa.DateTime(), nullable=True),
        sa.Column("next_execution_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_schedules_agent_id"), "execution_schedules", ["agent_id"], unique=False)
    op.create_index(op.f("ix_execution_schedules_is_active"), "execution_schedules", ["is_active"], unique=False)
    op.create_index(op.f("ix_execution_schedules_next_execution_at"), "execution_schedules", ["next_execution_at"], unique=False)
    op.create_index(op.f("ix_execution_schedules_user_id"), "execution_schedules", ["user_id"], unique=False)
    op.create_index("ix_execution_schedules_agent_active", "execution_schedules", ["agent_id", "is_active"], unique=False)
    op.create_index("ix_execution_schedules_next_execution", "execution_schedules", ["is_active", "next_execution_at"], unique=False)

    
    # ========================================================================
    # PERMISSION AND AUDIT TABLES
    # ========================================================================
    
    # Create permissions table
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("resource_type IN ('agent', 'block', 'workflow', 'knowledgebase')", name="check_permission_resource_type_valid"),
        sa.CheckConstraint("action IN ('read', 'write', 'execute', 'delete', 'share', 'admin')", name="check_permission_action_valid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "resource_type", "resource_id", "action", name="uq_permission"),
    )
    op.create_index(op.f("ix_permissions_resource_id"), "permissions", ["resource_id"], unique=False)
    op.create_index(op.f("ix_permissions_resource_type"), "permissions", ["resource_type"], unique=False)
    op.create_index(op.f("ix_permissions_user_id"), "permissions", ["user_id"], unique=False)
    op.create_index("ix_permissions_resource", "permissions", ["resource_type", "resource_id"], unique=False)
    op.create_index("ix_permissions_user_resource", "permissions", ["user_id", "resource_type", "resource_id"], unique=False)
    
    # Create resource_shares table
    op.create_table(
        "resource_shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("share_token", sa.String(length=255), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("resource_type IN ('agent', 'block', 'workflow', 'knowledgebase')", name="check_share_resource_type_valid"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resource_shares_created_by"), "resource_shares", ["created_by"], unique=False)
    op.create_index(op.f("ix_resource_shares_expires_at"), "resource_shares", ["expires_at"], unique=False)
    op.create_index(op.f("ix_resource_shares_resource_id"), "resource_shares", ["resource_id"], unique=False)
    op.create_index(op.f("ix_resource_shares_resource_type"), "resource_shares", ["resource_type"], unique=False)
    op.create_index(op.f("ix_resource_shares_share_token"), "resource_shares", ["share_token"], unique=True)
    op.create_index("ix_resource_shares_resource", "resource_shares", ["resource_type", "resource_id"], unique=False)
    
    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_timestamp"), "audit_logs", ["timestamp"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index("ix_audit_logs_user_timestamp", "audit_logs", ["user_id", "timestamp"], unique=False)
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"], unique=False)
    op.create_index("ix_audit_logs_action_timestamp", "audit_logs", ["action", "timestamp"], unique=False)


def downgrade() -> None:
    """Drop Agent Builder tables."""
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table("audit_logs")
    op.drop_table("resource_shares")
    op.drop_table("permissions")
    op.drop_table("execution_schedules")
    op.drop_table("execution_metrics")
    op.drop_table("execution_steps")
    op.drop_table("agent_executions")
    op.drop_table("secrets")
    op.drop_table("variables")
    op.drop_table("agent_knowledgebases")
    op.drop_table("knowledgebase_versions")
    op.drop_table("knowledgebase_documents")
    op.drop_table("knowledgebases")
    op.drop_table("workflow_executions")
    op.drop_table("workflow_edges")
    op.drop_table("workflow_nodes")
    op.drop_table("workflows")
    op.drop_table("block_test_cases")
    op.drop_table("block_dependencies")
    op.drop_table("block_versions")
    op.drop_table("blocks")
    op.drop_table("agent_tools")
    op.drop_table("tools")
    op.drop_table("prompt_template_versions")
    op.drop_table("agent_versions")
    op.drop_table("agents")
    op.drop_table("prompt_templates")
    op.drop_table("agent_templates")
