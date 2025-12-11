"""
Agent Builder Services

This module provides backward compatibility for imports while organizing
services into logical subdirectories.

New code should import from specific service modules:
    from backend.services.agent_builder.services.workflow import WorkflowService
    from backend.services.agent_builder.services.agent import AgentService

Old imports will continue to work but may show deprecation warnings in the future.
"""

import warnings
from typing import Any

# Import from new locations for backward compatibility
try:
    from .services.workflow.workflow_service import WorkflowService
    from .services.workflow.workflow_executor import WorkflowExecutor
    from .services.workflow.workflow_validator import WorkflowValidator
except ImportError:
    # Fallback to old location if new structure not ready
    try:
        from .workflow_service import WorkflowService
        from .workflow_executor import WorkflowExecutor
        from .workflow_validator import WorkflowValidator
    except ImportError:
        pass

try:
    from .services.agent.agent_service import AgentService
    from .services.agent.agent_executor import AgentExecutor
    from .services.agent.agentflow_executor import AgentflowExecutor
except ImportError:
    try:
        from .agent_service import AgentService
        from .agent_executor import AgentExecutor
        from .agentflow_executor import AgentflowExecutor
    except ImportError:
        pass

try:
    from .services.analytics.insights_service import InsightsService
    from .services.analytics.stats_service import StatsService
    from .services.analytics.cost_service import CostService
except ImportError:
    try:
        from .insights_service import InsightsService
        from .stats_service import StatsService
        from .cost_service import CostService
    except ImportError:
        pass

try:
    from .services.ai.nlp_generator import NLPWorkflowGenerator
    from .services.ai.ai_assistant import AIAssistant
    from .services.ai.prompt_optimizer import PromptOptimizer
except ImportError:
    try:
        from .nlp_generator import NLPWorkflowGenerator
        from .ai_assistant import AIAssistant
        from .prompt_optimizer import PromptOptimizer
    except ImportError:
        pass

try:
    from .services.flow.chatflow_service import ChatflowService
except ImportError:
    try:
        from .chatflow_service import ChatflowService
    except ImportError:
        pass

try:
    from .services.tools.tool_registry import ToolRegistry
    from .services.tools.tool_executor import ToolExecutor
except ImportError:
    try:
        from .tool_registry import ToolRegistry
        from .tool_executor import ToolExecutor
    except ImportError:
        pass

try:
    from .services.memory.memory_service import MemoryService
except ImportError:
    try:
        from .memory_service import MemoryService
    except ImportError:
        pass

try:
    from .services.block.block_service import BlockService
except ImportError:
    try:
        from .block_service import BlockService
    except ImportError:
        pass

try:
    from .services.knowledge.knowledgebase_service import KnowledgebaseService
except ImportError:
    try:
        from .knowledgebase_service import KnowledgebaseService
    except ImportError:
        pass

try:
    from .services.security.permission_system import PermissionSystem
    from .services.security.secret_manager import SecretManager
except ImportError:
    try:
        from .permission_system import PermissionSystem
        from .secret_manager import SecretManager
    except ImportError:
        pass

try:
    from .services.infrastructure_services.circuit_breaker import CircuitBreaker
    from .services.infrastructure_services.scheduler import Scheduler
except ImportError:
    try:
        from .circuit_breaker import CircuitBreaker
        from .scheduler import Scheduler
    except ImportError:
        pass

# Keep facade and dependencies at root level
from .facade import AgentBuilderFacade
from .dependencies import (
    get_agent_builder_facade,
    get_workflow_service,
    get_agent_service,
    get_execution_service,
    get_unified_executor,
    get_event_bus,
)

__all__ = [
    # Facade
    'AgentBuilderFacade',
    'get_agent_builder_facade',
    
    # Dependencies
    'get_workflow_service',
    'get_agent_service',
    'get_execution_service',
    'get_unified_executor',
    'get_event_bus',
    
    # Workflow
    'WorkflowService',
    'WorkflowExecutor',
    'WorkflowValidator',
    
    # Agent
    'AgentService',
    'AgentExecutor',
    'AgentflowExecutor',
    
    # Analytics
    'InsightsService',
    'StatsService',
    'CostService',
    
    # AI
    'NLPWorkflowGenerator',
    'AIAssistant',
    'PromptOptimizer',
    
    # Flow
    'ChatflowService',
    
    # Tools
    'ToolRegistry',
    'ToolExecutor',
    
    # Memory
    'MemoryService',
    
    # Block
    'BlockService',
    
    # Knowledge
    'KnowledgebaseService',
    
    # Security
    'PermissionSystem',
    'SecretManager',
    
    # Infrastructure
    'CircuitBreaker',
    'Scheduler',
]


def __getattr__(name: str) -> Any:
    """
    Dynamic attribute access for backward compatibility.
    
    This allows old imports to work while we migrate to the new structure.
    """
    # Try to import from new location
    try:
        if name.startswith('workflow_'):
            module = __import__(
                f'backend.services.agent_builder.services.workflow.{name}',
                fromlist=[name]
            )
            return getattr(module, name.replace('workflow_', '').title().replace('_', ''))
        elif name.startswith('agent_'):
            module = __import__(
                f'backend.services.agent_builder.services.agent.{name}',
                fromlist=[name]
            )
            return getattr(module, name.replace('agent_', '').title().replace('_', ''))
    except (ImportError, AttributeError):
        pass
    
    # Fallback to old location
    try:
        module = __import__(
            f'backend.services.agent_builder.{name}',
            fromlist=[name]
        )
        return module
    except ImportError:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
