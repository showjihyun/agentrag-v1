"""add missing document columns

Revision ID: 20260127_add_doc_cols
Revises: 20260127_add_kb_versions
Create Date: 2026-01-27 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260127_add_doc_cols'
down_revision = '20260127_add_kb_versions'
branch_labels = None
depends_on = None


def upgrade():
    # Check and add missing columns to documents table
    
    # Add base columns that should have been in initial schema
    base_columns = [
        ('filename', 'VARCHAR(255)'),
        ('original_filename', 'VARCHAR(255)'),
        ('file_path', 'VARCHAR(500)'),
        ('file_size_bytes', 'BIGINT'),
        ('mime_type', 'VARCHAR(100)'),
        ('status', "VARCHAR(50) DEFAULT 'pending'"),
        ('processing_started_at', 'TIMESTAMP'),
        ('processing_completed_at', 'TIMESTAMP'),
        ('error_message', 'TEXT'),
        ('milvus_collection', 'VARCHAR(255)'),
        ('chunk_count', 'INTEGER DEFAULT 0'),
        ('uploaded_at', 'TIMESTAMP DEFAULT NOW()'),
        ('extra_metadata', 'JSONB DEFAULT \'{}\'::jsonb'),
    ]
    
    for col_name, col_type in base_columns:
        op.execute(f"""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='documents' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE documents ADD COLUMN {col_name} {col_type};
                END IF;
            END $$;
        """)
    
    # Add version if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='version'
            ) THEN
                ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1;
            END IF;
        END $$;
    """)
    
    # Add previous_version_id if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='previous_version_id'
            ) THEN
                ALTER TABLE documents ADD COLUMN previous_version_id UUID;
                ALTER TABLE documents ADD CONSTRAINT fk_documents_previous_version 
                    FOREIGN KEY (previous_version_id) REFERENCES documents(id);
            END IF;
        END $$;
    """)
    
    # Add file_hash if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='file_hash'
            ) THEN
                ALTER TABLE documents ADD COLUMN file_hash VARCHAR(64);
            END IF;
        END $$;
    """)
    
    # Add archived_at if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='archived_at'
            ) THEN
                ALTER TABLE documents ADD COLUMN archived_at TIMESTAMP;
            END IF;
        END $$;
    """)
    
    # Add document metadata columns
    metadata_columns = [
        ('document_title', 'VARCHAR(500)'),
        ('document_author', 'VARCHAR(200)'),
        ('document_subject', 'VARCHAR(500)'),
        ('document_keywords', 'TEXT'),
        ('document_language', 'VARCHAR(10)'),
        ('document_creation_date', 'TIMESTAMP'),
        ('document_modification_date', 'TIMESTAMP'),
    ]
    
    for col_name, col_type in metadata_columns:
        op.execute(f"""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='documents' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE documents ADD COLUMN {col_name} {col_type};
                END IF;
            END $$;
        """)
    
    # Create indexes if they don't exist
    base_indexes = [
        ('ix_documents_status', 'status'),
        ('ix_documents_uploaded_at', 'uploaded_at'),
        ('ix_documents_user_id', 'user_id'),
        ('ix_documents_file_hash', 'file_hash'),
        ('ix_documents_document_author', 'document_author'),
        ('ix_documents_document_language', 'document_language'),
        ('ix_documents_document_creation_date', 'document_creation_date'),
    ]
    
    for index_name, column_name in base_indexes:
        op.execute(f"""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename='documents' AND indexname='{index_name}'
                ) THEN
                    CREATE INDEX {index_name} ON documents({column_name});
                END IF;
            END $$;
        """)
    
    # Update original_filename for existing records where it's NULL
    op.execute("""
        UPDATE documents 
        SET original_filename = filename 
        WHERE original_filename IS NULL;
    """)
    
    # Make original_filename NOT NULL after populating it
    op.execute("""
        ALTER TABLE documents ALTER COLUMN original_filename SET NOT NULL;
    """)


def downgrade():
    # Drop added columns (be careful with this in production)
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_modification_date")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_creation_date")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_language")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_keywords")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_subject")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_author")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS document_title")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS archived_at")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS file_hash")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS previous_version_id")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS version")
    # Note: We don't drop original_filename as it was in the original schema
