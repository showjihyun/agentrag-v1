"""add variables and secrets tables

Revision ID: 20260127_add_variables
Revises: 20260120_create_missing_tables
Create Date: 2026-01-27 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260127_add_variables'
down_revision = '20260120_add_system_config'
branch_labels = None
depends_on = None


def upgrade():
    # Create variables table
    op.create_table(
        'variables',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('value_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "scope IN ('global', 'workspace', 'user', 'agent')",
            name='check_variable_scope_valid'
        ),
        sa.CheckConstraint(
            "value_type IN ('string', 'number', 'boolean', 'json')",
            name='check_variable_type_valid'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'scope', 'scope_id', name='uq_variable_scope')
    )
    
    # Create indexes for variables table
    op.create_index('ix_variables_name', 'variables', ['name'])
    op.create_index('ix_variables_scope', 'variables', ['scope'])
    op.create_index('ix_variables_scope_id', 'variables', ['scope_id'])
    op.create_index('ix_variables_is_secret', 'variables', ['is_secret'])
    op.create_index('ix_variables_deleted_at', 'variables', ['deleted_at'])
    op.create_index('ix_variables_scope_id_composite', 'variables', ['scope', 'scope_id'])
    
    # Create secrets table
    op.create_table(
        'secrets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variable_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('encryption_key_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['variable_id'], ['variables.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('variable_id')
    )
    
    # Create indexes for secrets table
    op.create_index('ix_secrets_variable_id', 'secrets', ['variable_id'])


def downgrade():
    # Drop secrets table first (due to foreign key)
    op.drop_index('ix_secrets_variable_id', table_name='secrets')
    op.drop_table('secrets')
    
    # Drop variables table
    op.drop_index('ix_variables_scope_id_composite', table_name='variables')
    op.drop_index('ix_variables_deleted_at', table_name='variables')
    op.drop_index('ix_variables_is_secret', table_name='variables')
    op.drop_index('ix_variables_scope_id', table_name='variables')
    op.drop_index('ix_variables_scope', table_name='variables')
    op.drop_index('ix_variables_name', table_name='variables')
    op.drop_table('variables')
