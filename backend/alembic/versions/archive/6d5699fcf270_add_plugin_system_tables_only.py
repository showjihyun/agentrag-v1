"""Add plugin system tables only

Revision ID: 6d5699fcf270
Revises: 0d5a68c86ced
Create Date: 2026-01-10 17:30:44.897537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6d5699fcf270'
down_revision: Union[str, None] = '0d5a68c86ced'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create plugin_registry table
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
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'version', name='uq_plugin_name_version')
    )
    op.create_index('idx_plugin_registry_name', 'plugin_registry', ['name'], unique=False)
    op.create_index('idx_plugin_registry_category', 'plugin_registry', ['category'], unique=False)
    op.create_index('idx_plugin_registry_status', 'plugin_registry', ['status'], unique=False)

    # Create plugin_configurations table
    op.create_table('plugin_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plugin_id', 'user_id', 'environment', name='uq_plugin_config_user_env')
    )
    op.create_index('idx_plugin_configurations_plugin_user', 'plugin_configurations', ['plugin_id', 'user_id'], unique=False)

    # Create plugin_metrics table
    op.create_table('plugin_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(length=255), nullable=False),
        sa.Column('metric_value', sa.String(length=255), nullable=True),
        sa.Column('metric_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plugin_metrics_plugin_time', 'plugin_metrics', ['plugin_id', 'recorded_at'], unique=False)
    op.create_index('idx_plugin_metrics_name', 'plugin_metrics', ['metric_name'], unique=False)

    # Create plugin_dependencies table
    op.create_table('plugin_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_name', sa.String(length=255), nullable=False),
        sa.Column('version_constraint', sa.String(length=100), nullable=True),
        sa.Column('optional', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plugin_dependencies_plugin', 'plugin_dependencies', ['plugin_id'], unique=False)
    op.create_index('idx_plugin_dependencies_name', 'plugin_dependencies', ['dependency_name'], unique=False)

    # Create plugin_audit_logs table
    op.create_table('plugin_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plugin_audit_plugin', 'plugin_audit_logs', ['plugin_id'], unique=False)
    op.create_index('idx_plugin_audit_user', 'plugin_audit_logs', ['user_id'], unique=False)
    op.create_index('idx_plugin_audit_timestamp', 'plugin_audit_logs', ['timestamp'], unique=False)
    op.create_index('idx_plugin_audit_action', 'plugin_audit_logs', ['action'], unique=False)

    # Create plugin_security_scans table
    op.create_table('plugin_security_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plugin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_type', sa.String(length=50), nullable=False),
        sa.Column('scan_result', sa.String(length=20), nullable=False),
        sa.Column('findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scan_version', sa.String(length=20), nullable=True),
        sa.Column('scanned_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugin_registry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plugin_security_plugin', 'plugin_security_scans', ['plugin_id'], unique=False)
    op.create_index('idx_plugin_security_result', 'plugin_security_scans', ['scan_result'], unique=False)
    op.create_index('idx_plugin_security_timestamp', 'plugin_security_scans', ['scanned_at'], unique=False)


def downgrade() -> None:
    # Drop plugin tables in reverse order
    op.drop_table('plugin_security_scans')
    op.drop_table('plugin_audit_logs')
    op.drop_table('plugin_dependencies')
    op.drop_table('plugin_metrics')
    op.drop_table('plugin_configurations')
    op.drop_table('plugin_registry')
