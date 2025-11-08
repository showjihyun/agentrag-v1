"""
Test LangGraph setup and compatibility.
"""

import pytest
from langgraph.graph import StateGraph, END


def test_langgraph_import():
    """Test that LangGraph can be imported."""
    from langgraph.graph import StateGraph, END
    assert StateGraph is not None
    assert END is not None


def test_langgraph_state_graph_creation():
    """Test basic StateGraph creation and compilation."""
    
    # Define a simple state
    def node_1(state: dict) -> dict:
        state["count"] = state.get("count", 0) + 1
        return state
    
    def node_2(state: dict) -> dict:
        state["count"] = state.get("count", 0) * 2
        return state
    
    # Create graph
    graph = StateGraph(dict)
    graph.add_node("node_1", node_1)
    graph.add_node("node_2", node_2)
    graph.add_edge("node_1", "node_2")
    graph.set_entry_point("node_1")
    graph.set_finish_point("node_2")
    
    # Compile
    compiled = graph.compile()
    
    # Execute
    result = compiled.invoke({"count": 0})
    
    # Verify
    assert result["count"] == 2  # (0 + 1) * 2


@pytest.mark.asyncio
async def test_langgraph_async_execution():
    """Test async StateGraph execution."""
    
    async def async_node(state: dict) -> dict:
        state["value"] = "processed"
        return state
    
    # Create graph
    graph = StateGraph(dict)
    graph.add_node("process", async_node)
    graph.set_entry_point("process")
    graph.set_finish_point("process")
    
    # Compile
    compiled = graph.compile()
    
    # Execute async
    result = await compiled.ainvoke({"value": "initial"})
    
    # Verify
    assert result["value"] == "processed"


def test_langgraph_conditional_edges():
    """Test conditional edge routing."""
    
    def start_node(state: dict) -> dict:
        state["value"] = 10
        return state
    
    def positive_node(state: dict) -> dict:
        state["result"] = "positive"
        return state
    
    def negative_node(state: dict) -> dict:
        state["result"] = "negative"
        return state
    
    def route_condition(state: dict) -> str:
        return "positive" if state.get("value", 0) > 0 else "negative"
    
    # Create graph
    graph = StateGraph(dict)
    graph.add_node("start", start_node)
    graph.add_node("positive", positive_node)
    graph.add_node("negative", negative_node)
    
    graph.set_entry_point("start")
    graph.add_conditional_edges(
        "start",
        route_condition,
        {
            "positive": "positive",
            "negative": "negative"
        }
    )
    graph.set_finish_point("positive")
    graph.set_finish_point("negative")
    
    # Compile
    compiled = graph.compile()
    
    # Execute
    result = compiled.invoke({})
    
    # Verify
    assert result["result"] == "positive"
    assert result["value"] == 10
