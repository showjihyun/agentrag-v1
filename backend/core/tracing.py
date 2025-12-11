"""
Distributed Tracing with OpenTelemetry

Provides comprehensive tracing for the entire application stack.
"""

import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar
from functools import wraps

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

logger = logging.getLogger(__name__)

# Context variables for request tracking
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')
span_id_var: ContextVar[str] = ContextVar('span_id', default='')

# Global tracer
_tracer: Optional[trace.Tracer] = None


def setup_tracing(
    service_name: str = "agentic-rag",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    enable_console: bool = False
) -> trace.Tracer:
    """
    Setup distributed tracing with OpenTelemetry
    
    Args:
        service_name: Name of the service
        jaeger_host: Jaeger agent host
        jaeger_port: Jaeger agent port
        enable_console: Enable console exporter for debugging
        
    Returns:
        Configured tracer instance
    """
    global _tracer
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "2.0.0",
        "deployment.environment": "production"
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add Jaeger exporter
    try:
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        logger.info(f"Jaeger exporter configured: {jaeger_host}:{jaeger_port}")
    except Exception as e:
        logger.warning(f"Failed to configure Jaeger exporter: {e}")
    
    # Add console exporter for debugging
    if enable_console:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Get tracer
    _tracer = trace.get_tracer(__name__)
    
    logger.info(f"Tracing initialized for service: {service_name}")
    
    return _tracer


def instrument_app(app):
    """
    Instrument FastAPI application with automatic tracing
    
    Args:
        app: FastAPI application instance
    """
    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented for tracing")
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumented for tracing")
        
        # Instrument Redis
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented for tracing")
        
        # Instrument HTTPX
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumented for tracing")
        
    except Exception as e:
        logger.error(f"Failed to instrument application: {e}")


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = setup_tracing()
    return _tracer


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Decorator to trace a function
    
    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes
        
    Example:
        @trace_function(name="process_workflow", attributes={"workflow.type": "chatflow"})
        async def process_workflow(workflow_id: int):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as attributes
                if args:
                    span.set_attribute("function.args", str(args))
                if kwargs:
                    span.set_attribute("function.kwargs", str(kwargs))
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class TracingContext:
    """Context manager for manual span creation"""
    
    def __init__(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.attributes = attributes or {}
        self.span = None
        self.tracer = get_tracer()
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.set_attribute("error", True)
            self.span.set_attribute("error.type", exc_type.__name__)
            self.span.set_attribute("error.message", str(exc_val))
            self.span.record_exception(exc_val)
        self.span.end()
        return False


# Convenience functions for common operations

@trace_function(name="workflow.execute")
async def trace_workflow_execution(workflow_id: int, func, *args, **kwargs):
    """Trace workflow execution"""
    span = trace.get_current_span()
    span.set_attribute("workflow.id", workflow_id)
    
    result = await func(*args, **kwargs)
    
    if hasattr(result, 'status'):
        span.set_attribute("workflow.status", result.status)
    if hasattr(result, 'duration'):
        span.set_attribute("workflow.duration_ms", result.duration)
    
    return result


@trace_function(name="database.query")
def trace_database_query(query: str, func, *args, **kwargs):
    """Trace database query"""
    span = trace.get_current_span()
    span.set_attribute("db.statement", query[:200])  # Truncate long queries
    
    result = func(*args, **kwargs)
    
    if hasattr(result, '__len__'):
        span.set_attribute("db.result_count", len(result))
    
    return result


@trace_function(name="cache.operation")
async def trace_cache_operation(operation: str, key: str, func, *args, **kwargs):
    """Trace cache operation"""
    span = trace.get_current_span()
    span.set_attribute("cache.operation", operation)
    span.set_attribute("cache.key", key)
    
    result = await func(*args, **kwargs)
    
    span.set_attribute("cache.hit", result is not None)
    
    return result


@trace_function(name="llm.call")
async def trace_llm_call(model: str, func, *args, **kwargs):
    """Trace LLM API call"""
    span = trace.get_current_span()
    span.set_attribute("llm.model", model)
    
    result = await func(*args, **kwargs)
    
    if hasattr(result, 'usage'):
        span.set_attribute("llm.tokens", result.usage.total_tokens)
        span.set_attribute("llm.prompt_tokens", result.usage.prompt_tokens)
        span.set_attribute("llm.completion_tokens", result.usage.completion_tokens)
    
    return result


def get_current_trace_id() -> str:
    """Get current trace ID"""
    span = trace.get_current_span()
    if span:
        return format(span.get_span_context().trace_id, '032x')
    return trace_id_var.get()


def get_current_span_id() -> str:
    """Get current span ID"""
    span = trace.get_current_span()
    if span:
        return format(span.get_span_context().span_id, '016x')
    return span_id_var.get()
