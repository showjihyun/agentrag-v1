"""
Retry Handler with Exponential Backoff for ReAct Pattern.

Provides automatic retry logic for transient failures in action execution.
"""

import logging
import asyncio
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
import time

logger = logging.getLogger(__name__)


class RetryHandler:
    """
    Handle retries with exponential backoff for async operations.

    Features:
    - Exponential backoff with jitter
    - Configurable retry attempts
    - Exception type filtering
    - Detailed logging
    - Async/await support
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff (default: 2.0)
            jitter: Add random jitter to prevent thundering herd
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

        logger.info(
            f"RetryHandler initialized: max_retries={max_retries}, "
            f"base_delay={base_delay}s, max_delay={max_delay}s"
        )

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter (random factor between 0.5 and 1.5)
        if self.jitter:
            import random

            jitter_factor = 0.5 + random.random()  # 0.5 to 1.5
            delay *= jitter_factor

        return delay

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_on: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None,
        **kwargs,
    ) -> Any:
        """
        Execute async function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            retry_on: Tuple of exception types to retry on
            on_retry: Optional callback function called on each retry
            **kwargs: Keyword arguments for func

        Returns:
            Result from successful execution

        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Success
                if attempt > 0:
                    logger.info(
                        f"Retry successful on attempt {attempt + 1}/{self.max_retries + 1}"
                    )

                return result

            except retry_on as e:
                last_exception = e

                # Check if we should retry
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)

                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {type(e).__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            await on_retry(attempt, e, delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback error: {callback_error}")

                    # Wait before retry
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed. "
                        f"Last error: {type(e).__name__}: {str(e)}"
                    )
                    raise

            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable exception: {type(e).__name__}: {str(e)}")
                raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception

    def with_retry(
        self,
        retry_on: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None,
    ):
        """
        Decorator for adding retry logic to async functions.

        Args:
            retry_on: Tuple of exception types to retry on
            on_retry: Optional callback function called on each retry

        Returns:
            Decorated function

        Example:
            @retry_handler.with_retry(
                retry_on=(TimeoutError, ConnectionError)
            )
            async def my_function():
                # Your code here
                pass
        """

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.execute_with_retry(
                    func, *args, retry_on=retry_on, on_retry=on_retry, **kwargs
                )

            return wrapper

        return decorator


class RetryableActionExecutor:
    """
    Executor for ReAct actions with built-in retry logic.

    Wraps action execution with automatic retry on transient failures.
    """

    def __init__(
        self, retry_handler: Optional[RetryHandler] = None, max_retries: int = 3
    ):
        """
        Initialize retryable action executor.

        Args:
            retry_handler: Optional custom retry handler
            max_retries: Maximum retry attempts if no handler provided
        """
        self.retry_handler = retry_handler or RetryHandler(max_retries=max_retries)

        # Define retryable exceptions
        self.retryable_exceptions = (
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
            # Add more as needed
        )

        logger.info("RetryableActionExecutor initialized")

    async def execute_action_with_retry(
        self, action_func: Callable, action_name: str, *args, **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute action with retry logic.

        Args:
            action_func: Async function to execute
            action_name: Name of action for logging
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tuple of (success, result, error_message)
        """
        start_time = time.time()

        async def on_retry_callback(attempt: int, error: Exception, delay: float):
            """Callback for retry events."""
            logger.info(
                f"Action '{action_name}' retry {attempt + 1}: "
                f"waiting {delay:.2f}s before next attempt"
            )

        try:
            result = await self.retry_handler.execute_with_retry(
                action_func,
                *args,
                retry_on=self.retryable_exceptions,
                on_retry=on_retry_callback,
                **kwargs,
            )

            elapsed = time.time() - start_time
            logger.info(f"Action '{action_name}' succeeded in {elapsed:.2f}s")

            return True, result, None

        except self.retryable_exceptions as e:
            elapsed = time.time() - start_time
            error_msg = f"Action '{action_name}' failed after retries: {type(e).__name__}: {str(e)}"
            logger.error(f"{error_msg} (elapsed: {elapsed:.2f}s)")

            return False, None, error_msg

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Action '{action_name}' failed with non-retryable error: {type(e).__name__}: {str(e)}"
            logger.error(f"{error_msg} (elapsed: {elapsed:.2f}s)")

            return False, None, error_msg

    async def execute_vector_search_with_retry(
        self, vector_agent, query: str, top_k: int = 10
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute vector search with retry.

        Args:
            vector_agent: Vector search agent
            query: Search query
            top_k: Number of results

        Returns:
            Tuple of (success, results, error_message)
        """
        return await self.execute_action_with_retry(
            vector_agent.search, "vector_search", query=query, top_k=top_k
        )

    async def execute_web_search_with_retry(
        self, search_agent, query: str, num_results: int = 5
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute web search with retry.

        Args:
            search_agent: Web search agent
            query: Search query
            num_results: Number of results

        Returns:
            Tuple of (success, results, error_message)
        """
        return await self.execute_action_with_retry(
            search_agent.search_web, "web_search", query=query, num_results=num_results
        )

    async def execute_llm_call_with_retry(
        self, llm_manager, messages: list, **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute LLM call with retry.

        Args:
            llm_manager: LLM manager
            messages: Messages for LLM
            **kwargs: Additional arguments

        Returns:
            Tuple of (success, response, error_message)
        """
        return await self.execute_action_with_retry(
            llm_manager.generate, "llm_call", messages, **kwargs
        )


# Global retry handler instance
default_retry_handler = RetryHandler(
    max_retries=3, base_delay=1.0, max_delay=10.0, exponential_base=2.0, jitter=True
)
