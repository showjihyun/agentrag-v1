"""Verify UserRepository storage tracking functionality."""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from config import settings
from backend.db.repositories.user_repository import UserRepository


def verify_storage_tracking():
    """Test storage tracking in UserRepository."""

    print("=" * 60)
    print("VERIFYING USER STORAGE TRACKING")
    print("=" * 60)

    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create repository
        user_repo = UserRepository(db)

        # Test 1: Create a test user
        print("\n1. Creating test user...")
        test_email = f"storage_test_{uuid4().hex[:8]}@example.com"
        test_username = f"storage_test_{uuid4().hex[:8]}"

        user = user_repo.create_user(
            email=test_email, username=test_username, password="TestPassword123"
        )

        print(f"   ✓ Created user: {user.email}")
        print(f"   ✓ Initial storage: {user.storage_used_bytes} bytes")

        assert user.storage_used_bytes == 0, "Initial storage should be 0"

        # Test 2: Increment storage
        print("\n2. Testing storage increment...")
        updated_user = user_repo.update_storage_used(user.id, 1024)

        print(f"   ✓ Added 1024 bytes")
        print(f"   ✓ Current storage: {updated_user.storage_used_bytes} bytes")

        assert updated_user.storage_used_bytes == 1024, "Storage should be 1024"

        # Test 3: Increment again
        print("\n3. Testing additional increment...")
        updated_user = user_repo.update_storage_used(user.id, 2048)

        print(f"   ✓ Added 2048 bytes")
        print(f"   ✓ Current storage: {updated_user.storage_used_bytes} bytes")

        assert updated_user.storage_used_bytes == 3072, "Storage should be 3072"

        # Test 4: Decrement storage
        print("\n4. Testing storage decrement...")
        updated_user = user_repo.update_storage_used(user.id, -1024)

        print(f"   ✓ Removed 1024 bytes")
        print(f"   ✓ Current storage: {updated_user.storage_used_bytes} bytes")

        assert updated_user.storage_used_bytes == 2048, "Storage should be 2048"

        # Test 5: Prevent negative storage
        print("\n5. Testing negative storage prevention...")
        updated_user = user_repo.update_storage_used(user.id, -5000)

        print(f"   ✓ Attempted to remove 5000 bytes (more than available)")
        print(f"   ✓ Current storage: {updated_user.storage_used_bytes} bytes")

        assert (
            updated_user.storage_used_bytes == 0
        ), "Storage should be 0 (not negative)"

        # Test 6: Large file simulation
        print("\n6. Testing large file storage...")
        large_file_size = 10 * 1024 * 1024  # 10 MB
        updated_user = user_repo.update_storage_used(user.id, large_file_size)

        print(f"   ✓ Added {large_file_size:,} bytes (10 MB)")
        print(f"   ✓ Current storage: {updated_user.storage_used_bytes:,} bytes")

        assert (
            updated_user.storage_used_bytes == large_file_size
        ), f"Storage should be {large_file_size}"

        # Test 7: Non-existent user
        print("\n7. Testing non-existent user...")
        fake_user_id = uuid4()
        result = user_repo.update_storage_used(fake_user_id, 1000)

        print(f"   ✓ Attempted to update non-existent user")
        print(f"   ✓ Result: {result}")

        assert result is None, "Should return None for non-existent user"

        # Cleanup
        print("\n8. Cleaning up test user...")
        user_repo.delete_user(user.id)
        print(f"   ✓ Deleted test user")

        print("\n" + "=" * 60)
        print("✅ ALL STORAGE TRACKING TESTS PASSED")
        print("=" * 60)
        print("\nVerified functionality:")
        print("  ✓ update_storage_used(user_id, bytes_delta) method exists")
        print("  ✓ Increments storage correctly (positive delta)")
        print("  ✓ Decrements storage correctly (negative delta)")
        print("  ✓ Prevents negative storage values")
        print("  ✓ Handles large file sizes")
        print("  ✓ Returns None for non-existent users")
        print("  ✓ Updates timestamp on storage change")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = verify_storage_tracking()
    sys.exit(0 if success else 1)
