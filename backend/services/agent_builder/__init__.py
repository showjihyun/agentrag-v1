"""Agent Builder services package."""

# Note: Using try-except to handle optional imports
# This allows the package to work even if some dependencies are missing

__all__ = [
    "ToolRegistry",
    "VariableResolver",
    "SecretManager",
    "AgentService",
    "BlockService",
    "WorkflowService",
    "KnowledgebaseService",
    "HumanInTheLoop",
    "AutoPromptOptimizer",
    "HierarchicalMemory",
    "AutoAPIIntegrator",
    "CostOptimizer",
]

# Core services (always available)
try:
    from backend.services.agent_builder.tool_registry import ToolRegistry
except ImportError:
    ToolRegistry = None

try:
    from backend.services.agent_builder.variable_resolver import VariableResolver
except ImportError:
    VariableResolver = None

try:
    from backend.services.agent_builder.secret_manager import SecretManager
except ImportError:
    SecretManager = None

try:
    from backend.services.agent_builder.agent_service import AgentService
except ImportError:
    AgentService = None

try:
    from backend.services.agent_builder.block_service import BlockService
except ImportError:
    BlockService = None

try:
    from backend.services.agent_builder.workflow_service import WorkflowService
except ImportError:
    WorkflowService = None

try:
    from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
except ImportError:
    KnowledgebaseService = None

# New features (Sim.ai improvements)
try:
    from backend.services.agent_builder.human_in_loop import HumanInTheLoop
except ImportError:
    HumanInTheLoop = None

try:
    from backend.services.agent_builder.prompt_optimizer import AutoPromptOptimizer
except ImportError:
    AutoPromptOptimizer = None

try:
    from backend.services.agent_builder.hierarchical_memory import HierarchicalMemory
except ImportError:
    HierarchicalMemory = None

try:
    from backend.services.agent_builder.api_integrator import AutoAPIIntegrator
except ImportError:
    AutoAPIIntegrator = None

try:
    from backend.services.agent_builder.cost_optimizer import CostOptimizer
except ImportError:
    CostOptimizer = None
