"""
Unit tests for Aggregator Agent helper methods.

These tests focus on the parsing and formatting logic without requiring
full LangGraph integration.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
import json


def test_parse_planning_steps():
    """Test parsing of planning steps from LLM response."""
    # Import the class (we'll test the method directly)
    from backend.agents.aggregator import AggregatorAgent

    # Create a mock agent
    agent = MagicMock(spec=AggregatorAgent)
    agent._parse_planning_steps = AggregatorAgent._parse_planning_steps.__get__(agent)

    # Test with well-formatted response
    planning_response = """Step 1: Search vector database
- Information needed: Relevant documents
- Tool: vector_search
- Reasoning: Find existing knowledge

Step 2: Synthesize response
- Information needed: Combined findings
- Tool: synthesis
- Reasoning: Create answer"""

    steps = agent._parse_planning_steps(planning_response)

    assert len(steps) == 2
    assert "Step 1" in steps[0]
    assert "vector_search" in steps[0]
    assert "Step 2" in steps[1]


def test_parse_react_response():
    """Test parsing of ReAct response."""
    from backend.agents.aggregator import AggregatorAgent

    agent = MagicMock(spec=AggregatorAgent)
    agent._parse_react_response = AggregatorAgent._parse_react_response.__get__(agent)

    # Test with well-formatted ReAct response
    react_response = """Thought: I should search the vector database for relevant information
Action: vector_search
Action Input: {"query": "machine learning", "top_k": 10}"""

    thought, action, action_input = agent._parse_react_response(react_response)

    assert "search the vector database" in thought
    assert action == "vector_search"
    assert isinstance(action_input, dict)
    assert action_input["query"] == "machine learning"
    assert action_input["top_k"] == 10


def test_parse_react_response_with_invalid_action():
    """Test ReAct parsing with invalid action name."""
    from backend.agents.aggregator import AggregatorAgent

    agent = MagicMock(spec=AggregatorAgent)
    agent._parse_react_response = AggregatorAgent._parse_react_response.__get__(agent)

    react_response = """Thought: Do something
Action: invalid_action
Action Input: {"query": "test"}"""

    thought, action, action_input = agent._parse_react_response(react_response)

    # Should default to vector_search for invalid actions
    assert action == "vector_search"


def test_parse_reflection_decision():
    """Test parsing of reflection decision."""
    from backend.agents.aggregator import AggregatorAgent

    agent = MagicMock(spec=AggregatorAgent)
    agent._parse_reflection_decision = (
        AggregatorAgent._parse_reflection_decision.__get__(agent)
    )

    # Test continue decision
    reflection = """Decision: continue
Reasoning: We need more information to answer comprehensively."""

    decision = agent._parse_reflection_decision(reflection)
    assert decision == "continue"

    # Test synthesize decision
    reflection = """Decision: synthesize
Reasoning: We have enough information now."""

    decision = agent._parse_reflection_decision(reflection)
    assert decision == "synthesize"

    # Test end decision
    reflection = """Decision: end
Reasoning: Cannot answer this query."""

    decision = agent._parse_reflection_decision(reflection)
    assert decision == "end"


def test_format_action_history():
    """Test formatting of action history."""
    from backend.agents.aggregator import AggregatorAgent

    agent = MagicMock(spec=AggregatorAgent)
    agent._format_action_history = AggregatorAgent._format_action_history.__get__(agent)

    # Test with empty history
    formatted = agent._format_action_history([])
    assert formatted == "No previous actions"

    # Test with actions
    action_history = [
        {
            "action": "vector_search",
            "input": {"query": "test", "top_k": 10},
            "observation": "Found 5 documents",
        },
        {
            "action": "web_search",
            "input": {"query": "test"},
            "observation": "Found 3 web results",
        },
    ]

    formatted = agent._format_action_history(action_history)

    assert "1. Action: vector_search" in formatted
    assert "2. Action: web_search" in formatted
    assert "Found 5 documents" in formatted
    assert "Found 3 web results" in formatted


def test_summarize_memory_context():
    """Test summarizing memory context."""
    from backend.agents.aggregator import AggregatorAgent

    agent = MagicMock(spec=AggregatorAgent)
    agent._summarize_memory_context = AggregatorAgent._summarize_memory_context.__get__(
        agent
    )

    # Test with empty context
    summary = agent._summarize_memory_context({})
    assert "No prior context available" in summary

    # Test with full context
    memory_context = {
        "recent_history": [
            {"role": "user", "content": "What is ML?"},
            {"role": "assistant", "content": "Machine learning is..."},
        ],
        "similar_interactions": [{"query": "What is AI?", "response": "AI is..."}],
        "working_memory": {"key1": "value1"},
    }

    summary = agent._summarize_memory_context(memory_context)

    assert "Recent conversation" in summary
    assert "Similar past interactions" in summary
    assert "Working memory" in summary


def test_should_continue_max_iterations():
    """Test _should_continue with max iterations exceeded."""
    from backend.agents.aggregator import AggregatorAgent

    # Create agent with max_iterations
    agent = MagicMock(spec=AggregatorAgent)
    agent.max_iterations = 5
    agent._should_continue = AggregatorAgent._should_continue.__get__(agent)

    # State with too many actions
    state = {
        "action_history": [{}] * 10,
        "planning_steps": ["Step 1"],
        "retrieved_docs": [],
        "reflection_decision": "continue",
    }

    decision = agent._should_continue(state)
    assert decision == "synthesize"


def test_should_continue_normal_flow():
    """Test _should_continue with normal flow."""
    from backend.agents.aggregator import AggregatorAgent

    agent = MagicMock(spec=AggregatorAgent)
    agent.max_iterations = 10
    agent._should_continue = AggregatorAgent._should_continue.__get__(agent)

    # State with continue decision
    state = {
        "action_history": [{}],
        "planning_steps": ["Step 1", "Step 2"],
        "retrieved_docs": [],
        "reflection_decision": "continue",
    }

    decision = agent._should_continue(state)
    assert decision == "continue"

    # State with synthesize decision
    state["reflection_decision"] = "synthesize"
    decision = agent._should_continue(state)
    assert decision == "synthesize"


def test_parse_react_response_with_non_json_input():
    """Test ReAct parsing when action input is not JSON."""
    from backend.agents.aggregator import AggregatorAgent

    agent = MagicMock(spec=AggregatorAgent)
    agent._parse_react_response = AggregatorAgent._parse_react_response.__get__(agent)

    react_response = """Thought: Search for information
Action: vector_search
Action Input: machine learning basics"""

    thought, action, action_input = agent._parse_react_response(react_response)

    assert action == "vector_search"
    # Should wrap non-JSON input as query
    assert isinstance(action_input, dict)
    assert "query" in action_input


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
