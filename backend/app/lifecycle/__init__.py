"""
Application lifecycle management.

Handles startup and shutdown events.
"""

from backend.app.lifecycle.startup import startup_handler
from backend.app.lifecycle.shutdown import shutdown_handler

__all__ = ["startup_handler", "shutdown_handler"]
