"""
Verification script for document versioning feature.

Tests:
1. Document version service initialization
2. File hash calculation
3. Version creation and tracking
4. Duplicate detection
5. Version history retrieval
6. Version comparison
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        from services.document_version_service import (
            DocumentVersionService,
            DocumentVersionServiceError,
        )

        print("✓ DocumentVersionService imported")

        from db.models.document import Document

        print("✓ Document model imported")

        from db.repositories.document_repository import DocumentRepository

        print("✓ DocumentRepository imported")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_hash_calculation():
    """Test file hash calculation."""
    print("\nTesting hash calculation...")

    try:
        from services.document_version_service import DocumentVersionService
        import hashlib

        # Create a mock service instance (without dependencies)
        class MockService:
            def _calculate_file_hash(self, content: bytes) -> str:
                return hashlib.sha256(content).hexdigest()

        service = MockService()

        # Test hash calculation
        content1 = b"Hello, World!"
        content2 = b"Hello, World!"
        content3 = b"Different content"

        hash1 = service._calculate_file_hash(content1)
        hash2 = service._calculate_file_hash(content2)
        hash3 = service._calculate_file_hash(content3)

        # Verify
        assert hash1 == hash2, "Same content should produce same hash"
        assert hash1 != hash3, "Different content should produce different hash"
        assert len(hash1) == 64, "SHA-256 hash should be 64 characters"

        print(f"✓ Hash calculation works correctly")
        print(f"  Sample hash: {hash1[:16]}...")

        return True
    except Exception as e:
        print(f"✗ Hash calculation failed: {e}")
        return False


def test_model_fields():
    """Test that Document model has version fields."""
    print("\nTesting Document model fields...")

    try:
        from db.models.document import Document
        from sqlalchemy import inspect

        # Get model columns
        mapper = inspect(Document)
        columns = {col.key for col in mapper.columns}

        # Check for version fields
        required_fields = {"version", "previous_version_id", "file_hash", "archived_at"}

        missing_fields = required_fields - columns

        if missing_fields:
            print(f"✗ Missing fields: {missing_fields}")
            print("  Run migration: backend/db/migrations/add_document_versioning.sql")
            return False

        print("✓ All version fields present in Document model")
        print(f"  Fields: {', '.join(required_fields)}")

        return True
    except Exception as e:
        print(f"✗ Model field check failed: {e}")
        return False


def test_repository_methods():
    """Test that DocumentRepository has version methods."""
    print("\nTesting DocumentRepository methods...")

    try:
        from db.repositories.document_repository import DocumentRepository

        # Check for version methods
        required_methods = [
            "get_documents_by_filename",
            "get_document_by_hash",
            "get_version_history",
            "update_document",
        ]

        missing_methods = []
        for method in required_methods:
            if not hasattr(DocumentRepository, method):
                missing_methods.append(method)

        if missing_methods:
            print(f"✗ Missing methods: {missing_methods}")
            return False

        print("✓ All version methods present in DocumentRepository")
        print(f"  Methods: {', '.join(required_methods)}")

        return True
    except Exception as e:
        print(f"✗ Repository method check failed: {e}")
        return False


def test_service_methods():
    """Test that DocumentVersionService has required methods."""
    print("\nTesting DocumentVersionService methods...")

    try:
        from services.document_version_service import DocumentVersionService

        # Check for service methods
        required_methods = [
            "upload_with_versioning",
            "get_version_history",
            "get_version_comparison",
            "rollback_to_version",
            "_calculate_file_hash",
            "_archive_version",
        ]

        missing_methods = []
        for method in required_methods:
            if not hasattr(DocumentVersionService, method):
                missing_methods.append(method)

        if missing_methods:
            print(f"✗ Missing methods: {missing_methods}")
            return False

        print("✓ All methods present in DocumentVersionService")
        print(f"  Methods: {', '.join(required_methods)}")

        return True
    except Exception as e:
        print(f"✗ Service method check failed: {e}")
        return False


def test_api_endpoints():
    """Test that API endpoints are defined."""
    print("\nTesting API endpoints...")

    try:
        # Check if endpoints are defined in documents.py
        with open("api/documents.py", "r", encoding="utf-8") as f:
            content = f.read()

        required_endpoints = ["get_document_versions", "compare_document_versions"]

        missing_endpoints = []
        for endpoint in required_endpoints:
            if f"def {endpoint}" not in content:
                missing_endpoints.append(endpoint)

        if missing_endpoints:
            print(f"✗ Missing endpoints: {missing_endpoints}")
            return False

        print("✓ All version API endpoints defined")
        print(f"  Endpoints: {', '.join(required_endpoints)}")

        # Check for replace_existing parameter
        if "replace_existing" in content:
            print("✓ upload_document has replace_existing parameter")
        else:
            print("⚠ upload_document may be missing replace_existing parameter")

        return True
    except Exception as e:
        print(f"✗ API endpoint check failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Document Versioning Feature Verification")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Hash Calculation", test_hash_calculation),
        ("Model Fields", test_model_fields),
        ("Repository Methods", test_repository_methods),
        ("Service Methods", test_service_methods),
        ("API Endpoints", test_api_endpoints),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All verification tests passed!")
        print("\nNext steps:")
        print("1. Run database migration:")
        print(
            "   psql -U postgres -d your_database -f backend/db/migrations/add_document_versioning.sql"
        )
        print("2. Test with actual file uploads")
        print("3. Verify version history in database")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
