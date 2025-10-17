-- Migration: Add Rich Metadata Fields to Documents
-- Date: 2025-01-08
-- Description: Adds extracted metadata fields for better search and filtering

-- Add rich metadata columns
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS document_title VARCHAR(500),
ADD COLUMN IF NOT EXISTS document_author VARCHAR(200),
ADD COLUMN IF NOT EXISTS document_subject VARCHAR(500),
ADD COLUMN IF NOT EXISTS document_keywords TEXT,
ADD COLUMN IF NOT EXISTS document_language VARCHAR(10),
ADD COLUMN IF NOT EXISTS document_creation_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS document_modification_date TIMESTAMP;

-- Create indexes for filtering and search
CREATE INDEX IF NOT EXISTS ix_documents_author ON documents(document_author);
CREATE INDEX IF NOT EXISTS ix_documents_language ON documents(document_language);
CREATE INDEX IF NOT EXISTS ix_documents_creation_date ON documents(document_creation_date);
CREATE INDEX IF NOT EXISTS ix_documents_title ON documents USING gin(to_tsvector('english', document_title));

-- Add comments
COMMENT ON COLUMN documents.document_title IS 'Extracted document title';
COMMENT ON COLUMN documents.document_author IS 'Extracted document author';
COMMENT ON COLUMN documents.document_subject IS 'Extracted document subject/description';
COMMENT ON COLUMN documents.document_keywords IS 'Extracted keywords (comma-separated)';
COMMENT ON COLUMN documents.document_language IS 'Detected language (ISO 639-1 code)';
COMMENT ON COLUMN documents.document_creation_date IS 'Document creation date (from metadata)';
COMMENT ON COLUMN documents.document_modification_date IS 'Document last modification date (from metadata)';
