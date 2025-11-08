"""Agent Builder API endpoints for tool management."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from functools import lru_cache

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.core.tools.catalog import (
    ALL_TOOLS,
    TOOL_CATALOG,
    get_tools_by_category,
    get_tool_by_id,
    search_tools,
)

logger = logging.getLogger(__name__)

# Cache tool catalog in memory (immutable data)
@lru_cache(maxsize=1)
def get_cached_all_tools():
    """Get all tools with caching."""
    return ALL_TOOLS

@lru_cache(maxsize=10)
def get_cached_tools_by_category(category: str):
    """Get tools by category with caching."""
    return get_tools_by_category(category)

router = APIRouter(
    prefix="/api/agent-builder/tools",
    tags=["agent-builder-tools"],
)


@router.get("")
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query"),
    current_user: User = Depends(get_current_user),
):
    """
    List available tools from the catalog.
    
    **Query Parameters:**
    - category: Filter by tool category (ai, search, productivity, data, communication, developer)
    - search: Search tools by name or description
    
    **Returns:**
    - List of available tools with metadata
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Listing tools for user {current_user.id}, category={category}, search={search}")
        
        # Get tools based on filters (with caching)
        if search:
            tools = search_tools(search)  # Search not cached (dynamic)
        elif category:
            tools = get_cached_tools_by_category(category)
        else:
            tools = get_cached_all_tools()
        
        return {
            "tools": tools,
            "total": len(tools),
            "categories": list(TOOL_CATALOG.keys())
        }
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tools"
        )


@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_user),
):
    """
    List all tool categories.
    
    **Returns:**
    - List of categories with tool counts
    
    **Errors:**
    - 401: Unauthorized
    """
    try:
        categories = []
        for category, tools in TOOL_CATALOG.items():
            categories.append({
                "id": category,
                "name": category.title(),
                "count": len(tools)
            })
        
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Failed to list categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list categories"
        )


@router.get("/{tool_id}")
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get tool details from catalog.
    
    **Path Parameters:**
    - tool_id: Tool ID
    
    **Returns:**
    - Tool details including configuration and auth requirements
    
    **Errors:**
    - 401: Unauthorized
    - 404: Tool not found
    - 500: Internal server error
    """
    try:
        logger.info(f"Getting tool {tool_id} for user {current_user.id}")
        
        tool = get_tool_by_id(tool_id)
        
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found"
            )
        
        return tool
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tool"
        )
