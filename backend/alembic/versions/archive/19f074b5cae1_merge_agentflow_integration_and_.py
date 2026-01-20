"""merge agentflow integration and knowledge graph

Revision ID: 19f074b5cae1
Revises: add_agentflow_integration_fields, add_knowledge_graph_tables
Create Date: 2025-12-26 01:41:09.165353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19f074b5cae1'
down_revision: Union[str, None] = ('add_agentflow_integration_fields', 'add_knowledge_graph_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
