"""Sync tools from ToolRegistry to database."""

import logging
from sqlalchemy.orm import Session
from backend.db.models.agent_builder import Tool
from backend.core.tools.registry import ToolRegistry
from datetime import datetime

logger = logging.getLogger(__name__)


def sync_tools_to_database(db: Session) -> int:
    """
    Sync all tools from ToolRegistry to database.
    
    Args:
        db: Database session
        
    Returns:
        Number of tools synced
    """
    logger.info("🔄 Syncing tools from ToolRegistry to database...")
    
    synced_count = 0
    updated_count = 0
    
    try:
        # Get all tools from registry
        tool_ids = ToolRegistry.get_tool_ids()
        logger.info(f"📋 Found {len(tool_ids)} tools in ToolRegistry")
        
        for tool_id in tool_ids:
            config = ToolRegistry.get_tool_config(tool_id)
            if not config:
                logger.warning(f"⚠️  Tool config not found for: {tool_id}")
                continue
            
            # Check if tool exists in database
            existing_tool = db.query(Tool).filter(Tool.id == tool_id).first()
            
            # Build input schema from params
            input_schema = {"type": "object", "properties": {}}
            if config.params:
                for param in config.params:
                    # Handle both ParamConfig objects and strings
                    if isinstance(param, str):
                        input_schema["properties"][param] = {
                            "type": "string",
                            "description": f"Parameter: {param}"
                        }
                    else:
                        input_schema["properties"][param.name] = {
                            "type": param.type,
                            "description": param.description,
                            "required": param.required
                        }
            
            # Check if requires_auth attribute exists
            requires_auth = getattr(config, 'requires_auth', False)
            
            if existing_tool:
                # Update existing tool
                existing_tool.name = config.name
                existing_tool.description = config.description
                existing_tool.category = config.category
                existing_tool.input_schema = input_schema
                existing_tool.requires_auth = requires_auth
                existing_tool.is_builtin = True
                existing_tool.implementation_type = "builtin"
                existing_tool.implementation_ref = f"ToolRegistry.{tool_id}"
                existing_tool.updated_at = datetime.utcnow()
                updated_count += 1
                logger.debug(f"  ✏️  Updated: {tool_id}")
            else:
                # Create new tool
                new_tool = Tool(
                    id=tool_id,
                    name=config.name,
                    description=config.description,
                    category=config.category,
                    input_schema=input_schema,
                    requires_auth=requires_auth,
                    is_builtin=True,
                    implementation_type="builtin",
                    implementation_ref=f"ToolRegistry.{tool_id}",
                )
                db.add(new_tool)
                synced_count += 1
                logger.debug(f"  ➕ Created: {tool_id}")
        
        # Commit all changes
        db.commit()
        
        logger.info(f"✅ Tool sync complete: {synced_count} created, {updated_count} updated")
        return synced_count + updated_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to sync tools to database: {e}", exc_info=True)
        raise


def list_tools_in_database(db: Session) -> None:
    """List all tools currently in database."""
    tools = db.query(Tool).all()
    logger.info(f"\n📊 Tools in database ({len(tools)} total):")
    
    by_category = {}
    for tool in tools:
        category = tool.category or "uncategorized"
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool)
    
    for category, tools_list in sorted(by_category.items()):
        logger.info(f"\n  {category.upper()} ({len(tools_list)} tools):")
        for tool in sorted(tools_list, key=lambda t: t.name):
            logger.info(f"    - {tool.id}: {tool.name}")
