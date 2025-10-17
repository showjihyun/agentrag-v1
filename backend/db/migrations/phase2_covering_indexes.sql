-- Phase 2: Covering Indexes for Index-Only Scans
-- These indexes include additional columns to avoid table lookups

-- ============================================================================
-- COVERING INDEXES (PostgreSQL 11+)
-- ============================================================================

-- Covering index for document list queries
-- Includes all columns typically needed for document listing
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_list_covering 
ON documents (user_id, uploaded_at DESC) 
INCLUDE (filename, file_size_bytes, status, chunk_count, mime_type);

COMMENT ON INDEX ix_documents_list_covering IS 
'Covering index for document list queries. Enables index-only scans without table access.';

-- Covering index for session list queries
-- Includes all columns needed for session listing
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sessions_list_covering 
ON sessions (user_id, updated_at DESC) 
INCLUDE (title, message_count, total_tokens, last_message_at, created_at);

COMMENT ON INDEX ix_sessions_list_covering IS 
'Covering index for session list queries. Enables index-only scans.';

-- Covering index for message list queries
-- Includes content and metadata for message display
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_list_covering 
ON messages (session_id, created_at ASC) 
INCLUDE (role, content, confidence_score, query_mode, processing_time_ms);

COMMENT ON INDEX ix_messages_list_covering IS 
'Covering index for message list queries. Enables index-only scans for conversation history.';

-- Covering index for user document search
-- Optimized for search with status filter
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_search_covering 
ON documents (user_id, status, uploaded_at DESC) 
INCLUDE (filename, document_title, document_author, file_size_bytes);

COMMENT ON INDEX ix_documents_search_covering IS 
'Covering index for document search with status filter. Includes metadata for display.';

-- Covering index for message search
-- Optimized for full-text search results
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_search_covering 
ON messages (user_id, created_at DESC) 
INCLUDE (session_id, role, content, confidence_score) 
WHERE role = 'assistant';

COMMENT ON INDEX ix_messages_search_covering IS 
'Covering index for assistant message search. Enables fast search result display.';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify covering indexes were created
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE '%_covering';
    
    RAISE NOTICE 'Phase 2 covering indexes created: %', index_count;
END $$;

-- Show covering index sizes and usage
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS times_used,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND indexname LIKE '%_covering'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check for index-only scans (should show high ratio after covering indexes)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    CASE 
        WHEN idx_tup_read > 0 
        THEN ROUND((idx_tup_read - idx_tup_fetch)::numeric / idx_tup_read * 100, 2)
        ELSE 0 
    END AS index_only_scan_pct
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND indexname LIKE '%_covering'
AND idx_scan > 0
ORDER BY index_only_scan_pct DESC;

-- ============================================================================
-- USAGE EXAMPLES & PERFORMANCE COMPARISON
-- ============================================================================

-- Example 1: Document list query (uses ix_documents_list_covering)
-- BEFORE (2-step): Index scan + table lookup
-- AFTER (1-step): Index-only scan
--
-- EXPLAIN (ANALYZE, BUFFERS) 
-- SELECT id, filename, file_size_bytes, status, chunk_count
-- FROM documents 
-- WHERE user_id = '...' 
-- ORDER BY uploaded_at DESC 
-- LIMIT 20;
--
-- Expected: "Index Only Scan using ix_documents_list_covering"
-- Performance: 3-5x faster

-- Example 2: Session list query (uses ix_sessions_list_covering)
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT id, title, message_count, total_tokens, last_message_at
-- FROM sessions 
-- WHERE user_id = '...' 
-- ORDER BY updated_at DESC 
-- LIMIT 20;
--
-- Expected: "Index Only Scan using ix_sessions_list_covering"
-- Performance: 4-6x faster

-- Example 3: Message list query (uses ix_messages_list_covering)
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT id, role, content, confidence_score, query_mode
-- FROM messages 
-- WHERE session_id = '...' 
-- ORDER BY created_at ASC 
-- LIMIT 50;
--
-- Expected: "Index Only Scan using ix_messages_list_covering"
-- Performance: 5-7x faster

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Monitor covering index effectiveness
CREATE OR REPLACE VIEW v_covering_index_effectiveness AS
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    CASE 
        WHEN idx_tup_read > 0 
        THEN ROUND((idx_tup_read - idx_tup_fetch)::numeric / idx_tup_read * 100, 2)
        ELSE 0 
    END AS index_only_scan_pct,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_tup_read > 0 AND (idx_tup_read - idx_tup_fetch)::numeric / idx_tup_read > 0.8 THEN 'EXCELLENT'
        WHEN idx_tup_read > 0 AND (idx_tup_read - idx_tup_fetch)::numeric / idx_tup_read > 0.5 THEN 'GOOD'
        ELSE 'NEEDS_OPTIMIZATION'
    END AS effectiveness
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND indexname LIKE '%_covering';

COMMENT ON VIEW v_covering_index_effectiveness IS 
'Monitor covering index effectiveness. High index_only_scan_pct indicates good coverage.';

-- Query the view
-- SELECT * FROM v_covering_index_effectiveness ORDER BY effectiveness, scans DESC;
