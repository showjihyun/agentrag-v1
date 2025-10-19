"""
Warnings filter configuration
Suppresses known deprecation warnings from third-party libraries
"""

import warnings
from pydantic import PydanticDeprecatedSince20, PydanticDeprecatedSince211


def configure_warnings():
    """Configure warning filters for the application"""
    
    # Suppress Pydantic deprecation warnings from litellm
    warnings.filterwarnings(
        "ignore",
        category=PydanticDeprecatedSince20,
        module="litellm.*"
    )
    
    warnings.filterwarnings(
        "ignore",
        category=PydanticDeprecatedSince211,
        module="litellm.*"
    )
    
    # Suppress Pydantic serialization warnings
    warnings.filterwarnings(
        "ignore",
        message=".*Pydantic serializer warnings.*",
        category=UserWarning,
        module="pydantic.*"
    )
    
    # Suppress specific litellm warnings
    warnings.filterwarnings(
        "ignore",
        message=".*model_fields.*",
        category=PydanticDeprecatedSince211
    )
    
    warnings.filterwarnings(
        "ignore",
        message=".*The `dict` method is deprecated.*",
        category=PydanticDeprecatedSince20
    )
