"""Workflow Blocks System for Agent Builder.

This module provides the block system for visual workflow creation,
including block registry, base classes, and built-in block implementations.
"""

from backend.core.blocks.registry import BlockRegistry, register_block
from backend.core.blocks.base import (
    BaseBlock,
    BlockExecutionError,
    BlockValidationError,
)

# Import all block implementations to register them
from backend.core.blocks.condition_block import ConditionBlock
from backend.core.blocks.http_block import HTTPBlock
from backend.core.blocks.loop_block import LoopBlock
from backend.core.blocks.parallel_block import ParallelBlock
from backend.core.blocks.openai_block import OpenAIBlock
from backend.core.blocks.knowledge_base_block import KnowledgeBaseBlock, KnowledgeBaseUploadBlock

__all__ = [
    # Registry
    "BlockRegistry",
    "register_block",
    # Base classes
    "BaseBlock",
    "BlockExecutionError",
    "BlockValidationError",
    # Block implementations
    "ConditionBlock",
    "HTTPBlock",
    "LoopBlock",
    "ParallelBlock",
    "OpenAIBlock",
    "KnowledgeBaseBlock",
    "KnowledgeBaseUploadBlock",
]


def initialize_blocks():
    """
    Initialize all blocks and register them.
    
    This function is called during application startup to ensure
    all blocks are registered in the BlockRegistry.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # All blocks are registered via decorators when imported above
    registered = BlockRegistry.get_block_types()
    logger.info(f"Initialized {len(registered)} workflow blocks: {registered}")
    
    return registered


def get_available_blocks():
    """Get list of all available blocks for the UI."""
    return BlockRegistry.list_by_category()
