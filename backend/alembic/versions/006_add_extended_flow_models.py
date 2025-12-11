"""Add extended flow models (templates, token usage, embed config, pricing)

Revision ID: 006_extended_flows
Revises: 005_add_flow_tables
Create Date: 2024-12-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_extended_flows'
down_revision = '005_add_flow_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Flow Templates table
    op.create_table(
        'flow_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('flow_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('icon', sa.String(50)),
        sa.Column('configuration', postgresql.JSONB, nullable=False),
        sa.Column('tags', postgresql.JSONB, default=[]),
        sa.Column('use_case_examples', postgresql.JSONB, default=[]),
        sa.Column('requirements', postgresql.JSONB, default=[]),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('is_published', sa.Boolean, default=True),
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('rating', sa.Float, default=0.0),
        sa.Column('rating_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_flow_templates_type_category', 'flow_templates', ['flow_type', 'category'])
    op.create_index('ix_flow_templates_system_published', 'flow_templates', ['is_system', 'is_published'])
    op.create_index('ix_flow_templates_author_id', 'flow_templates', ['author_id'])

    # Token Usage table
    op.create_table(
        'token_usages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('flow_executions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('node_id', sa.String(255)),
        sa.Column('node_type', sa.String(100)),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('input_tokens', sa.Integer, nullable=False, default=0),
        sa.Column('output_tokens', sa.Integer, nullable=False, default=0),
        sa.Column('total_tokens', sa.Integer, nullable=False, default=0),
        sa.Column('cost_usd', sa.Float, nullable=False, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_token_usages_user_created', 'token_usages', ['user_id', 'created_at'])
    op.create_index('ix_token_usages_user_model', 'token_usages', ['user_id', 'model'])
    op.create_index('ix_token_usages_workflow', 'token_usages', ['workflow_id', 'created_at'])

    # Model Pricing table
    op.create_table(
        'model_pricings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('input_price_per_1k', sa.Float, nullable=False, default=0.0),
        sa.Column('output_price_per_1k', sa.Float, nullable=False, default=0.0),
        sa.Column('currency', sa.String(10), default='USD'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('provider', 'model', name='uq_model_pricing'),
    )
    op.create_index('ix_model_pricings_provider_model', 'model_pricings', ['provider', 'model'])
    op.create_index('ix_model_pricings_is_active', 'model_pricings', ['is_active'])

    # Embed Config table
    op.create_table(
        'embed_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chatflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('embed_token', sa.String(255), unique=True, nullable=False),
        sa.Column('theme', sa.String(50), default='light'),
        sa.Column('primary_color', sa.String(20), default='#6366f1'),
        sa.Column('position', sa.String(50), default='bottom-right'),
        sa.Column('widget_title', sa.String(255)),
        sa.Column('welcome_message', sa.Text),
        sa.Column('placeholder_text', sa.String(255), default='메시지를 입력하세요...'),
        sa.Column('show_branding', sa.Boolean, default=True),
        sa.Column('custom_css', sa.Text),
        sa.Column('allowed_domains', postgresql.JSONB, default=[]),
        sa.Column('rate_limit_per_ip', sa.Integer, default=100),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_embed_configs_chatflow_active', 'embed_configs', ['chatflow_id', 'is_active'])
    op.create_index('ix_embed_configs_token', 'embed_configs', ['embed_token'])
    op.create_index('ix_embed_configs_user_id', 'embed_configs', ['user_id'])

    # Marketplace Reviews table
    op.create_table(
        'marketplace_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('marketplace_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('comment', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('item_id', 'user_id', name='uq_marketplace_review_user'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_review_rating_range'),
    )
    op.create_index('ix_marketplace_reviews_item_created', 'marketplace_reviews', ['item_id', 'created_at'])
    op.create_index('ix_marketplace_reviews_user_id', 'marketplace_reviews', ['user_id'])


def downgrade() -> None:
    op.drop_table('marketplace_reviews')
    op.drop_table('embed_configs')
    op.drop_table('model_pricings')
    op.drop_table('token_usages')
    op.drop_table('flow_templates')
