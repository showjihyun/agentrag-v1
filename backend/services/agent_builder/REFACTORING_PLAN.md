# Service Layer Refactoring Plan

## Current State Analysis

**Total Python files in root**: 80+ files
**Problem**: Flat structure makes navigation and maintenance difficult

## Target Structure

```
backend/services/agent_builder/
├── domain/                    # ✅ Already well-structured
├── application/               # ✅ Already well-structured
├── infrastructure/            # ✅ Already well-structured
├── shared/                    # ✅ Already well-structured
│
├── services/                  # 🆕 NEW: Business services organized by domain
│   ├── __init__.py
│   │
│   ├── workflow/              # Workflow-related services
│   │   ├── __init__.py
│   │   ├── workflow_service.py
│   │   ├── workflow_executor.py
│   │   ├── workflow_executor_v2.py
│   │   ├── workflow_validator.py
│   │   ├── workflow_optimizer.py
│   │   ├── workflow_versioning.py
│   │   ├── workflow_version_service.py
│   │   ├── workflow_generator.py
│   │   ├── workflow_template_service.py
│   │   ├── workflow_cache.py
│   │   ├── workflow_debugger.py
│   │   ├── workflow_logger.py
│   │   ├── workflow_metrics.py
│   │   ├── workflow_monitor.py
│   │   ├── workflow_monitoring.py
│   │   ├── workflow_security.py
│   │   ├── workflow_state_manager.py
│   │   ├── workflow_testing.py
│   │   ├── workflow_rate_limiter.py
│   │   ├── workflow_event_bus.py
│   │   └── workflow_errors.py
│   │
│   ├── agent/                 # Agent-related services
│   │   ├── __init__.py
│   │   ├── agent_service.py
│   │   ├── agent_service_refactored.py
│   │   ├── agent_executor.py
│   │   ├── enhanced_agent_executor.py
│   │   ├── agent_aggregate.py
│   │   ├── agent_collaboration.py
│   │   ├── agent_marketplace.py
│   │   ├── agent_monitoring.py
│   │   ├── agent_optimizer.py
│   │   ├── agent_sandbox.py
│   │   ├── agent_team_orchestrator.py
│   │   ├── agent_templates.py
│   │   ├── agent_test_suite.py
│   │   ├── agent_testing.py
│   │   ├── agent_versioning.py
│   │   ├── agentflow_executor.py
│   │   ├── multi_agent_orchestrator.py
│   │   └── resilient_agent_service.py
│   │
│   ├── execution/             # Execution-related services
│   │   ├── __init__.py
│   │   ├── parallel_executor.py
│   │   ├── checkpoint_recovery.py
│   │   ├── block_executor.py
│   │   └── block_executor_secure.py
│   │
│   ├── knowledge/             # Knowledge base services
│   │   ├── __init__.py
│   │   ├── knowledgebase_service.py
│   │   ├── knowledgebase_service_enhanced.py
│   │   ├── knowledgebase_korean_processor.py
│   │   ├── knowledgebase_user_settings.py
│   │   ├── korean_text_processor.py
│   │   ├── bm25_persistent_index.py
│   │   └── query_optimizer.py
│   │
│   ├── analytics/             # Analytics and insights
│   │   ├── __init__.py
│   │   ├── insights_service.py
│   │   ├── stats_service.py
│   │   ├── cost_service.py
│   │   ├── cost_optimizer.py
│   │   └── performance_optimizer.py
│   │
│   ├── ai/                    # AI-powered services
│   │   ├── __init__.py
│   │   ├── nlp_generator.py
│   │   ├── nlp_workflow_service.py
│   │   ├── ai_assistant.py
│   │   ├── ai_agent_generator.py
│   │   ├── ai_workflow_optimizer.py
│   │   └── prompt_optimizer.py
│   │
│   ├── tools/                 # Tool management
│   │   ├── __init__.py
│   │   ├── tool_registry.py
│   │   ├── tool_executor.py
│   │   └── tool_execution_helper.py
│   │
│   ├── flow/                  # Flow services (chatflow/agentflow)
│   │   ├── __init__.py
│   │   └── chatflow_service.py
│   │
│   ├── memory/                # Memory services
│   │   ├── __init__.py
│   │   ├── memory_service.py
│   │   ├── hierarchical_memory.py
│   │   └── shared_memory_pool.py
│   │
│   ├── integration/           # External integrations
│   │   ├── __init__.py
│   │   └── api_integrator.py
│   │
│   ├── security/              # Security services
│   │   ├── __init__.py
│   │   ├── permission_system.py
│   │   └── secret_manager.py
│   │
│   ├── infrastructure_services/  # Infrastructure utilities
│   │   ├── __init__.py
│   │   ├── audit_logger.py
│   │   ├── circuit_breaker.py
│   │   ├── dead_letter_queue.py
│   │   ├── dlq_processor.py
│   │   ├── distributed_lock.py
│   │   ├── distributed_tracing.py
│   │   ├── error_handler.py
│   │   ├── hooks.py
│   │   ├── human_in_loop.py
│   │   ├── idempotency_manager.py
│   │   ├── quota_manager.py
│   │   ├── scheduler.py
│   │   ├── smart_error_recovery.py
│   │   ├── feedback_learning.py
│   │   └── variable_resolver.py
│   │
│   └── block/                 # Block services
│       ├── __init__.py
│       └── block_service.py
│
├── facade.py                  # ✅ Unified API facade (stays at root)
└── dependencies.py            # ✅ Dependency injection (stays at root)
```

## Migration Strategy

### Phase 1: Create Directory Structure (30 min)
1. Create all service subdirectories
2. Create `__init__.py` files with proper exports

### Phase 2: Move Files (1 hour)
1. Move files to appropriate directories
2. Keep original files temporarily for backward compatibility

### Phase 3: Update Imports (2 hours)
1. Update all internal imports
2. Update API layer imports
3. Update test imports

### Phase 4: Create Compatibility Layer (1 hour)
1. Add re-exports in root `__init__.py` for backward compatibility
2. Add deprecation warnings

### Phase 5: Test & Verify (1 hour)
1. Run all tests
2. Fix any import issues
3. Verify application starts correctly

### Phase 6: Cleanup (30 min)
1. Remove old files
2. Update documentation
3. Remove deprecation warnings

## Backward Compatibility Strategy

```python
# backend/services/agent_builder/__init__.py
"""
Agent Builder Services

This module provides backward compatibility for imports.
New code should import from specific service modules.
"""

import warnings

# Workflow services
from .services.workflow.workflow_service import WorkflowService
from .services.workflow.workflow_executor import WorkflowExecutor

# Agent services
from .services.agent.agent_service import AgentService
from .services.agent.agent_executor import AgentExecutor

# Analytics
from .services.analytics.insights_service import InsightsService

# AI services
from .services.ai.nlp_generator import NLPWorkflowGenerator

# ... etc

def _deprecated_import(old_path: str, new_path: str):
    warnings.warn(
        f"Importing from '{old_path}' is deprecated. "
        f"Use '{new_path}' instead.",
        DeprecationWarning,
        stacklevel=3
    )

# Maintain old import paths with deprecation warnings
__all__ = [
    'WorkflowService',
    'WorkflowExecutor',
    'AgentService',
    'AgentExecutor',
    'InsightsService',
    'NLPWorkflowGenerator',
    # ... etc
]
```

## File Mapping

### Workflow Services (21 files)
- workflow_service.py → services/workflow/
- workflow_executor.py → services/workflow/
- workflow_executor_v2.py → services/workflow/
- workflow_validator.py → services/workflow/
- workflow_optimizer.py → services/workflow/
- workflow_versioning.py → services/workflow/
- workflow_version_service.py → services/workflow/
- workflow_generator.py → services/workflow/
- workflow_template_service.py → services/workflow/
- workflow_cache.py → services/workflow/
- workflow_debugger.py → services/workflow/
- workflow_logger.py → services/workflow/
- workflow_metrics.py → services/workflow/
- workflow_monitor.py → services/workflow/
- workflow_monitoring.py → services/workflow/
- workflow_security.py → services/workflow/
- workflow_state_manager.py → services/workflow/
- workflow_testing.py → services/workflow/
- workflow_rate_limiter.py → services/workflow/
- workflow_event_bus.py → services/workflow/
- workflow_errors.py → services/workflow/

### Agent Services (19 files)
- agent_service.py → services/agent/
- agent_service_refactored.py → services/agent/
- agent_executor.py → services/agent/
- enhanced_agent_executor.py → services/agent/
- agent_aggregate.py → services/agent/
- agent_collaboration.py → services/agent/
- agent_marketplace.py → services/agent/
- agent_monitoring.py → services/agent/
- agent_optimizer.py → services/agent/
- agent_sandbox.py → services/agent/
- agent_team_orchestrator.py → services/agent/
- agent_templates.py → services/agent/
- agent_test_suite.py → services/agent/
- agent_testing.py → services/agent/
- agent_versioning.py → services/agent/
- agentflow_executor.py → services/agent/
- multi_agent_orchestrator.py → services/agent/
- resilient_agent_service.py → services/agent/

### Execution Services (4 files)
- parallel_executor.py → services/execution/
- checkpoint_recovery.py → services/execution/
- block_executor.py → services/execution/
- block_executor_secure.py → services/execution/

### Knowledge Services (7 files)
- knowledgebase_service.py → services/knowledge/
- knowledgebase_service_enhanced.py → services/knowledge/
- knowledgebase_korean_processor.py → services/knowledge/
- knowledgebase_user_settings.py → services/knowledge/
- korean_text_processor.py → services/knowledge/
- bm25_persistent_index.py → services/knowledge/
- query_optimizer.py → services/knowledge/

### Analytics Services (5 files)
- insights_service.py → services/analytics/
- stats_service.py → services/analytics/
- cost_service.py → services/analytics/
- cost_optimizer.py → services/analytics/
- performance_optimizer.py → services/analytics/

### AI Services (6 files)
- nlp_generator.py → services/ai/
- nlp_workflow_service.py → services/ai/
- ai_assistant.py → services/ai/
- ai_agent_generator.py → services/ai/
- ai_workflow_optimizer.py → services/ai/
- prompt_optimizer.py → services/ai/

### Tool Services (3 files)
- tool_registry.py → services/tools/
- tool_executor.py → services/tools/
- tool_execution_helper.py → services/tools/

### Flow Services (1 file)
- chatflow_service.py → services/flow/

### Memory Services (3 files)
- memory_service.py → services/memory/
- hierarchical_memory.py → services/memory/
- shared_memory_pool.py → services/memory/

### Integration Services (1 file)
- api_integrator.py → services/integration/

### Security Services (2 files)
- permission_system.py → services/security/
- secret_manager.py → services/security/

### Infrastructure Services (15 files)
- audit_logger.py → services/infrastructure_services/
- circuit_breaker.py → services/infrastructure_services/
- dead_letter_queue.py → services/infrastructure_services/
- dlq_processor.py → services/infrastructure_services/
- distributed_lock.py → services/infrastructure_services/
- distributed_tracing.py → services/infrastructure_services/
- error_handler.py → services/infrastructure_services/
- hooks.py → services/infrastructure_services/
- human_in_loop.py → services/infrastructure_services/
- idempotency_manager.py → services/infrastructure_services/
- quota_manager.py → services/infrastructure_services/
- scheduler.py → services/infrastructure_services/
- smart_error_recovery.py → services/infrastructure_services/
- feedback_learning.py → services/infrastructure_services/
- variable_resolver.py → services/infrastructure_services/

### Block Services (1 file)
- block_service.py → services/block/

## Total: 88 files to reorganize

## Risk Mitigation

1. **Backward Compatibility**: Keep old import paths working
2. **Incremental Migration**: Move one category at a time
3. **Comprehensive Testing**: Run full test suite after each category
4. **Rollback Plan**: Keep original files until fully verified
5. **Documentation**: Update all docs with new import paths

## Success Criteria

- ✅ All tests pass
- ✅ Application starts without errors
- ✅ No import errors in any module
- ✅ Backward compatibility maintained
- ✅ Documentation updated
- ✅ Developer feedback positive

## Timeline

- **Day 1**: Phase 1-2 (Structure + Move files)
- **Day 2**: Phase 3 (Update imports)
- **Day 3**: Phase 4-5 (Compatibility + Testing)
- **Day 4**: Phase 6 (Cleanup + Documentation)
- **Day 5**: Buffer for issues

## Next Steps

1. Get approval for structure
2. Create feature branch
3. Execute migration
4. Review and merge
