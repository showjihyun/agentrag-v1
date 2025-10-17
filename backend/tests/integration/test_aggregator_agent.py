"""
Integration tests for Aggregator Agent with ReAct and CoT.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.agents.aggregator import AggregatorAgent
from backend.models.agent import AgentStep
from backend.models.query import SearchResult
from backend.services.llm_manager import LLMManager, LLMProvider
from backend.memory.manager import MemoryManager
from backend.memory.stm import ShortTermMemory
from backend.memory.ltm import LongTermMemory
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent, WebSearchResult


@pytest.fixture
def mock_llm_manager():
    """Create a mock LLM manager."""
    llm = MagicMock(spec=LLMManager)

    # Mock generate method to return planning response
    async def mock_generate(messages, **kwargs):
        # Check what type of prompt this is
        content = messages[-1]["content"] if messages else ""

        if "step by step" in content.lower():
            # CoT planning response
            return """Step 1: Search vector database
- Information needed: Relevant documents about the query
- Tool: vector_search
- Reasoning: Need to find existing knowledge

Step 2: Synthesize response
- Information needed: Combine findings
- Tool: synthesis
- Reasoning: Create comprehensive answer"""

        elif "thought:" in content.lower() and "action:" in content.lower():
            # ReAct reasoning response
            return """Thought: I should search the vector database for relevant information
Action: vector_search
Action Input: {"query": "test query", "top_k": 10}"""

        elif "reflect" in content.lower():
            # Reflection response
            return """Decision: synthesize
Reasoning: We have enough information from the vector search to answer the query."""

        elif "comprehensive answer" in content.lower():
            # Synthesis response
            return "Based on the retrieved documents, here is a comprehensive answer with citations [Document 1]."

        return "Mock LLM response"

    llm.generate = AsyncMock(side_effect=mock_generate)
    return llm


@pytest.fixture
def mock_memory_manager():
    """Create a mock memory manager."""
    memory = MagicMock(spec=MemoryManager)

    # Mock get_context_for_query
    async def mock_get_context(session_id, query, **kwargs):
        from backend.memory.manager import MemoryContext

        return MemoryContext(
            recent_history=[],
            similar_interactions=[],
            working_memory={},
            session_info={"session_id": session_id},
        )

    memory.get_context_for_query = AsyncMock(side_effect=mock_get_context)

    # Mock consolidate_memory
    memory.consolidate_memory = AsyncMock(return_value="interaction_123")

    # Mock add_working_memory
    memory.add_working_memory = AsyncMock()

    return memory


@pytest.fixture
def mock_vector_agent():
    """Create a mock vector search agent."""
    agent = MagicMock(spec=VectorSearchAgent)

    # Mock search method
    async def mock_search(query, top_k=10, filters=None):
        return [
            SearchResult(
                chunk_id="chunk_1",
                document_id="doc_1",
                document_name="Test Document",
                text="This is relevant content about the query.",
                score=0.95,
                metadata={},
            ),
            SearchResult(
                chunk_id="chunk_2",
                document_id="doc_2",
                document_name="Another Document",
                text="More relevant information here.",
                score=0.85,
                metadata={},
            ),
        ]

    agent.search = AsyncMock(side_effect=mock_search)
    return agent


@pytest.fixture
def mock_local_agent():
    """Create a mock local data agent."""
    agent = MagicMock(spec=LocalDataAgent)

    # Mock read_file
    agent.read_file = AsyncMock(return_value="File content here")

    # Mock query_database
    agent.query_database = AsyncMock(
        return_value=[{"id": 1, "name": "Test"}, {"id": 2, "name": "Example"}]
    )

    return agent


@pytest.fixture
def mock_search_agent():
    """Create a mock web search agent."""
    agent = MagicMock(spec=WebSearchAgent)

    # Mock search_web
    async def mock_search_web(query, num_results=5, filters=None):
        return [
            WebSearchResult(
                title="Web Result 1",
                url="https://example.com/1",
                snippet="Web content about the query",
                score=0.9,
            )
        ]

    agent.search_web = AsyncMock(side_effect=mock_search_web)
    return agent


@pytest.fixture
def aggregator_agent(
    mock_llm_manager,
    mock_memory_manager,
    mock_vector_agent,
    mock_local_agent,
    mock_search_agent,
):
    """Create an aggregator agent with mocked dependencies."""
    return AggregatorAgent(
        llm_manager=mock_llm_manager,
        memory_manager=mock_memory_manager,
        vector_agent=mock_vector_agent,
        local_agent=mock_local_agent,
        search_agent=mock_search_agent,
        max_iterations=5,
    )


@pytest.mark.asyncio
async def test_cot_planning_generation(aggregator_agent):
    """Test Chain of Thought planning generation."""
    # Create initial state
    state = {
        "query": "What is machine learning?",
        "session_id": "test_session",
        "planning_steps": [],
        "action_history": [],
        "retrieved_docs": [],
        "reasoning_steps": [],
        "memory_context": {},
    }

    # Execute CoT planning
    result_state = await aggregator_agent._chain_of_thought_planning(state)

    # Verify planning steps were created
    assert len(result_state["planning_steps"]) > 0
    assert "Step 1" in result_state["planning_steps"][0]

    # Verify reasoning step was added
    assert len(result_state["reasoning_steps"]) > 0
    assert result_state["reasoning_steps"][0]["type"] == "planning"


@pytest.mark.asyncio
async def test_react_reasoning_loop(aggregator_agent):
    """Test ReAct reasoning loop."""
    # Create state with planning steps
    state = {
        "query": "What is machine learning?",
        "session_id": "test_session",
        "planning_steps": ["Step 1: Search vector database"],
        "action_history": [],
        "retrieved_docs": [],
        "reasoning_steps": [],
        "memory_context": {},
    }

    # Execute ReAct reasoning
    result_state = await aggregator_agent._react_reasoning(state)

    # Verify current action was set
    assert result_state["current_action"] is not None
    assert "action" in result_state["current_action"]
    assert "input" in result_state["current_action"]
    assert "thought" in result_state["current_action"]

    # Verify reasoning step was added
    reasoning_steps = result_state["reasoning_steps"]
    assert len(reasoning_steps) > 0
    assert reasoning_steps[0]["type"] == "thought"


@pytest.mark.asyncio
async def test_action_execution_vector_search(aggregator_agent, mock_vector_agent):
    """Test action execution with vector search."""
    # Create state with current action
    state = {
        "query": "What is machine learning?",
        "session_id": "test_session",
        "planning_steps": [],
        "action_history": [],
        "retrieved_docs": [],
        "reasoning_steps": [],
        "current_action": {
            "action": "vector_search",
            "input": {"query": "machine learning", "top_k": 10},
            "thought": "Search for relevant documents",
        },
    }

    # Execute action
    result_state = await aggregator_agent._execute_action(state)

    # Verify vector search was called
    mock_vector_agent.search.assert_called_once()

    # Verify results were added
    assert len(result_state["retrieved_docs"]) > 0
    assert len(result_state["action_history"]) == 1

    # Verify action history
    action = result_state["action_history"][0]
    assert action["action"] == "vector_search"
    assert "observation" in action


@pytest.mark.asyncio
async def test_action_execution_local_data(aggregator_agent, mock_local_agent):
    """Test action execution with local data."""
    # Create state with file read action
    state = {
        "query": "Read config file",
        "session_id": "test_session",
        "planning_steps": [],
        "action_history": [],
        "retrieved_docs": [],
        "reasoning_steps": [],
        "current_action": {
            "action": "local_data",
            "input": {"file_path": "/path/to/file.txt"},
            "thought": "Read the file",
        },
    }

    # Execute action
    result_state = await aggregator_agent._execute_action(state)

    # Verify local agent was called
    mock_local_agent.read_file.assert_called_once_with("/path/to/file.txt")

    # Verify action was recorded
    assert len(result_state["action_history"]) == 1
    assert result_state["action_history"][0]["action"] == "local_data"


@pytest.mark.asyncio
async def test_reflection_and_decision_making(aggregator_agent):
    """Test reflection and decision making."""
    # Create state with some results
    state = {
        "query": "What is machine learning?",
        "session_id": "test_session",
        "planning_steps": ["Step 1", "Step 2"],
        "action_history": [
            {"action": "vector_search", "input": {}, "observation": "Found 5 documents"}
        ],
        "retrieved_docs": [{"text": "doc1"}, {"text": "doc2"}],
        "reasoning_steps": [],
    }

    # Execute reflection
    result_state = await aggregator_agent._reflect_on_results(state)

    # Verify reflection decision was set
    assert result_state["reflection_decision"] in ["continue", "synthesize", "end"]

    # Verify reasoning step was added
    assert len(result_state["reasoning_steps"]) > 0
    assert result_state["reasoning_steps"][0]["type"] == "reflection"


@pytest.mark.asyncio
async def test_should_continue_logic(aggregator_agent):
    """Test _should_continue conditional logic."""
    # Test max iterations exceeded
    state = {
        "action_history": [{}] * 10,  # 10 actions
        "planning_steps": ["Step 1"],
        "retrieved_docs": [],
        "reflection_decision": "continue",
    }

    decision = aggregator_agent._should_continue(state)
    assert decision == "synthesize"  # Should force synthesize

    # Test normal continue
    state = {
        "action_history": [{}],
        "planning_steps": ["Step 1", "Step 2"],
        "retrieved_docs": [],
        "reflection_decision": "continue",
    }

    decision = aggregator_agent._should_continue(state)
    assert decision == "continue"

    # Test synthesize decision
    state = {
        "action_history": [{}],
        "planning_steps": ["Step 1"],
        "retrieved_docs": [{"text": "doc"}],
        "reflection_decision": "synthesize",
    }

    decision = aggregator_agent._should_continue(state)
    assert decision == "synthesize"


@pytest.mark.asyncio
async def test_end_to_end_query_processing(aggregator_agent):
    """Test end-to-end query processing."""
    query = "What is machine learning?"
    session_id = "test_session"

    # Collect all steps
    steps = []
    async for step in aggregator_agent.process_query(query, session_id):
        steps.append(step)

    # Verify we got steps
    assert len(steps) > 0

    # Verify step types
    step_types = [step.type for step in steps]

    # Should have at least memory, planning, and some actions
    assert "memory" in step_types
    assert "planning" in step_types

    # Should have final response
    assert any(step.type == "response" for step in steps)


@pytest.mark.asyncio
async def test_response_synthesis(aggregator_agent):
    """Test response synthesis."""
    # Create state with retrieved documents
    state = {
        "query": "What is machine learning?",
        "session_id": "test_session",
        "planning_steps": [],
        "action_history": [
            {"action": "vector_search", "observation": "Found 2 documents"}
        ],
        "retrieved_docs": [
            {
                "document_name": "ML Guide",
                "text": "Machine learning is a subset of AI",
                "score": 0.95,
            }
        ],
        "reasoning_steps": [],
        "memory_context": {},
    }

    # Execute synthesis
    result_state = await aggregator_agent._synthesize_response(state)

    # Verify final response was generated
    assert result_state["final_response"] is not None
    assert len(result_state["final_response"]) > 0

    # Verify response step was added
    response_steps = [
        s for s in result_state["reasoning_steps"] if s["type"] == "response"
    ]
    assert len(response_steps) > 0


@pytest.mark.asyncio
async def test_memory_saving(aggregator_agent, mock_memory_manager):
    """Test memory saving."""
    # Create state with final response
    state = {
        "query": "What is machine learning?",
        "session_id": "test_session",
        "planning_steps": ["Step 1"],
        "action_history": [{"action": "vector_search"}],
        "retrieved_docs": [{"text": "doc"}],
        "reasoning_steps": [],
        "final_response": "Machine learning is a subset of AI [Document 1].",
    }

    # Execute memory save
    result_state = await aggregator_agent._save_to_memory(state)

    # Verify consolidate_memory was called
    mock_memory_manager.consolidate_memory.assert_called_once()

    # Verify call arguments
    call_args = mock_memory_manager.consolidate_memory.call_args
    assert call_args.kwargs["session_id"] == "test_session"
    assert call_args.kwargs["query"] == "What is machine learning?"
    assert call_args.kwargs["success"] is True


@pytest.mark.asyncio
async def test_error_handling_in_action_execution(aggregator_agent, mock_vector_agent):
    """Test error handling during action execution."""
    # Make vector agent raise an error
    mock_vector_agent.search.side_effect = Exception("Search failed")

    # Create state with action
    state = {
        "query": "test",
        "session_id": "test_session",
        "planning_steps": [],
        "action_history": [],
        "retrieved_docs": [],
        "reasoning_steps": [],
        "current_action": {
            "action": "vector_search",
            "input": {"query": "test"},
            "thought": "Search",
        },
    }

    # Execute action
    result_state = await aggregator_agent._execute_action(state)

    # Verify error was handled
    assert len(result_state["action_history"]) == 1
    assert "error" in result_state["action_history"][0]["observation"].lower()

    # Verify error step was added
    error_steps = [s for s in result_state["reasoning_steps"] if s["type"] == "error"]
    assert len(error_steps) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
