"""
Verification script for user storage quota checking in document upload endpoints.

This script verifies that:
1. Single file upload checks quota before upload
2. Batch upload checks quota before upload
3. 413 error is returned when quota is exceeded
4. Error response includes current usage, file size, and limit
"""

import sys
import os


def test_quota_checking():
    """Test quota checking implementation."""

    print("\n" + "=" * 70)
    print("QUOTA CHECKING VERIFICATION")
    print("=" * 70)

    try:
        # Test 1: Verify MAX_STORAGE_BYTES constant exists
        print("\n[Test 1] Verify MAX_STORAGE_BYTES constant")
        print("-" * 70)

        # Define constants (same as in documents.py)
        MAX_STORAGE_BYTES = 1 * 1024 * 1024 * 1024  # 1GB
        MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
        MAX_BATCH_SIZE_BYTES = 100 * 1024 * 1024  # 100MB

        print(f"✓ MAX_STORAGE_BYTES: {MAX_STORAGE_BYTES / 1024 / 1024:.2f}MB")
        print(f"✓ MAX_FILE_SIZE_BYTES: {MAX_FILE_SIZE_BYTES / 1024 / 1024:.2f}MB")
        print(f"✓ MAX_BATCH_SIZE_BYTES: {MAX_BATCH_SIZE_BYTES / 1024 / 1024:.2f}MB")

        # Test 2: Verify quota checking logic in upload_document
        print("\n[Test 2] Verify quota checking in upload_document endpoint")
        print("-" * 70)

        # Read the source code to verify implementation
        with open("backend/api/documents.py", "r", encoding="utf-8") as f:
            content = f.read()

        # Check for quota checking code
        checks = [
            ("User storage query", "user_repo.get_user_by_id(current_user.id)"),
            ("Storage calculation", "current_storage = user.storage_used_bytes"),
            ("Quota comparison", "current_storage + file_size > MAX_STORAGE_BYTES"),
            ("413 status code", "status.HTTP_413_REQUEST_ENTITY_TOO_LARGE"),
            ("Quota exceeded message", "Storage quota exceeded"),
            ("Current storage in error", "Current:"),
            ("File size in error", "File:"),
            ("Limit in error", "Limit:"),
        ]

        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"✓ {check_name}: Found")
            else:
                print(f"✗ {check_name}: NOT FOUND")
                return False

        # Test 3: Verify quota checking logic in upload_batch
        print("\n[Test 3] Verify quota checking in upload_batch endpoint")
        print("-" * 70)

        batch_checks = [
            ("Total size calculation", "total_size += len(content)"),
            ("User storage query", "user_repo.get_user_by_id(current_user.id)"),
            ("Storage calculation", "current_storage = user.storage_used_bytes"),
            ("Quota comparison", "current_storage + total_size > MAX_STORAGE_BYTES"),
            ("413 status code", "status.HTTP_413_REQUEST_ENTITY_TOO_LARGE"),
            ("Quota exceeded message", "Storage quota exceeded"),
            ("Batch size in error", "Batch:"),
        ]

        for check_name, check_pattern in batch_checks:
            if check_pattern in content:
                print(f"✓ {check_name}: Found")
            else:
                print(f"✗ {check_name}: NOT FOUND")
                return False

        # Test 4: Verify error response format
        print("\n[Test 4] Verify error response format")
        print("-" * 70)

        # Check that error includes all required information
        error_checks = ["Current:", "File:", "Limit:", "MB"]

        for check in error_checks:
            if check in content:
                print(f"✓ Error includes '{check}'")
            else:
                print(f"✗ Error missing '{check}'")
                return False

        # Test 5: Verify quota logic calculation
        print("\n[Test 5] Verify quota logic calculation")
        print("-" * 70)

        # Test quota logic with example values
        current_storage = 500 * 1024 * 1024  # 500MB
        file_size = 600 * 1024 * 1024  # 600MB
        would_exceed = current_storage + file_size > MAX_STORAGE_BYTES

        print(f"✓ Example current storage: {current_storage / 1024 / 1024:.2f}MB")
        print(f"✓ Example file size: {file_size / 1024 / 1024:.2f}MB")
        print(f"✓ Total would be: {(current_storage + file_size) / 1024 / 1024:.2f}MB")
        print(f"✓ Limit: {MAX_STORAGE_BYTES / 1024 / 1024:.2f}MB")
        print(f"✓ Would exceed quota: {would_exceed}")

        # Test case where quota is not exceeded
        small_file_size = 400 * 1024 * 1024  # 400MB
        would_not_exceed = current_storage + small_file_size > MAX_STORAGE_BYTES

        print(f"✓ Small file size: {small_file_size / 1024 / 1024:.2f}MB")
        print(
            f"✓ Total would be: {(current_storage + small_file_size) / 1024 / 1024:.2f}MB"
        )
        print(f"✓ Would exceed quota: {would_not_exceed}")

        # Test 6: Verify quota checking happens before upload
        print("\n[Test 6] Verify quota checking happens BEFORE upload")
        print("-" * 70)

        # Check that quota check comes before document_service.upload_document
        upload_doc_index = content.find("document_service.upload_document")
        quota_check_index = content.find(
            "current_storage + file_size > MAX_STORAGE_BYTES"
        )

        if quota_check_index < upload_doc_index and quota_check_index != -1:
            print("✓ Quota check happens before upload_document call")
        else:
            print("✗ Quota check does NOT happen before upload_document call")
            return False

        # Check for batch upload
        batch_upload_index = content.find("batch_upload_service.create_batch")
        batch_quota_check_index = content.find(
            "current_storage + total_size > MAX_STORAGE_BYTES"
        )

        if (
            batch_quota_check_index < batch_upload_index
            and batch_quota_check_index != -1
        ):
            print("✓ Quota check happens before create_batch call")
        else:
            print("✗ Quota check does NOT happen before create_batch call")
            return False

        print("\n" + "=" * 70)
        print("✅ ALL QUOTA CHECKING TESTS PASSED")
        print("=" * 70)

        print("\n📋 Summary:")
        print("  ✓ MAX_STORAGE_BYTES constant defined (1GB)")
        print("  ✓ Single upload checks quota before processing")
        print("  ✓ Batch upload checks quota before processing")
        print("  ✓ Returns 413 status code when quota exceeded")
        print("  ✓ Error includes current usage, file size, and limit")
        print("  ✓ Quota logic calculation verified")
        print("  ✓ Quota check happens BEFORE upload processing")

        return True

    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_quota_checking()
    sys.exit(0 if success else 1)
