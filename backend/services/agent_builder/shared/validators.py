"""
Validators

Common validation functions.
"""

import re
from typing import Any, Optional
from uuid import UUID

from backend.services.agent_builder.shared.errors import ValidationError


def validate_uuid(value: Any, field_name: str = "id") -> UUID:
    """Validate and convert to UUID."""
    if isinstance(value, UUID):
        return value
    
    if not value:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        raise ValidationError(f"Invalid UUID format for {field_name}", field=field_name)


def validate_name(
    value: str,
    field_name: str = "name",
    min_length: int = 1,
    max_length: int = 255,
) -> str:
    """Validate name field."""
    if not value:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    value = value.strip()
    
    if len(value) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters",
            field=field_name,
        )
    
    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} characters",
            field=field_name,
        )
    
    return value


def validate_not_empty(value: Any, field_name: str) -> Any:
    """Validate that value is not empty."""
    if value is None:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)
    
    if isinstance(value, (list, dict)) and len(value) == 0:
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)
    
    return value


def validate_email(value: str, field_name: str = "email") -> str:
    """Validate email format."""
    if not value:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValidationError(f"Invalid email format", field=field_name)
    
    return value.lower()


def validate_url(value: str, field_name: str = "url") -> str:
    """Validate URL format."""
    if not value:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, value, re.IGNORECASE):
        raise ValidationError(f"Invalid URL format", field=field_name)
    
    return value


def validate_in_list(
    value: Any,
    allowed_values: list,
    field_name: str,
) -> Any:
    """Validate value is in allowed list."""
    if value not in allowed_values:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(str(v) for v in allowed_values)}",
            field=field_name,
        )
    return value


def validate_positive(value: int, field_name: str) -> int:
    """Validate positive integer."""
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer", field=field_name)
    return value


def validate_non_negative(value: int, field_name: str) -> int:
    """Validate non-negative integer."""
    if not isinstance(value, int) or value < 0:
        raise ValidationError(f"{field_name} must be a non-negative integer", field=field_name)
    return value
