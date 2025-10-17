"""
Verification script for BatchUploadService.

Tests:
1. Batch creation with validation
2. File count validation (≤100)
3. Total size validation (≤100MB)
4. Background processing simulation
5. Progress tracking
6. Failed file handling
7. SSE progress streaming
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from io import BytesIO
from unittest.mock import Mock, AsyncMock, MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.batch_upload_service import (
    BatchUploadService,
    BatchUploadServiceError,
)
from backend.db.repositories.batch_upload_repository import BatchUploadRepository
from backend.services.document_service import DocumentService
from backend.db.models.document import BatchUpload


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(
        self, filename: str, content: bytes, content_type: str = "application/pdf"
    ):
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
    """Create mock BatchUploadRepository."""
    repo = Mock(spec=BatchUploadRepository)

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
        return batch

    repo.create_batch = Mock(side_effect=mock_create_batch)

    # Mock update_batch_progress
    def mock_update_progress(batch_id, completed, failed):
        batch = Mock(spec=BatchUpload)
        batch.id = batch_id
        batch.completed_files = completed
        batch.failed_files = failed
        batch.total_files = 5  # Default for tests

        # Update status based on progress
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

    repo.update_batch_progress = Mock(side_effect=mock_update_progress)

    # Mock update_batch_status
    def mock_update_status(batch_id, status):
        batch = Mock(spec=BatchUpload)
        batch.id = batch_id
        batch.status = status
        return batch

    repo.update_batch_status = Mock(side_effect=mock_update_status)

    # Mock get_batch_by_id
    def mock_get_batch(batch_id, user_id):
        batch = Mock(spec=BatchUpload)
        batch.id = batch_id
        batch.user_id = user_id
        batch.total_files = 5
        batch.completed_files = 3
        batch.failed_files = 1
        batch.status = "processing"
        batch.extra_metadata = {
            "failed_files": [{"filename": "failed.pdf", "error": "Test error"}]
        }
        return batch

    repo.get_batch_by_id = Mock(side_effect=mock_get_batch)

    return repo


def create_mock_document_service():
    """Create mock DocumentService."""
    service = Mock(spec=DocumentService)

    # Mock upload_document
    async def mock_upload(user_id, file):
        # Simulate some files failing
        if "fail" in file.filename.lower():
            raise ValueError(f"Simulated failure for {file.filename}")

        # Return mock document
        doc = Mock()
        doc.id = uuid4()
        doc.filename = file.filename
        doc.status = "completed"
        return doc

    service.upload_document = AsyncMock(side_effect=mock_upload)

    return service


async def test_create_batch_validation():
    """Test batch creation with validation."""
    print("\n" + "=" * 60)
    print("TEST: Batch Creation with Validation")
    print("=" * 60)

    repo = create_mock_batch_repo()
    doc_service = create_mock_document_service()
    service = BatchUploadService(repo, doc_service)

    user_id = uuid4()

    # Test 1: Valid batch
    print("\n1. Creating valid batch (5 files, 5MB total)...")
    files = [
        MockUploadFile(f"file{i}.pdf", b"x" * (1024 * 1024)) for i in range(5)
    ]  # 1MB each

    try:
        batch = await service.create_batch(user_id, files)
        print(f"   ✓ Batch created: {batch.id}")
        print(f"   ✓ Total files: {batch.total_files}")
        print(f"   ✓ Status: {batch.status}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

    # Test 2: Empty file list
    print("\n2. Testing empty file list...")
    try:
        await service.create_batch(user_id, [])
        print("   ✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly rejected: {e}")

    # Test 3: Too many files
    print("\n3. Testing too many files (101 files)...")
    files = [MockUploadFile(f"file{i}.pdf", b"x" * 1024) for i in range(101)]

    try:
        await service.create_batch(user_id, files)
        print("   ✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly rejected: {e}")

    # Test 4: Total size too large
    print("\n4. Testing total size too large (101MB)...")
    files = [
        MockUploadFile(f"file{i}.pdf", b"x" * (21 * 1024 * 1024)) for i in range(5)
    ]  # 21MB each

    try:
        await service.create_batch(user_id, files)
        print("   ✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly rejected: {e}")

    print("\n✓ All validation tests passed!")
    return True


async def test_background_processing():
    """Test background batch processing."""
    print("\n" + "=" * 60)
    print("TEST: Background Batch Processing")
    print("=" * 60)

    repo = create_mock_batch_repo()
    doc_service = create_mock_document_service()
    service = BatchUploadService(repo, doc_service)

    user_id = uuid4()
    batch_id = uuid4()

    # Create files (some will fail)
    files = [
        MockUploadFile("file1.pdf", b"content1"),
        MockUploadFile("file2.pdf", b"content2"),
        MockUploadFile("fail3.pdf", b"content3"),  # Will fail
        MockUploadFile("file4.pdf", b"content4"),
        MockUploadFile("fail5.pdf", b"content5"),  # Will fail
    ]

    print(f"\n1. Processing batch {batch_id} with {len(files)} files...")
    print("   (2 files will fail intentionally)")

    # Process batch
    await service.process_batch_background(batch_id, user_id, files)

    # Verify calls
    print("\n2. Verifying processing results...")

    # Check that update_batch_status was called
    if repo.update_batch_status.called:
        print(f"   ✓ Batch status updated {repo.update_batch_status.call_count} times")
    else:
        print("   ✗ Batch status not updated")
        return False

    # Check that update_batch_progress was called for each file
    if repo.update_batch_progress.call_count == len(files):
        print(f"   ✓ Progress updated {repo.update_batch_progress.call_count} times")
    else:
        print(
            f"   ✗ Progress updated {repo.update_batch_progress.call_count} times, expected {len(files)}"
        )
        return False

    # Check that upload_document was called for each file
    if doc_service.upload_document.call_count == len(files):
        print(
            f"   ✓ Document upload attempted {doc_service.upload_document.call_count} times"
        )
    else:
        print(
            f"   ✗ Document upload attempted {doc_service.upload_document.call_count} times, expected {len(files)}"
        )
        return False

    # Verify final progress update (3 completed, 2 failed)
    last_progress_call = repo.update_batch_progress.call_args_list[-1]
    completed = last_progress_call[1]["completed"]
    failed = last_progress_call[1]["failed"]

    print(f"\n3. Final results:")
    print(f"   ✓ Completed: {completed}")
    print(f"   ✓ Failed: {failed}")

    if completed == 3 and failed == 2:
        print("   ✓ Correct counts!")
    else:
        print(f"   ✗ Expected 3 completed, 2 failed")
        return False

    print("\n✓ Background processing test passed!")
    return True


async def test_get_batch_status():
    """Test getting batch status."""
    print("\n" + "=" * 60)
    print("TEST: Get Batch Status")
    print("=" * 60)

    repo = create_mock_batch_repo()
    doc_service = create_mock_document_service()
    service = BatchUploadService(repo, doc_service)

    user_id = uuid4()
    batch_id = uuid4()

    print(f"\n1. Getting status for batch {batch_id}...")

    batch = await service.get_batch_status(batch_id, user_id)

    if batch:
        print(f"   ✓ Batch found: {batch.id}")
        print(f"   ✓ Status: {batch.status}")
        print(
            f"   ✓ Progress: {batch.completed_files + batch.failed_files}/{batch.total_files}"
        )
        print(f"   ✓ Completed: {batch.completed_files}")
        print(f"   ✓ Failed: {batch.failed_files}")
    else:
        print("   ✗ Batch not found")
        return False

    # Verify repository was called
    if repo.get_batch_by_id.called:
        print("   ✓ Repository method called")
    else:
        print("   ✗ Repository method not called")
        return False

    print("\n✓ Get batch status test passed!")
    return True


async def test_stream_progress():
    """Test SSE progress streaming."""
    print("\n" + "=" * 60)
    print("TEST: SSE Progress Streaming")
    print("=" * 60)

    repo = create_mock_batch_repo()
    doc_service = create_mock_document_service()
    service = BatchUploadService(repo, doc_service)

    user_id = uuid4()
    batch_id = uuid4()

    # Mock get_batch_by_id to simulate progress
    call_count = [0]

    def mock_get_batch_progressive(batch_id, user_id):
        call_count[0] += 1
        batch = Mock(spec=BatchUpload)
        batch.id = batch_id
        batch.user_id = user_id
        batch.total_files = 5

        # Simulate progress over multiple calls
        if call_count[0] == 1:
            batch.completed_files = 0
            batch.failed_files = 0
            batch.status = "pending"
        elif call_count[0] == 2:
            batch.completed_files = 2
            batch.failed_files = 0
            batch.status = "processing"
        elif call_count[0] == 3:
            batch.completed_files = 4
            batch.failed_files = 1
            batch.status = "processing"
        else:
            batch.completed_files = 4
            batch.failed_files = 1
            batch.status = "completed"

        batch.extra_metadata = {
            "failed_files": (
                [{"filename": "failed.pdf", "error": "Test error"}]
                if batch.failed_files > 0
                else []
            )
        }

        return batch

    repo.get_batch_by_id = Mock(side_effect=mock_get_batch_progressive)

    print(f"\n1. Streaming progress for batch {batch_id}...")

    updates = []
    try:
        async for update in service.stream_batch_progress(batch_id, user_id):
            updates.append(update)
            print(f"\n   Update {len(updates)}:")
            print(f"   - Status: {update['status']}")
            print(
                f"   - Progress: {update['completed_files'] + update['failed_files']}/{update['total_files']}"
            )
            print(f"   - Completed: {update['completed_files']}")
            print(f"   - Failed: {update['failed_files']}")
            print(f"   - Progress %: {update['progress_percent']}%")

            # Break after a few updates to avoid infinite loop
            if len(updates) >= 3:
                break
    except Exception as e:
        print(f"   ✗ Streaming failed: {e}")
        return False

    print(f"\n2. Received {len(updates)} progress updates")

    if len(updates) >= 3:
        print("   ✓ Multiple updates received")
    else:
        print("   ✗ Expected at least 3 updates")
        return False

    # Verify update structure
    print("\n3. Verifying update structure...")
    for i, update in enumerate(updates):
        required_fields = [
            "batch_id",
            "status",
            "total_files",
            "completed_files",
            "failed_files",
            "progress_percent",
            "failed_file_names",
            "timestamp",
        ]

        missing = [f for f in required_fields if f not in update]
        if missing:
            print(f"   ✗ Update {i+1} missing fields: {missing}")
            return False

    print("   ✓ All updates have required fields")

    print("\n✓ SSE progress streaming test passed!")
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BATCH UPLOAD SERVICE VERIFICATION")
    print("=" * 60)

    tests = [
        ("Batch Creation Validation", test_create_batch_validation),
        ("Background Processing", test_background_processing),
        ("Get Batch Status", test_get_batch_status),
        ("SSE Progress Streaming", test_stream_progress),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
