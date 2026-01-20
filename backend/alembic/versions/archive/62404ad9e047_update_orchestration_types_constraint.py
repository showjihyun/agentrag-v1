"""update_orchestration_types_constraint

Revision ID: 62404ad9e047
Revises: e43511051f56
Create Date: 2025-12-23 23:40:24.747531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62404ad9e047'
down_revision: Union[str, None] = 'e43511051f56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint('check_orchestration_type_valid', 'agentflows', type_='check')
    
    # Add the new constraint with all orchestration types
    op.create_check_constraint(
        'check_orchestration_type_valid',
        'agentflows',
        "orchestration_type IN ("
        "'sequential', 'parallel', 'hierarchical', 'adaptive', "  # Core patterns
        "'consensus_building', 'dynamic_routing', 'swarm_intelligence', 'event_driven', 'reflection', "  # 2025 trends
        "'neuromorphic', 'quantum_enhanced', 'bio_inspired', 'self_evolving', 'federated', 'emotional_ai', 'predictive'"  # 2026 trends
        ")"
    )


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint('check_orchestration_type_valid', 'agentflows', type_='check')
    
    # Restore the old constraint with only core types
    op.create_check_constraint(
        'check_orchestration_type_valid',
        'agentflows',
        "orchestration_type IN ('sequential', 'parallel', 'hierarchical', 'adaptive')"
    )
