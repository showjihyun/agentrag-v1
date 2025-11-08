"""Tool catalog for Agent Builder.

This module provides a centralized catalog of all available tools
organized by category, similar to sim.ai's tool structure.
"""

from typing import Dict, List, Any
from .ai_tools import AI_TOOLS
from .search_tools import SEARCH_TOOLS
from .productivity_tools import PRODUCTIVITY_TOOLS
from .data_tools import DATA_TOOLS
from .communication_tools import COMMUNICATION_TOOLS
from .developer_tools import DEVELOPER_TOOLS

# All tools organized by category
TOOL_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "ai": AI_TOOLS,
    "search": SEARCH_TOOLS,
    "productivity": PRODUCTIVITY_TOOLS,
    "data": DATA_TOOLS,
    "communication": COMMUNICATION_TOOLS,
    "developer": DEVELOPER_TOOLS,
}

# Flatten all tools for easy access
ALL_TOOLS = []
for category_tools in TOOL_CATALOG.values():
    ALL_TOOLS.extend(category_tools)


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all tools in a specific category."""
    return TOOL_CATALOG.get(category, [])


def get_tool_by_id(tool_id: str) -> Dict[str, Any]:
    """Get a specific tool by ID."""
    for tool in ALL_TOOLS:
        if tool["id"] == tool_id:
            return tool
    return None


def search_tools(query: str) -> List[Dict[str, Any]]:
    """Search tools by name or description."""
    query_lower = query.lower()
    results = []
    for tool in ALL_TOOLS:
        if (query_lower in tool["name"].lower() or 
            query_lower in tool["description"].lower()):
            results.append(tool)
    return results


__all__ = [
    "TOOL_CATALOG",
    "ALL_TOOLS",
    "get_tools_by_category",
    "get_tool_by_id",
    "search_tools",
]
