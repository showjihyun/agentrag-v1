"""Tests for authentication dependencies."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

from backend.core.auth_dependencies import (
    get_current_user,
    get_optional_user,
    require_role,
)
from backend.services.auth_service import AuthService
from backend.db.models.user import User


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def mock_user():
    """Mock user object."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.username = "testuser"
    user.role = "user"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user object."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.username = "admin"
    user.role = "admin"
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    return user


@pytest.mark.asyncio
async def test_get_current_user_valid_token(mock_db, mock_user, monkeypatch):
    """Test get_current_user with valid token."""
    # Create valid token
    token = AuthService.create_access_token({"sub": str(mock_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Mock UserRepository
    mock_repo = Mock()
    mock_repo.get_user_by_id.return_value = mock_user

    def mock_repo_init(db):
        return mock_repo

    monkeypatch.setattr("core.auth_dependencies.UserRepository", mock_repo_init)

    # Call dependency
    user = await get_current_user(credentials, mock_db)

    # Verify
    assert user == mock_user
    mock_repo.get_user_by_id.assert_called_once_with(mock_user.id)


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_db):
    """Test get_current_user with invalid token."""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid_token"
    )

    # Should raise 401
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, mock_db)

    assert exc_info.value.status_code == 401
    assert "Invalid or expired token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(mock_db, monkeypatch):
    """Test get_current_user when user not found in database."""
    user_id = uuid4()
    token = AuthService.create_access_token({"sub": str(user_id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Mock UserRepository to return None
    mock_repo = Mock()
    mock_repo.get_user_by_id.return_value = None

    def mock_repo_init(db):
        return mock_repo

    monkeypatch.setattr("core.auth_dependencies.UserRepository", mock_repo_init)

    # Should raise 401
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, mock_db)

    assert exc_info.value.status_code == 401
    assert "User not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(mock_db, mock_user, monkeypatch):
    """Test get_current_user with inactive user."""
    mock_user.is_active = False
    token = AuthService.create_access_token({"sub": str(mock_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Mock UserRepository
    mock_repo = Mock()
    mock_repo.get_user_by_id.return_value = mock_user

    def mock_repo_init(db):
        return mock_repo

    monkeypatch.setattr("core.auth_dependencies.UserRepository", mock_repo_init)

    # Should raise 401
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, mock_db)

    assert exc_info.value.status_code == 401
    assert "inactive" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_optional_user_no_credentials(mock_db):
    """Test get_optional_user with no credentials."""
    user = await get_optional_user(None, mock_db)
    assert user is None


@pytest.mark.asyncio
async def test_get_optional_user_valid_token(mock_db, mock_user, monkeypatch):
    """Test get_optional_user with valid token."""
    token = AuthService.create_access_token({"sub": str(mock_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Mock UserRepository
    mock_repo = Mock()
    mock_repo.get_user_by_id.return_value = mock_user

    def mock_repo_init(db):
        return mock_repo

    monkeypatch.setattr("core.auth_dependencies.UserRepository", mock_repo_init)

    # Call dependency
    user = await get_optional_user(credentials, mock_db)

    # Verify
    assert user == mock_user


@pytest.mark.asyncio
async def test_get_optional_user_invalid_token(mock_db):
    """Test get_optional_user with invalid token returns None."""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid_token"
    )

    # Should return None (not raise exception)
    user = await get_optional_user(credentials, mock_db)
    assert user is None


@pytest.mark.asyncio
async def test_require_role_success(mock_admin_user):
    """Test require_role with correct role."""
    role_checker = require_role("admin")

    # Should not raise exception
    await role_checker(mock_admin_user)


@pytest.mark.asyncio
async def test_require_role_failure(mock_user):
    """Test require_role with incorrect role."""
    role_checker = require_role("admin")

    # Should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await role_checker(mock_user)

    assert exc_info.value.status_code == 403
    assert "admin" in exc_info.value.detail


@pytest.mark.asyncio
async def test_require_role_premium(mock_user):
    """Test require_role with premium role."""
    mock_user.role = "premium"
    role_checker = require_role("premium")

    # Should not raise exception
    await role_checker(mock_user)
