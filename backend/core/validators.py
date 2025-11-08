"""Input validation utilities."""

import re
from typing import Optional
from pydantic import BaseModel, validator, EmailStr, constr


class EmailValidator:
    """Email validation utilities."""

    @staticmethod
    def is_valid(email: str) -> bool:
        """Check if email format is valid."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))


class PasswordValidator:
    """Password validation utilities."""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @staticmethod
    def validate(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < PasswordValidator.MIN_LENGTH:
            return (
                False,
                f"Password must be at least {PasswordValidator.MIN_LENGTH} characters",
            )

        if len(password) > PasswordValidator.MAX_LENGTH:
            return (
                False,
                f"Password must be at most {PasswordValidator.MAX_LENGTH} characters",
            )

        # Check for at least one letter
        if not re.search(r"[a-zA-Z]", password):
            return False, "Password must contain at least one letter"

        # Check for at least one number
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"

        return True, None


class UsernameValidator:
    """Username validation utilities."""

    MIN_LENGTH = 3
    MAX_LENGTH = 50
    PATTERN = r"^[a-zA-Z0-9_-]+$"

    @staticmethod
    def validate(username: str) -> tuple[bool, Optional[str]]:
        """
        Validate username format.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(username) < UsernameValidator.MIN_LENGTH:
            return (
                False,
                f"Username must be at least {UsernameValidator.MIN_LENGTH} characters",
            )

        if len(username) > UsernameValidator.MAX_LENGTH:
            return (
                False,
                f"Username must be at most {UsernameValidator.MAX_LENGTH} characters",
            )

        if not re.match(UsernameValidator.PATTERN, username):
            return (
                False,
                "Username can only contain letters, numbers, underscores, and hyphens",
            )

        return True, None


class QueryValidator:
    """Query input validation."""

    MIN_LENGTH = 1
    MAX_LENGTH = 5000

    @staticmethod
    def validate(query: str) -> tuple[bool, Optional[str]]:
        """
        Validate query input.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"

        if len(query) < QueryValidator.MIN_LENGTH:
            return False, "Query is too short"

        if len(query) > QueryValidator.MAX_LENGTH:
            return (
                False,
                f"Query must be at most {QueryValidator.MAX_LENGTH} characters",
            )

        return True, None


# Pydantic models for request validation
class UserRegistrationRequest(BaseModel):
    """User registration request validation."""

    email: EmailStr
    username: constr(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: constr(min_length=8, max_length=128)
    full_name: Optional[str] = None

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        is_valid, error = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error)
        return v


class UserLoginRequest(BaseModel):
    """User login request validation."""

    email: EmailStr
    password: str


class QueryRequest(BaseModel):
    """Query request validation."""

    query: constr(min_length=1, max_length=5000)
    mode: Optional[str] = "balanced"
    session_id: Optional[str] = None

    @validator("query")
    def validate_query(cls, v):
        """Validate query input."""
        is_valid, error = QueryValidator.validate(v)
        if not is_valid:
            raise ValueError(error)
        return v

    @validator("mode")
    def validate_mode(cls, v):
        """Validate query mode."""
        allowed_modes = ["fast", "balanced", "deep"]
        if v not in allowed_modes:
            raise ValueError(f"Mode must be one of: {', '.join(allowed_modes)}")
        return v
