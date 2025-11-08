"""Add notifications tables

Revision ID: 002_notifications
Revises: 001_bookmarks
Create Date: 2025-10-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_notifications'
down_revision = '001_bookmarks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_type enum
    notification_type = postgresql.ENUM('info', 'success', 'warning', 'error', 'system', name='notificationtype')
    notification_type.create(op.get_bind())
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', notification_type, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('action_label', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('read_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Create indexes for notifications
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('idx_notifications_user_unread', 'notifications', ['user_id', 'is_read'])
    
    # Create notification_settings table
    op.create_table(
        'notification_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('email_notifications', sa.Boolean, default=True),
        sa.Column('push_notifications', sa.Boolean, default=True),
        sa.Column('notify_on_share', sa.Boolean, default=True),
        sa.Column('notify_on_comment', sa.Boolean, default=True),
        sa.Column('notify_on_mention', sa.Boolean, default=True),
        sa.Column('notify_on_system_update', sa.Boolean, default=False),
        sa.Column('quiet_hours_enabled', sa.Boolean, default=False),
        sa.Column('quiet_hours_start', sa.String(5), default='22:00'),
        sa.Column('quiet_hours_end', sa.String(5), default='08:00'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create index for notification_settings
    op.create_index('idx_notification_settings_user_id', 'notification_settings', ['user_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_notification_settings_user_id', table_name='notification_settings')
    op.drop_index('idx_notifications_user_unread', table_name='notifications')
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    
    # Drop tables
    op.drop_table('notification_settings')
    op.drop_table('notifications')
    
    # Drop enum
    notification_type = postgresql.ENUM('info', 'success', 'warning', 'error', 'system', name='notificationtype')
    notification_type.drop(op.get_bind())
