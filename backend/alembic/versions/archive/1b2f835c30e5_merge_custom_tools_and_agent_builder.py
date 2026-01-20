"""merge custom tools and agent builder

Revision ID: 1b2f835c30e5
Revises: add_custom_tools_001, b667d05f8afb
Create Date: 2025-11-08 19:15:27.045920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b2f835c30e5'
down_revision: Union[str, None] = ('add_custom_tools_001', 'b667d05f8afb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
