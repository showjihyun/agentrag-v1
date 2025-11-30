"""
Custom Validators for Input Validation

Provides reusable validators for common input patterns:
- Email validation
- Password strength validation
- UUID validation
- String sanitization
- Numeric range validation
- Date/time validation
"""

import re
import uuid
from typing import Any, Callable, List, Optional, TypeVar, Union
from datetime import datetime, date
from functools import wraps

from pydantic import field_validator, model_validator, ValidationInfo
from pydantic_core import PydanticCustomError


# ============================================================================
# Regex Patterns
# ============================================================================

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)

# Username: alphanumeric, underscore, hyphen, 3-30 chars
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")

# Slug: lowercase alphanumeric, hyphen, 1-100 chars
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Phone number (international format)
PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{1,14}$")

# URL pattern
URL_PATTERN = re.compile(
    r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
)

# SQL injection patterns to block
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
    r"(--|;|\/\*|\*\/)",
    r"(\bOR\b\s+\d+\s*=\s*\d+)",
    r"(\bAND\b\s+\d+\s*=\s*\d+)",
]

# XSS patterns to block
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
]


# ============================================================================
# Validation Functions
# ============================================================================

def validate_email(email: str) -> str:
    """Validate email format."""
    if not email:
        raise PydanticCustomError(
            "email_required",
            "Email is required"
        )
    
    email = email.strip().lower()
    
    if len(email) > 254:
        raise PydanticCustomError(
            "email_too_long",
            "Email must be 254 characters or less"
        )
    
    if not EMAIL_PATTERN.match(email):
        raise PydanticCustomError(
            "email_invalid",
            "Invalid email format"
        )
    
    return email


def validate_password(password: str, min_length: int = 8) -> str:
    """
    Validate password strength.
    
    Requirements:
    - Minimum length (default 8)
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character (@$!%*?&)
    """
    if not password:
        raise PydanticCustomError(
            "password_required",
            "Password is required"
        )
    
    if len(password) < min_length:
        raise PydanticCustomError(
            "password_too_short",
            f"Password must be at least {min_length} characters"
        )
    
    if len(password) > 128:
        raise PydanticCustomError(
            "password_too_long",
            "Password must be 128 characters or less"
        )
    
    if not re.search(r"[a-z]", password):
        raise PydanticCustomError(
            "password_no_lowercase",
            "Password must contain at least one lowercase letter"
        )
    
    if not re.search(r"[A-Z]", password):
        raise PydanticCustomError(
            "password_no_uppercase",
            "Password must contain at least one uppercase letter"
        )
    
    if not re.search(r"\d", password):
        raise PydanticCustomError(
            "password_no_digit",
            "Password must contain at least one digit"
        )
    
    if not re.search(r"[@$!%*?&]", password):
        raise PydanticCustomError(
            "password_no_special",
            "Password must contain at least one special character (@$!%*?&)"
        )
    
    return password


def validate_username(username: str) -> str:
    """Validate username format."""
    if not username:
        raise PydanticCustomError(
            "username_required",
            "Username is required"
        )
    
    username = username.strip()
    
    if len(username) < 3:
        raise PydanticCustomError(
            "username_too_short",
            "Username must be at least 3 characters"
        )
    
    if len(username) > 30:
        raise PydanticCustomError(
            "username_too_long",
            "Username must be 30 characters or less"
        )
    
    if not USERNAME_PATTERN.match(username):
        raise PydanticCustomError(
            "username_invalid",
            "Username can only contain letters, numbers, underscores, and hyphens"
        )
    
    return username


def validate_uuid(value: str) -> str:
    """Validate UUID format."""
    if not value:
        raise PydanticCustomError(
            "uuid_required",
            "UUID is required"
        )
    
    try:
        uuid.UUID(str(value))
        return str(value)
    except ValueError:
        raise PydanticCustomError(
            "uuid_invalid",
            "Invalid UUID format"
        )


def validate_slug(slug: str) -> str:
    """Validate slug format."""
    if not slug:
        raise PydanticCustomError(
            "slug_required",
            "Slug is required"
        )
    
    slug = slug.strip().lower()
    
    if len(slug) > 100:
        raise PydanticCustomError(
            "slug_too_long",
            "Slug must be 100 characters or less"
        )
    
    if not SLUG_PATTERN.match(slug):
        raise PydanticCustomError(
            "slug_invalid",
            "Slug can only contain lowercase letters, numbers, and hyphens"
        )
    
    return slug


def validate_url(url: str) -> str:
    """Validate URL format."""
    if not url:
        raise PydanticCustomError(
            "url_required",
            "URL is required"
        )
    
    url = url.strip()
    
    if len(url) > 2048:
        raise PydanticCustomError(
            "url_too_long",
            "URL must be 2048 characters or less"
        )
    
    if not URL_PATTERN.match(url):
        raise PydanticCustomError(
            "url_invalid",
            "Invalid URL format"
        )
    
    return url


def validate_phone(phone: str) -> str:
    """Validate phone number format."""
    if not phone:
        raise PydanticCustomError(
            "phone_required",
            "Phone number is required"
        )
    
    # Remove spaces and dashes
    phone = re.sub(r"[\s-]", "", phone.strip())
    
    if not PHONE_PATTERN.match(phone):
        raise PydanticCustomError(
            "phone_invalid",
            "Invalid phone number format"
        )
    
    return phone


# ============================================================================
# Sanitization Functions
# ============================================================================

def sanitize_string(
    value: str,
    max_length: Optional[int] = None,
    strip: bool = True,
    lowercase: bool = False,
    remove_html: bool = True,
) -> str:
    """
    Sanitize a string value.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        strip: Whether to strip whitespace
        lowercase: Whether to convert to lowercase
        remove_html: Whether to remove HTML tags
    """
    if not value:
        return value
    
    if strip:
        value = value.strip()
    
    if lowercase:
        value = value.lower()
    
    if remove_html:
        # Remove HTML tags
        value = re.sub(r"<[^>]+>", "", value)
    
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def sanitize_for_sql(value: str) -> str:
    """
    Sanitize string to prevent SQL injection.
    
    Note: This is a secondary defense. Always use parameterized queries.
    """
    if not value:
        return value
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise PydanticCustomError(
                "sql_injection_detected",
                "Invalid characters detected in input"
            )
    
    return value


def sanitize_for_xss(value: str) -> str:
    """
    Sanitize string to prevent XSS attacks.
    
    Note: This is a secondary defense. Always escape output properly.
    """
    if not value:
        return value
    
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise PydanticCustomError(
                "xss_detected",
                "Invalid content detected in input"
            )
    
    return value


# ============================================================================
# Numeric Validators
# ============================================================================

def validate_positive_int(value: int) -> int:
    """Validate that integer is positive."""
    if value <= 0:
        raise PydanticCustomError(
            "not_positive",
            "Value must be a positive integer"
        )
    return value


def validate_non_negative_int(value: int) -> int:
    """Validate that integer is non-negative."""
    if value < 0:
        raise PydanticCustomError(
            "negative_value",
            "Value must be non-negative"
        )
    return value


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> Union[int, float]:
    """Validate that value is within range."""
    if min_value is not None and value < min_value:
        raise PydanticCustomError(
            "below_minimum",
            f"Value must be at least {min_value}"
        )
    
    if max_value is not None and value > max_value:
        raise PydanticCustomError(
            "above_maximum",
            f"Value must be at most {max_value}"
        )
    
    return value


def validate_percentage(value: Union[int, float]) -> Union[int, float]:
    """Validate that value is a valid percentage (0-100)."""
    return validate_range(value, 0, 100)


# ============================================================================
# Date/Time Validators
# ============================================================================

def validate_future_date(value: Union[datetime, date]) -> Union[datetime, date]:
    """Validate that date is in the future."""
    now = datetime.utcnow() if isinstance(value, datetime) else date.today()
    
    if value <= now:
        raise PydanticCustomError(
            "not_future_date",
            "Date must be in the future"
        )
    
    return value


def validate_past_date(value: Union[datetime, date]) -> Union[datetime, date]:
    """Validate that date is in the past."""
    now = datetime.utcnow() if isinstance(value, datetime) else date.today()
    
    if value >= now:
        raise PydanticCustomError(
            "not_past_date",
            "Date must be in the past"
        )
    
    return value


def validate_date_range(
    start_date: Union[datetime, date],
    end_date: Union[datetime, date],
) -> bool:
    """Validate that start_date is before end_date."""
    if start_date >= end_date:
        raise PydanticCustomError(
            "invalid_date_range",
            "Start date must be before end date"
        )
    
    return True


# ============================================================================
# List Validators
# ============================================================================

def validate_non_empty_list(value: List[Any]) -> List[Any]:
    """Validate that list is not empty."""
    if not value:
        raise PydanticCustomError(
            "empty_list",
            "List cannot be empty"
        )
    return value


def validate_list_length(
    value: List[Any],
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> List[Any]:
    """Validate list length."""
    if min_length is not None and len(value) < min_length:
        raise PydanticCustomError(
            "list_too_short",
            f"List must have at least {min_length} items"
        )
    
    if max_length is not None and len(value) > max_length:
        raise PydanticCustomError(
            "list_too_long",
            f"List must have at most {max_length} items"
        )
    
    return value


def validate_unique_list(value: List[Any]) -> List[Any]:
    """Validate that list contains unique items."""
    if len(value) != len(set(value)):
        raise PydanticCustomError(
            "duplicate_items",
            "List must contain unique items"
        )
    return value


# ============================================================================
# Pydantic Validator Decorators
# ============================================================================

def create_string_validator(
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[re.Pattern] = None,
    pattern_error: str = "Invalid format",
    strip: bool = True,
    lowercase: bool = False,
):
    """
    Create a reusable string validator.
    
    Usage:
        class MyModel(BaseModel):
            name: str
            
            _validate_name = field_validator('name')(
                create_string_validator(min_length=1, max_length=100)
            )
    """
    def validator(cls, v: str) -> str:
        if v is None:
            return v
        
        if strip:
            v = v.strip()
        
        if lowercase:
            v = v.lower()
        
        if min_length is not None and len(v) < min_length:
            raise PydanticCustomError(
                "string_too_short",
                f"String must be at least {min_length} characters"
            )
        
        if max_length is not None and len(v) > max_length:
            raise PydanticCustomError(
                "string_too_long",
                f"String must be at most {max_length} characters"
            )
        
        if pattern is not None and not pattern.match(v):
            raise PydanticCustomError(
                "pattern_mismatch",
                pattern_error
            )
        
        return v
    
    return validator
