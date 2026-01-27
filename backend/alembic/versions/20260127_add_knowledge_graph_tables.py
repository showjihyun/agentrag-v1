"""add knowledge graph tables

Revision ID: 20260127_add_kg_tables
Revises: 20260127_add_doc_cols
Create Date: 2026-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260127_add_kg_tables'
down_revision = '20260127_add_doc_cols'
branch_labels = None
depends_on = None


def upgrade():
    # Check if knowledge_graphs table exists and add missing columns
    op.execute("""
        DO $$
        BEGIN
            -- Create table if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='knowledge_graphs') THEN
                CREATE TABLE knowledge_graphs (
                    id UUID PRIMARY KEY,
                    knowledgebase_id UUID NOT NULL UNIQUE REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    auto_extraction_enabled BOOLEAN DEFAULT TRUE,
                    entity_extraction_model VARCHAR(100) DEFAULT 'spacy_en_core_web_sm',
                    relation_extraction_model VARCHAR(100) DEFAULT 'rebel_large',
                    entity_count INTEGER DEFAULT 0,
                    relationship_count INTEGER DEFAULT 0,
                    last_processed_at TIMESTAMP,
                    processing_status VARCHAR(50) DEFAULT 'ready',
                    processing_error TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT check_kg_processing_status_valid 
                        CHECK (processing_status IN ('ready', 'processing', 'error', 'updating'))
                );
            ELSE
                -- Add missing columns if table exists
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='knowledgebase_id') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN knowledgebase_id UUID;
                    ALTER TABLE knowledge_graphs ADD CONSTRAINT fk_kg_knowledgebase 
                        FOREIGN KEY (knowledgebase_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='auto_extraction_enabled') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN auto_extraction_enabled BOOLEAN DEFAULT TRUE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='entity_extraction_model') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN entity_extraction_model VARCHAR(100) DEFAULT 'spacy_en_core_web_sm';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='relation_extraction_model') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN relation_extraction_model VARCHAR(100) DEFAULT 'rebel_large';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='entity_count') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN entity_count INTEGER DEFAULT 0;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='relationship_count') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN relationship_count INTEGER DEFAULT 0;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='last_processed_at') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN last_processed_at TIMESTAMP;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='processing_status') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN processing_status VARCHAR(50) DEFAULT 'ready';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='knowledge_graphs' AND column_name='processing_error') THEN
                    ALTER TABLE knowledge_graphs ADD COLUMN processing_error TEXT;
                END IF;
            END IF;
        END $$;
    """)
    
    # Create indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_knowledge_graphs_knowledgebase_id 
            ON knowledge_graphs(knowledgebase_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_knowledge_graphs_user_id 
            ON knowledge_graphs(user_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_knowledge_graphs_created_at 
            ON knowledge_graphs(created_at);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_user_created 
            ON knowledge_graphs(user_id, created_at);
    """)
    
    # Create kg_entities table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS kg_entities (
            id UUID PRIMARY KEY,
            knowledge_graph_id UUID NOT NULL REFERENCES knowledge_graphs(id) ON DELETE CASCADE,
            name VARCHAR(500) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            description TEXT,
            canonical_name VARCHAR(500) NOT NULL,
            properties JSONB DEFAULT '{}'::jsonb,
            aliases JSONB DEFAULT '[]'::jsonb,
            confidence_score FLOAT DEFAULT 1.0,
            extraction_source VARCHAR(100),
            embedding JSONB,
            source_documents JSONB DEFAULT '[]'::jsonb,
            source_chunks JSONB DEFAULT '[]'::jsonb,
            mention_count INTEGER DEFAULT 1,
            relationship_count INTEGER DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_kg_entity_canonical UNIQUE (knowledge_graph_id, canonical_name),
            CONSTRAINT check_entity_confidence_range 
                CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
            CONSTRAINT check_entity_mention_count_positive 
                CHECK (mention_count >= 0)
        );
    """)
    
    # Create indexes for kg_entities
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_entities_knowledge_graph_id 
            ON kg_entities(knowledge_graph_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_entities_entity_type 
            ON kg_entities(entity_type);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_entities_canonical_name 
            ON kg_entities(canonical_name);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_entities_created_at 
            ON kg_entities(created_at);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_entities_kg_type 
            ON kg_entities(knowledge_graph_id, entity_type);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_entities_canonical 
            ON kg_entities(canonical_name);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_entities_confidence 
            ON kg_entities(confidence_score);
    """)
    
    # Create kg_relationships table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS kg_relationships (
            id UUID PRIMARY KEY,
            knowledge_graph_id UUID NOT NULL REFERENCES knowledge_graphs(id) ON DELETE CASCADE,
            source_entity_id UUID NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
            target_entity_id UUID NOT NULL REFERENCES kg_entities(id) ON DELETE CASCADE,
            relation_type VARCHAR(50) NOT NULL,
            relation_label VARCHAR(200),
            description TEXT,
            properties JSONB DEFAULT '{}'::jsonb,
            is_bidirectional BOOLEAN DEFAULT FALSE,
            confidence_score FLOAT DEFAULT 1.0,
            extraction_source VARCHAR(100),
            source_documents JSONB DEFAULT '[]'::jsonb,
            source_chunks JSONB DEFAULT '[]'::jsonb,
            source_sentences JSONB DEFAULT '[]'::jsonb,
            temporal_start TIMESTAMP,
            temporal_end TIMESTAMP,
            mention_count INTEGER DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_kg_relationship 
                UNIQUE (knowledge_graph_id, source_entity_id, target_entity_id, relation_type),
            CONSTRAINT check_relationship_confidence_range 
                CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
            CONSTRAINT check_relationship_mention_count_positive 
                CHECK (mention_count >= 0),
            CONSTRAINT check_no_self_relationship 
                CHECK (source_entity_id != target_entity_id)
        );
    """)
    
    # Create indexes for kg_relationships
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_knowledge_graph_id 
            ON kg_relationships(knowledge_graph_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_source_entity_id 
            ON kg_relationships(source_entity_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_target_entity_id 
            ON kg_relationships(target_entity_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_relation_type 
            ON kg_relationships(relation_type);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_created_at 
            ON kg_relationships(created_at);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_kg_type 
            ON kg_relationships(knowledge_graph_id, relation_type);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_source_target 
            ON kg_relationships(source_entity_id, target_entity_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_confidence 
            ON kg_relationships(confidence_score);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_kg_relationships_temporal 
            ON kg_relationships(temporal_start, temporal_end);
    """)


def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.execute("DROP TABLE IF EXISTS kg_relationships CASCADE")
    op.execute("DROP TABLE IF EXISTS kg_entities CASCADE")
    op.execute("DROP TABLE IF EXISTS knowledge_graphs CASCADE")
