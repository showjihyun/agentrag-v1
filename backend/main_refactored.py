"""
FastAPI application entry point (Refactored).

This is the new modular entry point that uses the application factory pattern.
The application is now organized into:
- backend/app/factory.py: Application creation and configuration
- backend/app/middleware/: HTTP middleware components
- backend/app/routers/: API router registration
- backend/app/lifecycle/: Startup and shutdown handlers
- backend/app/exception_handlers.py: Exception handling

Usage:
    uvicorn backend.main_refactored:app --reload --port 8000
    
Or:
    python -m backend.main_refactored
"""

import warnings


def configure_warnings():
    """Configure warning filters for known third-party library warnings."""
    
    # Pydantic v2 migration warnings
    warnings.filterwarnings(
        "ignore",
        message=".*Pydantic.*deprecated.*",
        category=DeprecationWarning
    )
    warnings.filterwarnings(
        "ignore", 
        message=".*model_fields.*",
        category=DeprecationWarning
    )
    
    # LiteLLM streaming warnings
    warnings.filterwarnings(
        "ignore",
        message=".*StreamingChoices.*",
        category=UserWarning
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Message.*serialized value.*",
        category=UserWarning
    )
    
    # SQLAlchemy 2.0 migration warnings
    warnings.filterwarnings(
        "ignore",
        message=".*SQLAlchemy.*deprecated.*",
        category=DeprecationWarning
    )
    
    # Suppress Pydantic deprecation categories if available
    try:
        from pydantic import PydanticDeprecatedSince20, PydanticDeprecatedSince211
        warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
        warnings.filterwarnings("ignore", category=PydanticDeprecatedSince211)
    except ImportError:
        pass


# Apply warning configuration
configure_warnings()

# Create the application using the factory
from backend.app.factory import create_app

app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
