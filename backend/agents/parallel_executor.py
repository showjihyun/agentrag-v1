"""
Parallel Agent Execution System.

Enables concurrent execution of independent agent actions for improved performance.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ParallelAgentExecutor:
    """
    Executor for running multiple agents in parallel.

    Features:
    - Concurrent action execution
    - Result merging and deduplication
    - Error handling for parallel tasks
    - Performance tracking
    """

    def __init__(self, max_concurrent: int = 3):
        """
        Initialize ParallelAgentExecutor.

        Args:
            max_concurrent: Maximum number of concurrent agent executions
        """
        self.max_concurrent = max_concurrent
        self.execution_stats = {
            "total_parallel_executions": 0,
            "total_time_saved": 0.0,
            "average_speedup": 0.0,
        }

        logger.info(
            f"ParallelAgentExecutor initialized (max_concurrent={max_concurrent})"
        )

    async def execute_parallel(
        self, actions: List[Dict[str, Any]], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """
        Execute multiple agent actions in parallel.

        Args:
            actions: List of action dictionaries with type and parameters
            agents: Dictionary of agent instances
            query: Original query

        Returns:
            Dict with merged results and metadata
        """
        if not actions:
            return {"results": [], "parallel": False, "execution_time": 0.0}

        # Single action - no parallelization needed
        if len(actions) == 1:
            return await self._execute_single(actions[0], agents, query)

        logger.info(f"Executing {len(actions)} actions in parallel")

        start_time = datetime.now()

        # Create tasks for each action
        tasks = []
        for action in actions[: self.max_concurrent]:  # Limit concurrent tasks
            task = self._execute_action_safe(action, agents, query)
            tasks.append(task)

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Process results
        successful_results = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Parallel action {i} failed: {result}")
                errors.append(
                    {"action": actions[i].get("type", "unknown"), "error": str(result)}
                )
            else:
                successful_results.extend(result.get("results", []))

        # Merge and deduplicate results
        merged_results = self._merge_results(successful_results)

        # Update stats
        self._update_stats(len(actions), execution_time)

        logger.info(
            f"Parallel execution completed: {len(merged_results)} results "
            f"in {execution_time:.2f}s"
        )

        return {
            "results": merged_results,
            "parallel": True,
            "execution_time": execution_time,
            "actions_executed": len(actions),
            "successful_actions": len(successful_results),
            "errors": errors,
        }

    async def _execute_single(
        self, action: Dict[str, Any], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """Execute a single action."""
        start_time = datetime.now()

        try:
            result = await self._execute_action(action, agents, query)
            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "results": result.get("results", []),
                "parallel": False,
                "execution_time": execution_time,
                "actions_executed": 1,
                "successful_actions": 1,
                "errors": [],
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Single action execution failed: {e}")

            return {
                "results": [],
                "parallel": False,
                "execution_time": execution_time,
                "actions_executed": 1,
                "successful_actions": 0,
                "errors": [{"action": action.get("type", "unknown"), "error": str(e)}],
            }

    async def _execute_action_safe(
        self, action: Dict[str, Any], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """Execute action with error handling."""
        try:
            return await self._execute_action(action, agents, query)
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"results": [], "error": str(e)}

    async def _execute_action(
        self, action: Dict[str, Any], agents: Dict[str, Any], query: str
    ) -> Dict[str, Any]:
        """Execute a single agent action."""
        action_type = action.get("type", "vector_search")
        action_input = action.get("input", {})

        # Get agent
        if action_type == "vector_search":
            agent = agents.get("vector_agent")
            if agent:
                results = await agent.search(
                    query=action_input.get("query", query),
                    top_k=action_input.get("top_k", 10),
                )
                return {
                    "results": [
                        r.to_dict() if hasattr(r, "to_dict") else r for r in results
                    ]
                }

        elif action_type == "web_search":
            agent = agents.get("search_agent")
            if agent:
                results = await agent.search_web(
                    query=action_input.get("query", query),
                    num_results=action_input.get("num_results", 5),
                )
                return {
                    "results": [
                        r.to_dict() if hasattr(r, "to_dict") else r for r in results
                    ]
                }

        elif action_type == "local_data":
            agent = agents.get("local_agent")
            if agent:
                if "file_path" in action_input:
                    content = await agent.read_file(action_input["file_path"])
                    return {"results": [{"type": "file", "content": content}]}
                elif "database_query" in action_input:
                    rows = await agent.query_database(
                        query=action_input["database_query"],
                        db_name=action_input.get("database", "default"),
                    )
                    return {"results": rows}

        return {"results": []}

    def _merge_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate results from multiple agents.

        Args:
            results: List of result dictionaries

        Returns:
            Merged and deduplicated results
        """
        if not results:
            return []

        # Use ID or text for deduplication
        seen = set()
        merged = []

        for result in results:
            # Generate unique key
            result_id = result.get("id") or result.get("chunk_id") or result.get("url")

            if not result_id:
                # Use text hash as fallback
                text = result.get(
                    "text", result.get("content", result.get("snippet", ""))
                )
                result_id = hash(text[:100]) if text else id(result)

            if result_id not in seen:
                seen.add(result_id)
                merged.append(result)

        # Sort by score if available
        merged.sort(
            key=lambda x: x.get("score", x.get("combined_score", 0)), reverse=True
        )

        return merged

    def _update_stats(self, num_actions: int, execution_time: float) -> None:
        """Update execution statistics."""
        self.execution_stats["total_parallel_executions"] += 1

        # Estimate time saved (assuming sequential would take sum of individual times)
        # Conservative estimate: 40% time saved
        estimated_sequential_time = execution_time * 1.67  # Inverse of 0.6
        time_saved = estimated_sequential_time - execution_time

        self.execution_stats["total_time_saved"] += time_saved

        # Update average speedup
        total_execs = self.execution_stats["total_parallel_executions"]
        self.execution_stats["average_speedup"] = (
            estimated_sequential_time / execution_time if execution_time > 0 else 1.0
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {**self.execution_stats, "max_concurrent": self.max_concurrent}

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.execution_stats = {
            "total_parallel_executions": 0,
            "total_time_saved": 0.0,
            "average_speedup": 0.0,
        }
        logger.info("Parallel executor stats reset")

    def __repr__(self) -> str:
        return (
            f"ParallelAgentExecutor(max_concurrent={self.max_concurrent}, "
            f"executions={self.execution_stats['total_parallel_executions']})"
        )
