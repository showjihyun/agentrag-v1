"""Initialize all tool integrations.

This module imports all tool integration modules to register them with the ToolRegistry.
"""

import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger(__name__)


def initialize_tools():
    """
    Initialize all tool integrations.
    
    This function imports all tool integration modules, which triggers
    the @ToolRegistry.register decorators to register the tools.
    """
    logger.info("Initializing tool integrations...")
    
    try:
        # Import registry to access module-level storage
        from backend.core.tools.registry import ToolRegistry, _tools, _tool_instances
        
        # Clear any existing tools to avoid duplicates
        if len(_tools) > 0:
            logger.info(f"Clearing {len(_tools)} existing tools")
            _tools.clear()
            _tool_instances.clear()
        
        # Import all tool integration modules
        logger.info("Importing tool integration modules...")
        from backend.core.tools.integrations import ai_agent_tools
        from backend.core.tools.integrations import ai_tools
        from backend.core.tools.integrations import communication_tools
        from backend.core.tools.integrations import productivity_tools
        from backend.core.tools.integrations import data_tools
        from backend.core.tools.integrations import search_tools
        from backend.core.tools.integrations import http_tools
        
        # Get tool count from module-level storage
        tool_count = len(_tools)
        
        logger.info(f"Successfully initialized {tool_count} tools")
        
        # Log tools by category
        by_category = ToolRegistry.list_by_category()
        for category, tools in by_category.items():
            logger.info(f"  {category}: {len(tools)} tools")
        
        # Verify registry persistence
        stats = ToolRegistry.get_registry_stats()
        logger.info(f"Registry stats: {stats}")
        
        return tool_count
        
    except Exception as e:
        logger.error(f"Failed to initialize tools: {e}", exc_info=True)
        raise


def get_tool_summary():
    """
    Get summary of all registered tools.
    
    Returns:
        Dict with tool statistics
    """
    from backend.core.tools.registry import ToolRegistry, _tools
    
    by_category = ToolRegistry.list_by_category()
    
    return {
        "total_tools": len(_tools),
        "by_category": {
            category: len(tools)
            for category, tools in by_category.items()
        },
        "categories": list(by_category.keys())
    }
