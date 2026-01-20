"""Add rate limit configuration tables

Revision ID: 004_rate_limit_config
Revises: 003_add_credit_system
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_rate_limit_config'
down_revision = '003_credit_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    rate_limit_tier_enum = postgresql.ENUM(
        'free', 'basic', 'pro', 'business', 'enterprise', 'custom',
        name='ratelimittier',
        create_type=False
    )
    rate_limit_tier_enum.create(op.get_bind(), checkfirst=True)
    
    rate_limit_scope_enum = postgresql.ENUM(
        'global', 'organization', 'user', 'api_key',
        name='ratelimitscope',
        create_type=False
    )
    rate_limit_scope_enum.create(op.get_bind(), checkfirst=True)
    
    # Create rate_limit_configs table
    op.create_table(
        'rate_limit_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scope', rate_limit_scope_enum, nullable=False),
        sa.Column('scope_id', sa.String(255), nullable=True),
        sa.Column('tier', rate_limit_tier_enum, nullable=False),
        sa.Column('requests_per_minute', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('requests_per_hour', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('requests_per_day', sa.Integer(), nullable=False, server_default='10000'),
        sa.Column('endpoint_overrides', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index('idx_rate_limit_configs_scope', 'rate_limit_configs', ['scope', 'scope_id'])
    op.create_index('idx_rate_limit_configs_active', 'rate_limit_configs', ['is_active'])
    
    # Create rate_limit_overrides table
    op.create_table(
        'rate_limit_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scope', rate_limit_scope_enum, nullable=False),
        sa.Column('scope_id', sa.String(255), nullable=False),
        sa.Column('requests_per_minute', sa.Integer(), nullable=True),
        sa.Column('requests_per_hour', sa.Integer(), nullable=True),
        sa.Column('requests_per_day', sa.Integer(), nullable=True),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_rate_limit_overrides_scope', 'rate_limit_overrides', ['scope', 'scope_id'])
    op.create_index('idx_rate_limit_overrides_time', 'rate_limit_overrides', ['starts_at', 'expires_at'])
    op.create_index('idx_rate_limit_overrides_active', 'rate_limit_overrides', ['is_active'])
    
    # Create rate_limit_usage table
    op.create_table(
        'rate_limit_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('identifier', sa.String(255), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('requests_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('blocked_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('window_start', sa.DateTime(), nullable=False),
        sa.Column('window_end', sa.DateTime(), nullable=False),
        sa.Column('window_type', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_rate_limit_usage_identifier', 'rate_limit_usage', ['identifier'])
    op.create_index('idx_rate_limit_usage_window', 'rate_limit_usage', ['window_start', 'window_type'])


def downgrade():
    # Drop tables
    op.drop_table('rate_limit_usage')
    op.drop_table('rate_limit_overrides')
    op.drop_table('rate_limit_configs')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS ratelimitscope')
    op.execute('DROP TYPE IF EXISTS ratelimittier')
