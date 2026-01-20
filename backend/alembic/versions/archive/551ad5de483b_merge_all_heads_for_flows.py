"""merge_all_heads_for_flows

Revision ID: 551ad5de483b
Revises: 006_extended_flows, 6fd293ea7a48, db_optimizations_002, add_dashboard_chat, add_missing_indexes_and_tables, add_user_settings_001
Create Date: 2025-12-06 00:39:18.639924

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '551ad5de483b'
down_revision: Union[str, None] = ('006_extended_flows', '6fd293ea7a48', 'db_optimizations_002', 'add_dashboard_chat', 'add_missing_indexes_and_tables', 'add_user_settings_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
