"""
Application lifecycle management.

Handles startup and shutdown events.
"""

from backend.app.lifecycle.startup import startup_handler
from backend.app.lifecycle.shutdown import shutdown_handler
from backend.app.lifecycle.agent_plugin_startup import create_startup_handler, create_shutdown_handler

__all__ = ["startup_handler", "shutdown_handler", "create_startup_handler", "create_shutdown_handler"]
