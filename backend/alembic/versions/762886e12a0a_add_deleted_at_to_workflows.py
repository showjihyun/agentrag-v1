"""add_deleted_at_to_workflows

Revision ID: 762886e12a0a
Revises: 009_add_flows_tables
Create Date: 2025-12-21 23:06:54.992059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '762886e12a0a'
down_revision: Union[str, None] = '009_add_flows_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at column to workflows table for soft delete support
    op.add_column('workflows', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Add index for better query performance on deleted_at
    op.create_index('ix_workflows_deleted_at', 'workflows', ['deleted_at'])


def downgrade() -> None:
    # Remove the index first
    op.drop_index('ix_workflows_deleted_at', 'workflows')
    
    # Remove the deleted_at column
    op.drop_column('workflows', 'deleted_at')
