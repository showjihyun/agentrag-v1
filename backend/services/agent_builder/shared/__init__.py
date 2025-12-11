"""
Shared Module

Common utilities, errors, and validators used across layers.
"""

from backend.services.agent_builder.shared.errors import (
    DomainError,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthorizationError,
)
from backend.services.agent_builder.shared.validators import (
    validate_uuid,
    validate_name,
    validate_not_empty,
)
from backend.services.agent_builder.shared.utils import (
    generate_id,
    utc_now,
)

__all__ = [
    # Errors
    "DomainError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "AuthorizationError",
    # Validators
    "validate_uuid",
    "validate_name",
    "validate_not_empty",
    # Utils
    "generate_id",
    "utc_now",
]
