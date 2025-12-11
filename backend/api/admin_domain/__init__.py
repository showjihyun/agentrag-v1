"""
Admin domain API routers

Groups all admin-related endpoints:
- admin.py: Admin operations
- config.py: System configuration
- llm_settings.py: LLM configuration
- models.py: Model management
- cache_management.py: Cache administration
- enterprise.py: Enterprise features
- experiments.py: A/B testing and experiments
"""

# Re-export routers for easy access
# Usage: from backend.api.admin import admin_router

__all__ = [
    "admin",
    "config",
    "llm_settings",
    "models",
    "cache_management",
    "enterprise",
    "experiments",
]
