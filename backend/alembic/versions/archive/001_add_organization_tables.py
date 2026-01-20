"""Add organization and team tables for multi-tenancy

Revision ID: 001_org_multitenancy
Revises: 20260115220929
Create Date: 2026-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_org_multitenancy'
down_revision = '20260115220929'  # Latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE organizationrole AS ENUM ('owner', 'admin', 'member', 'viewer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE teamrole AS ENUM ('lead', 'member', 'viewer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('max_members', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_agents', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_workflows', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create organization_members table (using string type for enum to avoid auto-creation)
    op.execute("""
        CREATE TABLE organization_members (
            id UUID PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role organizationrole NOT NULL DEFAULT 'member',
            invited_by UUID REFERENCES users(id),
            invited_at TIMESTAMP NOT NULL DEFAULT now(),
            joined_at TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.create_index('ix_organization_members_organization_id', 'organization_members', ['organization_id'])
    op.create_index('ix_organization_members_user_id', 'organization_members', ['user_id'])
    op.create_index('ix_org_members_org_user', 'organization_members', ['organization_id', 'user_id'], unique=True)

    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_teams_org_slug', 'teams', ['organization_id', 'slug'], unique=True)

    # Create team_members table (using string type for enum to avoid auto-creation)
    op.execute("""
        CREATE TABLE team_members (
            id UUID PRIMARY KEY,
            team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role teamrole NOT NULL DEFAULT 'member',
            added_by UUID REFERENCES users(id),
            added_at TIMESTAMP NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('ix_team_members_team_user', 'team_members', ['team_id', 'user_id'], unique=True)


def downgrade() -> None:
    # Drop tables
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('organization_members')
    op.drop_table('organizations')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS teamrole')
    op.execute('DROP TYPE IF EXISTS organizationrole')
