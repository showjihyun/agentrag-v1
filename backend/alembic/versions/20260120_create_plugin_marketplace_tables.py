"""Create plugin system and marketplace tables

Revision ID: 20260120_plugin_marketplace
Revises: 20260120_create_missing_tables
Create Date: 2026-01-20 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260120_plugin_marketplace'
down_revision: Union[str, None] = '20260120_create_missing_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create plugin system and marketplace tables."""
    
    # ==========================================
    # 1. Plugin Registry Table
    # ==========================================
    op.create_table('plugin_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('manifest', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('installed_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'version', name='uq_plugin_name_version'),
        sa.Index('idx_plugin_registry_name', 'name'),
        sa.Index('idx_plugin_registry_category', 'category'),
        sa.Index('idx_plugin_registry_status', 'status'),
    )
    
    # ==========================================
    # 2. Plugin Configurations Table
    # ==========================================
    op.create_table('plugin_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plugin_id', 'user_id', 'environment', name='uq_plugin_config_user_env'),
        sa.Index('idx_plugin_configurations_plugin_user', 'plugin_id', 'user_id'),
    )
    
    # ==========================================
    # 3. Plugin Metrics Table
    # ==========================================
    op.create_table('plugin_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(length=255), nullable=False),
        sa.Column('metric_value', sa.String(length=255), nullable=True),
        sa.Column('metric_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_plugin_metrics_plugin_time', 'plugin_id', 'recorded_at'),
        sa.Index('idx_plugin_metrics_name', 'metric_name'),
    )
    
    # ==========================================
    # 4. Plugin Dependencies Table
    # ==========================================
    op.create_table('plugin_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_name', sa.String(length=255), nullable=False),
        sa.Column('version_constraint', sa.String(length=100), nullable=True),
        sa.Column('optional', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_plugin_dependencies_plugin', 'plugin_id'),
        sa.Index('idx_plugin_dependencies_name', 'dependency_name'),
    )
    
    # ==========================================
    # 5. Plugin Audit Logs Table
    # ==========================================
    op.create_table('plugin_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_plugin_audit_plugin', 'plugin_id'),
        sa.Index('idx_plugin_audit_user', 'user_id'),
        sa.Index('idx_plugin_audit_timestamp', 'timestamp'),
        sa.Index('idx_plugin_audit_action', 'action'),
    )
    
    # ==========================================
    # 6. Plugin Security Scans Table
    # ==========================================
    op.create_table('plugin_security_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_type', sa.String(length=50), nullable=False),
        sa.Column('scan_result', sa.String(length=20), nullable=False),
        sa.Column('findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scan_version', sa.String(length=20), nullable=True),
        sa.Column('scanned_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_plugin_security_plugin', 'plugin_id'),
        sa.Index('idx_plugin_security_result', 'scan_result'),
        sa.Index('idx_plugin_security_timestamp', 'scanned_at'),
    )
    
    # ==========================================
    # 7. Marketplace Purchases Table
    # ==========================================
    op.create_table('marketplace_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='USD'),
        sa.Column('payment_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_marketplace_purchases_user_id', 'user_id'),
        sa.Index('idx_marketplace_purchases_agent_id', 'agent_id'),
        sa.Index('idx_marketplace_purchases_status', 'payment_status'),
        sa.Index('idx_marketplace_purchases_created_at', 'created_at'),
    )
    
    # ==========================================
    # 8. Marketplace Reviews Table
    # ==========================================
    op.create_table('marketplace_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),  # 1-5
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('helpful_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'agent_id', name='uq_review_user_agent'),
        sa.Index('idx_marketplace_reviews_user_id', 'user_id'),
        sa.Index('idx_marketplace_reviews_agent_id', 'agent_id'),
        sa.Index('idx_marketplace_reviews_rating', 'rating'),
        sa.Index('idx_marketplace_reviews_created_at', 'created_at'),
    )
    
    # ==========================================
    # 9. Marketplace Revenue Table
    # ==========================================
    op.create_table('marketplace_revenue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('purchase_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('platform_fee', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('seller_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('payout_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_id'], ['marketplace_purchases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_marketplace_revenue_agent_id', 'agent_id'),
        sa.Index('idx_marketplace_revenue_seller_id', 'seller_id'),
        sa.Index('idx_marketplace_revenue_status', 'status'),
        sa.Index('idx_marketplace_revenue_created_at', 'created_at'),
    )
    
    # ==========================================
    # 10. Credits Table
    # ==========================================
    op.create_table('credits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),  # purchase, usage, refund, bonus
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),  # purchase, execution, etc.
        sa.Column('balance_after', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_credits_user_id', 'user_id'),
        sa.Index('idx_credits_transaction_type', 'transaction_type'),
        sa.Index('idx_credits_created_at', 'created_at'),
        sa.Index('idx_credits_reference', 'reference_id', 'reference_type'),
    )
    
    # ==========================================
    # 11. Rate Limit Configs Table
    # ==========================================
    op.create_table('rate_limit_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('limit_type', sa.String(length=50), nullable=False),  # api, query, execution
        sa.Column('limit_value', sa.Integer(), nullable=False),
        sa.Column('time_window', sa.Integer(), nullable=False),  # seconds
        sa.Column('time_unit', sa.String(length=20), nullable=True, server_default='second'),  # second, minute, hour, day
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_rate_limit_configs_user_id', 'user_id'),
        sa.Index('idx_rate_limit_configs_org_id', 'organization_id'),
        sa.Index('idx_rate_limit_configs_limit_type', 'limit_type'),
        sa.Index('idx_rate_limit_configs_is_active', 'is_active'),
    )


def downgrade() -> None:
    """Drop all created tables."""
    op.drop_table('rate_limit_configs')
    op.drop_table('credits')
    op.drop_table('marketplace_revenue')
    op.drop_table('marketplace_reviews')
    op.drop_table('marketplace_purchases')
    op.drop_table('plugin_security_scans')
    op.drop_table('plugin_audit_logs')
    op.drop_table('plugin_dependencies')
    op.drop_table('plugin_metrics')
    op.drop_table('plugin_configurations')
    op.drop_table('plugin_registry')
