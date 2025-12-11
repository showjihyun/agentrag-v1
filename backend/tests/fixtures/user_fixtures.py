"""User-related test fixtures."""

import pytest
from typing import Dict, Any


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Password123",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_admin_user_data() -> Dict[str, Any]:
    """Sample admin user data for testing."""
    return {
        "email": "admin@example.com",
        "username": "adminuser",
        "password": "AdminPass123",
        "full_name": "Admin User",
        "is_admin": True,
    }


@pytest.fixture
def multiple_users_data() -> list[Dict[str, Any]]:
    """Multiple user data for batch testing."""
    return [
        {
            "email": f"user{i}@example.com",
            "username": f"testuser{i}",
            "password": "Password123",
            "full_name": f"Test User {i}",
        }
        for i in range(5)
    ]


@pytest.fixture
def invalid_user_data() -> Dict[str, Any]:
    """Invalid user data for validation testing."""
    return {
        "email": "invalid-email",
        "username": "",
        "password": "short",
        "full_name": "",
    }
