"""Update node_type constraint to support all node types

Revision ID: update_node_types_001
Revises: b667d05f8afb
Create Date: 2024-11-14 22:56:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_node_types_001'
down_revision = 'b667d05f8afb'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema"""
    
    # Drop old constraint
    op.drop_constraint('check_node_type_valid', 'workflow_nodes', type_='check')
    
    # Add new constraint with all node types
    op.create_check_constraint(
        'check_node_type_valid',
        'workflow_nodes',
        """node_type IN (
            'start', 'end', 'agent', 'block', 'condition', 'switch',
            'loop', 'parallel', 'delay', 'merge', 'http_request', 'code',
            'slack', 'discord', 'email', 'google_drive', 's3', 'database',
            'memory', 'human_approval', 'consensus', 'manager_agent',
            'webhook_trigger', 'schedule_trigger', 'webhook_response',
            'trigger', 'try_catch', 'control'
        )"""
    )
    
    # Also update edge_type constraint if it exists
    try:
        op.drop_constraint('check_edge_type_valid', 'workflow_edges', type_='check')
        op.create_check_constraint(
            'check_edge_type_valid',
            'workflow_edges',
            "edge_type IN ('normal', 'conditional', 'true', 'false', 'custom')"
        )
    except:
        # Constraint might not exist in older versions
        pass


def downgrade():
    """Downgrade database schema"""
    
    # Drop new constraint
    op.drop_constraint('check_node_type_valid', 'workflow_nodes', type_='check')
    
    # Restore old constraint
    op.create_check_constraint(
        'check_node_type_valid',
        'workflow_nodes',
        "node_type IN ('agent', 'block', 'control')"
    )
    
    # Restore old edge constraint if it was updated
    try:
        op.drop_constraint('check_edge_type_valid', 'workflow_edges', type_='check')
        op.create_check_constraint(
            'check_edge_type_valid',
            'workflow_edges',
            "edge_type IN ('normal', 'conditional')"
        )
    except:
        pass
