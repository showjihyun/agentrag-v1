"""
Application package for modular FastAPI setup.

This package contains:
- middleware: HTTP middleware components
- routers: API router registration
- lifecycle: Startup and shutdown handlers
"""

from backend.app.factory import create_app

__all__ = ["create_app"]
