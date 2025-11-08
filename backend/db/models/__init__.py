"""Database models package."""

from backend.db.models.user import User
from backend.db.models.conversation import Session, Message, MessageSource
from backend.db.models.document import Document, BatchUpload
from backend.db.models.feedback import AnswerFeedback
from backend.db.models.usage import UsageLog
from backend.db.models.oauth import OAuthCredential, OAuthState
from backend.db.models.agent_builder import (
    # Agent models
    Agent,
    AgentVersion,
    Tool,
    AgentTool,
    AgentTemplate,
    PromptTemplate,
    PromptTemplateVersion,
    # Block models
    Block,
    BlockVersion,
    BlockDependency,
    BlockTestCase,
    # Workflow models
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowExecution,
    # Knowledgebase models
    Knowledgebase,
    KnowledgebaseDocument,
    KnowledgebaseVersion,
    AgentKnowledgebase,
    # Variable models
    Variable,
    Secret,
    # Execution models
    AgentExecution,
    ExecutionStep,
    ExecutionMetrics,
    ExecutionSchedule,
    # Permission models
    Permission,
    ResourceShare,
    AuditLog,
)

__all__ = [
    "User",
    "Session",
    "Message",
    "MessageSource",
    "Document",
    "BatchUpload",
    "AnswerFeedback",
    "UsageLog",
    # OAuth models
    "OAuthCredential",
    "OAuthState",
    # Agent Builder models
    "Agent",
    "AgentVersion",
    "Tool",
    "AgentTool",
    "AgentTemplate",
    "PromptTemplate",
    "PromptTemplateVersion",
    "Block",
    "BlockVersion",
    "BlockDependency",
    "BlockTestCase",
    "Workflow",
    "WorkflowNode",
    "WorkflowEdge",
    "WorkflowExecution",
    "Knowledgebase",
    "KnowledgebaseDocument",
    "KnowledgebaseVersion",
    "AgentKnowledgebase",
    "Variable",
    "Secret",
    "AgentExecution",
    "ExecutionStep",
    "ExecutionMetrics",
    "ExecutionSchedule",
    "Permission",
    "ResourceShare",
    "AuditLog",
]
