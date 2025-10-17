"""
Agent Error Recovery System.

Provides robust error handling and recovery strategies for agent failures.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class AgentErrorRecovery:
    """
    Error recovery system for agent failures.

    Features:
    - Multi-level fallback strategies
    - Repeated failure detection
    - Error history tracking
    - Automatic retry with backoff
    """

    def __init__(self):
        """Initialize AgentErrorRecovery."""
        # Fallback chain for each agent
        self.fallback_strategies = {
            "vector_search": ["web_search", "direct_llm"],
            "web_search": ["vector_search", "direct_llm"],
            "local_data": ["vector_search", "direct_llm"],
        }

        # Error history
        self.error_history: List[Dict[str, Any]] = []
        self.failure_counts = defaultdict(int)

        # Configuration
        self.max_retries = 1
        self.failure_threshold = 3  # Skip agent after 3 failures
        self.history_window = timedelta(minutes=5)  # Track failures in 5min window

        logger.info("AgentErrorRecovery initialized")

    async def recover(
        self,
        error: Exception,
        failed_action: str,
        query: str,
        context: Dict[str, Any],
        execute_func: Callable,
    ) -> Dict[str, Any]:
        """
        Attempt to recover from agent failure.

        Args:
            error: The exception that occurred
            failed_action: Name of the failed agent/action
            query: Original query
            context: Execution context
            execute_func: Function to execute fallback actions

        Returns:
            Recovery result or raises exception if all attempts fail
        """
        logger.warning(
            f"Attempting recovery from {failed_action} failure: {str(error)}"
        )

        # Record error
        self._record_error(failed_action, error)

        # Check if this agent is repeatedly failing
        if self._is_repeated_failure(failed_action):
            logger.error(
                f"Agent {failed_action} has failed {self.failure_counts[failed_action]} times. "
                "Skipping retry and using fallback."
            )
        else:
            # Try retry once
            try:
                logger.info(f"Retrying {failed_action}...")
                result = await execute_func(failed_action, query, context)
                logger.info(f"Retry successful for {failed_action}")
                return {
                    "success": True,
                    "action": failed_action,
                    "result": result,
                    "recovery_method": "retry",
                }
            except Exception as retry_error:
                logger.warning(f"Retry failed: {retry_error}")

        # Try fallback strategies
        fallbacks = self.fallback_strategies.get(failed_action, ["direct_llm"])

        for fallback_action in fallbacks:
            # Skip if fallback is also failing
            if self._is_repeated_failure(fallback_action):
                logger.warning(
                    f"Skipping fallback {fallback_action} (repeated failures)"
                )
                continue

            try:
                logger.info(f"Trying fallback: {fallback_action}")
                result = await execute_func(fallback_action, query, context)
                logger.info(f"Fallback successful: {fallback_action}")

                return {
                    "success": True,
                    "action": fallback_action,
                    "result": result,
                    "recovery_method": "fallback",
                    "original_action": failed_action,
                }

            except Exception as fallback_error:
                logger.warning(f"Fallback {fallback_action} failed: {fallback_error}")
                self._record_error(fallback_action, fallback_error)
                continue

        # All recovery attempts failed
        error_msg = (
            f"All recovery attempts failed for {failed_action}. "
            f"Original error: {str(error)}"
        )
        logger.error(error_msg)

        return {
            "success": False,
            "action": failed_action,
            "error": error_msg,
            "recovery_method": "none",
        }

    def _record_error(self, action: str, error: Exception) -> None:
        """Record error in history."""
        error_record = {
            "action": action,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.now(),
        }

        self.error_history.append(error_record)
        self.failure_counts[action] += 1

        # Keep only recent errors
        self._cleanup_old_errors()

    def _is_repeated_failure(self, action: str) -> bool:
        """Check if action is repeatedly failing."""
        # Count recent failures
        cutoff_time = datetime.now() - self.history_window
        recent_failures = sum(
            1
            for error in self.error_history
            if error["action"] == action and error["timestamp"] > cutoff_time
        )

        return recent_failures >= self.failure_threshold

    def _cleanup_old_errors(self) -> None:
        """Remove old errors from history."""
        cutoff_time = datetime.now() - self.history_window

        self.error_history = [
            error for error in self.error_history if error["timestamp"] > cutoff_time
        ]

        # Reset failure counts for actions with no recent errors
        for action in list(self.failure_counts.keys()):
            recent_count = sum(
                1 for error in self.error_history if error["action"] == action
            )
            if recent_count == 0:
                del self.failure_counts[action]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        return {
            "total_errors": len(self.error_history),
            "failure_counts": dict(self.failure_counts),
            "recent_errors": [
                {
                    "action": error["action"],
                    "error_type": error["error_type"],
                    "timestamp": error["timestamp"].isoformat(),
                }
                for error in self.error_history[-10:]  # Last 10 errors
            ],
        }

    def reset(self) -> None:
        """Reset error history and counts."""
        self.error_history.clear()
        self.failure_counts.clear()
        logger.info("Error recovery state reset")

    def __repr__(self) -> str:
        return (
            f"AgentErrorRecovery(errors={len(self.error_history)}, "
            f"failing_agents={len(self.failure_counts)})"
        )
