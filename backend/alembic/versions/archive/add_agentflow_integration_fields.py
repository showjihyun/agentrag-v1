"""Add agentflow integration fields

Revision ID: add_agentflow_integration_fields
Revises: e43511051f56
Create Date: 2025-12-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_agentflow_integration_fields'
down_revision = 'e43511051f56'  # Updated to use the latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to agentflow_agents table
    op.add_column('agentflow_agents', sa.Column('block_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('agentflow_agents', sa.Column('input_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=sa.text("'{}'::jsonb")))
    op.add_column('agentflow_agents', sa.Column('output_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=sa.text("'{}'::jsonb")))
    op.add_column('agentflow_agents', sa.Column('conditional_logic', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=sa.text("'{}'::jsonb")))
    op.add_column('agentflow_agents', sa.Column('parallel_group', sa.String(length=100), nullable=True))
    op.add_column('agentflow_agents', sa.Column('position_x', sa.Float(), nullable=True, default=0))
    op.add_column('agentflow_agents', sa.Column('position_y', sa.Float(), nullable=True, default=0))
    
    # Add foreign key constraint for block_id
    op.create_foreign_key(
        'fk_agentflow_agents_block_id',
        'agentflow_agents', 'blocks',
        ['block_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for block_id
    op.create_index('ix_agentflow_agents_block', 'agentflow_agents', ['block_id'])
    
    # Create agentflow_edges table
    op.create_table(
        'agentflow_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('agentflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edge_type', sa.String(length=50), nullable=False, default='data_flow'),
        sa.Column('condition', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=sa.text("'{}'::jsonb")),
        sa.Column('data_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=sa.text("'{}'::jsonb")),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('style', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
    )
    
    # Add foreign key constraints for agentflow_edges
    op.create_foreign_key(
        'fk_agentflow_edges_agentflow_id',
        'agentflow_edges', 'agentflows',
        ['agentflow_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_agentflow_edges_source_agent_id',
        'agentflow_edges', 'agentflow_agents',
        ['source_agent_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_agentflow_edges_target_agent_id',
        'agentflow_edges', 'agentflow_agents',
        ['target_agent_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Add indexes for agentflow_edges
    op.create_index('ix_agentflow_edges_flow', 'agentflow_edges', ['agentflow_id'])
    
    # Add unique constraint for edge uniqueness
    op.create_unique_constraint(
        'uq_agentflow_edge',
        'agentflow_edges',
        ['source_agent_id', 'target_agent_id']
    )
    
    # Add check constraint for edge_type
    op.create_check_constraint(
        'check_edge_type_valid',
        'agentflow_edges',
        "edge_type IN ('data_flow', 'control_flow', 'conditional')"
    )


def downgrade():
    # Drop agentflow_edges table
    op.drop_table('agentflow_edges')
    
    # Remove new columns from agentflow_agents
    op.drop_index('ix_agentflow_agents_block', 'agentflow_agents')
    op.drop_constraint('fk_agentflow_agents_block_id', 'agentflow_agents', type_='foreignkey')
    op.drop_column('agentflow_agents', 'position_y')
    op.drop_column('agentflow_agents', 'position_x')
    op.drop_column('agentflow_agents', 'parallel_group')
    op.drop_column('agentflow_agents', 'conditional_logic')
    op.drop_column('agentflow_agents', 'output_mapping')
    op.drop_column('agentflow_agents', 'input_mapping')
    op.drop_column('agentflow_agents', 'block_id')