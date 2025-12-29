-- Database Optimization Migration Script
-- Implements high-priority recommendations from DATABASE_REVIEW.md
-- Phase 1: Immediate Performance Improvements

-- ============================================================================
-- ENHANCED INDEXING OPTIMIZATIONS
-- ============================================================================

-- Partial indexes for active records only (better performance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_workflows_active_user 
ON workflows (user_id, created_at DESC) 
WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_agents_active_public 
ON agents (is_public, created_at DESC) 
WHERE deleted_at IS NULL AND agent_type = 'custom';

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_blocks_active_user_type 
ON blocks (user_id, block_type, created_at DESC) 
WHERE is_public = true;

-- Covering indexes for common dashboard queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_workflow_executions_covering 
ON workflow_executions (workflow_id, started_at DESC) 
INCLUDE (status, duration_ms, user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_agent_executions_covering 
ON agent_executions (agent_id, started_at DESC) 
INCLUDE (status, duration_ms, user_id);

-- GIN indexes for JSONB search optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_workflows_graph_gin 
ON workflows USING GIN (graph_definition);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_agent_config_gin 
ON agents USING GIN (configuration);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_blocks_config_gin 
ON blocks USING GIN (configuration);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_workflows_fulltext 
ON workflows USING GIN (to_tsvector('english', name || ' ' || COALESCE(description, '')));

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_agents_fulltext 
ON agents USING GIN (to_tsvector('english', name || ' ' || COALESCE(description, '')));

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_blocks_fulltext 
ON blocks USING GIN (to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- ============================================================================
-- ADVANCED CONSTRAINT MANAGEMENT
-- ============================================================================

-- Add more sophisticated constraints for data integrity
ALTER TABLE workflow_executions 
ADD CONSTRAINT IF NOT EXISTS check_execution_timing 
CHECK (completed_at IS NULL OR completed_at >= started_at);

ALTER TABLE workflow_executions 
ADD CONSTRAINT IF NOT EXISTS check_duration_consistency 
CHECK (
    (completed_at IS NULL AND duration_ms IS NULL) OR 
    (completed_at IS NOT NULL AND duration_ms IS NOT NULL)
);

ALTER TABLE agent_executions 
ADD CONSTRAINT IF NOT EXISTS check_agent_execution_timing 
CHECK (completed_at IS NULL OR completed_at >= started_at);

ALTER TABLE agent_executions 
ADD CONSTRAINT IF NOT EXISTS check_agent_duration_consistency 
CHECK (
    (completed_at IS NULL AND duration_ms IS NULL) OR 
    (completed_at IS NOT NULL AND duration_ms IS NOT NULL)
);

-- Conditional constraints for better data integrity
ALTER TABLE agents 
ADD CONSTRAINT IF NOT EXISTS check_public_agent_description 
CHECK (NOT is_public OR (is_public AND description IS NOT NULL));

ALTER TABLE workflows 
ADD CONSTRAINT IF NOT EXISTS check_public_workflow_description 
CHECK (NOT is_public OR (is_public AND description IS NOT NULL));

-- ============================================================================
-- ENHANCED DATA TYPES
-- ============================================================================

-- Use more specific data types for better performance
-- Note: These changes require careful migration in production

-- Create enum types for better performance and data integrity
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'execution_status') THEN
        CREATE TYPE execution_status AS ENUM (
            'pending', 'running', 'completed', 'failed', 'timeout', 'cancelled'
        );
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agent_type_enum') THEN
        CREATE TYPE agent_type_enum AS ENUM (
            'custom', 'template_based'
        );
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'block_type_enum') THEN
        CREATE TYPE block_type_enum AS ENUM (
            'llm', 'tool', 'logic', 'composite'
        );
    END IF;
END $$;

-- ============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================================================

-- Materialized view for dashboard analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS workflow_analytics AS
SELECT 
    w.user_id,
    COUNT(*) as total_workflows,
    COUNT(*) FILTER (WHERE w.is_public) as public_workflows,
    AVG(we.duration_ms) as avg_execution_time,
    COUNT(we.id) as total_executions,
    COUNT(we.id) FILTER (WHERE we.status = 'completed') as successful_executions,
    COUNT(we.id) FILTER (WHERE we.status = 'failed') as failed_executions,
    MAX(w.updated_at) as last_workflow_update,
    MAX(we.started_at) as last_execution
FROM workflows w
LEFT JOIN workflow_executions we ON w.id = we.workflow_id
WHERE w.deleted_at IS NULL
GROUP BY w.user_id;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX IF NOT EXISTS ix_workflow_analytics_user 
ON workflow_analytics (user_id);

-- Agent analytics materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_analytics AS
SELECT 
    a.user_id,
    COUNT(*) as total_agents,
    COUNT(*) FILTER (WHERE a.is_public) as public_agents,
    AVG(ae.duration_ms) as avg_execution_time,
    COUNT(ae.id) as total_executions,
    COUNT(ae.id) FILTER (WHERE ae.status = 'completed') as successful_executions,
    COUNT(ae.id) FILTER (WHERE ae.status = 'failed') as failed_executions,
    MAX(a.updated_at) as last_agent_update,
    MAX(ae.started_at) as last_execution
FROM agents a
LEFT JOIN agent_executions ae ON a.id = ae.agent_id
WHERE a.deleted_at IS NULL
GROUP BY a.user_id;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX IF NOT EXISTS ix_agent_analytics_user 
ON agent_analytics (user_id);

-- ============================================================================
-- PERFORMANCE MONITORING VIEWS
-- ============================================================================

-- Slow query monitoring view
CREATE OR REPLACE VIEW slow_queries AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Index usage statistics view
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE 
        WHEN idx_scan = 0 THEN 'Unused'
        WHEN idx_scan < 100 THEN 'Low Usage'
        WHEN idx_scan < 1000 THEN 'Medium Usage'
        ELSE 'High Usage'
    END as usage_category
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Table size monitoring view
CREATE OR REPLACE VIEW table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- AUTOMATED FUNCTIONS
-- ============================================================================

-- Function to refresh analytics materialized views
CREATE OR REPLACE FUNCTION refresh_analytics()
RETURNS void AS $
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY workflow_analytics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY agent_analytics;
    
    -- Log refresh
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('refresh_analytics', 'system', '{"views": ["workflow_analytics", "agent_analytics"]}', NOW());
END;
$ LANGUAGE plpgsql;

-- Function to update workflow statistics in real-time
CREATE OR REPLACE FUNCTION update_workflow_stats()
RETURNS TRIGGER AS $
BEGIN
    -- Only process workflow executions
    IF TG_TABLE_NAME != 'workflow_executions' THEN
        RETURN COALESCE(NEW, OLD);
    END IF;
    
    IF TG_OP = 'INSERT' THEN
        -- Update execution count in workflow_execution_stats
        INSERT INTO workflow_execution_stats (workflow_id, user_id, date, execution_count)
        VALUES (NEW.workflow_id, NEW.user_id, DATE(NEW.started_at), 1)
        ON CONFLICT (workflow_id, user_id, date) 
        DO UPDATE SET execution_count = workflow_execution_stats.execution_count + 1;
        
    ELSIF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        -- Update success/failure counts
        UPDATE workflow_execution_stats 
        SET 
            success_count = success_count + CASE WHEN NEW.status = 'completed' THEN 1 ELSE 0 END,
            failed_count = failed_count + CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
            avg_duration_ms = CASE 
                WHEN NEW.duration_ms IS NOT NULL THEN 
                    (COALESCE(avg_duration_ms * execution_count, 0) + NEW.duration_ms) / GREATEST(execution_count, 1)
                ELSE avg_duration_ms 
            END
        WHERE workflow_id = NEW.workflow_id 
        AND user_id = NEW.user_id 
        AND date = DATE(NEW.started_at);
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$ LANGUAGE plpgsql;

-- Create trigger for real-time stats updates
DROP TRIGGER IF EXISTS workflow_execution_stats_trigger ON workflow_executions;
CREATE TRIGGER workflow_execution_stats_trigger
    AFTER INSERT OR UPDATE ON workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_workflow_stats();

-- ============================================================================
-- DATABASE HEALTH CHECK FUNCTION
-- ============================================================================

-- Database health check function
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS TABLE(
    metric TEXT,
    value TEXT,
    status TEXT,
    recommendation TEXT
) AS $
BEGIN
    -- Connection count
    RETURN QUERY SELECT 
        'Active Connections'::TEXT,
        (SELECT count(*)::TEXT FROM pg_stat_activity WHERE state = 'active'),
        CASE WHEN (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') > 100 
             THEN 'WARNING' ELSE 'OK' END,
        'Monitor connection pooling'::TEXT;
    
    -- Database size
    RETURN QUERY SELECT 
        'Database Size'::TEXT,
        pg_size_pretty(pg_database_size(current_database())),
        'OK'::TEXT,
        'Regular monitoring'::TEXT;
    
    -- Largest tables
    RETURN QUERY SELECT 
        'Largest Table'::TEXT,
        (SELECT schemaname||'.'||tablename FROM pg_tables 
         WHERE schemaname = 'public' 
         ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 1),
        'INFO'::TEXT,
        'Consider partitioning if > 10GB'::TEXT;
    
    -- Index usage
    RETURN QUERY SELECT 
        'Unused Indexes'::TEXT,
        (SELECT count(*)::TEXT FROM pg_stat_user_indexes WHERE idx_scan = 0),
        CASE WHEN (SELECT count(*) FROM pg_stat_user_indexes WHERE idx_scan = 0) > 5 
             THEN 'WARNING' ELSE 'OK' END,
        'Review and drop unused indexes'::TEXT;
    
    -- Cache hit ratio
    RETURN QUERY SELECT 
        'Cache Hit Ratio'::TEXT,
        (SELECT round(
            sum(heap_blks_hit) / GREATEST(sum(heap_blks_hit + heap_blks_read), 1) * 100, 2
        )::TEXT || '%' FROM pg_statio_user_tables),
        CASE WHEN (SELECT sum(heap_blks_hit) / GREATEST(sum(heap_blks_hit + heap_blks_read), 1) * 100 
                   FROM pg_statio_user_tables) < 95 
             THEN 'WARNING' ELSE 'OK' END,
        'Increase shared_buffers if low'::TEXT;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- CLEANUP AND MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to clean up old execution data
CREATE OR REPLACE FUNCTION cleanup_old_executions(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old workflow executions
    DELETE FROM workflow_executions 
    WHERE started_at < NOW() - (retention_days || ' days')::INTERVAL
    AND status IN ('completed', 'failed', 'cancelled');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete old agent executions
    DELETE FROM agent_executions 
    WHERE started_at < NOW() - (retention_days || ' days')::INTERVAL
    AND status IN ('completed', 'failed', 'cancelled');
    
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    
    -- Log cleanup
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('cleanup_executions', 'system', 
            json_build_object('retention_days', retention_days, 'deleted_count', deleted_count), 
            NOW());
    
    RETURN deleted_count;
END;
$ LANGUAGE plpgsql;

-- Function to vacuum and analyze tables
CREATE OR REPLACE FUNCTION maintenance_vacuum_analyze()
RETURNS void AS $
DECLARE
    table_name TEXT;
BEGIN
    -- Vacuum and analyze key tables
    FOR table_name IN 
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN ('workflows', 'agents', 'workflow_executions', 'agent_executions', 'blocks')
    LOOP
        EXECUTE 'VACUUM ANALYZE ' || quote_ident(table_name);
    END LOOP;
    
    -- Refresh materialized views
    PERFORM refresh_analytics();
    
    -- Log maintenance
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('maintenance_vacuum', 'system', '{"action": "vacuum_analyze_refresh"}', NOW());
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON FUNCTION refresh_analytics() IS 'Refreshes workflow and agent analytics materialized views';
COMMENT ON FUNCTION update_workflow_stats() IS 'Trigger function to update workflow execution statistics in real-time';
COMMENT ON FUNCTION database_health_check() IS 'Returns database health metrics and recommendations';
COMMENT ON FUNCTION cleanup_old_executions(INTEGER) IS 'Cleans up old execution records older than specified days';
COMMENT ON FUNCTION maintenance_vacuum_analyze() IS 'Performs vacuum analyze on key tables and refreshes materialized views';

COMMENT ON MATERIALIZED VIEW workflow_analytics IS 'Aggregated workflow statistics for dashboard performance';
COMMENT ON MATERIALIZED VIEW agent_analytics IS 'Aggregated agent statistics for dashboard performance';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE 'Database optimization migration completed successfully!';
    RAISE NOTICE 'Applied optimizations:';
    RAISE NOTICE '- Enhanced indexing (partial, covering, GIN, full-text)';
    RAISE NOTICE '- Advanced constraints for data integrity';
    RAISE NOTICE '- Materialized views for analytics performance';
    RAISE NOTICE '- Real-time statistics triggers';
    RAISE NOTICE '- Health monitoring and maintenance functions';
    RAISE NOTICE 'Next steps: Run ANALYZE on all tables and monitor performance';
END $$;