"""Agent Builder API endpoints for tool management."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from functools import lru_cache

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.session_utils import get_db_session
from backend.db.models.user import User
from backend.core.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

def convert_tool_config_to_dict(tool_config):
    """Convert ToolConfig to dictionary format."""
    try:
        return {
            "id": tool_config.id,
            "name": tool_config.name,
            "description": tool_config.description,
            "category": tool_config.category,
            "icon": getattr(tool_config, "icon", "tool"),
            "bg_color": getattr(tool_config, "bg_color", "#6B7280"),
            "docs_link": getattr(tool_config, "docs_link", None),
            "params": {
                name: {
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default,
                    "enum": param.enum,
                    "min": getattr(param, "min_value", None),
                    "max": getattr(param, "max_value", None),
                    "pattern": param.pattern,
                }
                for name, param in (tool_config.params if tool_config.params else {}).items()
            },
            "outputs": {
                name: {
                    "type": output.type,
                    "description": output.description,
                }
                for name, output in (tool_config.outputs if tool_config.outputs else {}).items()
            },
        }
    except Exception as e:
        logger.error(f"Failed to convert tool config {tool_config.id}: {e}", exc_info=True)
        raise

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
        
        # Get tools from ToolRegistry
        tool_configs = ToolRegistry.list_tools(category=category)
        
        # Convert to dict format
        tools = [convert_tool_config_to_dict(tc) for tc in tool_configs]
        
        # Also get tools from database (custom tools)
        from backend.db.models.agent_builder import Tool as DBTool
        with get_db_session() as db:
            query = db.query(DBTool)
            if category:
                query = query.filter(DBTool.category == category)
            
            db_tools = query.all()
            
            # Convert DB tools to dict format
            for db_tool in db_tools:
                # Skip if already in registry
                if any(t['id'] == db_tool.id for t in tools):
                    continue
                
                tools.append({
                    "id": db_tool.id,
                    "name": db_tool.name,
                    "description": db_tool.description or "",
                    "category": db_tool.category or "utility",
                    "icon": "tool",
                    "bg_color": "#6B7280",
                    "docs_link": None,
                    "params": db_tool.input_schema or {},
                    "outputs": db_tool.output_schema or {},
                })
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            tools = [
                t for t in tools
                if search_lower in t["name"].lower() or search_lower in t["description"].lower()
            ]
        
        # Get all categories
        categorized = ToolRegistry.list_by_category()
        all_categories = set(categorized.keys())
        all_categories.update(t["category"] for t in tools)
        categories = sorted(list(all_categories))
        
        return {
            "tools": tools,
            "total": len(tools),
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tools"
        )


@router.get("/{tool_id}")
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get tool details by ID.
    
    **Path Parameters:**
    - tool_id: Tool identifier
    
    **Returns:**
    - Tool details with full configuration
    
    **Errors:**
    - 401: Unauthorized
    - 404: Tool not found
    """
    try:
        logger.info(f"Getting tool {tool_id} for user {current_user.id}")
        
        # Try to get executor schema from tool executor registry
        from backend.services.tools.tool_executor_registry import ToolExecutorRegistry
        
        executor = ToolExecutorRegistry.get_executor(tool_id)
        if executor and hasattr(executor, 'params_schema'):
            return {
                "id": tool_id,
                "name": executor.tool_name,
                "description": f"{executor.tool_name} tool",
                "category": getattr(executor, 'category', 'utility'),
                "icon": "tool",
                "bg_color": "#6B7280",
                "docs_link": None,
                "params": executor.params_schema,
                "outputs": {},
            }
        
        # Try ToolRegistry
        tool_config = ToolRegistry.get_tool(tool_id)
        if tool_config:
            return convert_tool_config_to_dict(tool_config)
        
        # Try database
        from backend.db.models.agent_builder import Tool as DBTool
        with get_db_session() as db:
            db_tool = db.query(DBTool).filter(DBTool.id == tool_id).first()
            if db_tool:
                return {
                    "id": db_tool.id,
                    "name": db_tool.name,
                    "description": db_tool.description or "",
                    "category": db_tool.category or "utility",
                    "icon": "tool",
                    "bg_color": "#6B7280",
                    "docs_link": None,
                    "params": db_tool.input_schema or {},
                    "outputs": db_tool.output_schema or {},
                }
        
        # Not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tool"
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
        categorized = ToolRegistry.list_by_category()
        categories = []
        for category, tools in categorized.items():
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


@router.post("/recommend")
async def recommend_tools(
    agent_type: Optional[str] = Query(None, description="Agent type"),
    description: Optional[str] = Query(None, description="Agent description"),
    current_user: User = Depends(get_current_user),
):
    """
    Get tool recommendations based on agent type and description.
    
    **Query Parameters:**
    - agent_type: Type of agent (custom, template_based, etc.)
    - description: Agent description for context-aware recommendations
    
    **Returns:**
    - List of recommended tools with reasoning
    
    **Errors:**
    - 401: Unauthorized
    - 500: Internal server error
    """
    try:
        logger.info(f"Getting tool recommendations for user {current_user.id}")
        
        # Get all available tools
        tool_configs = ToolRegistry.list_tools()
        tools = [convert_tool_config_to_dict(tc) for tc in tool_configs]
        
        # Simple keyword-based recommendation logic
        recommendations = []
        
        # Keywords mapping for different use cases
        keyword_mappings = {
            'search': ['web_search', 'brave_search', 'google_search'],
            'data': ['vector_search', 'database', 'sql', 'postgres'],
            'code': ['python_code', 'code_interpreter', 'github'],
            'file': ['filesystem', 'file_manager'],
            'communication': ['slack', 'email', 'discord'],
            'analysis': ['data_analysis', 'statistical_analysis'],
            'image': ['image_generation', 'vision', 'dalle'],
            'document': ['pdf_reader', 'document_parser'],
        }
        
        description_lower = (description or '').lower()
        
        for tool in tools:
            score = 0
            reasons = []
            
            # Check description keywords
            for keyword, tool_ids in keyword_mappings.items():
                if keyword in description_lower:
                    if any(tid in tool['id'].lower() for tid in tool_ids):
                        score += 3
                        reasons.append(f"'{keyword}' 관련 작업에 적합")
            
            # Category-based scoring
            if 'search' in description_lower and tool['category'] == 'search':
                score += 2
                reasons.append("검색 기능 제공")
            elif 'data' in description_lower and tool['category'] == 'data':
                score += 2
                reasons.append("데이터 처리 기능 제공")
            elif 'code' in description_lower and tool['category'] == 'developer':
                score += 2
                reasons.append("코드 실행 기능 제공")
            
            # Popular tools get a small boost
            popular_tools = ['web_search', 'vector_search', 'python_code']
            if tool['id'] in popular_tools:
                score += 1
                reasons.append("인기 도구")
            
            if score > 0:
                recommendations.append({
                    "tool": tool,
                    "score": score,
                    "reasons": reasons,
                    "recommended": score >= 2
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top 10 recommendations
        return {
            "recommendations": recommendations[:10],
            "total": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get tool recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tool recommendations"
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
        
        tool_config = ToolRegistry.get_tool_config(tool_id)
        
        if not tool_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found"
            )
        
        return convert_tool_config_to_dict(tool_config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tool"
        )
