"""
Router registration module.

Centralizes all API router imports and registration.
"""

from fastapi import FastAPI
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


def register_core_routers(app: FastAPI) -> None:
    """Register core API routers."""
    from backend.api import (
        auth,
        conversations,
        documents,
        query,
        tasks,
        feedback,
        analytics,
        health,
        confidence,
        permissions,
        metrics,
        config,
        database_metrics,
        export,
        share,
        bookmarks,
        dashboard,
        notifications,
        usage,
        models,
        react_stats,
        advanced_rag,
        enterprise,
        monitoring_stats,
        web_search,
        monitoring as monitoring_api,
        paddleocr_advanced,
        document_preview,
        pool_metrics,
        cache_metrics,
        admin,
        circuit_breaker_status,
        knowledge_base,
        llm_settings,
        cache_management,
        auth_sessions,
        exports as exports_api,
        chat_history as chat_history_api,
    )
    from backend.api.v1 import health as health_v1
    from backend.api.security import api_keys as security_api_keys

    # Legacy health router (backward compatibility)
    app.include_router(health.router)

    # v1 API routers (Kubernetes-ready health checks)
    app.include_router(health_v1.router)
    app.include_router(auth.router)
    app.include_router(conversations.router)
    app.include_router(documents.router)
    app.include_router(query.router)
    app.include_router(tasks.router)
    app.include_router(feedback.router)
    app.include_router(analytics.router)
    app.include_router(confidence.router)
    app.include_router(permissions.router)
    app.include_router(metrics.router)
    app.include_router(config.router)
    app.include_router(database_metrics.router)
    app.include_router(models.router)
    
    # Priority 2 & 3 features
    app.include_router(export.router)
    app.include_router(share.router)
    app.include_router(bookmarks.router)
    app.include_router(dashboard.router)
    app.include_router(notifications.router)
    app.include_router(usage.router)
    
    # ReAct Statistics API
    app.include_router(react_stats.router)
    
    # Monitoring APIs
    app.include_router(monitoring_stats.router)
    app.include_router(monitoring_api.router)
    
    # Advanced RAG API (Priority 3)
    app.include_router(advanced_rag.router)
    
    # Enterprise API (Priority 4)
    app.include_router(enterprise.router)
    
    # Web Search API
    app.include_router(web_search.router)
    
    # PaddleOCR Advanced API
    app.include_router(paddleocr_advanced.router)
    app.include_router(document_preview.router)
    
    # Connection Pool & Cache Metrics
    app.include_router(pool_metrics.router)
    app.include_router(cache_metrics.router)
    
    # Admin API
    app.include_router(admin.router)
    
    # Knowledge Base & LLM Settings
    app.include_router(knowledge_base.router)
    app.include_router(llm_settings.router)
    
    # Circuit Breaker Status (Phase 1 Architecture)
    app.include_router(circuit_breaker_status.router)
    
    # Cache Management (Priority 9)
    app.include_router(cache_management.router)
    
    # Session Management
    app.include_router(auth_sessions.router)
    
    # PDF Export & Chat History
    app.include_router(exports_api.router)
    app.include_router(chat_history_api.router)
    
    # Security API (API Key Management)
    app.include_router(security_api_keys.router)
    
    logger.info("Core routers registered")


def register_agent_builder_routers(app: FastAPI) -> None:
    """Register Agent Builder API routers."""
    logger.info("Starting Agent Builder router registration...")
    
    try:
        from backend.api.agent_builder import (
            agents,
            blocks,
            workflows,
            knowledgebases,
            variables,
            executions,
            permissions,
            audit_logs,
            dashboard,
            oauth,
            webhooks,
            chat,
            memory,
            cost,
            branches,
            collaboration,
            prompt_optimization,
            insights as insights_old,
            marketplace,
            advanced_export,
            tools,
            analytics,
            custom_tools,
            api_keys,
            workflow_generator,
            agent_chat,
            kb_monitoring,
            embedding_models,
            milvus_admin,
            triggers,
            approvals,
            templates,
            versions,
            tool_execution,
            tool_metrics,
            tool_marketplace,
            tool_config,
            workflow_debug,
            workflow_monitoring,
            ai_assistant,
            ai_agent_chat,
            cost_tracking,
            agent_team,
            workflow_templates,
            workflow_nlp_generator,
            code_execution,
            ai_copilot,
            code_debugger,
            code_analyzer,
            code_profiler,
            code_secrets,
            flows,
            embed,
            flow_templates,
            chatflow_chat,
            prometheus_metrics,
            agentflow_execution,
            environment_variables,
            user_settings,
            workflow_execution_stream,
            ai_agent_stream,
            memory_management,
            nlp_generator,
            insights,
        )
        logger.info("Standard Agent Builder modules imported successfully")
    except Exception as e:
        logger.error(f"Failed to import standard Agent Builder modules: {e}")
        raise
    
    # Try to import A2A module separately
    try:
        from backend.api.agent_builder import a2a_simple as a2a
        logger.info("A2A simple module imported successfully")
    except Exception as e:
        logger.error(f"Failed to import A2A simple module: {e}")
        # Continue without A2A for now
        a2a = None

    # Dashboard & Core
    app.include_router(dashboard.router)
    app.include_router(agents.router)
    app.include_router(blocks.router)
    app.include_router(workflows.router)
    app.include_router(knowledgebases.router)
    app.include_router(variables.router)
    app.include_router(executions.router)
    app.include_router(permissions.router)
    app.include_router(audit_logs.router)
    app.include_router(oauth.router)
    app.include_router(webhooks.router)
    app.include_router(chat.router)
    
    # Memory & Cost
    app.include_router(memory.router)
    app.include_router(cost.router)
    
    # Collaboration
    app.include_router(branches.router)
    app.include_router(collaboration.router)
    
    # AI Features
    app.include_router(prompt_optimization.router)
    app.include_router(insights_old.router)
    app.include_router(ai_assistant.router)
    app.include_router(ai_agent_chat.router)
    app.include_router(ai_copilot.router)
    
    # NLP Generator & Insights (New)
    app.include_router(nlp_generator.router)
    app.include_router(insights.router)
    
    # Marketplace & Export
    app.include_router(marketplace.router)
    app.include_router(advanced_export.router)
    
    # Tools
    app.include_router(api_keys.router)
    app.include_router(tools.router)
    app.include_router(analytics.router)
    app.include_router(custom_tools.router)
    app.include_router(tool_execution.router)
    app.include_router(tool_metrics.router)
    app.include_router(tool_marketplace.router)
    app.include_router(tool_config.router)
    
    # Workflow
    app.include_router(workflow_generator.router)
    app.include_router(workflow_debug.router)
    app.include_router(workflow_monitoring.router)
    app.include_router(workflow_templates.router)
    app.include_router(workflow_nlp_generator.router)
    
    # Knowledge Base
    app.include_router(agent_chat.router)
    app.include_router(kb_monitoring.router)
    app.include_router(embedding_models.router)
    app.include_router(milvus_admin.router)
    
    # Triggers & Approvals
    app.include_router(triggers.router)
    app.include_router(approvals.router)
    
    # Templates & Versions
    app.include_router(templates.router)
    app.include_router(versions.router)
    
    # Cost Tracking
    app.include_router(cost_tracking.router)
    
    # Agent Team
    app.include_router(agent_team.router)
    
    # Code Execution
    app.include_router(code_execution.router)
    app.include_router(code_debugger.router)
    app.include_router(code_analyzer.router)
    app.include_router(code_profiler.router)
    app.include_router(code_secrets.router)
    
    # Flows (Agentflow & Chatflow)
    app.include_router(flows.router)
    app.include_router(embed.router)
    app.include_router(flow_templates.router)
    app.include_router(chatflow_chat.router)
    app.include_router(agentflow_execution.router)
    
    # Metrics
    app.include_router(prometheus_metrics.router)
    
    # Environment & Settings
    app.include_router(environment_variables.router, prefix="/api/agent-builder", tags=["environment-variables"])
    app.include_router(user_settings.router)
    
    # Streaming
    app.include_router(workflow_execution_stream.router, prefix="/api/agent-builder", tags=["workflow-execution-stream"])
    app.include_router(ai_agent_stream.router)
    
    # Memory Management
    app.include_router(memory_management.router)
    
    # A2A Protocol (Google Agent-to-Agent)
    if a2a is not None:
        try:
            app.include_router(a2a.router, prefix="/api/agent-builder", tags=["a2a-protocol"])
            logger.info("A2A router registered successfully")
        except Exception as e:
            logger.error(f"Failed to register A2A router: {e}")
    else:
        logger.warning("A2A module not available, skipping router registration")
    
    logger.info("Agent Builder routers registered")


def register_v2_routers(app: FastAPI) -> None:
    """Register v2 API routers."""
    from backend.api.v2 import workflows as v2_workflows
    from backend.api.v2 import auth as v2_auth
    
    app.include_router(v2_workflows.router)
    app.include_router(v2_auth.router)
    
    logger.info("v2 API routers registered")


def register_all_routers(app: FastAPI) -> None:
    """Register all API routers."""
    register_core_routers(app)
    register_agent_builder_routers(app)
    register_v2_routers(app)
    logger.info("All routers registered successfully")
