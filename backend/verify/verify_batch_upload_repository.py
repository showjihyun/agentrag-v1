"""Verification script for BatchUploadRepository."""

import sys
from uuid import uuid4
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.db.repositories import BatchUploadRepository, UserRepository


def verify_batch_upload_repository():
    """Verify BatchUploadRepository functionality."""

    print("=" * 60)
    print("BATCH UPLOAD REPOSITORY VERIFICATION")
    print("=" * 60)

    db: Session = SessionLocal()

    try:
        # Initialize repositories
        batch_repo = BatchUploadRepository(db)
        user_repo = UserRepository(db)

        # Create test user
        print("\n1. Creating test user...")
        test_email = f"batch_test_{uuid4().hex[:8]}@example.com"
        test_user = user_repo.create_user(
            email=test_email,
            username=f"batch_user_{uuid4().hex[:8]}",
            password="TestPassword123",
        )
        print(f"   ✓ Created user: {test_user.id}")

        # Test 1: Create batch
        print("\n2. Testing create_batch...")
        batch = batch_repo.create_batch(
            user_id=test_user.id,
            total_files=5,
            metadata={"source": "test", "description": "Test batch upload"},
        )
        assert batch is not None
        assert batch.user_id == test_user.id
        assert batch.total_files == 5
        assert batch.completed_files == 0
        assert batch.failed_files == 0
        assert batch.status == "pending"
        assert batch.extra_metadata.get("source") == "test"
        print(f"   ✓ Created batch: {batch.id}")
        print(f"     - Total files: {batch.total_files}")
        print(f"     - Status: {batch.status}")
        print(f"     - Metadata: {batch.extra_metadata}")

        # Test 2: Get batch by ID
        print("\n3. Testing get_batch_by_id...")
        retrieved_batch = batch_repo.get_batch_by_id(batch.id, test_user.id)
        assert retrieved_batch is not None
        assert retrieved_batch.id == batch.id
        print(f"   ✓ Retrieved batch: {retrieved_batch.id}")

        # Test 3: Update batch progress (first file)
        print("\n4. Testing update_batch_progress (first file)...")
        updated_batch = batch_repo.update_batch_progress(
            batch_id=batch.id, completed=1, failed=0
        )
        assert updated_batch is not None
        assert updated_batch.completed_files == 1
        assert updated_batch.failed_files == 0
        assert updated_batch.status == "processing"
        assert updated_batch.started_at is not None
        print(
            f"   ✓ Updated progress: {updated_batch.completed_files}/{updated_batch.total_files}"
        )
        print(f"     - Status: {updated_batch.status}")
        print(f"     - Started at: {updated_batch.started_at}")

        # Test 4: Update batch progress (more files)
        print("\n5. Testing update_batch_progress (more files)...")
        updated_batch = batch_repo.update_batch_progress(
            batch_id=batch.id, completed=3, failed=1
        )
        assert updated_batch is not None
        assert updated_batch.completed_files == 3
        assert updated_batch.failed_files == 1
        assert updated_batch.status == "processing"
        print(
            f"   ✓ Updated progress: {updated_batch.completed_files}/{updated_batch.total_files}"
        )
        print(f"     - Failed: {updated_batch.failed_files}")

        # Test 5: Update batch progress (complete)
        print("\n6. Testing update_batch_progress (complete)...")
        updated_batch = batch_repo.update_batch_progress(
            batch_id=batch.id, completed=4, failed=1
        )
        assert updated_batch is not None
        assert updated_batch.completed_files == 4
        assert updated_batch.failed_files == 1
        assert updated_batch.status == "completed"
        assert updated_batch.completed_at is not None
        print(
            f"   ✓ Batch completed: {updated_batch.completed_files}/{updated_batch.total_files}"
        )
        print(f"     - Status: {updated_batch.status}")
        print(f"     - Completed at: {updated_batch.completed_at}")

        # Test 6: Create another batch
        print("\n7. Testing create_batch (second batch)...")
        batch2 = batch_repo.create_batch(
            user_id=test_user.id, total_files=3, metadata={"source": "test2"}
        )
        assert batch2 is not None
        print(f"   ✓ Created second batch: {batch2.id}")

        # Test 7: Get user batches
        print("\n8. Testing get_user_batches...")
        user_batches = batch_repo.get_user_batches(
            user_id=test_user.id, limit=10, offset=0
        )
        assert len(user_batches) == 2
        assert user_batches[0].id == batch2.id  # Most recent first
        assert user_batches[1].id == batch.id
        print(f"   ✓ Retrieved {len(user_batches)} batches for user")
        for i, b in enumerate(user_batches, 1):
            print(
                f"     {i}. Batch {b.id}: {b.completed_files}/{b.total_files} - {b.status}"
            )

        # Test 8: Update batch status
        print("\n9. Testing update_batch_status...")
        updated_batch = batch_repo.update_batch_status(
            batch_id=batch2.id, status="failed"
        )
        assert updated_batch is not None
        assert updated_batch.status == "failed"
        assert updated_batch.completed_at is not None
        print(f"   ✓ Updated batch status to: {updated_batch.status}")

        # Test 9: Ownership verification
        print("\n10. Testing ownership verification...")
        other_user_id = uuid4()
        not_found = batch_repo.get_batch_by_id(batch.id, other_user_id)
        assert not_found is None
        print(f"   ✓ Ownership verification works (returns None for wrong user)")

        # Test 10: Pagination
        print("\n11. Testing pagination...")
        page1 = batch_repo.get_user_batches(test_user.id, limit=1, offset=0)
        page2 = batch_repo.get_user_batches(test_user.id, limit=1, offset=1)
        assert len(page1) == 1
        assert len(page2) == 1
        assert page1[0].id != page2[0].id
        print(f"   ✓ Pagination works")
        print(f"     - Page 1: {page1[0].id}")
        print(f"     - Page 2: {page2[0].id}")

        # Cleanup
        print("\n12. Cleaning up test data...")
        user_repo.delete_user(test_user.id)
        db.commit()
        print("   ✓ Cleaned up test data")

        print("\n" + "=" * 60)
        print("✅ ALL BATCH UPLOAD REPOSITORY TESTS PASSED")
        print("=" * 60)

        return True

    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = verify_batch_upload_repository()
    sys.exit(0 if success else 1)
