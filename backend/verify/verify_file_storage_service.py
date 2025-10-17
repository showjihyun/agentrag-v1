"""
Verification script for FileStorageService.

Tests all methods and validates functionality.
"""

import asyncio
import io
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.file_storage_service import FileStorageService, FileStorageError


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content = content
        self.position = 0

    async def read(self, size: int = -1) -> bytes:
        """Read file content."""
        if size == -1:
            data = self.content[self.position :]
            self.position = len(self.content)
        else:
            data = self.content[self.position : self.position + size]
            self.position += len(data)
        return data


async def test_file_storage_service():
    """Test FileStorageService functionality."""

    print("=" * 70)
    print("FILE STORAGE SERVICE VERIFICATION")
    print("=" * 70)

    # Use test directory
    test_base_path = "./test_uploads"
    service = FileStorageService(base_path=test_base_path)

    test_user_id = uuid4()
    print(f"\n✓ FileStorageService initialized")
    print(f"  Base path: {test_base_path}")
    print(f"  Test user ID: {test_user_id}")

    # Test 1: Sanitize filename
    print("\n" + "-" * 70)
    print("TEST 1: Filename Sanitization")
    print("-" * 70)

    test_filenames = [
        ("normal_file.pdf", "normal_file.pdf"),
        ("file with spaces.txt", "file_with_spaces.txt"),
        (
            "../../../etc/passwd",
            "passwd",
        ),  # Path traversal prevented, only basename kept
        ("file@#$%^&*.docx", "file.docx"),
        ("very___long___underscores.pdf", "very_long_underscores.pdf"),
        ("file.PDF", "file.pdf"),
        ("", ValueError),
    ]

    for original, expected in test_filenames:
        try:
            sanitized = service.sanitize_filename(original)
            if isinstance(expected, type) and issubclass(expected, Exception):
                print(f"✗ FAILED: Expected exception for '{original}'")
            else:
                if sanitized == expected:
                    print(f"✓ '{original}' -> '{sanitized}'")
                else:
                    print(
                        f"✗ FAILED: '{original}' -> '{sanitized}' (expected: '{expected}')"
                    )
        except Exception as e:
            if isinstance(expected, type) and isinstance(e, expected):
                print(f"✓ Correctly raised {type(e).__name__} for '{original}'")
            else:
                print(f"✗ FAILED: Unexpected exception for '{original}': {e}")

    # Test 2: File type validation
    print("\n" + "-" * 70)
    print("TEST 2: File Type Validation")
    print("-" * 70)

    valid_files = ["document.pdf", "text.txt", "doc.docx", "readme.md"]
    invalid_files = ["script.exe", "image.jpg", "archive.zip"]

    for filename in valid_files:
        if service.validate_file_type(filename):
            print(f"✓ Valid: {filename}")
        else:
            print(f"✗ FAILED: {filename} should be valid")

    for filename in invalid_files:
        if not service.validate_file_type(filename):
            print(f"✓ Invalid (as expected): {filename}")
        else:
            print(f"✗ FAILED: {filename} should be invalid")

    # Test 3: File size validation
    print("\n" + "-" * 70)
    print("TEST 3: File Size Validation")
    print("-" * 70)

    max_size = 10 * 1024 * 1024  # 10MB

    test_sizes = [
        (1024, True),  # 1KB - valid
        (5 * 1024 * 1024, True),  # 5MB - valid
        (10 * 1024 * 1024, True),  # 10MB - valid (at limit)
        (11 * 1024 * 1024, False),  # 11MB - invalid
        (0, False),  # 0 bytes - invalid
        (-1, False),  # negative - invalid
    ]

    for size, expected_valid in test_sizes:
        is_valid = service.validate_file_size(size, max_size)
        size_mb = size / 1024 / 1024 if size > 0 else size
        if is_valid == expected_valid:
            status = "valid" if is_valid else "invalid"
            print(f"✓ {size_mb:.2f} MB: {status}")
        else:
            print(f"✗ FAILED: {size_mb:.2f} MB validation incorrect")

    # Test 4: User directory creation
    print("\n" + "-" * 70)
    print("TEST 4: User Directory Creation")
    print("-" * 70)

    user_dir = service.ensure_user_directory(test_user_id)
    if Path(user_dir).exists():
        print(f"✓ User directory created: {user_dir}")
    else:
        print(f"✗ FAILED: User directory not created")

    # Test 5: File path generation
    print("\n" + "-" * 70)
    print("TEST 5: File Path Generation")
    print("-" * 70)

    filename = "test_document.pdf"
    file_path = service.get_file_path(test_user_id, filename)
    expected_path = str(Path(test_base_path) / str(test_user_id) / filename)

    if file_path == expected_path:
        print(f"✓ File path correct: {file_path}")
    else:
        print(f"✗ FAILED: Expected {expected_path}, got {file_path}")

    # Test 6: Save file
    print("\n" + "-" * 70)
    print("TEST 6: Save File")
    print("-" * 70)

    test_content = b"This is a test PDF file content. " * 100
    mock_file = MockUploadFile("test_document.pdf", test_content)

    try:
        saved_path, saved_size = await service.save_file(mock_file, test_user_id)

        if Path(saved_path).exists():
            print(f"✓ File saved: {saved_path}")
            print(f"  Size: {saved_size} bytes ({saved_size / 1024:.2f} KB)")

            # Verify content
            with open(saved_path, "rb") as f:
                saved_content = f.read()

            if saved_content == test_content:
                print(f"✓ File content verified")
            else:
                print(f"✗ FAILED: File content mismatch")
        else:
            print(f"✗ FAILED: File not found after save")
    except Exception as e:
        print(f"✗ FAILED: Save file error: {e}")

    # Test 7: Save file with invalid type
    print("\n" + "-" * 70)
    print("TEST 7: Save File with Invalid Type")
    print("-" * 70)

    invalid_file = MockUploadFile("malware.exe", b"malicious content")

    try:
        await service.save_file(invalid_file, test_user_id)
        print(f"✗ FAILED: Should have rejected invalid file type")
    except ValueError as e:
        print(f"✓ Correctly rejected invalid file type: {e}")
    except Exception as e:
        print(f"✗ FAILED: Unexpected exception: {e}")

    # Test 8: Get file size
    print("\n" + "-" * 70)
    print("TEST 8: Get File Size")
    print("-" * 70)

    if Path(saved_path).exists():
        file_size = service.get_file_size(saved_path)
        if file_size == saved_size:
            print(f"✓ File size retrieved: {file_size} bytes")
        else:
            print(f"✗ FAILED: Size mismatch (expected {saved_size}, got {file_size})")

    # Test 9: Get user storage used
    print("\n" + "-" * 70)
    print("TEST 9: Get User Storage Used")
    print("-" * 70)

    storage_used = service.get_user_storage_used(test_user_id)
    print(f"✓ User storage: {storage_used} bytes ({storage_used / 1024:.2f} KB)")

    # Test 10: Delete file
    print("\n" + "-" * 70)
    print("TEST 10: Delete File")
    print("-" * 70)

    if service.delete_file(saved_path):
        if not Path(saved_path).exists():
            print(f"✓ File deleted successfully")
        else:
            print(f"✗ FAILED: File still exists after delete")
    else:
        print(f"✗ FAILED: Delete operation returned False")

    # Test 11: Cleanup user files
    print("\n" + "-" * 70)
    print("TEST 11: Cleanup User Files")
    print("-" * 70)

    # Create a few test files
    for i in range(3):
        mock_file = MockUploadFile(f"test_file_{i}.txt", b"test content")
        await service.save_file(mock_file, test_user_id)

    if service.cleanup_user_files(test_user_id):
        user_dir_path = Path(test_base_path) / str(test_user_id)
        if not user_dir_path.exists():
            print(f"✓ User files cleaned up successfully")
        else:
            print(f"✗ FAILED: User directory still exists")
    else:
        print(f"✗ FAILED: Cleanup operation returned False")

    # Cleanup test directory
    print("\n" + "-" * 70)
    print("CLEANUP")
    print("-" * 70)

    import shutil

    if Path(test_base_path).exists():
        shutil.rmtree(test_base_path)
        print(f"✓ Test directory removed: {test_base_path}")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_file_storage_service())
