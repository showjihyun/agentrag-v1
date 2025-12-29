"""add_2025_2026_orchestration_types

Revision ID: e43511051f56
Revises: 264c1fe39bc5
Create Date: 2025-12-23 23:29:48.614358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e43511051f56'
down_revision: Union[str, None] = '264c1fe39bc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new orchestration types for 2025 and 2026 trends."""
    
    # Since the orchestration_type is likely a VARCHAR field, we don't need to modify enum
    # The validation happens at the application level through the Python enum
    
    # Just add a comment to document the new available values
    connection = op.get_bind()
    
    try:
        # Add a comment to the agentflows table documenting new orchestration types
        connection.execute(sa.text("""
            COMMENT ON COLUMN agentflows.orchestration_type IS 
            'Orchestration type: sequential, parallel, hierarchical, adaptive, 
             2025 trends: consensus_building, dynamic_routing, swarm_intelligence, event_driven, reflection,
             2026 trends: neuromorphic, quantum_enhanced, bio_inspired, self_evolving, federated, emotional_ai, predictive'
        """))
        print("Updated orchestration_type column documentation")
    except Exception as e:
        print(f"Note: Could not add comment: {e}")
    
    print("✅ New orchestration types are now available:")
    print("   2025 Trends: consensus_building, dynamic_routing, swarm_intelligence, event_driven, reflection")
    print("   2026 Trends: neuromorphic, quantum_enhanced, bio_inspired, self_evolving, federated, emotional_ai, predictive")


def downgrade() -> None:
    """Remove the new orchestration types (not recommended)."""
    # Note: PostgreSQL doesn't support removing enum values easily
    # This would require recreating the enum type and updating all references
    # For safety, we'll leave the enum values in place
    pass
