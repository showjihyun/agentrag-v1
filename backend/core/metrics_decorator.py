# Metrics Collection Decorator
import time
import functools
import logging
from typing import Callable, Any
import asyncio

from backend.services.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)


def track_query_metrics(mode: str = "unknown"):
    """
    Decorator to track query execution metrics.

    Usage:
        @track_query_metrics(mode="fast")
        async def process_query(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            finally:
                latency_ms = (time.time() - start_time) * 1000

                # Record metrics
                collector = get_metrics_collector()
                await collector.record_query_latency(
                    latency_ms=latency_ms, mode=mode, success=success
                )

                logger.info(
                    f"Query completed: mode={mode}, "
                    f"latency={latency_ms:.2f}ms, success={success}"
                )

        return wrapper

    return decorator


def track_vector_search():
    """
    Decorator to track vector search metrics.

    Usage:
        @track_vector_search()
        async def search_vectors(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            result = await func(*args, **kwargs)

            latency_ms = (time.time() - start_time) * 1000

            # Extract metrics from result
            num_results = len(result) if isinstance(result, list) else 0
            top_k = kwargs.get("top_k", kwargs.get("k", 10))

            # Record metrics
            collector = get_metrics_collector()
            await collector.record_vector_search(
                latency_ms=latency_ms, num_results=num_results, top_k=top_k
            )

            return result

        return wrapper

    return decorator


def track_agent_execution(agent_name: str):
    """
    Decorator to track agent execution metrics.

    Usage:
        @track_agent_execution("vector_search")
        async def execute_agent(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000

                # Record metrics
                collector = get_metrics_collector()
                await collector.record_agent_execution(
                    agent_name=agent_name, latency_ms=latency_ms, success=success
                )

        return wrapper

    return decorator


def track_cache_access(cache_type: str):
    """
    Decorator to track cache access metrics.

    Usage:
        @track_cache_access("semantic")
        async def get_from_cache(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)

            # Determine if cache hit
            hit = result is not None

            # Record metrics
            collector = get_metrics_collector()
            await collector.record_cache_hit(hit=hit, cache_type=cache_type)

            return result

        return wrapper

    return decorator


def track_llm_usage(provider: str, model: str):
    """
    Decorator to track LLM usage metrics.

    Usage:
        @track_llm_usage("ollama", "llama3.1")
        async def call_llm(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            result = await func(*args, **kwargs)

            latency_ms = (time.time() - start_time) * 1000

            # Extract token counts from result if available
            prompt_tokens = 0
            completion_tokens = 0

            if isinstance(result, dict):
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

            # Record metrics
            collector = get_metrics_collector()
            await collector.record_llm_usage(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
            )

            return result

        return wrapper

    return decorator
