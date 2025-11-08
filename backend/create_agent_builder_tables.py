"""Create Agent Builder tables directly."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.db.database import engine, Base
from backend.db.models.agent_builder import (
    Agent,
    AgentVersion,
    Tool,
    AgentTool,
    AgentTemplate,
    PromptTemplate,
    PromptTemplateVersion,
    Block,
    BlockVersion,
    BlockDependency,
    BlockTestCase,
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowExecution,
    AgentBlock,
    AgentEdge,
    WorkflowSchedule,
    WorkflowWebhook,
    WorkflowSubflow,
    Knowledgebase,
    KnowledgebaseDocument,
    KnowledgebaseChunk,
    KnowledgebaseVersion,
    AgentKnowledgebase,
    Variable,
    AgentExecution,
    AgentExecutionStep,
    AgentExecutionMetrics,
    Permission,
    ResourceShare,
    AuditLog,
    OAuthConnection,
    ApprovalRequest,
)

def create_tables():
    """Create all Agent Builder tables."""
    print("Creating Agent Builder tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✅ Agent Builder tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        agent_builder_tables = [
            'agents', 'agent_versions', 'tools', 'agent_tools',
            'agent_templates', 'prompt_templates', 'prompt_template_versions',
            'blocks', 'block_versions', 'block_dependencies', 'block_test_cases',
            'workflows', 'workflow_nodes', 'workflow_edges', 'workflow_executions',
            'agent_blocks', 'agent_edges', 'workflow_schedules', 'workflow_webhooks',
            'workflow_subflows', 'knowledgebases', 'knowledgebase_documents',
            'knowledgebase_chunks', 'knowledgebase_versions', 'agent_knowledgebases',
            'variables', 'agent_executions', 'agent_execution_steps',
            'agent_execution_metrics', 'permissions', 'resource_shares',
            'audit_logs', 'oauth_connections', 'approval_requests'
        ]
        
        print("\nAgent Builder tables in database:")
        for table in agent_builder_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (missing)")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_tables()
