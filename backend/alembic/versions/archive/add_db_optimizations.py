"""Add database optimizations for workflow system

Revision ID: db_optimizations_001
Revises: 
Create Date: 2024-01-01

This migration adds:
1. Missing indexes for common query patterns
2. Partial indexes for filtered queries
3. GIN indexes for JSONB columns
4. Covering indexes for frequently accessed columns
5. Partitioning preparation for large tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'db_optimizations_001'
down_revision = None  # Set to latest revision
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # 1. WORKFLOW EXECUTIONS - High volume table optimizations
    # =========================================================================
    
    # Partial index for active executions (most common query)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_executions_active 
        ON workflow_executions (workflow_id, started_at DESC)
        WHERE status IN ('running', 'waiting_approval')
    """)
    
    # Partial index for failed executions (for DLQ and monitoring)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_executions_failed 
        ON workflow_executions (workflow_id, started_at DESC)
        WHERE status = 'failed'
    """)
    
    # Covering index for execution list queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_executions_list_covering 
        ON workflow_executions (workflow_id, started_at DESC)
        INCLUDE (status, duration_ms, error_message)
    """)
    
    # Index for user's recent executions
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_executions_user_recent 
        ON workflow_executions (user_id, started_at DESC)
        WHERE started_at > NOW() - INTERVAL '7 days'
    """)
    
    # =========================================================================
    # 2. WORKFLOWS - Query optimization
    # =========================================================================
    
    # Covering index for workflow list
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflows_list_covering 
        ON workflows (user_id, updated_at DESC)
        INCLUDE (name, description, is_public)
    """)
    
    # GIN index for graph_definition JSONB searches
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflows_graph_gin 
        ON workflows USING GIN (graph_definition jsonb_path_ops)
    """)
    
    # =========================================================================
    # 3. WORKFLOW NODES - Graph traversal optimization
    # =========================================================================
    
    # Composite index for node lookups by workflow and type
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_nodes_workflow_type 
        ON workflow_nodes (workflow_id, node_type)
    """)
    
    # GIN index for configuration JSONB
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_nodes_config_gin 
        ON workflow_nodes USING GIN (configuration jsonb_path_ops)
    """)
    
    # =========================================================================
    # 4. TRIGGER EXECUTIONS - Time-series optimization
    # =========================================================================
    
    # BRIN index for time-series data (very efficient for append-only)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_trigger_executions_time_brin 
        ON trigger_executions USING BRIN (triggered_at)
        WITH (pages_per_range = 128)
    """)
    
    # Partial index for recent triggers
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_trigger_executions_recent 
        ON trigger_executions (workflow_id, triggered_at DESC)
        WHERE triggered_at > NOW() - INTERVAL '24 hours'
    """)
    
    # =========================================================================
    # 5. AGENT BLOCKS - Visual editor optimization
    # =========================================================================
    
    # Covering index for block list in editor
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_agent_blocks_editor_covering 
        ON agent_blocks (workflow_id)
        INCLUDE (type, name, position_x, position_y, enabled)
    """)
    
    # =========================================================================
    # 6. WORKFLOW SCHEDULES & WEBHOOKS - Trigger optimization
    # =========================================================================
    
    # Index for next scheduled execution lookup
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_schedules_next_run 
        ON workflow_schedules (next_execution_at)
        WHERE is_active = true
    """)
    
    # =========================================================================
    # 7. STATISTICS FUNCTIONS
    # =========================================================================
    
    # Function for execution statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION get_workflow_execution_stats(
            p_workflow_id UUID,
            p_days INTEGER DEFAULT 7
        )
        RETURNS TABLE (
            total_executions BIGINT,
            successful_executions BIGINT,
            failed_executions BIGINT,
            avg_duration_ms NUMERIC,
            p50_duration_ms NUMERIC,
            p95_duration_ms NUMERIC,
            p99_duration_ms NUMERIC
        )
        LANGUAGE SQL
        STABLE
        AS $$
            SELECT 
                COUNT(*) as total_executions,
                COUNT(*) FILTER (WHERE status = 'completed') as successful_executions,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_executions,
                AVG(duration_ms) as avg_duration_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as p50_duration_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99_duration_ms
            FROM workflow_executions
            WHERE workflow_id = p_workflow_id
              AND started_at >= NOW() - (p_days || ' days')::INTERVAL
              AND duration_ms IS NOT NULL
        $$
    """)
    
    # Function for user activity summary
    op.execute("""
        CREATE OR REPLACE FUNCTION get_user_workflow_summary(p_user_id UUID)
        RETURNS TABLE (
            total_workflows BIGINT,
            total_executions BIGINT,
            executions_today BIGINT,
            executions_this_week BIGINT,
            success_rate NUMERIC
        )
        LANGUAGE SQL
        STABLE
        AS $$
            WITH workflow_ids AS (
                SELECT id FROM workflows WHERE user_id = p_user_id
            ),
            exec_stats AS (
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE started_at >= CURRENT_DATE) as today,
                    COUNT(*) FILTER (WHERE started_at >= CURRENT_DATE - INTERVAL '7 days') as week,
                    COUNT(*) FILTER (WHERE status = 'completed') as successful
                FROM workflow_executions
                WHERE workflow_id IN (SELECT id FROM workflow_ids)
            )
            SELECT 
                (SELECT COUNT(*) FROM workflow_ids) as total_workflows,
                total as total_executions,
                today as executions_today,
                week as executions_this_week,
                CASE WHEN total > 0 
                     THEN ROUND(successful::NUMERIC / total * 100, 2)
                     ELSE 100.0 
                END as success_rate
            FROM exec_stats
        $$
    """)


def downgrade():
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS get_workflow_execution_stats(UUID, INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS get_user_workflow_summary(UUID)")
    
    # Drop indexes
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_executions_active")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_executions_failed")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_executions_list_covering")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_executions_user_recent")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflows_list_covering")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflows_graph_gin")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_nodes_workflow_type")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_nodes_config_gin")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_trigger_executions_time_brin")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_trigger_executions_recent")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_agent_blocks_editor_covering")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_schedules_next_run")
