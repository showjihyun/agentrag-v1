-- Create monitoring statistics tables

-- File Upload Statistics
CREATE TABLE IF NOT EXISTS file_upload_stats (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(255) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_mb FLOAT NOT NULL,
    status VARCHAR(50) NOT NULL,
    processing_time_ms FLOAT,
    error_message VARCHAR(1000),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_file_upload_file_id ON file_upload_stats(file_id);
CREATE INDEX IF NOT EXISTS idx_file_upload_created ON file_upload_stats(created_at);
CREATE INDEX IF NOT EXISTS idx_file_upload_created_status ON file_upload_stats(created_at, status);
CREATE INDEX IF NOT EXISTS idx_file_upload_type ON file_upload_stats(file_type);

-- Embedding Statistics
CREATE TABLE IF NOT EXISTS embedding_stats (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    total_chunks INTEGER NOT NULL,
    chunking_strategy VARCHAR(50) NOT NULL,
    embedding_time_ms FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_embedding_document_id ON embedding_stats(document_id);
CREATE INDEX IF NOT EXISTS idx_embedding_created ON embedding_stats(created_at);
CREATE INDEX IF NOT EXISTS idx_embedding_model ON embedding_stats(embedding_model);

-- Hybrid Search Statistics
CREATE TABLE IF NOT EXISTS hybrid_search_stats (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    search_type VARCHAR(50) NOT NULL,
    query_text VARCHAR(1000),
    results_count INTEGER NOT NULL,
    search_time_ms FLOAT NOT NULL,
    cache_hit INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_session_id ON hybrid_search_stats(session_id);
CREATE INDEX IF NOT EXISTS idx_search_created ON hybrid_search_stats(created_at);
CREATE INDEX IF NOT EXISTS idx_search_created_type ON hybrid_search_stats(created_at, search_type);
CREATE INDEX IF NOT EXISTS idx_search_cache ON hybrid_search_stats(cache_hit);

-- RAG Processing Statistics
CREATE TABLE IF NOT EXISTS rag_processing_stats (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    query_text VARCHAR(1000),
    mode VARCHAR(50) NOT NULL,
    complexity VARCHAR(50),
    response_time_ms FLOAT NOT NULL,
    confidence_score FLOAT,
    success INTEGER DEFAULT 1,
    error_message VARCHAR(1000),
    token_usage JSONB,
    quality_scores JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rag_session_id ON rag_processing_stats(session_id);
CREATE INDEX IF NOT EXISTS idx_rag_created ON rag_processing_stats(created_at);
CREATE INDEX IF NOT EXISTS idx_rag_created_mode ON rag_processing_stats(created_at, mode);
CREATE INDEX IF NOT EXISTS idx_rag_success ON rag_processing_stats(success);
CREATE INDEX IF NOT EXISTS idx_rag_complexity ON rag_processing_stats(complexity);

-- Daily Accuracy Trends
CREATE TABLE IF NOT EXISTS daily_accuracy_trends (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL UNIQUE,
    total_queries INTEGER NOT NULL DEFAULT 0,
    avg_confidence FLOAT,
    high_confidence_rate FLOAT,
    success_rate FLOAT,
    avg_response_time_ms FLOAT,
    avg_token_usage FLOAT,
    avg_quality_score FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_daily_trend_date ON daily_accuracy_trends(date);

-- Comments
COMMENT ON TABLE file_upload_stats IS 'File upload statistics for monitoring';
COMMENT ON TABLE embedding_stats IS 'Embedding generation statistics';
COMMENT ON TABLE hybrid_search_stats IS 'Hybrid search statistics';
COMMENT ON TABLE rag_processing_stats IS 'RAG processing statistics with quality metrics';
COMMENT ON TABLE daily_accuracy_trends IS 'Daily aggregated accuracy and performance trends';
