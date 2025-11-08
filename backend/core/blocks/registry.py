"""Block Registry for managing workflow blocks in Agent Builder.

This registry manages the available block types that can be used in visual workflows.
It follows a similar pattern to the ToolRegistry but is designed for workflow blocks.
"""

import logging
from typing import Dict, List, Optional, Type, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class BlockRegistry:
    """
    Registry for managing workflow blocks.
    
    Blocks are registered using a decorator pattern and can be looked up by type.
    Each block has a configuration that defines its UI representation and behavior.
    """
    
    _blocks: Dict[str, Dict[str, Any]] = {}
    _block_classes: Dict[str, Type] = {}
    
    @classmethod
    def register(
        cls,
        block_type: str,
        name: str,
        description: str,
        category: str = "blocks",
        sub_blocks: List[Dict[str, Any]] = None,
        inputs: Dict[str, Any] = None,
        outputs: Dict[str, Any] = None,
        bg_color: str = "#3B82F6",
        icon: str = "cube",
        auth_mode: Optional[str] = None,
        docs_link: Optional[str] = None
    ) -> Callable:
        """
        Decorator to register a block class.
        
        Args:
            block_type: Unique block type identifier (e.g., "openai", "http")
            name: Display name for the block
            description: Block description
            category: Block category ("blocks", "tools", "triggers")
            sub_blocks: List of SubBlock configurations for UI
            inputs: Input schema definition
            outputs: Output schema definition
            bg_color: Background color for block UI
            icon: Icon name for block UI
            auth_mode: Authentication mode ("oauth", "api_key", "none")
            docs_link: Link to documentation
            
        Returns:
            Decorator function
            
        Example:
            @BlockRegistry.register(
                block_type="openai",
                name="OpenAI",
                description="Call OpenAI API",
                category="tools",
                sub_blocks=[
                    {
                        "id": "model",
                        "type": "dropdown",
                        "title": "Model",
                        "required": True,
                        "options": ["gpt-4", "gpt-3.5-turbo"]
                    }
                ]
            )
            class OpenAIBlock(BaseBlock):
                async def execute(self, inputs, context):
                    # Implementation
                    pass
        """
        def decorator(block_class: Type) -> Type:
            # Store block configuration
            cls._blocks[block_type] = {
                "type": block_type,
                "name": name,
                "description": description,
                "category": category,
                "sub_blocks": sub_blocks or [],
                "inputs": inputs or {},
                "outputs": outputs or {},
                "bg_color": bg_color,
                "icon": icon,
                "auth_mode": auth_mode,
                "docs_link": docs_link,
            }
            
            # Store block class
            cls._block_classes[block_type] = block_class
            
            logger.info(f"Registered block: {block_type} ({name})")
            
            return block_class
        
        return decorator
    
    @classmethod
    def get_block_config(cls, block_type: str) -> Optional[Dict[str, Any]]:
        """
        Get block configuration by type.
        
        Args:
            block_type: Block type identifier
            
        Returns:
            Block configuration dict or None if not found
        """
        return cls._blocks.get(block_type)
    
    @classmethod
    def get_block_class(cls, block_type: str) -> Optional[Type]:
        """
        Get block class by type.
        
        Args:
            block_type: Block type identifier
            
        Returns:
            Block class or None if not found
        """
        return cls._block_classes.get(block_type)
    
    @classmethod
    def create_block_instance(cls, block_type: str, **kwargs) -> Any:
        """
        Create a block instance by type.
        
        Args:
            block_type: Block type identifier
            **kwargs: Arguments to pass to block constructor
            
        Returns:
            Block instance
            
        Raises:
            ValueError: If block type not found
        """
        block_class = cls.get_block_class(block_type)
        if not block_class:
            raise ValueError(f"Block type not found: {block_type}")
        
        return block_class(**kwargs)
    
    @classmethod
    def list_blocks(
        cls,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all registered blocks.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of block configurations
        """
        blocks = list(cls._blocks.values())
        
        if category:
            blocks = [b for b in blocks if b["category"] == category]
        
        return blocks
    
    @classmethod
    def list_by_category(cls) -> Dict[str, List[Dict[str, Any]]]:
        """
        List blocks grouped by category.
        
        Returns:
            Dict mapping category to list of block configurations
        """
        categorized = {}
        
        for block in cls._blocks.values():
            category = block["category"]
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(block)
        
        return categorized
    
    @classmethod
    def get_block_types(cls) -> List[str]:
        """
        Get list of all registered block types.
        
        Returns:
            List of block type identifiers
        """
        return list(cls._blocks.keys())
    
    @classmethod
    def is_registered(cls, block_type: str) -> bool:
        """
        Check if a block type is registered.
        
        Args:
            block_type: Block type identifier
            
        Returns:
            True if registered, False otherwise
        """
        return block_type in cls._blocks
    
    @classmethod
    def validate_block_config(cls, block_type: str, config: Dict[str, Any]) -> bool:
        """
        Validate block configuration against registered schema.
        
        Args:
            block_type: Block type identifier
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        block_config = cls.get_block_config(block_type)
        if not block_config:
            logger.warning(f"Block type not found: {block_type}")
            return False
        
        # Validate required sub_blocks
        sub_blocks = block_config.get("sub_blocks", [])
        for sub_block in sub_blocks:
            if sub_block.get("required", False):
                sub_block_id = sub_block["id"]
                if sub_block_id not in config:
                    logger.warning(
                        f"Missing required sub_block '{sub_block_id}' "
                        f"for block type '{block_type}'"
                    )
                    return False
        
        return True
    
    @classmethod
    def get_block_schema(cls, block_type: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON schema for block inputs/outputs.
        
        Args:
            block_type: Block type identifier
            
        Returns:
            Schema dict with 'inputs' and 'outputs' keys
        """
        block_config = cls.get_block_config(block_type)
        if not block_config:
            return None
        
        return {
            "inputs": block_config.get("inputs", {}),
            "outputs": block_config.get("outputs", {})
        }
    
    @classmethod
    def clear_registry(cls):
        """Clear all registered blocks (useful for testing)."""
        cls._blocks.clear()
        cls._block_classes.clear()
        logger.info("Cleared block registry")


# Convenience function for external use
def register_block(
    block_type: str,
    name: str,
    description: str,
    **kwargs
) -> Callable:
    """
    Convenience function to register a block.
    
    This is an alias for BlockRegistry.register() for easier imports.
    
    Args:
        block_type: Unique block type identifier
        name: Display name for the block
        description: Block description
        **kwargs: Additional configuration options
        
    Returns:
        Decorator function
    """
    return BlockRegistry.register(
        block_type=block_type,
        name=name,
        description=description,
        **kwargs
    )
