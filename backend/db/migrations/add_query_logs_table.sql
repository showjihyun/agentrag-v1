-- Migration: Add query_logs table for monitoring
-- Date: 2025-01-18
-- Description: Creates query_logs table to track query execution for monitoring and analytics

-- Create query_logs table
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    query_mode VARCHAR(50),
    response_time_ms FLOAT,
    confidence_score FLOAT,
    query_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS ix_query_logs_created_at ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS ix_query_logs_query_mode ON query_logs(query_mode);
CREATE INDEX IF NOT EXISTS ix_query_logs_confidence_score ON query_logs(confidence_score);

-- Add comments
COMMENT ON TABLE query_logs IS 'Query execution logs for monitoring and analytics';
COMMENT ON COLUMN query_logs.query_text IS 'The query text submitted by user';
COMMENT ON COLUMN query_logs.query_mode IS 'Query execution mode (fast, balanced, deep)';
COMMENT ON COLUMN query_logs.response_time_ms IS 'Response time in milliseconds';
COMMENT ON COLUMN query_logs.confidence_score IS 'Confidence score of the response (0-1)';
COMMENT ON COLUMN query_logs.query_metadata IS 'Additional metadata (search type, complexity, etc.)';
