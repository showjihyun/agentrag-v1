"""Verify auth dependencies implementation."""

import sys
import asyncio
from uuid import uuid4
from unittest.mock import Mock
from fastapi.security import HTTPAuthorizationCredentials

# Add backend to path
sys.path.insert(0, ".")

from backend.core.auth_dependencies import (
    get_current_user,
    get_optional_user,
    require_role,
)
from backend.services.auth_service import AuthService
from backend.db.models.user import User


def create_mock_user(role="user", is_active=True):
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.username = "testuser"
    user.role = role
    user.is_active = is_active
    return user


async def test_get_current_user():
    """Test get_current_user dependency."""
    print("\n=== Testing get_current_user ===")

    # Create mock user and token
    mock_user = create_mock_user()
    token = AuthService.create_access_token({"sub": str(mock_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Mock database and repository
    mock_db = Mock()

    # Mock UserRepository
    from db.repositories.user_repository import UserRepository

    original_init = UserRepository.__init__
    original_get = UserRepository.get_user_by_id

    def mock_init(self, db):
        self.db = db

    def mock_get(self, user_id):
        if user_id == mock_user.id:
            return mock_user
        return None

    UserRepository.__init__ = mock_init
    UserRepository.get_user_by_id = mock_get

    try:
        # Test valid token
        user = await get_current_user(credentials, mock_db)
        assert user == mock_user
        print("✓ Valid token authentication works")

        # Test invalid token
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )
        try:
            await get_current_user(invalid_credentials, mock_db)
            print("✗ Invalid token should raise exception")
        except Exception as e:
            if "401" in str(e) or "Invalid" in str(e):
                print("✓ Invalid token raises 401 exception")
            else:
                print(f"✗ Unexpected exception: {e}")

        # Test inactive user
        inactive_user = create_mock_user(is_active=False)
        inactive_token = AuthService.create_access_token({"sub": str(inactive_user.id)})
        inactive_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=inactive_token
        )

        def mock_get_inactive(self, user_id):
            if user_id == inactive_user.id:
                return inactive_user
            return None

        UserRepository.get_user_by_id = mock_get_inactive

        try:
            await get_current_user(inactive_credentials, mock_db)
            print("✗ Inactive user should raise exception")
        except Exception as e:
            if "401" in str(e) or "inactive" in str(e).lower():
                print("✓ Inactive user raises 401 exception")
            else:
                print(f"✗ Unexpected exception: {e}")

    finally:
        # Restore original methods
        UserRepository.__init__ = original_init
        UserRepository.get_user_by_id = original_get


async def test_get_optional_user():
    """Test get_optional_user dependency."""
    print("\n=== Testing get_optional_user ===")

    # Create mock user and token
    mock_user = create_mock_user()
    token = AuthService.create_access_token({"sub": str(mock_user.id)})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Mock database and repository
    mock_db = Mock()

    from db.repositories.user_repository import UserRepository

    original_init = UserRepository.__init__
    original_get = UserRepository.get_user_by_id

    def mock_init(self, db):
        self.db = db

    def mock_get(self, user_id):
        if user_id == mock_user.id:
            return mock_user
        return None

    UserRepository.__init__ = mock_init
    UserRepository.get_user_by_id = mock_get

    try:
        # Test with valid token
        user = await get_optional_user(credentials, mock_db)
        assert user == mock_user
        print("✓ Valid token returns user")

        # Test with no credentials
        user = await get_optional_user(None, mock_db)
        assert user is None
        print("✓ No credentials returns None")

        # Test with invalid token (should return None, not raise)
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )
        user = await get_optional_user(invalid_credentials, mock_db)
        assert user is None
        print("✓ Invalid token returns None (no exception)")

    finally:
        # Restore original methods
        UserRepository.__init__ = original_init
        UserRepository.get_user_by_id = original_get


async def test_require_role():
    """Test require_role dependency factory."""
    print("\n=== Testing require_role ===")

    # Create mock users
    regular_user = create_mock_user(role="user")
    admin_user = create_mock_user(role="admin")
    premium_user = create_mock_user(role="premium")

    # Test admin role requirement
    admin_checker = require_role("admin")

    try:
        await admin_checker(admin_user)
        print("✓ Admin user passes admin role check")
    except Exception as e:
        print(f"✗ Admin user should pass: {e}")

    try:
        await admin_checker(regular_user)
        print("✗ Regular user should fail admin role check")
    except Exception as e:
        if "403" in str(e) or "Forbidden" in str(e):
            print("✓ Regular user fails admin role check with 403")
        else:
            print(f"✗ Unexpected exception: {e}")

    # Test premium role requirement
    premium_checker = require_role("premium")

    try:
        await premium_checker(premium_user)
        print("✓ Premium user passes premium role check")
    except Exception as e:
        print(f"✗ Premium user should pass: {e}")

    try:
        await premium_checker(regular_user)
        print("✗ Regular user should fail premium role check")
    except Exception as e:
        if "403" in str(e) or "Forbidden" in str(e):
            print("✓ Regular user fails premium role check with 403")
        else:
            print(f"✗ Unexpected exception: {e}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Auth Dependencies Verification")
    print("=" * 60)

    await test_get_current_user()
    await test_get_optional_user()
    await test_require_role()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
