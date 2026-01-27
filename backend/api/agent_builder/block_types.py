"""
Block Types API

Provides endpoints for listing available block types from the BlockRegistry.
This includes built-in blocks and agentic workflow blocks.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Query

from backend.core.blocks import BlockRegistry

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/block-types",
    tags=["agent-builder-block-types"],
)


@router.get(
    "",
    response_model=Dict[str, List[Dict[str, Any]]],
    summary="List all available block types",
    description="Get all registered block types grouped by category"
)
async def list_block_types():
    """
    List all available block types from the BlockRegistry.
    
    Returns blocks grouped by category:
    - blocks: Standard workflow blocks
    - tools: Tool integration blocks
    - triggers: Event trigger blocks
    - agentic: Agentic workflow blocks (NEW)
    
    **Returns:**
    ```json
    {
        "agentic": [
            {
                "type": "agentic_rag",
                "name": "Agentic RAG",
                "description": "Intelligent retrieval with query decomposition...",
                "category": "agentic",
                "bg_color": "#EC4899",
                "icon": "brain",
                "sub_blocks": [...],
                "inputs": {...},
                "outputs": {...}
            },
            ...
        ],
        "blocks": [...],
        "tools": [...]
    }
    ```
    """
    try:
        blocks_by_category = BlockRegistry.list_by_category()
        logger.info(f"Listed {len(blocks_by_category)} block categories")
        return blocks_by_category
    except Exception as e:
        logger.error(f"Error listing block types: {e}", exc_info=True)
        return {}


@router.get(
    "/category/{category}",
    response_model=List[Dict[str, Any]],
    summary="List block types by category",
    description="Get all block types in a specific category"
)
async def list_block_types_by_category(category: str):
    """
    List block types filtered by category.
    
    **Parameters:**
    - category: Category name (agentic, blocks, tools, triggers)
    
    **Returns:**
    - List of block configurations in the specified category
    """
    try:
        blocks = BlockRegistry.list_blocks(category=category)
        logger.info(f"Listed {len(blocks)} blocks in category '{category}'")
        return blocks
    except Exception as e:
        logger.error(f"Error listing blocks for category '{category}': {e}", exc_info=True)
        return []


@router.get(
    "/{block_type}",
    response_model=Dict[str, Any],
    summary="Get block type configuration",
    description="Get detailed configuration for a specific block type"
)
async def get_block_type(block_type: str):
    """
    Get configuration for a specific block type.
    
    **Parameters:**
    - block_type: Block type identifier (e.g., "agentic_rag", "openai")
    
    **Returns:**
    - Block configuration with schema, sub_blocks, and metadata
    
    **Errors:**
    - 404: Block type not found
    """
    from fastapi import HTTPException
    
    config = BlockRegistry.get_block_config(block_type)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Block type '{block_type}' not found"
        )
    
    return config


@router.get(
    "/{block_type}/schema",
    response_model=Dict[str, Any],
    summary="Get block type schema",
    description="Get input/output schema for a specific block type"
)
async def get_block_type_schema(block_type: str):
    """
    Get JSON schema for block inputs and outputs.
    
    **Parameters:**
    - block_type: Block type identifier
    
    **Returns:**
    ```json
    {
        "inputs": {
            "query": {"type": "string", "required": true},
            "strategy": {"type": "string", "default": "adaptive"}
        },
        "outputs": {
            "answer": {"type": "string"},
            "confidence_score": {"type": "number"}
        }
    }
    ```
    
    **Errors:**
    - 404: Block type not found
    """
    from fastapi import HTTPException
    
    schema = BlockRegistry.get_block_schema(block_type)
    if not schema:
        raise HTTPException(
            status_code=404,
            detail=f"Block type '{block_type}' not found"
        )
    
    return schema


@router.get(
    "/stats/summary",
    response_model=Dict[str, Any],
    summary="Get block registry statistics",
    description="Get summary statistics about registered blocks"
)
async def get_block_stats():
    """
    Get statistics about the block registry.
    
    **Returns:**
    ```json
    {
        "total_blocks": 15,
        "by_category": {
            "agentic": 4,
            "blocks": 6,
            "tools": 3,
            "triggers": 2
        },
        "block_types": ["agentic_rag", "agentic_reflection", ...]
    }
    ```
    """
    try:
        blocks_by_category = BlockRegistry.list_by_category()
        block_types = BlockRegistry.get_block_types()
        
        stats = {
            "total_blocks": len(block_types),
            "by_category": {
                category: len(blocks)
                for category, blocks in blocks_by_category.items()
            },
            "block_types": block_types,
            "categories": list(blocks_by_category.keys())
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting block stats: {e}", exc_info=True)
        return {
            "total_blocks": 0,
            "by_category": {},
            "block_types": [],
            "categories": []
        }
