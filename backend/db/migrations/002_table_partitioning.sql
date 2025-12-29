-- Table Partitioning Migration Script
-- Implements partitioning strategy for large tables from DATABASE_REVIEW.md
-- Phase 2: Advanced Performance Optimizations

-- ============================================================================
-- WORKFLOW EXECUTIONS PARTITIONING
-- ============================================================================

-- Create partitioned table for workflow_executions (by month)
-- Note: This requires careful migration in production with downtime

-- Step 1: Create new partitioned table
CREATE TABLE IF NOT EXISTS workflow_executions_partitioned (
    LIKE workflow_executions INCLUDING ALL
) PARTITION BY RANGE (started_at);

-- Step 2: Create partitions for current and future months
DO $$ 
DECLARE
    start_date date;
    end_date date;
    table_name text;
    i integer;
BEGIN
    -- Create partitions for last 6 months and next 6 months
    FOR i IN -6..6 LOOP
        start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::interval;
        end_date := start_date + interval '1 month';
        table_name := 'workflow_executions_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF workflow_executions_partitioned 
             FOR VALUES FROM (%L) TO (%L)',
            table_name, start_date, end_date
        );
        
        -- Add indexes to each partition
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (workflow_id, started_at DESC)',
            'ix_' || table_name || '_workflow_started', table_name
        );
        
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (user_id, status)',
            'ix_' || table_name || '_user_status', table_name
        );
    END LOOP;
END $$;

-- ============================================================================
-- AUDIT LOGS PARTITIONING
-- ============================================================================

-- Create partitioned table for audit_logs (by month)
CREATE TABLE IF NOT EXISTS audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create audit log partitions
DO $$ 
DECLARE
    start_date date;
    end_date date;
    table_name text;
    i integer;
BEGIN
    -- Create partitions for last 12 months and next 3 months
    FOR i IN -12..3 LOOP
        start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::interval;
        end_date := start_date + interval '1 month';
        table_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs_partitioned 
             FOR VALUES FROM (%L) TO (%L)',
            table_name, start_date, end_date
        );
        
        -- Add indexes to each partition
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (user_id, timestamp DESC)',
            'ix_' || table_name || '_user_timestamp', table_name
        );
        
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (action, timestamp DESC)',
            'ix_' || table_name || '_action_timestamp', table_name
        );
    END LOOP;
END $$;

-- ============================================================================
-- AGENT EXECUTIONS PARTITIONING
-- ============================================================================

-- Create partitioned table for agent_executions (by month)
CREATE TABLE IF NOT EXISTS agent_executions_partitioned (
    LIKE agent_executions INCLUDING ALL
) PARTITION BY RANGE (started_at);

-- Create agent execution partitions
DO $$ 
DECLARE
    start_date date;
    end_date date;
    table_name text;
    i integer;
BEGIN
    -- Create partitions for last 6 months and next 6 months
    FOR i IN -6..6 LOOP
        start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::interval;
        end_date := start_date + interval '1 month';
        table_name := 'agent_executions_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF agent_executions_partitioned 
             FOR VALUES FROM (%L) TO (%L)',
            table_name, start_date, end_date
        );
        
        -- Add indexes to each partition
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (agent_id, started_at DESC)',
            'ix_' || table_name || '_agent_started', table_name
        );
        
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (user_id, status)',
            'ix_' || table_name || '_user_status', table_name
        );
    END LOOP;
END $$;

-- ============================================================================
-- AUTOMATIC PARTITION MANAGEMENT
-- ============================================================================

-- Function to create monthly partitions automatically
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $
DECLARE
    start_date date;
    end_date date;
    table_name text;
    partition_tables text[] := ARRAY['workflow_executions_partitioned', 'audit_logs_partitioned', 'agent_executions_partitioned'];
    base_table text;
    i integer;
BEGIN
    -- Create partitions for next 3 months for each partitioned table
    FOREACH base_table IN ARRAY partition_tables LOOP
        FOR i IN 1..3 LOOP
            start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::interval;
            end_date := start_date + interval '1 month';
            
            -- Generate partition table name
            CASE base_table
                WHEN 'workflow_executions_partitioned' THEN
                    table_name := 'workflow_executions_' || to_char(start_date, 'YYYY_MM');
                WHEN 'audit_logs_partitioned' THEN
                    table_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
                WHEN 'agent_executions_partitioned' THEN
                    table_name := 'agent_executions_' || to_char(start_date, 'YYYY_MM');
            END CASE;
            
            -- Create partition if it doesn't exist
            BEGIN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                    table_name, base_table, start_date, end_date
                );
                
                -- Add appropriate indexes based on table type
                IF base_table = 'workflow_executions_partitioned' THEN
                    EXECUTE format('CREATE INDEX %I ON %I (workflow_id, started_at DESC)', 
                                 'ix_' || table_name || '_workflow_started', table_name);
                    EXECUTE format('CREATE INDEX %I ON %I (user_id, status)', 
                                 'ix_' || table_name || '_user_status', table_name);
                ELSIF base_table = 'audit_logs_partitioned' THEN
                    EXECUTE format('CREATE INDEX %I ON %I (user_id, timestamp DESC)', 
                                 'ix_' || table_name || '_user_timestamp', table_name);
                    EXECUTE format('CREATE INDEX %I ON %I (action, timestamp DESC)', 
                                 'ix_' || table_name || '_action_timestamp', table_name);
                ELSIF base_table = 'agent_executions_partitioned' THEN
                    EXECUTE format('CREATE INDEX %I ON %I (agent_id, started_at DESC)', 
                                 'ix_' || table_name || '_agent_started', table_name);
                    EXECUTE format('CREATE INDEX %I ON %I (user_id, status)', 
                                 'ix_' || table_name || '_user_status', table_name);
                END IF;
                
                RAISE NOTICE 'Created partition: %', table_name;
            EXCEPTION
                WHEN duplicate_table THEN
                    -- Partition already exists, skip
                    NULL;
            END;
        END LOOP;
    END LOOP;
    
    -- Log partition creation
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('create_partitions', 'system', 
            json_build_object('tables', partition_tables, 'created_for_months', 3), 
            NOW());
END;
$ LANGUAGE plpgsql;

-- Function to drop old partitions (older than retention period)
CREATE OR REPLACE FUNCTION drop_old_partitions(retention_months INTEGER DEFAULT 12)
RETURNS INTEGER AS $
DECLARE
    cutoff_date date;
    partition_name text;
    dropped_count integer := 0;
    partition_tables text[] := ARRAY['workflow_executions', 'audit_logs', 'agent_executions'];
    base_table text;
BEGIN
    cutoff_date := date_trunc('month', CURRENT_DATE) - (retention_months || ' months')::interval;
    
    -- Find and drop old partitions
    FOR partition_name IN 
        SELECT schemaname||'.'||tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND (
            tablename ~ '^workflow_executions_\d{4}_\d{2}$' OR
            tablename ~ '^audit_logs_\d{4}_\d{2}$' OR
            tablename ~ '^agent_executions_\d{4}_\d{2}$'
        )
        AND to_date(substring(tablename from '\d{4}_\d{2}$'), 'YYYY_MM') < cutoff_date
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || partition_name;
        dropped_count := dropped_count + 1;
        RAISE NOTICE 'Dropped old partition: %', partition_name;
    END LOOP;
    
    -- Log partition cleanup
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('drop_old_partitions', 'system', 
            json_build_object('retention_months', retention_months, 'dropped_count', dropped_count), 
            NOW());
    
    RETURN dropped_count;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- PARTITION MAINTENANCE SCHEDULER
-- ============================================================================

-- Function to perform all partition maintenance tasks
CREATE OR REPLACE FUNCTION partition_maintenance()
RETURNS void AS $
BEGIN
    -- Create new partitions for upcoming months
    PERFORM create_monthly_partitions();
    
    -- Drop old partitions (keep 12 months by default)
    PERFORM drop_old_partitions(12);
    
    -- Update statistics on partitioned tables
    ANALYZE workflow_executions_partitioned;
    ANALYZE audit_logs_partitioned;
    ANALYZE agent_executions_partitioned;
    
    -- Log maintenance completion
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('partition_maintenance', 'system', '{"status": "completed"}', NOW());
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- MIGRATION HELPER FUNCTIONS
-- ============================================================================

-- Function to migrate data from non-partitioned to partitioned tables
-- WARNING: This should be run during maintenance window
CREATE OR REPLACE FUNCTION migrate_to_partitioned_tables()
RETURNS void AS $
DECLARE
    record_count integer;
BEGIN
    RAISE NOTICE 'Starting migration to partitioned tables...';
    
    -- Migrate workflow_executions
    RAISE NOTICE 'Migrating workflow_executions...';
    INSERT INTO workflow_executions_partitioned 
    SELECT * FROM workflow_executions 
    ON CONFLICT DO NOTHING;
    GET DIAGNOSTICS record_count = ROW_COUNT;
    RAISE NOTICE 'Migrated % workflow execution records', record_count;
    
    -- Migrate audit_logs
    RAISE NOTICE 'Migrating audit_logs...';
    INSERT INTO audit_logs_partitioned 
    SELECT * FROM audit_logs 
    ON CONFLICT DO NOTHING;
    GET DIAGNOSTICS record_count = ROW_COUNT;
    RAISE NOTICE 'Migrated % audit log records', record_count;
    
    -- Migrate agent_executions
    RAISE NOTICE 'Migrating agent_executions...';
    INSERT INTO agent_executions_partitioned 
    SELECT * FROM agent_executions 
    ON CONFLICT DO NOTHING;
    GET DIAGNOSTICS record_count = ROW_COUNT;
    RAISE NOTICE 'Migrated % agent execution records', record_count;
    
    RAISE NOTICE 'Migration to partitioned tables completed!';
    
    -- Log migration
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('migrate_to_partitioned', 'system', '{"status": "completed"}', NOW());
END;
$ LANGUAGE plpgsql;

-- Function to switch to partitioned tables (rename tables)
-- WARNING: This requires application downtime
CREATE OR REPLACE FUNCTION switch_to_partitioned_tables()
RETURNS void AS $
BEGIN
    RAISE NOTICE 'Switching to partitioned tables (requires downtime)...';
    
    -- Rename original tables to backup
    ALTER TABLE workflow_executions RENAME TO workflow_executions_backup;
    ALTER TABLE audit_logs RENAME TO audit_logs_backup;
    ALTER TABLE agent_executions RENAME TO agent_executions_backup;
    
    -- Rename partitioned tables to original names
    ALTER TABLE workflow_executions_partitioned RENAME TO workflow_executions;
    ALTER TABLE audit_logs_partitioned RENAME TO audit_logs;
    ALTER TABLE agent_executions_partitioned RENAME TO agent_executions;
    
    RAISE NOTICE 'Successfully switched to partitioned tables!';
    RAISE NOTICE 'Original tables backed up with _backup suffix';
    
    -- Log switch
    INSERT INTO audit_logs (action, resource_type, details, timestamp)
    VALUES ('switch_to_partitioned', 'system', '{"status": "completed"}', NOW());
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- PARTITION MONITORING
-- ============================================================================

-- View to monitor partition sizes and usage
CREATE OR REPLACE VIEW partition_info AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
    CASE 
        WHEN tablename ~ '_\d{4}_\d{2}$' THEN 
            to_date(substring(tablename from '\d{4}_\d{2}$'), 'YYYY_MM')
        ELSE NULL 
    END as partition_date,
    CASE 
        WHEN tablename ~ '^workflow_executions_' THEN 'workflow_executions'
        WHEN tablename ~ '^audit_logs_' THEN 'audit_logs'
        WHEN tablename ~ '^agent_executions_' THEN 'agent_executions'
        ELSE 'other'
    END as table_family
FROM pg_tables 
WHERE schemaname = 'public' 
AND (
    tablename ~ '^workflow_executions_\d{4}_\d{2}$' OR
    tablename ~ '^audit_logs_\d{4}_\d{2}$' OR
    tablename ~ '^agent_executions_\d{4}_\d{2}$'
)
ORDER BY table_family, partition_date DESC;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON FUNCTION create_monthly_partitions() IS 'Creates monthly partitions for the next 3 months';
COMMENT ON FUNCTION drop_old_partitions(INTEGER) IS 'Drops partitions older than specified months (default 12)';
COMMENT ON FUNCTION partition_maintenance() IS 'Performs complete partition maintenance (create new, drop old, analyze)';
COMMENT ON FUNCTION migrate_to_partitioned_tables() IS 'Migrates data from original tables to partitioned versions';
COMMENT ON FUNCTION switch_to_partitioned_tables() IS 'Switches application to use partitioned tables (requires downtime)';

COMMENT ON VIEW partition_info IS 'Monitoring view for partition sizes and dates';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE 'Table partitioning setup completed successfully!';
    RAISE NOTICE 'Created partitioned tables for:';
    RAISE NOTICE '- workflow_executions (by month)';
    RAISE NOTICE '- audit_logs (by month)';
    RAISE NOTICE '- agent_executions (by month)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps for production deployment:';
    RAISE NOTICE '1. Test partitioned tables in staging environment';
    RAISE NOTICE '2. Schedule maintenance window for migration';
    RAISE NOTICE '3. Run migrate_to_partitioned_tables() during maintenance';
    RAISE NOTICE '4. Run switch_to_partitioned_tables() to activate';
    RAISE NOTICE '5. Set up cron job for partition_maintenance()';
    RAISE NOTICE '';
    RAISE NOTICE 'Monitor partition usage with: SELECT * FROM partition_info;';
END $$;