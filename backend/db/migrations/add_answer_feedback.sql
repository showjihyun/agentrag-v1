-- Migration: Add Answer Feedback Table
-- Date: 2025-01-08
-- Description: Adds table for tracking answer quality and user feedback

-- Create answer_feedback table
CREATE TABLE IF NOT EXISTS answer_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    
    -- Query and Answer
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    
    -- Quality Metrics
    overall_score FLOAT NOT NULL,
    source_relevance FLOAT,
    grounding_score FLOAT,
    hallucination_risk FLOAT,
    completeness_score FLOAT,
    length_score FLOAT,
    citation_score FLOAT,
    
    -- User Feedback
    user_rating INTEGER,  -- 1=good, 0=neutral, -1=bad
    user_comment TEXT,
    
    -- Context
    source_count INTEGER DEFAULT 0,
    mode VARCHAR(50),
    quality_level VARCHAR(20),
    
    -- Metadata
    suggestions JSONB DEFAULT '[]'::jsonb,
    extra_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    feedback_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_feedback_user_id ON answer_feedback(user_id);
CREATE INDEX IF NOT EXISTS ix_feedback_session_id ON answer_feedback(session_id);
CREATE INDEX IF NOT EXISTS ix_feedback_message_id ON answer_feedback(message_id);
CREATE INDEX IF NOT EXISTS ix_feedback_overall_score ON answer_feedback(overall_score);
CREATE INDEX IF NOT EXISTS ix_feedback_user_rating ON answer_feedback(user_rating);
CREATE INDEX IF NOT EXISTS ix_feedback_quality_level ON answer_feedback(quality_level);
CREATE INDEX IF NOT EXISTS ix_feedback_created_at ON answer_feedback(created_at);
CREATE INDEX IF NOT EXISTS ix_feedback_user_created ON answer_feedback(user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_feedback_quality_created ON answer_feedback(quality_level, created_at);
CREATE INDEX IF NOT EXISTS ix_feedback_rating_created ON answer_feedback(user_rating, created_at);

-- Add comments
COMMENT ON TABLE answer_feedback IS 'Tracks answer quality metrics and user feedback';
COMMENT ON COLUMN answer_feedback.overall_score IS 'Overall quality score (0-1)';
COMMENT ON COLUMN answer_feedback.user_rating IS 'User feedback: 1=good, 0=neutral, -1=bad';
COMMENT ON COLUMN answer_feedback.quality_level IS 'Quality level: excellent, good, acceptable, poor, very_poor';
COMMENT ON COLUMN answer_feedback.hallucination_risk IS 'Risk of hallucination (0-1, higher = more risk)';
COMMENT ON COLUMN answer_feedback.grounding_score IS 'How well answer is grounded in sources (0-1)';
