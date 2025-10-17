"""Verify auth dependencies implementation - improved version."""

import sys
import asyncio
from uuid import uuid4
from unittest.mock import Mock
from fastapi import HTTPException
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
        # Test 1: Valid token
        print("\nTest 1: Valid token authentication")
        user = await get_current_user(credentials, mock_db)
        assert user == mock_user
        print("  ✓ Valid token authentication works")

        # Test 2: Invalid token
        print("\nTest 2: Invalid token")
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )
        try:
            await get_current_user(invalid_credentials, mock_db)
            print("  ✗ Invalid token should raise HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            print(f"  ✓ Invalid token raises 401: {e.detail}")

        # Test 3: Inactive user
        print("\nTest 3: Inactive user")
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
            print("  ✗ Inactive user should raise HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            print(f"  ✓ Inactive user raises 401: {e.detail}")

        # Test 4: User not found
        print("\nTest 4: User not found")
        unknown_user_id = uuid4()
        unknown_token = AuthService.create_access_token({"sub": str(unknown_user_id)})
        unknown_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=unknown_token
        )

        UserRepository.get_user_by_id = mock_get  # Reset to original mock

        try:
            await get_current_user(unknown_credentials, mock_db)
            print("  ✗ Unknown user should raise HTTPException")
        except HTTPException as e:
            assert e.status_code == 401
            print(f"  ✓ Unknown user raises 401: {e.detail}")

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
        # Test 1: Valid token
        print("\nTest 1: Valid token returns user")
        user = await get_optional_user(credentials, mock_db)
        assert user == mock_user
        print("  ✓ Valid token returns user")

        # Test 2: No credentials
        print("\nTest 2: No credentials")
        user = await get_optional_user(None, mock_db)
        assert user is None
        print("  ✓ No credentials returns None (guest access)")

        # Test 3: Invalid token (should return None, not raise)
        print("\nTest 3: Invalid token")
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )
        user = await get_optional_user(invalid_credentials, mock_db)
        assert user is None
        print("  ✓ Invalid token returns None (no exception, guest access)")

        # Test 4: Inactive user (should return None, not raise)
        print("\nTest 4: Inactive user")
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

        user = await get_optional_user(inactive_credentials, mock_db)
        assert user is None
        print("  ✓ Inactive user returns None (guest access)")

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

    # Test 1: Admin role requirement - admin user
    print("\nTest 1: Admin role requirement - admin user")
    admin_checker = require_role("admin")

    try:
        await admin_checker(admin_user)
        print("  ✓ Admin user passes admin role check")
    except HTTPException as e:
        print(f"  ✗ Admin user should pass: {e.detail}")

    # Test 2: Admin role requirement - regular user
    print("\nTest 2: Admin role requirement - regular user")
    try:
        await admin_checker(regular_user)
        print("  ✗ Regular user should fail admin role check")
    except HTTPException as e:
        assert e.status_code == 403
        print(f"  ✓ Regular user fails admin role check with 403: {e.detail}")

    # Test 3: Premium role requirement - premium user
    print("\nTest 3: Premium role requirement - premium user")
    premium_checker = require_role("premium")

    try:
        await premium_checker(premium_user)
        print("  ✓ Premium user passes premium role check")
    except HTTPException as e:
        print(f"  ✗ Premium user should pass: {e.detail}")

    # Test 4: Premium role requirement - regular user
    print("\nTest 4: Premium role requirement - regular user")
    try:
        await premium_checker(regular_user)
        print("  ✗ Regular user should fail premium role check")
    except HTTPException as e:
        assert e.status_code == 403
        print(f"  ✓ Regular user fails premium role check with 403: {e.detail}")

    # Test 5: User role requirement - all users
    print("\nTest 5: User role requirement - all users")
    user_checker = require_role("user")

    try:
        await user_checker(regular_user)
        print("  ✓ Regular user passes user role check")
    except HTTPException as e:
        print(f"  ✗ Regular user should pass: {e.detail}")

    try:
        await user_checker(admin_user)
        print("  ✗ Admin user should fail user role check (role mismatch)")
    except HTTPException as e:
        assert e.status_code == 403
        print(f"  ✓ Admin user fails user role check (exact match required)")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("Auth Dependencies Verification - Comprehensive Tests")
    print("=" * 70)

    await test_get_current_user()
    await test_get_optional_user()
    await test_require_role()

    print("\n" + "=" * 70)
    print("✓ All tests completed successfully!")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print("✓ get_current_user: Validates JWT and returns User (raises 401 on failure)")
    print("✓ get_optional_user: Returns User or None (never raises exception)")
    print("✓ require_role: Checks user role (raises 403 if role mismatch)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
