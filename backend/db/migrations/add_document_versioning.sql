-- Migration: Add Document Versioning Support
-- Date: 2025-01-08
-- Description: Adds version management fields to documents table

-- Add version management columns
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS previous_version_id UUID REFERENCES documents(id),
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;

-- Create indexes for version management
CREATE INDEX IF NOT EXISTS ix_documents_user_filename ON documents(user_id, filename);
CREATE INDEX IF NOT EXISTS ix_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS ix_documents_version ON documents(version);

-- Update constraint to include 'archived' status
ALTER TABLE documents DROP CONSTRAINT IF EXISTS check_status_valid;
ALTER TABLE documents ADD CONSTRAINT check_status_valid 
CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'archived'));

-- Add version constraint
ALTER TABLE documents ADD CONSTRAINT IF NOT EXISTS check_version_positive 
CHECK (version > 0);

-- Set default version for existing documents
UPDATE documents SET version = 1 WHERE version IS NULL;

-- Make version NOT NULL after setting defaults
ALTER TABLE documents ALTER COLUMN version SET NOT NULL;

-- Add comment
COMMENT ON COLUMN documents.version IS 'Document version number (starts at 1)';
COMMENT ON COLUMN documents.previous_version_id IS 'Reference to previous version of this document';
COMMENT ON COLUMN documents.file_hash IS 'SHA-256 hash of file content for deduplication';
COMMENT ON COLUMN documents.archived_at IS 'Timestamp when document was archived';
