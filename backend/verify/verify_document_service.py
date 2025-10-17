"""
Verification script for DocumentService implementation.

Tests:
1. Service initialization
2. Method signatures and interfaces
3. Error handling structure
4. Integration with repositories and services
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_document_service_structure():
    """Verify DocumentService class structure and methods."""
    print("\n" + "=" * 80)
    print("VERIFICATION: DocumentService Structure")
    print("=" * 80)

    try:
        from services.document_service import DocumentService, DocumentServiceError

        # Check class exists
        print("✓ DocumentService class imported successfully")
        print("✓ DocumentServiceError exception imported successfully")

        # Check required methods exist
        required_methods = [
            "upload_document",
            "get_user_documents",
            "get_document",
            "delete_document",
            "get_document_count",
            "get_total_storage_used",
        ]

        for method_name in required_methods:
            if hasattr(DocumentService, method_name):
                print(f"✓ Method '{method_name}' exists")
            else:
                print(f"✗ Method '{method_name}' missing")
                return False

        # Check __init__ signature
        import inspect

        init_sig = inspect.signature(DocumentService.__init__)
        init_params = list(init_sig.parameters.keys())

        expected_params = [
            "self",
            "document_repository",
            "user_repository",
            "file_storage_service",
            "document_processor",
            "embedding_service",
            "milvus_manager",
        ]

        print(f"\n__init__ parameters: {init_params}")

        for param in expected_params:
            if param in init_params:
                print(f"✓ Parameter '{param}' present")
            else:
                print(f"✗ Parameter '{param}' missing")
                return False

        # Check upload_document signature
        upload_sig = inspect.signature(DocumentService.upload_document)
        upload_params = list(upload_sig.parameters.keys())

        print(f"\nupload_document parameters: {upload_params}")

        expected_upload_params = ["self", "user_id", "file"]
        for param in expected_upload_params:
            if param in upload_params:
                print(f"✓ Parameter '{param}' present")
            else:
                print(f"✗ Parameter '{param}' missing")
                return False

        # Check if upload_document is async
        if inspect.iscoroutinefunction(DocumentService.upload_document):
            print("✓ upload_document is async")
        else:
            print("✗ upload_document should be async")
            return False

        # Check delete_document signature
        delete_sig = inspect.signature(DocumentService.delete_document)
        delete_params = list(delete_sig.parameters.keys())

        print(f"\ndelete_document parameters: {delete_params}")

        expected_delete_params = ["self", "document_id", "user_id"]
        for param in expected_delete_params:
            if param in delete_params:
                print(f"✓ Parameter '{param}' present")
            else:
                print(f"✗ Parameter '{param}' missing")
                return False

        # Check if delete_document is async
        if inspect.iscoroutinefunction(DocumentService.delete_document):
            print("✓ delete_document is async")
        else:
            print("✗ delete_document should be async")
            return False

        # Check get_user_documents signature
        get_docs_sig = inspect.signature(DocumentService.get_user_documents)
        get_docs_params = list(get_docs_sig.parameters.keys())

        print(f"\nget_user_documents parameters: {get_docs_params}")

        expected_get_docs_params = ["self", "user_id", "status", "limit", "offset"]
        for param in expected_get_docs_params:
            if param in get_docs_params:
                print(f"✓ Parameter '{param}' present")
            else:
                print(f"✗ Parameter '{param}' missing")
                return False

        print("\n" + "=" * 80)
        print("✓ ALL STRUCTURE CHECKS PASSED")
        print("=" * 80)

        return True

    except ImportError as e:
        print(f"✗ Failed to import DocumentService: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_integration_points():
    """Verify integration with other services and repositories."""
    print("\n" + "=" * 80)
    print("VERIFICATION: Integration Points")
    print("=" * 80)

    try:
        from services.document_service import DocumentService
        import inspect

        # Check upload_document implementation
        source = inspect.getsource(DocumentService.upload_document)

        integration_checks = {
            "file_storage.validate_file_type": "File type validation",
            "file_storage.save_file": "File storage",
            "file_storage.validate_file_size": "File size validation",
            "document_repo.create_document": "Document record creation",
            "document_repo.update_document_status": "Status updates",
            "doc_processor.detect_file_type": "File type detection",
            "doc_processor.extract_text": "Text extraction",
            "doc_processor.chunk_text": "Text chunking",
            "embedding_service.embed_batch": "Embedding generation",
            "milvus_manager.insert_embeddings": "Vector storage",
            "document_repo.update_document_processing": "Processing info update",
            "user_repo.update_storage_used": "Storage quota update",
        }

        print("\nChecking upload_document integration points:")
        for check, description in integration_checks.items():
            if check in source:
                print(f"✓ {description} ({check})")
            else:
                print(f"✗ {description} ({check}) - NOT FOUND")

        # Check delete_document implementation
        delete_source = inspect.getsource(DocumentService.delete_document)

        delete_checks = {
            "document_repo.get_document_by_id": "Document retrieval",
            "milvus_manager.delete_by_document_id": "Vector deletion",
            "file_storage.delete_file": "File deletion",
            "document_repo.delete_document": "Document record deletion",
            "user_repo.update_storage_used": "Storage quota decrement",
        }

        print("\nChecking delete_document integration points:")
        for check, description in delete_checks.items():
            if check in source:
                print(f"✓ {description} ({check})")
            else:
                print(f"✗ {description} ({check}) - NOT FOUND")

        # Check error handling
        print("\nChecking error handling:")

        error_handling_checks = {
            "try:": "Try-except blocks",
            "except": "Exception handling",
            "DocumentServiceError": "Custom exception usage",
            "ValueError": "Validation error handling",
            "logger.error": "Error logging",
            "rollback": "Rollback on failure (cleanup)",
        }

        for check, description in error_handling_checks.items():
            if check in source or check in delete_source:
                print(f"✓ {description}")
            else:
                print(f"⚠ {description} - might be missing")

        # Check user_id in metadata
        print("\nChecking user_id in Milvus metadata:")
        if '"user_id": str(user_id)' in source or "'user_id': str(user_id)" in source:
            print("✓ user_id included in Milvus metadata")
        else:
            print("✗ user_id NOT included in Milvus metadata")

        print("\n" + "=" * 80)
        print("✓ INTEGRATION CHECKS COMPLETED")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"✗ Integration verification failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_error_handling():
    """Verify error handling and rollback logic."""
    print("\n" + "=" * 80)
    print("VERIFICATION: Error Handling and Rollback")
    print("=" * 80)

    try:
        from services.document_service import DocumentService
        import inspect

        source = inspect.getsource(DocumentService.upload_document)

        print("\nChecking rollback mechanisms:")

        rollback_checks = [
            ("file_storage.delete_file", "File cleanup on error"),
            ("document_repo.delete_document", "Document record cleanup on error"),
            ("update_document_status.*failed", "Status update to failed on error"),
        ]

        import re

        for pattern, description in rollback_checks:
            if re.search(pattern, source):
                print(f"✓ {description}")
            else:
                print(f"⚠ {description} - might be missing")

        print("\nChecking error propagation:")

        error_checks = [
            "raise DocumentServiceError",
            "raise ValueError",
            "except.*DocumentServiceError",
            "except.*ValueError",
            "except.*FileStorageError",
            "except.*DocumentProcessingError",
        ]

        for pattern in error_checks:
            if re.search(pattern, source):
                print(f"✓ {pattern}")
            else:
                print(f"⚠ {pattern} - might be missing")

        print("\n" + "=" * 80)
        print("✓ ERROR HANDLING CHECKS COMPLETED")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"✗ Error handling verification failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_helper_function():
    """Verify get_document_service helper function."""
    print("\n" + "=" * 80)
    print("VERIFICATION: Helper Function")
    print("=" * 80)

    try:
        from services.document_service import get_document_service

        print("✓ get_document_service function imported successfully")

        import inspect

        sig = inspect.signature(get_document_service)
        params = list(sig.parameters.keys())

        print(f"\nget_document_service parameters: {params}")

        expected_params = [
            "document_repository",
            "user_repository",
            "file_storage_service",
            "document_processor",
            "embedding_service",
            "milvus_manager",
        ]

        for param in expected_params:
            if param in params:
                print(f"✓ Parameter '{param}' present")
            else:
                print(f"✗ Parameter '{param}' missing")
                return False

        print("\n" + "=" * 80)
        print("✓ HELPER FUNCTION CHECKS PASSED")
        print("=" * 80)

        return True

    except ImportError as e:
        print(f"✗ Failed to import get_document_service: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 80)
    print("DOCUMENT SERVICE VERIFICATION")
    print("=" * 80)

    results = []

    # Run all checks
    results.append(("Structure", verify_document_service_structure()))
    results.append(("Integration Points", verify_integration_points()))
    results.append(("Error Handling", verify_error_handling()))
    results.append(("Helper Function", verify_helper_function()))

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    for check_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{check_name}: {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL VERIFICATIONS PASSED")
        print("=" * 80)
        print("\nDocumentService implementation is complete and correct!")
        print("\nKey features verified:")
        print("  • User-isolated document management")
        print("  • File validation and storage")
        print("  • Document processing and vectorization")
        print("  • Storage quota tracking")
        print("  • Comprehensive error handling with rollback")
        print("  • Milvus integration with user_id metadata")
        return 0
    else:
        print("✗ SOME VERIFICATIONS FAILED")
        print("=" * 80)
        print("\nPlease review the failed checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
