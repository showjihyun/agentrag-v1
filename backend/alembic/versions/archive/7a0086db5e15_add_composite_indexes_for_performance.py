"""add_composite_indexes_for_performance

Revision ID: 7a0086db5e15
Revises: 81864d743c0c
Create Date: 2025-11-15 15:11:06.122538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a0086db5e15'
down_revision: Union[str, None] = '81864d743c0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for performance optimization"""
    
    # WorkflowExecution 복합 인덱스
    op.create_index(
        'ix_workflow_exec_user_workflow_status',
        'workflow_executions',
        ['user_id', 'workflow_id', 'status'],
        unique=False
    )
    op.create_index(
        'ix_workflow_exec_status_started',
        'workflow_executions',
        ['status', 'started_at'],
        unique=False
    )
    op.create_index(
        'ix_workflow_exec_user_started',
        'workflow_executions',
        ['user_id', 'started_at'],
        unique=False
    )
    
    # AgentExecution 복합 인덱스
    op.create_index(
        'ix_agent_exec_user_agent_started',
        'agent_executions',
        ['user_id', 'agent_id', 'started_at'],
        unique=False
    )
    op.create_index(
        'ix_agent_exec_session_status',
        'agent_executions',
        ['session_id', 'status'],
        unique=False
    )
    
    print("✅ Added 5 composite indexes for performance optimization")


def downgrade() -> None:
    """Remove composite indexes"""
    
    # WorkflowExecution 인덱스 제거
    op.drop_index('ix_workflow_exec_user_workflow_status', table_name='workflow_executions')
    op.drop_index('ix_workflow_exec_status_started', table_name='workflow_executions')
    op.drop_index('ix_workflow_exec_user_started', table_name='workflow_executions')
    
    # AgentExecution 인덱스 제거
    op.drop_index('ix_agent_exec_user_agent_started', table_name='agent_executions')
    op.drop_index('ix_agent_exec_session_status', table_name='agent_executions')
