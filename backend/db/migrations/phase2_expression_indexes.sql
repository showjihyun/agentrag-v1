-- Phase 2: Expression Indexes for Advanced Query Optimization
-- These indexes enable efficient queries on computed expressions

-- ============================================================================
-- EXPRESSION INDEXES
-- ============================================================================

-- Case-insensitive filename search
-- Use case: Search documents by filename regardless of case
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_filename_lower 
ON documents (user_id, LOWER(filename));

COMMENT ON INDEX ix_documents_filename_lower IS 
'Expression index for case-insensitive filename search. Use with LOWER(filename) in queries.';

-- Date-based aggregation for documents
-- Use case: Daily/monthly statistics and reports
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_date 
ON documents (user_id, DATE(uploaded_at));

COMMENT ON INDEX ix_documents_date IS 
'Expression index for date-based document aggregation. Use with DATE(uploaded_at) in queries.';

-- Date-based aggregation for messages
-- Use case: Daily conversation statistics
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_date 
ON messages (user_id, DATE(created_at));

COMMENT ON INDEX ix_messages_date IS 
'Expression index for date-based message aggregation. Use with DATE(created_at) in queries.';

-- Year-month aggregation for documents (for monthly reports)
-- Use case: Monthly upload statistics
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_year_month 
ON documents (user_id, EXTRACT(YEAR FROM uploaded_at), EXTRACT(MONTH FROM uploaded_at));

COMMENT ON INDEX ix_documents_year_month IS 
'Expression index for year-month aggregation. Use with EXTRACT(YEAR/MONTH FROM uploaded_at).';

-- Confidence score buckets for analysis
-- Use case: Grouping messages by confidence ranges
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_messages_confidence_bucket 
ON messages (user_id, 
    CASE 
        WHEN confidence_score >= 0.8 THEN 'high'
        WHEN confidence_score >= 0.5 THEN 'medium'
        ELSE 'low'
    END
) WHERE role = 'assistant';

COMMENT ON INDEX ix_messages_confidence_bucket IS 
'Expression index for confidence score buckets (high/medium/low). Used for quality analysis.';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify expression indexes were created
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND (
        indexname LIKE '%_lower' 
        OR indexname LIKE '%_date'
        OR indexname LIKE '%_year_month'
        OR indexname LIKE '%_confidence_bucket'
    );
    
    RAISE NOTICE 'Phase 2 expression indexes created: %', index_count;
END $$;

-- Show expression index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS times_used
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND (
    indexname LIKE '%_lower' 
    OR indexname LIKE '%_date'
    OR indexname LIKE '%_year_month'
    OR indexname LIKE '%_confidence_bucket'
)
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Case-insensitive filename search (uses ix_documents_filename_lower)
-- SELECT * FROM documents 
-- WHERE user_id = '...' AND LOWER(filename) LIKE '%report%';

-- Example 2: Daily document count (uses ix_documents_date)
-- SELECT DATE(uploaded_at) as date, COUNT(*) 
-- FROM documents 
-- WHERE user_id = '...' 
-- GROUP BY DATE(uploaded_at);

-- Example 3: Monthly upload statistics (uses ix_documents_year_month)
-- SELECT 
--     EXTRACT(YEAR FROM uploaded_at) as year,
--     EXTRACT(MONTH FROM uploaded_at) as month,
--     COUNT(*) as uploads
-- FROM documents 
-- WHERE user_id = '...'
-- GROUP BY year, month;

-- Example 4: Confidence bucket analysis (uses ix_messages_confidence_bucket)
-- SELECT 
--     CASE 
--         WHEN confidence_score >= 0.8 THEN 'high'
--         WHEN confidence_score >= 0.5 THEN 'medium'
--         ELSE 'low'
--     END as confidence_bucket,
--     COUNT(*) as count
-- FROM messages 
-- WHERE user_id = '...' AND role = 'assistant'
-- GROUP BY confidence_bucket;
