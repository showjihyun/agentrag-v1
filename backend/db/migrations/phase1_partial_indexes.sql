-- Phase 1: Partial Indexes for Performance Optimization
-- These indexes reduce index size and improve query performance by indexing only relevant rows

-- ============================================================================
-- DOCUMENTS TABLE PARTIAL INDEXES
-- ============================================================================

-- Index for active documents only (excludes archived)
-- Use case: Most queries filter out archived documents
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_active_user_uploaded 
ON documents (user_id, uploaded_at DESC) 
WHERE status != 'archived';

COMMENT ON INDEX ix_documents_active_user_uploaded IS 
'Partial index for active documents, excludes archived. Used for document listing.';

-- Index for failed documents (for error analysis)
-- Use case: Admin dashboard showing failed uploads
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_failed 
ON documents (user_id, processing_completed_at DESC) 
WHERE status = 'failed';

COMMENT ON INDEX ix_documents_failed IS 
'Partial index for failed documents. Used for error analysis and retry operations.';

-- Index for pending/processing documents (for status monitoring)
-- Use case: Background job monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_processing 
ON documents (processing_started_at DESC) 
WHERE status IN ('pending', 'processing');

COMMENT ON INDEX ix_documents_processing IS 
'Partial index for documents being processed. Used for job queue monitoring.';

-- ============================================================================
-- MESSAGES TABLE PARTIAL INDEXES
-- ============================================================================

-- Index for recent messages only (last 30 days)
-- Use case: Most queries focus on recent conversation history
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_recent 
ON messages (user_id, created_at DESC) 
WHERE created_at > NOW() - INTERVAL '30 days';

COMMENT ON INDEX ix_messages_recent IS 
'Partial index for recent messages (30 days). Reduces index size significantly.';

-- Index for assistant messages with low confidence (for quality improvement)
-- Use case: Identifying responses that need improvement
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_low_confidence 
ON messages (user_id, confidence_score, created_at DESC) 
WHERE role = 'assistant' AND confidence_score < 0.5;

COMMENT ON INDEX ix_messages_low_confidence IS 
'Partial index for low-confidence assistant responses. Used for quality analysis.';

-- Index for cached responses (for cache hit analysis)
-- Use case: Cache performance monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_cache_hits 
ON messages (user_id, cache_match_type, created_at DESC) 
WHERE cache_hit = true;

COMMENT ON INDEX ix_messages_cache_hits IS 
'Partial index for cached responses. Used for cache performance analysis.';

-- ============================================================================
-- SESSIONS TABLE PARTIAL INDEXES
-- ============================================================================

-- Index for active sessions (with recent activity)
-- Use case: Active conversation monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sessions_active 
ON sessions (user_id, last_message_at DESC) 
WHERE last_message_at > NOW() - INTERVAL '7 days';

COMMENT ON INDEX ix_sessions_active IS 
'Partial index for active sessions (7 days). Used for active user monitoring.';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify indexes were created
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE 'ix_%_active%' 
    OR indexname LIKE 'ix_%_failed%'
    OR indexname LIKE 'ix_%_recent%'
    OR indexname LIKE 'ix_%_processing%'
    OR indexname LIKE 'ix_%_low_confidence%'
    OR indexname LIKE 'ix_%_cache_hits%';
    
    RAISE NOTICE 'Phase 1 partial indexes created: %', index_count;
END $$;

-- Show index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND (
    indexname LIKE 'ix_%_active%' 
    OR indexname LIKE 'ix_%_failed%'
    OR indexname LIKE 'ix_%_recent%'
    OR indexname LIKE 'ix_%_processing%'
    OR indexname LIKE 'ix_%_low_confidence%'
    OR indexname LIKE 'ix_%_cache_hits%'
)
ORDER BY pg_relation_size(indexrelid) DESC;
