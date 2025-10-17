"""
Unit tests for Agent improvements (Phase 1).

Tests:
1. Agent Router
2. Parallel Executor
3. Error Recovery
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from backend.agents.router import AgentRouter
from backend.agents.parallel_executor import ParallelAgentExecutor
from backend.agents.error_recovery import AgentErrorRecovery


class TestAgentRouter:
    """Test Agent Router functionality."""

    def test_router_initialization(self):
        """Test router initializes correctly."""
        router = AgentRouter()

        assert router is not None
        assert len(router.routing_rules) > 0
        assert len(router.keywords) > 0

    @pytest.mark.asyncio
    async def test_quick_route_document_query(self):
        """Test quick routing for document queries."""
        router = AgentRouter()

        result = await router.route("What is in the document?")

        assert result is not None
        assert "agents" in result
        assert "vector_search" in result["agents"]

    @pytest.mark.asyncio
    async def test_quick_route_web_search(self):
        """Test quick routing for web search queries."""
        router = AgentRouter()

        result = await router.route("What is the latest news about AI?")

        assert result is not None
        assert "agents" in result
        assert "web_search" in result["agents"]

    @pytest.mark.asyncio
    async def test_quick_route_comparison(self):
        """Test quick routing for comparison queries."""
        router = AgentRouter()

        result = await router.route("Compare machine learning and deep learning")

        assert result is not None
        assert "agents" in result
        assert len(result["agents"]) >= 1
        # Should suggest parallel execution for comparison
        assert result.get("parallel", False) or len(result["agents"]) > 1

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test routing cache works."""
        router = AgentRouter()

        query = "What is machine learning?"

        # First call
        result1 = await router.route(query, use_cache=True)

        # Second call (should use cache)
        result2 = await router.route(query, use_cache=True)

        assert result1 == result2
        assert len(router.cache) > 0

    def test_cache_clear(self):
        """Test cache clearing."""
        router = AgentRouter()
        router.cache["test"] = "value"

        router.clear_cache()

        assert len(router.cache) == 0


class TestParallelAgentExecutor:
    """Test Parallel Agent Executor."""

    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        executor = ParallelAgentExecutor(max_concurrent=3)

        assert executor.max_concurrent == 3
        assert executor.execution_stats["total_parallel_executions"] == 0

    @pytest.mark.asyncio
    async def test_single_action_execution(self):
        """Test single action execution."""
        executor = ParallelAgentExecutor()

        # Mock agent
        mock_agent = Mock()
        mock_agent.search = AsyncMock(return_value=[{"text": "result1", "score": 0.9}])

        agents = {"vector_agent": mock_agent}
        actions = [{"type": "vector_search", "input": {"query": "test"}}]

        result = await executor.execute_parallel(actions, agents, "test query")

        assert result is not None
        assert result["parallel"] == False  # Single action
        assert result["actions_executed"] == 1

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel execution of multiple actions."""
        executor = ParallelAgentExecutor()

        # Mock agents
        mock_vector = Mock()
        mock_vector.search = AsyncMock(
            return_value=[{"text": "vector result", "score": 0.9}]
        )

        mock_search = Mock()
        mock_search.search_web = AsyncMock(
            return_value=[Mock(to_dict=lambda: {"text": "web result", "score": 0.8})]
        )

        agents = {"vector_agent": mock_vector, "search_agent": mock_search}

        actions = [
            {"type": "vector_search", "input": {"query": "test"}},
            {"type": "web_search", "input": {"query": "test"}},
        ]

        result = await executor.execute_parallel(actions, agents, "test query")

        assert result is not None
        assert result["parallel"] == True
        assert result["actions_executed"] == 2
        assert len(result["results"]) >= 1

    def test_result_merging(self):
        """Test result merging and deduplication."""
        executor = ParallelAgentExecutor()

        results = [
            {"id": "1", "text": "result1", "score": 0.9},
            {"id": "2", "text": "result2", "score": 0.8},
            {"id": "1", "text": "result1", "score": 0.85},  # Duplicate
        ]

        merged = executor._merge_results(results)

        assert len(merged) == 2  # Duplicate removed
        assert merged[0]["score"] == 0.9  # Sorted by score

    def test_stats_tracking(self):
        """Test statistics tracking."""
        executor = ParallelAgentExecutor()

        executor._update_stats(2, 1.5)

        stats = executor.get_stats()

        assert stats["total_parallel_executions"] == 1
        assert stats["average_speedup"] > 1.0


class TestAgentErrorRecovery:
    """Test Agent Error Recovery."""

    def test_recovery_initialization(self):
        """Test recovery system initializes correctly."""
        recovery = AgentErrorRecovery()

        assert recovery is not None
        assert len(recovery.fallback_strategies) > 0
        assert recovery.max_retries == 1

    def test_error_recording(self):
        """Test error recording."""
        recovery = AgentErrorRecovery()

        error = ValueError("Test error")
        recovery._record_error("vector_search", error)

        assert len(recovery.error_history) == 1
        assert recovery.failure_counts["vector_search"] == 1

    def test_repeated_failure_detection(self):
        """Test repeated failure detection."""
        recovery = AgentErrorRecovery()

        # Record multiple failures
        for i in range(3):
            recovery._record_error("vector_search", ValueError(f"Error {i}"))

        assert recovery._is_repeated_failure("vector_search") == True
        assert recovery._is_repeated_failure("web_search") == False

    @pytest.mark.asyncio
    async def test_recovery_with_retry(self):
        """Test recovery with successful retry."""
        recovery = AgentErrorRecovery()

        # Mock execute function that succeeds on retry
        call_count = 0

        async def mock_execute(action, query, context):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First attempt fails")
            return {"success": True}

        result = await recovery.recover(
            error=ValueError("Test error"),
            failed_action="vector_search",
            query="test",
            context={},
            execute_func=mock_execute,
        )

        assert result["success"] == True
        assert result["recovery_method"] == "retry"

    @pytest.mark.asyncio
    async def test_recovery_with_fallback(self):
        """Test recovery with fallback strategy."""
        recovery = AgentErrorRecovery()

        # Mock execute function that fails for primary, succeeds for fallback
        async def mock_execute(action, query, context):
            if action == "vector_search":
                raise ValueError("Vector search fails")
            return {"success": True, "action": action}

        result = await recovery.recover(
            error=ValueError("Test error"),
            failed_action="vector_search",
            query="test",
            context={},
            execute_func=mock_execute,
        )

        assert result["success"] == True
        assert result["recovery_method"] == "fallback"
        assert result["action"] in ["web_search", "direct_llm"]

    def test_error_summary(self):
        """Test error summary generation."""
        recovery = AgentErrorRecovery()

        recovery._record_error("vector_search", ValueError("Error 1"))
        recovery._record_error("web_search", ValueError("Error 2"))

        summary = recovery.get_error_summary()

        assert summary["total_errors"] == 2
        assert len(summary["failure_counts"]) == 2
        assert len(summary["recent_errors"]) == 2

    def test_reset(self):
        """Test recovery state reset."""
        recovery = AgentErrorRecovery()

        recovery._record_error("vector_search", ValueError("Error"))
        recovery.reset()

        assert len(recovery.error_history) == 0
        assert len(recovery.failure_counts) == 0


# Integration tests
class TestAgentImprovementsIntegration:
    """Integration tests for agent improvements."""

    @pytest.mark.asyncio
    async def test_router_with_executor(self):
        """Test router and executor working together."""
        router = AgentRouter()
        executor = ParallelAgentExecutor()

        # Route query
        routing = await router.route("Compare ML and DL")

        # Check if parallel execution is suggested
        assert "agents" in routing
        assert "parallel" in routing

    @pytest.mark.asyncio
    async def test_full_workflow_with_improvements(self):
        """Test complete workflow with all improvements."""
        router = AgentRouter()
        executor = ParallelAgentExecutor()
        recovery = AgentErrorRecovery()

        # 1. Route query
        routing = await router.route("What is machine learning?")
        assert routing["agents"] == ["vector_search"]

        # 2. Mock execution
        mock_agent = Mock()
        mock_agent.search = AsyncMock(return_value=[{"text": "ML is...", "score": 0.9}])

        agents = {"vector_agent": mock_agent}
        actions = [{"type": "vector_search", "input": {"query": "test"}}]

        # 3. Execute
        result = await executor.execute_parallel(actions, agents, "test")

        assert result["successful_actions"] == 1
        assert len(result["results"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
