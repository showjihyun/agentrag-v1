"""merge_multiple_heads

Revision ID: 641d3018cdb5
Revises: 003_conversation_shares, 004_add_workflow_blocks_and_triggers, add_query_logs_001
Create Date: 2025-11-02 22:09:32.893741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '641d3018cdb5'
down_revision: Union[str, None] = ('003_conversation_shares', '004_add_workflow_blocks_and_triggers', 'add_query_logs_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
