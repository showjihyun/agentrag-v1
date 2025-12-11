"""
Node Handler Registry

Central registry for all node type handlers.
"""

import logging
from typing import Dict, Type, Optional

from .base_handler import BaseNodeHandler

logger = logging.getLogger(__name__)


class NodeHandlerRegistry:
    """
    Registry for node handlers.
    
    Allows dynamic registration and lookup of handlers by node type.
    """
    
    _instance: Optional["NodeHandlerRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers: Dict[str, BaseNodeHandler] = {}
            cls._instance._handler_classes: Dict[str, Type[BaseNodeHandler]] = {}
        return cls._instance
    
    def register(self, handler_class: Type[BaseNodeHandler]) -> None:
        """
        Register a handler class.
        
        Args:
            handler_class: The handler class to register
        """
        # Create instance to get node_type
        handler = handler_class()
        node_type = handler.node_type
        
        self._handlers[node_type] = handler
        self._handler_classes[node_type] = handler_class
        
        logger.info(f"Registered handler for node type: {node_type}")
    
    def get_handler(self, node_type: str) -> Optional[BaseNodeHandler]:
        """
        Get handler for a node type.
        
        Args:
            node_type: The node type
            
        Returns:
            Handler instance or None if not found
        """
        return self._handlers.get(node_type)
    
    def has_handler(self, node_type: str) -> bool:
        """Check if handler exists for node type."""
        return node_type in self._handlers
    
    @property
    def supported_types(self) -> list[str]:
        """Get list of supported node types."""
        return list(self._handlers.keys())
    
    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        self._handler_classes.clear()


def register_handler(handler_class: Type[BaseNodeHandler]) -> Type[BaseNodeHandler]:
    """
    Decorator to register a handler class.
    
    Usage:
        @register_handler
        class MyNodeHandler(BaseNodeHandler):
            ...
    """
    NodeHandlerRegistry().register(handler_class)
    return handler_class


# Global registry instance
node_handler_registry = NodeHandlerRegistry()
