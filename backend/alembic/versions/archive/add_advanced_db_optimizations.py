"""Add advanced database optimizations V2

Revision ID: db_optimizations_002
Revises: db_optimizations_001
Create Date: 2024-11-29

This migration adds:
1. Additional missing indexes
2. Table partitioning preparation
3. Data archiving functions
4. Enhanced statistics functions
5. Maintenance automation
"""

from alembic import op
import sqlalchemy as sa

revision = 'db_optimizations_002'
down_revision = 'db_optimizations_001'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # 1. ADDITIONAL MISSING INDEXES
    # =========================================================================
    
    # User's recent workflows (soft delete aware)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflows_user_updated_active
        ON workflows (user_id, updated_at DESC)
        WHERE deleted_at IS NULL
    """)
    
    # Agent executions by agent
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_agent_executions_agent_started
        ON agent_executions (agent_id, started_at DESC)
    """)
    
    # Session-based execution lookup
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_executions_session
        ON workflow_executions (session_id, started_at DESC)
        WHERE session_id IS NOT NULL
    """)
    
    # Active triggers lookup
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_schedules_active_next
        ON workflow_schedules (next_execution_at ASC)
        WHERE is_active = true
    """)
    
    # Webhook by secret (for validation)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_workflow_webhooks_secret
        ON workflow_webhooks (secret_key)
        WHERE is_active = true
    """)
    
    # Block type filtering
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
        ix_agent_blocks_type_enabled
        ON agent_blocks (workflow_id, type)
        WHERE enabled = true
    """)
    
    # =========================================================================
    # 2. ARCHIVE TABLE AND FUNCTIONS
    # =========================================================================
    
    # Create archive table for old executions
    op.execute("""
        CREATE TABLE IF NOT EXISTS workflow_executions_archive (
            LIKE workflow_executions INCLUDING ALL
        )
    """)
    
    # Add archived_at column to archive table
    op.execute("""
        ALTER TABLE workflow_executions_archive 
        ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP DEFAULT NOW()
    """)
    
    # Archive function
    op.execute("""
        CREATE OR REPLACE FUNCTION archive_old_executions(
            p_retention_days INTEGER DEFAULT 90,
            p_batch_size INTEGER DEFAULT 10000
        )
        RETURNS TABLE (
            archived_count INTEGER,
            execution_time_ms NUMERIC
        )
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_start_time TIMESTAMP;
            v_archived INTEGER := 0;
            v_cutoff_date TIMESTAMP;
        BEGIN
            v_start_time := clock_timestamp();
            v_cutoff_date := NOW() - (p_retention_days || ' days')::INTERVAL;
            
            -- Archive in batches to avoid long locks
            LOOP
                WITH to_archive AS (
                    SELECT id FROM workflow_executions
                    WHERE started_at < v_cutoff_date
                      AND status IN ('completed', 'failed', 'cancelled', 'timeout')
                    LIMIT p_batch_size
                    FOR UPDATE SKIP LOCKED
                ),
                moved AS (
                    DELETE FROM workflow_executions
                    WHERE id IN (SELECT id FROM to_archive)
                    RETURNING *
                )
                INSERT INTO workflow_executions_archive
                SELECT *, NOW() as archived_at FROM moved;
                
                GET DIAGNOSTICS v_archived = ROW_COUNT;
                
                EXIT WHEN v_archived = 0;
                
                -- Commit each batch
                COMMIT;
            END LOOP;
            
            archived_count := v_archived;
            execution_time_ms := EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time)) * 1000;
            
            RETURN NEXT;
        END;
        $$
    """)
    
    # =========================================================================
    # 3. ENHANCED STATISTICS FUNCTIONS
    # =========================================================================
    
    # Hourly execution statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION get_hourly_execution_stats(
            p_workflow_id UUID,
            p_hours INTEGER DEFAULT 24
        )
        RETURNS TABLE (
            hour_bucket TIMESTAMP,
            total_count BIGINT,
            success_count BIGINT,
            failed_count BIGINT,
            avg_duration_ms NUMERIC,
            max_duration_ms NUMERIC
        )
        LANGUAGE SQL
        STABLE
        AS $$
            SELECT 
                DATE_TRUNC('hour', started_at) as hour_bucket,
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE status = 'completed') as success_count,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
                AVG(duration_ms) as avg_duration_ms,
                MAX(duration_ms) as max_duration_ms
            FROM workflow_executions
            WHERE workflow_id = p_workflow_id
              AND started_at >= NOW() - (p_hours || ' hours')::INTERVAL
            GROUP BY DATE_TRUNC('hour', started_at)
            ORDER BY hour_bucket DESC
        $$
    """)
    
    # Node type performance statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION get_node_type_stats(
            p_workflow_id UUID,
            p_days INTEGER DEFAULT 7
        )
        RETURNS TABLE (
            node_type TEXT,
            execution_count BIGINT,
            avg_duration_ms NUMERIC,
            error_count BIGINT,
            error_rate NUMERIC
        )
        LANGUAGE SQL
        STABLE
        AS $$
            WITH node_executions AS (
                SELECT 
                    (jsonb_array_elements(execution_context->'node_results')->>'node_type') as node_type,
                    (jsonb_array_elements(execution_context->'node_results')->>'duration_ms')::NUMERIC as duration_ms,
                    (jsonb_array_elements(execution_context->'node_results')->>'status') as status
                FROM workflow_executions
                WHERE workflow_id = p_workflow_id
                  AND started_at >= NOW() - (p_days || ' days')::INTERVAL
                  AND execution_context IS NOT NULL
            )
            SELECT 
                node_type,
                COUNT(*) as execution_count,
                AVG(duration_ms) as avg_duration_ms,
                COUNT(*) FILTER (WHERE status = 'error') as error_count,
                ROUND(COUNT(*) FILTER (WHERE status = 'error')::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as error_rate
            FROM node_executions
            WHERE node_type IS NOT NULL
            GROUP BY node_type
            ORDER BY execution_count DESC
        $$
    """)
    
    # =========================================================================
    # 4. TABLE SIZE MONITORING FUNCTION
    # =========================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION get_table_sizes()
        RETURNS TABLE (
            table_name TEXT,
            total_size TEXT,
            data_size TEXT,
            index_size TEXT,
            row_count BIGINT
        )
        LANGUAGE SQL
        STABLE
        AS $$
            SELECT 
                relname::TEXT as table_name,
                pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                pg_size_pretty(pg_relation_size(relid)) as data_size,
                pg_size_pretty(pg_indexes_size(relid)) as index_size,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(relid) DESC
        $$
    """)
    
    # =========================================================================
    # 5. INDEX HEALTH CHECK FUNCTION
    # =========================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION get_unused_indexes()
        RETURNS TABLE (
            table_name TEXT,
            index_name TEXT,
            index_size TEXT,
            index_scans BIGINT
        )
        LANGUAGE SQL
        STABLE
        AS $$
            SELECT 
                relname::TEXT as table_name,
                indexrelname::TEXT as index_name,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                idx_scan as index_scans
            FROM pg_stat_user_indexes
            WHERE idx_scan < 50  -- Less than 50 scans
              AND pg_relation_size(indexrelid) > 1024 * 1024  -- Larger than 1MB
            ORDER BY pg_relation_size(indexrelid) DESC
        $$
    """)
    
    # =========================================================================
    # 6. AUTOVACUUM TUNING FOR HIGH-VOLUME TABLES
    # =========================================================================
    
    op.execute("""
        ALTER TABLE workflow_executions SET (
            autovacuum_vacuum_scale_factor = 0.05,
            autovacuum_analyze_scale_factor = 0.02,
            autovacuum_vacuum_cost_delay = 10
        )
    """)
    
    op.execute("""
        ALTER TABLE agent_blocks SET (
            autovacuum_vacuum_scale_factor = 0.1,
            autovacuum_analyze_scale_factor = 0.05
        )
    """)
    
    op.execute("""
        ALTER TABLE workflow_nodes SET (
            autovacuum_vacuum_scale_factor = 0.1,
            autovacuum_analyze_scale_factor = 0.05
        )
    """)
    
    # =========================================================================
    # 7. CLEANUP OLD DATA FUNCTION
    # =========================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_data(
            p_days INTEGER DEFAULT 30
        )
        RETURNS TABLE (
            table_name TEXT,
            deleted_count INTEGER
        )
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_cutoff TIMESTAMP;
            v_count INTEGER;
        BEGIN
            v_cutoff := NOW() - (p_days || ' days')::INTERVAL;
            
            -- Clean old trigger executions
            DELETE FROM trigger_executions
            WHERE triggered_at < v_cutoff;
            GET DIAGNOSTICS v_count = ROW_COUNT;
            table_name := 'trigger_executions';
            deleted_count := v_count;
            RETURN NEXT;
            
            -- Clean old query logs if exists
            BEGIN
                DELETE FROM query_logs
                WHERE created_at < v_cutoff;
                GET DIAGNOSTICS v_count = ROW_COUNT;
                table_name := 'query_logs';
                deleted_count := v_count;
                RETURN NEXT;
            EXCEPTION WHEN undefined_table THEN
                -- Table doesn't exist, skip
            END;
            
            RETURN;
        END;
        $$
    """)


def downgrade():
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS archive_old_executions(INTEGER, INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS get_hourly_execution_stats(UUID, INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS get_node_type_stats(UUID, INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS get_table_sizes()")
    op.execute("DROP FUNCTION IF EXISTS get_unused_indexes()")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_data(INTEGER)")
    
    # Drop archive table
    op.execute("DROP TABLE IF EXISTS workflow_executions_archive")
    
    # Drop indexes
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflows_user_updated_active")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_agent_executions_agent_started")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_executions_session")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_schedules_active_next")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_workflow_webhooks_secret")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_agent_blocks_type_enabled")
    
    # Reset autovacuum settings
    op.execute("ALTER TABLE workflow_executions RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor, autovacuum_vacuum_cost_delay)")
    op.execute("ALTER TABLE agent_blocks RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor)")
    op.execute("ALTER TABLE workflow_nodes RESET (autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor)")
