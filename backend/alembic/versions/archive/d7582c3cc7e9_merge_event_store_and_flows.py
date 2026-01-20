"""merge_event_store_and_flows

Revision ID: d7582c3cc7e9
Revises: 008_add_event_store, 551ad5de483b
Create Date: 2025-12-06 20:30:13.888090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7582c3cc7e9'
down_revision: Union[str, None] = ('008_add_event_store', '551ad5de483b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
