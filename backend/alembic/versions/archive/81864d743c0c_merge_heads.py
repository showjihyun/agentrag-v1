"""merge_heads

Revision ID: 81864d743c0c
Revises: 1b2f835c30e5, update_node_types_001
Create Date: 2025-11-15 15:10:59.143280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81864d743c0c'
down_revision: Union[str, None] = ('1b2f835c30e5', 'update_node_types_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
