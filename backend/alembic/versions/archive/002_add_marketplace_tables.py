"""Add marketplace purchase, review, and revenue tables

Revision ID: 002_marketplace
Revises: 001_org_multitenancy
Create Date: 2026-01-15 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_marketplace'
down_revision = '001_org_multitenancy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create marketplace_categories table
    op.create_table(
        'marketplace_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['parent_id'], ['marketplace_categories.id'], ondelete='CASCADE'),
    )

    # Create marketplace_tags table
    op.create_table(
        'marketplace_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('slug', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Check if marketplace_items exists before creating dependent tables
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'marketplace_items' in tables:
        # Create marketplace_item_tags table only if marketplace_items exists
        op.create_table(
            'marketplace_item_tags',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['item_id'], ['marketplace_items.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tag_id'], ['marketplace_tags.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_item_tags_item_tag', 'marketplace_item_tags', ['item_id', 'tag_id'], unique=True)

        # Create marketplace_purchases table
        op.create_table(
            'marketplace_purchases',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('price_paid', sa.Numeric(10, 2), nullable=False),
            sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
            sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),
            sa.Column('stripe_charge_id', sa.String(255), nullable=True),
            sa.Column('payment_status', sa.String(50), nullable=False, server_default='pending'),
            sa.Column('license_key', sa.String(255), nullable=True, unique=True),
            sa.Column('license_type', sa.String(50), nullable=False, server_default='single_user'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('refunded_at', sa.DateTime(), nullable=True),
            sa.Column('refund_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['item_id'], ['marketplace_items.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_purchases_buyer_item', 'marketplace_purchases', ['buyer_id', 'item_id'])
        op.create_index('ix_purchases_status', 'marketplace_purchases', ['payment_status', 'is_active'])

        # Create marketplace_reviews table
        op.create_table(
            'marketplace_reviews',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('purchase_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('helpful_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('not_helpful_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_verified_purchase', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['item_id'], ['marketplace_items.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['purchase_id'], ['marketplace_purchases.id'], ondelete='SET NULL'),
            sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_review_rating_range'),
        )
        op.create_index('ix_reviews_item_user', 'marketplace_reviews', ['item_id', 'user_id'], unique=True)

        # Create marketplace_revenue table
        op.create_table(
            'marketplace_revenue',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('purchase_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
            sa.Column('gross_amount', sa.Numeric(10, 2), nullable=False),
            sa.Column('platform_fee', sa.Numeric(10, 2), nullable=False),
            sa.Column('seller_amount', sa.Numeric(10, 2), nullable=False),
            sa.Column('payout_status', sa.String(50), nullable=False, server_default='pending'),
            sa.Column('payout_method', sa.String(50), nullable=True),
            sa.Column('payout_id', sa.String(255), nullable=True),
            sa.Column('payout_date', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['purchase_id'], ['marketplace_purchases.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['item_id'], ['marketplace_items.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_revenue_seller_status', 'marketplace_revenue', ['seller_id', 'payout_status'])
        op.create_index('ix_revenue_created', 'marketplace_revenue', ['created_at'])
    else:
        print("Warning: marketplace_items table not found. Skipping dependent tables.")


def downgrade() -> None:
    op.drop_table('marketplace_revenue')
    op.drop_table('marketplace_reviews')
    op.drop_table('marketplace_purchases')
    op.drop_table('marketplace_item_tags')
    op.drop_table('marketplace_tags')
    op.drop_table('marketplace_categories')
