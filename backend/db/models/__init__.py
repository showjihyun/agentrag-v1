"""Database models package."""

from backend.db.models.user import User
from backend.db.models.conversation import Session, Message, MessageSource
from backend.db.models.conversation_share import ConversationShare, ShareRole
from backend.db.models.document import Document, BatchUpload
from backend.db.models.feedback import AnswerFeedback
from backend.db.models.usage import UsageLog
from backend.db.models.oauth import OAuthCredential, OAuthState
from backend.db.models.api_keys import APIKey
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
from backend.db.models.flows import (
    # Flow models
    Agentflow,
    AgentflowAgent,
    Chatflow,
    ChatflowTool,
    ChatSession,
    ChatMessage,
    FlowExecution,
    NodeExecution,
    ExecutionLog,
    MarketplaceItem,
    # Extended flow models
    FlowTemplate,
    TokenUsage,
    ModelPricing,
    EmbedConfig,
    MarketplaceReview,
)
from backend.db.models.plugin import (
    PluginRegistry,
    PluginConfiguration,
    PluginMetric,
    PluginDependency,
    PluginAuditLog,
    PluginSecurityScan,
)

__all__ = [
    "User",
    "Session",
    "Message",
    "MessageSource",
    "ConversationShare",
    "ShareRole",
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
    # Flow models
    "Agentflow",
    "AgentflowAgent",
    "Chatflow",
    "ChatflowTool",
    "ChatSession",
    "ChatMessage",
    "FlowExecution",
    "NodeExecution",
    "ExecutionLog",
    "APIKey",
    "MarketplaceItem",
    # Extended flow models
    "FlowTemplate",
    "TokenUsage",
    "ModelPricing",
    "EmbedConfig",
    "MarketplaceReview",
    # Plugin models
    "PluginRegistry",
    "PluginConfiguration",
    "PluginMetric",
    "PluginDependency",
    "PluginAuditLog",
    "PluginSecurityScan",
]
