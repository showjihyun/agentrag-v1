"""Add Knowledge Graph tables

Revision ID: add_knowledge_graph_tables
Revises: [previous_revision]
Create Date: 2024-12-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_knowledge_graph_tables'
down_revision = '62404ad9e047'
branch_labels = None
depends_on = None


def upgrade():
    # Create knowledge_graphs table
    op.create_table('knowledge_graphs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledgebase_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('auto_extraction_enabled', sa.Boolean(), nullable=True),
        sa.Column('entity_extraction_model', sa.String(length=100), nullable=True),
        sa.Column('relation_extraction_model', sa.String(length=100), nullable=True),
        sa.Column('entity_count', sa.Integer(), nullable=True),
        sa.Column('relationship_count', sa.Integer(), nullable=True),
        sa.Column('last_processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("processing_status IN ('ready', 'processing', 'error', 'updating')", name='check_kg_processing_status_valid'),
        sa.ForeignKeyConstraint(['knowledgebase_id'], ['knowledgebases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledgebase_id')
    )
    op.create_index('ix_kg_user_created', 'knowledge_graphs', ['user_id', 'created_at'])

    # Create kg_entities table
    op.create_table('kg_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_graph_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('canonical_name', sa.String(length=500), nullable=False),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extraction_source', sa.String(length=100), nullable=True),
        sa.Column('embedding', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_chunks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mention_count', sa.Integer(), nullable=True),
        sa.Column('relationship_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0', name='check_entity_confidence_range'),
        sa.CheckConstraint('mention_count >= 0', name='check_entity_mention_count_positive'),
        sa.ForeignKeyConstraint(['knowledge_graph_id'], ['knowledge_graphs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledge_graph_id', 'canonical_name', name='uq_kg_entity_canonical')
    )
    op.create_index('ix_kg_entities_kg_type', 'kg_entities', ['knowledge_graph_id', 'entity_type'])
    op.create_index('ix_kg_entities_canonical', 'kg_entities', ['canonical_name'])
    op.create_index('ix_kg_entities_confidence', 'kg_entities', ['confidence_score'])

    # Create kg_relationships table
    op.create_table('kg_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_graph_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('relation_label', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_bidirectional', sa.Boolean(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extraction_source', sa.String(length=100), nullable=True),
        sa.Column('source_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_chunks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_sentences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('temporal_start', sa.DateTime(), nullable=True),
        sa.Column('temporal_end', sa.DateTime(), nullable=True),
        sa.Column('mention_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0', name='check_relationship_confidence_range'),
        sa.CheckConstraint('mention_count >= 0', name='check_relationship_mention_count_positive'),
        sa.CheckConstraint('source_entity_id != target_entity_id', name='check_no_self_relationship'),
        sa.ForeignKeyConstraint(['knowledge_graph_id'], ['knowledge_graphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_entity_id'], ['kg_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_entity_id'], ['kg_entities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledge_graph_id', 'source_entity_id', 'target_entity_id', 'relation_type', name='uq_kg_relationship')
    )
    op.create_index('ix_kg_relationships_kg_type', 'kg_relationships', ['knowledge_graph_id', 'relation_type'])
    op.create_index('ix_kg_relationships_source_target', 'kg_relationships', ['source_entity_id', 'target_entity_id'])
    op.create_index('ix_kg_relationships_confidence', 'kg_relationships', ['confidence_score'])
    op.create_index('ix_kg_relationships_temporal', 'kg_relationships', ['temporal_start', 'temporal_end'])

    # Create kg_entity_mentions table
    op.create_table('kg_entity_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mention_text', sa.Text(), nullable=False),
        sa.Column('context_before', sa.Text(), nullable=True),
        sa.Column('context_after', sa.Text(), nullable=True),
        sa.Column('chunk_id', sa.String(length=100), nullable=True),
        sa.Column('start_position', sa.Integer(), nullable=True),
        sa.Column('end_position', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0', name='check_mention_confidence_range'),
        sa.ForeignKeyConstraint(['entity_id'], ['kg_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_kg_mentions_entity_doc', 'kg_entity_mentions', ['entity_id', 'document_id'])
    op.create_index('ix_kg_mentions_confidence', 'kg_entity_mentions', ['confidence_score'])

    # Create kg_queries table
    op.create_table('kg_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_graph_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=False),
        sa.Column('query_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("query_type IN ('entity_search', 'relationship_search', 'path_finding', 'subgraph', 'similarity', 'custom')", name='check_kg_query_type_valid'),
        sa.ForeignKeyConstraint(['knowledge_graph_id'], ['knowledge_graphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_kg_queries_kg_user', 'kg_queries', ['knowledge_graph_id', 'user_id'])
    op.create_index('ix_kg_queries_type_created', 'kg_queries', ['query_type', 'created_at'])

    # Create kg_schemas table
    op.create_table('kg_schemas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_graph_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('entity_types', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('relationship_types', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['knowledge_graph_id'], ['knowledge_graphs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledge_graph_id', 'name', name='uq_kg_schema_name')
    )

    # Create kg_extraction_jobs table
    op.create_table('kg_extraction_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_graph_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('documents_to_process', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('documents_processed', sa.Integer(), nullable=True),
        sa.Column('documents_total', sa.Integer(), nullable=True),
        sa.Column('entities_extracted', sa.Integer(), nullable=True),
        sa.Column('relationships_extracted', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("job_type IN ('full_extraction', 'incremental', 'document_specific', 'schema_update')", name='check_kg_job_type_valid'),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')", name='check_kg_job_status_valid'),
        sa.ForeignKeyConstraint(['knowledge_graph_id'], ['knowledge_graphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_kg_jobs_kg_status', 'kg_extraction_jobs', ['knowledge_graph_id', 'status'])
    op.create_index('ix_kg_jobs_user_created', 'kg_extraction_jobs', ['user_id', 'created_at'])

    # Update knowledgebases table to add KG fields (if not already present)
    try:
        op.add_column('knowledgebases', sa.Column('kb_type', sa.String(length=50), nullable=False, server_default='vector'))
        op.add_column('knowledgebases', sa.Column('kg_enabled', sa.Boolean(), nullable=True, server_default='false'))
        op.add_column('knowledgebases', sa.Column('kg_auto_extraction', sa.Boolean(), nullable=True, server_default='true'))
        op.add_column('knowledgebases', sa.Column('kg_entity_extraction_model', sa.String(length=100), nullable=True, server_default='spacy_en_core_web_sm'))
        op.add_column('knowledgebases', sa.Column('kg_relation_extraction_model', sa.String(length=100), nullable=True, server_default='rebel_large'))
        op.add_column('knowledgebases', sa.Column('search_strategy', sa.String(length=50), nullable=True, server_default='vector'))
        op.add_column('knowledgebases', sa.Column('hybrid_weight_vector', sa.Float(), nullable=True, server_default='0.7'))
        op.add_column('knowledgebases', sa.Column('hybrid_weight_graph', sa.Float(), nullable=True, server_default='0.3'))
        
        # Add constraints
        op.create_check_constraint(
            'check_kb_type_valid',
            'knowledgebases',
            "kb_type IN ('vector', 'graph', 'hybrid')"
        )
        op.create_check_constraint(
            'check_search_strategy_valid',
            'knowledgebases',
            "search_strategy IN ('vector', 'graph', 'hybrid')"
        )
        op.create_check_constraint(
            'check_hybrid_weight_vector_range',
            'knowledgebases',
            'hybrid_weight_vector >= 0.0 AND hybrid_weight_vector <= 1.0'
        )
        op.create_check_constraint(
            'check_hybrid_weight_graph_range',
            'knowledgebases',
            'hybrid_weight_graph >= 0.0 AND hybrid_weight_graph <= 1.0'
        )
        
        # Add indexes
        op.create_index('ix_knowledgebases_kg_enabled', 'knowledgebases', ['kg_enabled'])
        
    except Exception as e:
        # Columns might already exist, ignore the error
        print(f"Warning: Could not add columns to knowledgebases table: {e}")


def downgrade():
    # Drop indexes first
    op.drop_index('ix_kg_jobs_user_created', table_name='kg_extraction_jobs')
    op.drop_index('ix_kg_jobs_kg_status', table_name='kg_extraction_jobs')
    op.drop_index('ix_kg_queries_type_created', table_name='kg_queries')
    op.drop_index('ix_kg_queries_kg_user', table_name='kg_queries')
    op.drop_index('ix_kg_mentions_confidence', table_name='kg_entity_mentions')
    op.drop_index('ix_kg_mentions_entity_doc', table_name='kg_entity_mentions')
    op.drop_index('ix_kg_relationships_temporal', table_name='kg_relationships')
    op.drop_index('ix_kg_relationships_confidence', table_name='kg_relationships')
    op.drop_index('ix_kg_relationships_source_target', table_name='kg_relationships')
    op.drop_index('ix_kg_relationships_kg_type', table_name='kg_relationships')
    op.drop_index('ix_kg_entities_confidence', table_name='kg_entities')
    op.drop_index('ix_kg_entities_canonical', table_name='kg_entities')
    op.drop_index('ix_kg_entities_kg_type', table_name='kg_entities')
    op.drop_index('ix_kg_user_created', table_name='knowledge_graphs')
    
    # Drop tables
    op.drop_table('kg_extraction_jobs')
    op.drop_table('kg_schemas')
    op.drop_table('kg_queries')
    op.drop_table('kg_entity_mentions')
    op.drop_table('kg_relationships')
    op.drop_table('kg_entities')
    op.drop_table('knowledge_graphs')
    
    # Remove columns from knowledgebases table (optional, might want to keep them)
    try:
        op.drop_index('ix_knowledgebases_kg_enabled', table_name='knowledgebases')
        op.drop_constraint('check_hybrid_weight_graph_range', 'knowledgebases')
        op.drop_constraint('check_hybrid_weight_vector_range', 'knowledgebases')
        op.drop_constraint('check_search_strategy_valid', 'knowledgebases')
        op.drop_constraint('check_kb_type_valid', 'knowledgebases')
        op.drop_column('knowledgebases', 'hybrid_weight_graph')
        op.drop_column('knowledgebases', 'hybrid_weight_vector')
        op.drop_column('knowledgebases', 'search_strategy')
        op.drop_column('knowledgebases', 'kg_relation_extraction_model')
        op.drop_column('knowledgebases', 'kg_entity_extraction_model')
        op.drop_column('knowledgebases', 'kg_auto_extraction')
        op.drop_column('knowledgebases', 'kg_enabled')
        op.drop_column('knowledgebases', 'kb_type')
    except Exception as e:
        print(f"Warning: Could not remove columns from knowledgebases table: {e}")