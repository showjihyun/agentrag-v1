"""rename knowledgebases to knowledge_bases

Revision ID: 20260120_rename_kb
Revises: 20260120_add_system_config
Create Date: 2026-01-20 21:38:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260120_rename_kb'
down_revision = '20260120_add_system_config'
branch_labels = None
depends_on = None


def upgrade():
    """Rename knowledgebases table to knowledge_bases."""
    # Rename the table
    op.rename_table('knowledgebases', 'knowledge_bases')
    
    # Update foreign key references in related tables
    # knowledgebase_documents table
    with op.batch_alter_table('knowledgebase_documents', schema=None) as batch_op:
        batch_op.drop_constraint('knowledgebase_documents_knowledgebase_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'knowledgebase_documents_knowledgebase_id_fkey',
            'knowledge_bases',
            ['knowledgebase_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    # agent_knowledgebases table
    with op.batch_alter_table('agent_knowledgebases', schema=None) as batch_op:
        batch_op.drop_constraint('agent_knowledgebases_knowledgebase_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'agent_knowledgebases_knowledgebase_id_fkey',
            'knowledge_bases',
            ['knowledgebase_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    # knowledgebase_versions table (if exists)
    try:
        with op.batch_alter_table('knowledgebase_versions', schema=None) as batch_op:
            batch_op.drop_constraint('knowledgebase_versions_knowledgebase_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'knowledgebase_versions_knowledgebase_id_fkey',
                'knowledge_bases',
                ['knowledgebase_id'],
                ['id'],
                ondelete='CASCADE'
            )
    except:
        pass  # Table might not exist
    
    # knowledge_graphs table
    try:
        with op.batch_alter_table('knowledge_graphs', schema=None) as batch_op:
            batch_op.drop_constraint('knowledge_graphs_knowledgebase_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'knowledge_graphs_knowledgebase_id_fkey',
                'knowledge_bases',
                ['knowledgebase_id'],
                ['id'],
                ondelete='CASCADE'
            )
    except:
        pass  # Constraint might not exist


def downgrade():
    """Rename knowledge_bases table back to knowledgebases."""
    # Revert foreign key references
    with op.batch_alter_table('knowledgebase_documents', schema=None) as batch_op:
        batch_op.drop_constraint('knowledgebase_documents_knowledgebase_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'knowledgebase_documents_knowledgebase_id_fkey',
            'knowledgebases',
            ['knowledgebase_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    with op.batch_alter_table('agent_knowledgebases', schema=None) as batch_op:
        batch_op.drop_constraint('agent_knowledgebases_knowledgebase_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'agent_knowledgebases_knowledgebase_id_fkey',
            'knowledgebases',
            ['knowledgebase_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    try:
        with op.batch_alter_table('knowledgebase_versions', schema=None) as batch_op:
            batch_op.drop_constraint('knowledgebase_versions_knowledgebase_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'knowledgebase_versions_knowledgebase_id_fkey',
                'knowledgebases',
                ['knowledgebase_id'],
                ['id'],
                ondelete='CASCADE'
            )
    except:
        pass
    
    try:
        with op.batch_alter_table('knowledge_graphs', schema=None) as batch_op:
            batch_op.drop_constraint('knowledge_graphs_knowledgebase_id_fkey', type_='foreignkey')
            batch_op.create_foreign_key(
                'knowledge_graphs_knowledgebase_id_fkey',
                'knowledgebases',
                ['knowledgebase_id'],
                ['id'],
                ondelete='CASCADE'
            )
    except:
        pass
    
    # Rename the table back
    op.rename_table('knowledge_bases', 'knowledgebases')
