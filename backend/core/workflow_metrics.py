"""
Workflow Metrics for Prometheus

Provides metrics collection for workflow execution monitoring.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import prometheus_client, make it optional
try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    # Only log prometheus warning in debug mode or if explicitly requested
    import os
    if os.getenv("DEBUG", "false").lower() == "true" or os.getenv("SHOW_PROMETHEUS_WARNING", "false").lower() == "true":
        logger.warning("prometheus_client not installed. Metrics will be disabled. Install with: pip install prometheus-client")
    PROMETHEUS_AVAILABLE = False
    
    # Create dummy classes for when prometheus is not available
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def observe(self, *args, **kwargs):
            pass
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
    
    class Info:
        def __init__(self, *args, **kwargs):
            pass
        def info(self, *args, **kwargs):
            pass

# Workflow execution metrics
workflow_executions_total = Counter(
    'workflow_executions_total',
    'Total number of workflow executions',
    ['workflow_id', 'status', 'user_id']
)

workflow_execution_duration_seconds = Histogram(
    'workflow_execution_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_id'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float('inf'))
)

workflow_node_executions_total = Counter(
    'workflow_node_executions_total',
    'Total number of node executions',
    ['workflow_id', 'node_type', 'status']
)

workflow_node_execution_duration_seconds = Histogram(
    'workflow_node_execution_duration_seconds',
    'Node execution duration in seconds',
    ['node_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float('inf'))
)

workflow_cache_hits_total = Counter(
    'workflow_cache_hits_total',
    'Total number of cache hits',
    ['node_type']
)

workflow_cache_misses_total = Counter(
    'workflow_cache_misses_total',
    'Total number of cache misses',
    ['node_type']
)

workflow_retries_total = Counter(
    'workflow_retries_total',
    'Total number of node execution retries',
    ['node_type', 'attempt']
)

workflow_errors_total = Counter(
    'workflow_errors_total',
    'Total number of workflow errors',
    ['workflow_id', 'error_type']
)

active_workflow_executions = Gauge(
    'active_workflow_executions',
    'Number of currently executing workflows'
)

workflow_queue_size = Gauge(
    'workflow_queue_size',
    'Number of workflows waiting in queue'
)

# Human approval metrics
workflow_approval_requests_total = Counter(
    'workflow_approval_requests_total',
    'Total number of approval requests',
    ['workflow_id']
)

workflow_approval_duration_seconds = Histogram(
    'workflow_approval_duration_seconds',
    'Time taken for approval',
    ['workflow_id', 'status'],
    buckets=(60.0, 300.0, 600.0, 1800.0, 3600.0, 7200.0, 86400.0, float('inf'))
)

# Agent execution metrics
agent_executions_total = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_id', 'status']
)

agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_id'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float('inf'))
)

# LLM API metrics
llm_api_calls_total = Counter(
    'llm_api_calls_total',
    'Total number of LLM API calls',
    ['provider', 'model', 'status']
)

llm_api_duration_seconds = Histogram(
    'llm_api_duration_seconds',
    'LLM API call duration in seconds',
    ['provider', 'model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float('inf'))
)

llm_tokens_used_total = Counter(
    'llm_tokens_used_total',
    'Total number of LLM tokens used',
    ['provider', 'model', 'type']  # type: prompt, completion
)

# Database operation metrics
database_operations_total = Counter(
    'database_operations_total',
    'Total number of database operations',
    ['db_type', 'operation', 'status']
)

database_operation_duration_seconds = Histogram(
    'database_operation_duration_seconds',
    'Database operation duration in seconds',
    ['db_type', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, float('inf'))
)

# Storage operation metrics
storage_operations_total = Counter(
    'storage_operations_total',
    'Total number of storage operations',
    ['service', 'operation', 'status']  # service: s3, google_drive
)

storage_operation_duration_seconds = Histogram(
    'storage_operation_duration_seconds',
    'Storage operation duration in seconds',
    ['service', 'operation'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float('inf'))
)

# System info
workflow_system_info = Info(
    'workflow_system',
    'Workflow system information'
)


class WorkflowMetrics:
    """Helper class for recording workflow metrics."""
    
    @staticmethod
    def record_execution_start(workflow_id: str, user_id: Optional[str] = None):
        """Record workflow execution start."""
        active_workflow_executions.inc()
    
    @staticmethod
    def record_execution_complete(
        workflow_id: str,
        user_id: Optional[str],
        status: str,
        duration: float
    ):
        """Record workflow execution completion."""
        workflow_executions_total.labels(
            workflow_id=workflow_id,
            status=status,
            user_id=user_id or 'anonymous'
        ).inc()
        
        workflow_execution_duration_seconds.labels(
            workflow_id=workflow_id
        ).observe(duration)
        
        active_workflow_executions.dec()
    
    @staticmethod
    def record_node_execution(
        workflow_id: str,
        node_type: str,
        status: str,
        duration: float
    ):
        """Record node execution."""
        workflow_node_executions_total.labels(
            workflow_id=workflow_id,
            node_type=node_type,
            status=status
        ).inc()
        
        workflow_node_execution_duration_seconds.labels(
            node_type=node_type
        ).observe(duration)
    
    @staticmethod
    def record_cache_hit(node_type: str):
        """Record cache hit."""
        workflow_cache_hits_total.labels(node_type=node_type).inc()
    
    @staticmethod
    def record_cache_miss(node_type: str):
        """Record cache miss."""
        workflow_cache_misses_total.labels(node_type=node_type).inc()
    
    @staticmethod
    def record_retry(node_type: str, attempt: int):
        """Record retry attempt."""
        workflow_retries_total.labels(
            node_type=node_type,
            attempt=str(attempt)
        ).inc()
    
    @staticmethod
    def record_error(workflow_id: str, error_type: str):
        """Record workflow error."""
        workflow_errors_total.labels(
            workflow_id=workflow_id,
            error_type=error_type
        ).inc()
    
    @staticmethod
    def record_approval_request(workflow_id: str):
        """Record approval request."""
        workflow_approval_requests_total.labels(
            workflow_id=workflow_id
        ).inc()
    
    @staticmethod
    def record_approval_duration(
        workflow_id: str,
        status: str,
        duration: float
    ):
        """Record approval duration."""
        workflow_approval_duration_seconds.labels(
            workflow_id=workflow_id,
            status=status
        ).observe(duration)
    
    @staticmethod
    def record_llm_call(
        provider: str,
        model: str,
        status: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ):
        """Record LLM API call."""
        llm_api_calls_total.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        llm_api_duration_seconds.labels(
            provider=provider,
            model=model
        ).observe(duration)
        
        if prompt_tokens > 0:
            llm_tokens_used_total.labels(
                provider=provider,
                model=model,
                type='prompt'
            ).inc(prompt_tokens)
        
        if completion_tokens > 0:
            llm_tokens_used_total.labels(
                provider=provider,
                model=model,
                type='completion'
            ).inc(completion_tokens)
    
    @staticmethod
    def record_database_operation(
        db_type: str,
        operation: str,
        status: str,
        duration: float
    ):
        """Record database operation."""
        database_operations_total.labels(
            db_type=db_type,
            operation=operation,
            status=status
        ).inc()
        
        database_operation_duration_seconds.labels(
            db_type=db_type,
            operation=operation
        ).observe(duration)
    
    @staticmethod
    def record_storage_operation(
        service: str,
        operation: str,
        status: str,
        duration: float
    ):
        """Record storage operation."""
        storage_operations_total.labels(
            service=service,
            operation=operation,
            status=status
        ).inc()
        
        storage_operation_duration_seconds.labels(
            service=service,
            operation=operation
        ).observe(duration)
