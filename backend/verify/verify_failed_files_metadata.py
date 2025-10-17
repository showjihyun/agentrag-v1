"""
Verification script for failed file names in batch metadata.

Tests that failed file names are properly stored in batch metadata
during batch upload processing.
"""

import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.batch_upload_service import BatchUploadService
from backend.db.repositories.batch_upload_repository import BatchUploadRepository
from backend.services.document_service import DocumentService, DocumentServiceError
from backend.db.models.document import BatchUpload, Document


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self._position = 0

    async def read(self, size: int = -1) -> bytes:
        """Read file content."""
        if size == -1:
            result = self.content[self._position :]
            self._position = len(self.content)
        else:
            result = self.content[self._position : self._position + size]
            self._position += len(result)
        return result

    async def seek(self, position: int) -> None:
        """Seek to position."""
        self._position = position


def create_mock_batch_repo():
    """Create mock BatchUploadRepository with metadata tracking."""
    repo = Mock(spec=BatchUploadRepository)

    # Store batches in memory
    batches = {}

    # Mock create_batch
    def mock_create_batch(user_id, total_files, metadata=None):
        batch = Mock(spec=BatchUpload)
        batch.id = uuid4()
        batch.user_id = user_id
        batch.total_files = total_files
        batch.completed_files = 0
        batch.failed_files = 0
        batch.status = "pending"
        batch.extra_metadata = metadata or {}
        batches[batch.id] = batch
        return batch

    repo.create_batch = Mock(side_effect=mock_create_batch)

    # Mock update_batch_progress
    def mock_update_progress(batch_id, completed, failed):
        if batch_id in batches:
            batch = batches[batch_id]
            batch.completed_files = completed
            batch.failed_files = failed

            # Update status
            if completed + failed >= batch.total_files:
                if failed == 0:
                    batch.status = "completed"
                elif completed == 0:
                    batch.status = "failed"
                else:
                    batch.status = "completed"
            else:
                batch.status = "processing"

            return batch
        return None

    repo.update_batch_progress = Mock(side_effect=mock_update_progress)

    # Mock update_batch_status
    def mock_update_status(batch_id, status):
        if batch_id in batches:
            batch = batches[batch_id]
            batch.status = status
            return batch
        return None

    repo.update_batch_status = Mock(side_effect=mock_update_status)

    # Mock update_batch_metadata
    def mock_update_metadata(batch_id, metadata):
        if batch_id in batches:
            batch = batches[batch_id]
            batch.extra_metadata = metadata
            return batch
        return None

    repo.update_batch_metadata = Mock(side_effect=mock_update_metadata)

    # Mock get_batch_by_id
    def mock_get_batch(batch_id, user_id):
        if batch_id in batches:
            batch = batches[batch_id]
            if batch.user_id == user_id:
                return batch
        return None

    repo.get_batch_by_id = Mock(side_effect=mock_get_batch)

    return repo


def create_mock_document_service():
    """Create mock DocumentService that simulates failures."""
    service = Mock(spec=DocumentService)

    # Track which files should fail
    failing_files = ["too_large.txt", "invalid.exe"]

    async def mock_upload(user_id, file):
        """Mock upload that fails for specific files."""
        if file.filename in failing_files:
            if "too_large" in file.filename:
                raise DocumentServiceError("File size exceeds maximum limit of 10MB")
            elif "invalid" in file.filename:
                raise ValueError("Invalid file type: .exe not allowed")

        # Success case
        doc = Mock(spec=Document)
        doc.id = uuid4()
        doc.filename = file.filename
        doc.status = "completed"
        return doc

    service.upload_document = AsyncMock(side_effect=mock_upload)

    return service


async def test_failed_files_metadata():
    """Test that failed file names are stored in batch metadata."""

    print("\n" + "=" * 80)
    print("TESTING: Failed File Names in Batch Metadata")
    print("=" * 80)

    try:
        # Create mock services
        batch_repo = create_mock_batch_repo()
        doc_service = create_mock_document_service()
        batch_service = BatchUploadService(batch_repo, doc_service)

        print("\n✓ Initialized mock services")

        # Create test user ID
        user_id = uuid4()
        print(f"✓ Using test user ID: {user_id}")

        # Create test files - mix of valid and invalid
        files = [
            MockUploadFile("valid_file.txt", b"Valid content", "text/plain"),
            MockUploadFile("too_large.txt", b"x" * 100, "text/plain"),
            MockUploadFile("invalid.exe", b"Invalid", "application/x-msdownload"),
            MockUploadFile("valid_file2.txt", b"More valid content", "text/plain"),
        ]

        print(f"\n✓ Created {len(files)} test files (2 valid, 2 should fail)")

        # Create batch
        batch = await batch_service.create_batch(user_id, files)
        print(f"\n✓ Created batch: {batch.id}")
        print(f"  - Total files: {batch.total_files}")
        print(f"  - Status: {batch.status}")

        # Process batch in background
        print("\n⏳ Processing batch in background...")
        await batch_service.process_batch_background(batch.id, user_id, files)

        # Get final batch status
        final_batch = await batch_service.get_batch_status(batch.id, user_id)

        print(f"\n✓ Batch processing completed")
        print(f"  - Status: {final_batch.status}")
        print(f"  - Completed files: {final_batch.completed_files}")
        print(f"  - Failed files: {final_batch.failed_files}")

        # Check metadata for failed files
        print("\n" + "-" * 80)
        print("CHECKING METADATA FOR FAILED FILES")
        print("-" * 80)

        if final_batch.extra_metadata:
            print(f"\n✓ Metadata exists")

            if "failed_files" in final_batch.extra_metadata:
                failed_files = final_batch.extra_metadata["failed_files"]
                print(f"✓ Found 'failed_files' key in metadata")
                print(f"  - Number of failed files: {len(failed_files)}")

                if len(failed_files) > 0:
                    print("\n  Failed files details:")
                    for i, failed_file in enumerate(failed_files, 1):
                        print(
                            f"\n  {i}. Filename: {failed_file.get('filename', 'N/A')}"
                        )
                        print(f"     Error: {failed_file.get('error', 'N/A')}")
                        print(f"     Timestamp: {failed_file.get('timestamp', 'N/A')}")

                    # Verify expected failures
                    failed_filenames = [f["filename"] for f in failed_files]

                    print("\n" + "-" * 80)
                    print("VERIFICATION RESULTS")
                    print("-" * 80)

                    # Check if expected files failed
                    expected_failures = ["too_large.txt", "invalid.exe"]
                    all_expected_failed = all(
                        filename in failed_filenames for filename in expected_failures
                    )

                    if all_expected_failed:
                        print(
                            "\n✅ SUCCESS: All expected files are in failed_files metadata"
                        )
                        print(f"   Expected: {expected_failures}")
                        print(f"   Found: {failed_filenames}")
                    else:
                        print(
                            "\n❌ FAILURE: Not all expected files are in failed_files metadata"
                        )
                        print(f"   Expected: {expected_failures}")
                        print(f"   Found: {failed_filenames}")
                        return False

                    # Verify each failed file has required fields
                    all_have_required_fields = all(
                        "filename" in f and "error" in f and "timestamp" in f
                        for f in failed_files
                    )

                    if all_have_required_fields:
                        print(
                            "✅ SUCCESS: All failed files have required fields (filename, error, timestamp)"
                        )
                    else:
                        print(
                            "❌ FAILURE: Some failed files are missing required fields"
                        )
                        return False

                    # Verify update_batch_metadata was called
                    if batch_repo.update_batch_metadata.called:
                        print("✅ SUCCESS: update_batch_metadata was called")
                        call_args = batch_repo.update_batch_metadata.call_args
                        print(f"   Called with batch_id: {call_args[0][0]}")
                    else:
                        print("❌ FAILURE: update_batch_metadata was not called")
                        return False

                    print("\n" + "=" * 80)
                    print("✅ ALL TESTS PASSED")
                    print("=" * 80)
                    return True

                else:
                    print(
                        "\n⚠️  WARNING: No failed files in metadata (expected some failures)"
                    )
                    return False
            else:
                print("\n❌ FAILURE: 'failed_files' key not found in metadata")
                print(f"   Available keys: {list(final_batch.extra_metadata.keys())}")
                return False
        else:
            print("\n❌ FAILURE: No metadata found in batch")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("BATCH UPLOAD - FAILED FILES METADATA VERIFICATION")
    print("=" * 80)

    success = asyncio.run(test_failed_files_metadata())

    if success:
        print("\n✅ Verification completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Verification failed")
        sys.exit(1)
