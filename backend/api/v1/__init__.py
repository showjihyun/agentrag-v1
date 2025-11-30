"""
API v1 Module.

Versioned API endpoints for better backward compatibility.
All new APIs should be added here with proper versioning.
"""

from backend.api.v1 import health

__all__ = ["health"]
