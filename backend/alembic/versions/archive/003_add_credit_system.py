"""Add credit system tables

Revision ID: 003_credit_system
Revises: 002_marketplace
Create Date: 2026-01-15 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_credit_system'
down_revision = '002_marketplace'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE transactiontype AS ENUM ('purchase', 'usage', 'refund', 'bonus', 'adjustment');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create credit_balances table
    op.create_table(
        'credit_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('balance', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('lifetime_purchased', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('lifetime_used', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('auto_recharge_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('auto_recharge_threshold', sa.Numeric(12, 2), nullable=True),
        sa.Column('auto_recharge_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('auto_recharge_package', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_purchase_at', sa.DateTime(), nullable=True),
        sa.Column('last_usage_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('balance >= 0', name='check_balance_non_negative'),
    )

    # Create credit_purchases table
    op.create_table(
        'credit_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('package', sa.String(50), nullable=False),
        sa.Column('credits_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('price_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),
        sa.Column('stripe_charge_id', sa.String(255), nullable=True),
        sa.Column('payment_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('is_auto_recharge', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_credit_purchases_user_status', 'credit_purchases', ['user_id', 'payment_status'])

    # Create credit_transactions table
    op.execute("""
        CREATE TABLE credit_transactions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            transaction_type transactiontype NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            balance_after NUMERIC(12, 2) NOT NULL,
            description TEXT,
            meta_data JSONB DEFAULT '{}',
            purchase_id UUID REFERENCES credit_purchases(id) ON DELETE SET NULL,
            usage_id UUID,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.create_index('ix_credit_transactions_user_id', 'credit_transactions', ['user_id'])
    op.create_index('ix_credit_transactions_transaction_type', 'credit_transactions', ['transaction_type'])
    op.create_index('ix_credit_transactions_user_type', 'credit_transactions', ['user_id', 'transaction_type'])
    op.create_index('ix_credit_transactions_created_at', 'credit_transactions', ['created_at'])

    # Create credit_usage table
    op.create_table(
        'credit_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('resource_name', sa.String(255), nullable=True),
        sa.Column('credits_used', sa.Numeric(12, 2), nullable=False),
        sa.Column('estimated_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('actual_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('execution_duration_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_credit_usage_user_resource', 'credit_usage', ['user_id', 'resource_type'])
    op.create_index('ix_credit_usage_resource', 'credit_usage', ['resource_type', 'resource_id'])

    # Add foreign key for usage_id in credit_transactions
    op.execute("""
        ALTER TABLE credit_transactions
        ADD CONSTRAINT fk_credit_transactions_usage_id
        FOREIGN KEY (usage_id) REFERENCES credit_usage(id) ON DELETE SET NULL
    """)

    # Create credit_pricing table
    op.create_table(
        'credit_pricing',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resource_type', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('resource_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_cost', sa.Numeric(12, 6), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('multipliers', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create credit_alerts table
    op.create_table(
        'credit_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('threshold', sa.Numeric(12, 2), nullable=True),
        sa.Column('current_balance', sa.Numeric(12, 2), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_credit_alerts_user_unread', 'credit_alerts', ['user_id', 'is_read'])


def downgrade() -> None:
    op.drop_table('credit_alerts')
    op.drop_table('credit_pricing')
    op.drop_table('credit_transactions')
    op.drop_table('credit_usage')
    op.drop_table('credit_purchases')
    op.drop_table('credit_balances')
    op.execute('DROP TYPE IF EXISTS transactiontype')
