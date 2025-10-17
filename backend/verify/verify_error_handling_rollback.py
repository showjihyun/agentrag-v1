"""
Verification script for DocumentService error handling and rollback.

Tests:
1. File validation errors trigger proper cleanup
2. Database errors trigger file cleanup
3. Processing errors trigger full rollback
4. Milvus errors trigger full rollback
5. Partial failures are properly logged
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from io import BytesIO

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.document_service import DocumentService, DocumentServiceError
from backend.services.file_storage_service import FileStorageService, FileStorageError
from backend.services.document_processor import (
    DocumentProcessor,
    DocumentProcessingError,
)
from backend.db.repositories.document_repository import DocumentRepository
from backend.db.repositories.user_repository import UserRepository
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.db.models.document import Document


class MockUploadFile:
    """Mock UploadFile for testing."""

    def __init__(self, filename: str, content: bytes = b"test content"):
        self.filename = filename
        self.content = content
        self.file = BytesIO(content)

    async def read(self) -> bytes:
        return self.content

    async def seek(self, position: int) -> None:
        self.file.seek(position)


def create_mock_document(document_id, user_id, filename="test.pdf"):
    """Create a mock document."""
    doc = Mock(spec=Document)
    doc.id = document_id
    doc.user_id = user_id
    doc.filename = filename
    doc.file_path = f"uploads/{user_id}/{filename}"
    doc.file_size_bytes = 1024
    doc.mime_type = "application/pdf"
    doc.status = "pending"
    doc.chunk_count = 0
    doc.collection = None
    doc.error_message = None
    return doc


async def test_file_validation_error():
    """Test that file validation errors don't leave orphaned data."""
    print("\n=== Test 1: File Validation Error ===")

    # Setup mocks
    doc_repo = Mock(spec=DocumentRepository)
    user_repo = Mock(spec=UserRepository)
    file_storage = Mock(spec=FileStorageService)
    doc_processor = Mock(spec=DocumentProcessor)
    embedding_service = Mock(spec=EmbeddingService)
    milvus_manager = Mock(spec=MilvusManager)

    # Configure file_storage to reject file type
    file_storage.validate_file_type.return_value = False
    file_storage.ALLOWED_EXTENSIONS = {".pdf": "application/pdf", ".txt": "text/plain"}

    # Create service
    service = DocumentService(
        document_repository=doc_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )

    # Test upload with invalid file type
    user_id = uuid4()
    file = MockUploadFile("test.exe")

    try:
        await service.upload_document(user_id, file)
        print("❌ FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"✅ PASSED: Raised ValueError: {e}")

        # Verify no file was saved
        file_storage.save_file.assert_not_called()
        print("✅ PASSED: No file was saved")

        # Verify no document record was created
        doc_repo.create_document.assert_not_called()
        print("✅ PASSED: No document record was created")

        return True


async def test_file_storage_error():
    """Test that file storage errors trigger proper cleanup."""
    print("\n=== Test 2: File Storage Error ===")

    # Setup mocks
    doc_repo = Mock(spec=DocumentRepository)
    user_repo = Mock(spec=UserRepository)
    file_storage = Mock(spec=FileStorageService)
    doc_processor = Mock(spec=DocumentProcessor)
    embedding_service = Mock(spec=EmbeddingService)
    milvus_manager = Mock(spec=MilvusManager)

    # Configure file_storage to accept file type but fail on save
    file_storage.validate_file_type.return_value = True
    file_storage.ALLOWED_EXTENSIONS = {".pdf": "application/pdf"}
    file_storage.save_file = AsyncMock(side_effect=FileStorageError("Disk full"))

    # Create service
    service = DocumentService(
        document_repository=doc_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )

    # Test upload with storage error
    user_id = uuid4()
    file = MockUploadFile("test.pdf")

    try:
        await service.upload_document(user_id, file)
        print("❌ FAILED: Should have raised DocumentServiceError")
        return False
    except DocumentServiceError as e:
        print(f"✅ PASSED: Raised DocumentServiceError: {e}")

        # Verify no document record was created
        doc_repo.create_document.assert_not_called()
        print("✅ PASSED: No document record was created")

        return True


async def test_database_error():
    """Test that database errors trigger file cleanup."""
    print("\n=== Test 3: Database Error ===")

    # Setup mocks
    doc_repo = Mock(spec=DocumentRepository)
    user_repo = Mock(spec=UserRepository)
    file_storage = Mock(spec=FileStorageService)
    doc_processor = Mock(spec=DocumentProcessor)
    embedding_service = Mock(spec=EmbeddingService)
    milvus_manager = Mock(spec=MilvusManager)

    # Configure file_storage to succeed
    file_storage.validate_file_type.return_value = True
    file_storage.ALLOWED_EXTENSIONS = {".pdf": "application/pdf"}
    file_storage.save_file = AsyncMock(return_value=("uploads/test.pdf", 1024))
    file_storage.validate_file_size.return_value = True
    file_storage.delete_file = Mock()

    # Configure doc_repo to fail on create
    doc_repo.create_document.side_effect = Exception("Database connection failed")

    # Create service
    service = DocumentService(
        document_repository=doc_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )

    # Test upload with database error
    user_id = uuid4()
    file = MockUploadFile("test.pdf")

    try:
        await service.upload_document(user_id, file)
        print("❌ FAILED: Should have raised DocumentServiceError")
        return False
    except DocumentServiceError as e:
        print(f"✅ PASSED: Raised DocumentServiceError: {e}")

        # Verify file was cleaned up
        file_storage.delete_file.assert_called_once_with("uploads/test.pdf")
        print("✅ PASSED: File was cleaned up")

        return True


async def test_processing_error():
    """Test that processing errors trigger full rollback."""
    print("\n=== Test 4: Processing Error ===")

    # Setup mocks
    doc_repo = Mock(spec=DocumentRepository)
    user_repo = Mock(spec=UserRepository)
    file_storage = Mock(spec=FileStorageService)
    doc_processor = Mock(spec=DocumentProcessor)
    embedding_service = Mock(spec=EmbeddingService)
    milvus_manager = Mock(spec=MilvusManager)

    user_id = uuid4()
    document_id = uuid4()

    # Configure file_storage to succeed
    file_storage.validate_file_type.return_value = True
    file_storage.ALLOWED_EXTENSIONS = {".pdf": "application/pdf"}
    file_storage.save_file = AsyncMock(return_value=("uploads/test.pdf", 1024))
    file_storage.validate_file_size.return_value = True
    file_storage.delete_file = Mock()

    # Configure doc_repo to succeed on create
    mock_doc = create_mock_document(document_id, user_id)
    doc_repo.create_document.return_value = mock_doc
    doc_repo.update_document_status = Mock()
    doc_repo.delete_document = Mock()

    # Configure doc_processor to fail
    doc_processor.detect_file_type.return_value = "pdf"
    doc_processor.extract_text.side_effect = DocumentProcessingError("Corrupted PDF")

    # Create service
    service = DocumentService(
        document_repository=doc_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )

    # Mock file reading
    with patch("builtins.open", MagicMock()):
        try:
            await service.upload_document(user_id, MockUploadFile("test.pdf"))
            print("❌ FAILED: Should have raised DocumentServiceError")
            return False
        except DocumentServiceError as e:
            print(f"✅ PASSED: Raised DocumentServiceError: {e}")

            # Verify status was updated to failed
            doc_repo.update_document_status.assert_any_call(
                document_id, "failed", error_message="Corrupted PDF"
            )
            print("✅ PASSED: Document status updated to failed")

            # Verify cleanup was called
            file_storage.delete_file.assert_called_once()
            doc_repo.delete_document.assert_called_once()
            print("✅ PASSED: Cleanup was performed")

            return True


async def test_milvus_error():
    """Test that Milvus errors trigger full rollback."""
    print("\n=== Test 5: Milvus Error ===")

    # Setup mocks
    doc_repo = Mock(spec=DocumentRepository)
    user_repo = Mock(spec=UserRepository)
    file_storage = Mock(spec=FileStorageService)
    doc_processor = Mock(spec=DocumentProcessor)
    embedding_service = Mock(spec=EmbeddingService)
    milvus_manager = Mock(spec=MilvusManager)

    user_id = uuid4()
    document_id = uuid4()

    # Configure file_storage to succeed
    file_storage.validate_file_type.return_value = True
    file_storage.ALLOWED_EXTENSIONS = {".pdf": "application/pdf"}
    file_storage.save_file = AsyncMock(return_value=("uploads/test.pdf", 1024))
    file_storage.validate_file_size.return_value = True
    file_storage.delete_file = Mock()

    # Configure doc_repo to succeed
    mock_doc = create_mock_document(document_id, user_id)
    doc_repo.create_document.return_value = mock_doc
    doc_repo.update_document_status = Mock()
    doc_repo.delete_document = Mock()

    # Configure doc_processor to succeed
    doc_processor.detect_file_type.return_value = "pdf"
    doc_processor.extract_text.return_value = "Test content"

    mock_chunk = Mock()
    mock_chunk.chunk_id = "chunk1"
    mock_chunk.text = "Test content"
    mock_chunk.chunk_index = 0
    doc_processor.chunk_text.return_value = [mock_chunk]

    # Configure embedding_service to succeed
    embedding_service.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

    # Configure milvus_manager to fail
    milvus_manager.insert_embeddings = AsyncMock(
        side_effect=Exception("Milvus connection timeout")
    )
    milvus_manager.collection_name = "test_collection"

    # Create service
    service = DocumentService(
        document_repository=doc_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )

    # Mock file reading
    with patch("builtins.open", MagicMock()):
        try:
            await service.upload_document(user_id, MockUploadFile("test.pdf"))
            print("❌ FAILED: Should have raised DocumentServiceError")
            return False
        except DocumentServiceError as e:
            print(f"✅ PASSED: Raised DocumentServiceError: {e}")

            # Verify status was updated to failed
            doc_repo.update_document_status.assert_any_call(
                document_id,
                "failed",
                error_message="Vector storage failed: Milvus connection timeout",
            )
            print("✅ PASSED: Document status updated to failed")

            # Verify cleanup was called
            file_storage.delete_file.assert_called_once()
            doc_repo.delete_document.assert_called_once()
            print("✅ PASSED: Cleanup was performed")

            return True


async def test_cleanup_method():
    """Test the _cleanup_failed_upload method directly."""
    print("\n=== Test 6: Cleanup Method ===")

    # Setup mocks
    doc_repo = Mock(spec=DocumentRepository)
    user_repo = Mock(spec=UserRepository)
    file_storage = Mock(spec=FileStorageService)
    doc_processor = Mock(spec=DocumentProcessor)
    embedding_service = Mock(spec=EmbeddingService)
    milvus_manager = Mock(spec=MilvusManager)

    file_storage.delete_file = Mock()
    doc_repo.delete_document = Mock()
    milvus_manager.delete_by_document_id = Mock(return_value=5)

    # Create service
    service = DocumentService(
        document_repository=doc_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )

    user_id = uuid4()
    document_id = uuid4()
    file_path = "uploads/test.pdf"

    # Test cleanup with all resources
    service._cleanup_failed_upload(
        file_path=file_path,
        document_id=document_id,
        user_id=user_id,
        vectors_inserted=True,
    )

    # Verify all cleanup operations were called
    milvus_manager.delete_by_document_id.assert_called_once_with(str(document_id))
    print("✅ PASSED: Milvus vectors deleted")

    file_storage.delete_file.assert_called_once_with(file_path)
    print("✅ PASSED: File deleted")

    doc_repo.delete_document.assert_called_once_with(document_id, user_id)
    print("✅ PASSED: Document record deleted")

    return True


async def test_cleanup_resilience():
    """Test that cleanup continues even if individual operations fail."""
    print("\n=== Test 7: Cleanup Resilience ===")

    # Setup mocks
    doc_repo = Mock(spec=DocumentRepository)
    user_repo = Mock(spec=UserRepository)
    file_storage = Mock(spec=FileStorageService)
    doc_processor = Mock(spec=DocumentProcessor)
    embedding_service = Mock(spec=EmbeddingService)
    milvus_manager = Mock(spec=MilvusManager)

    # Configure cleanup operations to fail
    file_storage.delete_file = Mock(side_effect=Exception("File not found"))
    doc_repo.delete_document = Mock(side_effect=Exception("Database error"))
    milvus_manager.delete_by_document_id = Mock(side_effect=Exception("Milvus error"))

    # Create service
    service = DocumentService(
        document_repository=doc_repo,
        user_repository=user_repo,
        file_storage_service=file_storage,
        document_processor=doc_processor,
        embedding_service=embedding_service,
        milvus_manager=milvus_manager,
    )

    user_id = uuid4()
    document_id = uuid4()
    file_path = "uploads/test.pdf"

    # Test cleanup - should not raise exceptions
    try:
        service._cleanup_failed_upload(
            file_path=file_path,
            document_id=document_id,
            user_id=user_id,
            vectors_inserted=True,
        )
        print("✅ PASSED: Cleanup completed without raising exceptions")

        # Verify all cleanup operations were attempted
        milvus_manager.delete_by_document_id.assert_called_once()
        file_storage.delete_file.assert_called_once()
        doc_repo.delete_document.assert_called_once()
        print("✅ PASSED: All cleanup operations were attempted")

        return True
    except Exception as e:
        print(f"❌ FAILED: Cleanup raised exception: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("DocumentService Error Handling and Rollback Verification")
    print("=" * 60)

    tests = [
        ("File Validation Error", test_file_validation_error),
        ("File Storage Error", test_file_storage_error),
        ("Database Error", test_database_error),
        ("Processing Error", test_processing_error),
        ("Milvus Error", test_milvus_error),
        ("Cleanup Method", test_cleanup_method),
        ("Cleanup Resilience", test_cleanup_resilience),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' failed with exception: {e}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")

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
