"""Authentication Pydantic models."""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re


class UserCreate(BaseModel):
    """Model for user registration."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")

    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "SecurePass123",
                "full_name": "John Doe",
            }
        }


class UserLogin(BaseModel):
    """Model for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {"email": "user@example.com", "password": "SecurePass123"}
        }


class UserResponse(BaseModel):
    """Model for user information response."""

    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="Email address")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    role: str = Field(..., description="User role (user, premium, admin)")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    query_count: int = Field(..., description="Total number of queries")
    storage_used_bytes: int = Field(..., description="Storage used in bytes")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "last_login_at": "2024-01-01T12:00:00Z",
                "query_count": 42,
                "storage_used_bytes": 1048576,
            }
        }


class TokenResponse(BaseModel):
    """Model for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "username": "john_doe",
                    "full_name": "John Doe",
                    "role": "user",
                    "is_active": True,
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z",
                    "last_login_at": "2024-01-01T12:00:00Z",
                    "query_count": 42,
                    "storage_used_bytes": 1048576,
                },
            }
        }


class TokenRefresh(BaseModel):
    """Model for token refresh request."""

    refresh_token: str = Field(..., description="JWT refresh token")

    class Config:
        json_schema_extra = {
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }


class UserUpdate(BaseModel):
    """Model for updating user information."""

    username: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Username"
    )
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    current_password: Optional[str] = Field(
        None, description="Current password (required for password change)"
    )
    new_password: Optional[str] = Field(
        None, min_length=8, max_length=100, description="New password"
    )

    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v

    @validator("new_password")
    def validate_password_strength(cls, v, values):
        """Validate password strength."""
        if v is not None:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not re.search(r"[A-Za-z]", v):
                raise ValueError("Password must contain at least one letter")
            if not re.search(r"\d", v):
                raise ValueError("Password must contain at least one number")
            # Ensure current_password is provided when changing password
            if "current_password" not in values or values["current_password"] is None:
                raise ValueError("Current password is required to set a new password")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe_updated",
                "full_name": "John Doe Jr.",
                "email": "newemail@example.com",
                "current_password": "OldPass123",
                "new_password": "NewSecurePass456",
            }
        }
