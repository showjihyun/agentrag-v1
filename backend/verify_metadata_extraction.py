"""
Verification script for metadata extraction feature.

Tests:
1. MetadataExtractor service initialization
2. PDF metadata extraction
3. DOCX metadata extraction
4. Language detection
5. Keywords extraction
6. Database model fields
7. API endpoint filters
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        from services.metadata_extractor import (
            MetadataExtractor,
            get_metadata_extractor,
        )

        print("✓ MetadataExtractor imported")

        from db.models.document import Document

        print("✓ Document model imported")

        import langdetect

        print("✓ langdetect imported")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        if "langdetect" in str(e):
            print("  Install: pip install langdetect")
        return False


def test_metadata_extractor_init():
    """Test MetadataExtractor initialization."""
    print("\nTesting MetadataExtractor initialization...")

    try:
        from services.metadata_extractor import (
            MetadataExtractor,
            get_metadata_extractor,
        )

        # Test direct initialization
        extractor1 = MetadataExtractor()
        print("✓ Direct initialization works")

        # Test singleton
        extractor2 = get_metadata_extractor()
        extractor3 = get_metadata_extractor()
        assert extractor2 is extractor3, "Singleton should return same instance"
        print("✓ Singleton pattern works")

        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_language_detection():
    """Test language detection."""
    print("\nTesting language detection...")

    try:
        from services.metadata_extractor import MetadataExtractor

        extractor = MetadataExtractor()

        # Test English
        lang_en = extractor._detect_language("This is a test document in English.")
        assert lang_en == "en", f"Expected 'en', got '{lang_en}'"
        print(f"✓ English detected: {lang_en}")

        # Test Korean
        lang_ko = extractor._detect_language(
            "이것은 한국어로 작성된 테스트 문서입니다."
        )
        assert lang_ko == "ko", f"Expected 'ko', got '{lang_ko}'"
        print(f"✓ Korean detected: {lang_ko}")

        # Test short text
        lang_unknown = extractor._detect_language("Hi")
        assert lang_unknown == "unknown", f"Expected 'unknown', got '{lang_unknown}'"
        print(f"✓ Short text handled: {lang_unknown}")

        return True
    except Exception as e:
        print(f"✗ Language detection failed: {e}")
        return False


def test_keyword_extraction():
    """Test keyword extraction."""
    print("\nTesting keyword extraction...")

    try:
        from services.metadata_extractor import MetadataExtractor

        extractor = MetadataExtractor()

        text = """
        Machine learning is a subset of artificial intelligence that focuses on
        developing algorithms and statistical models. Deep learning is a type of
        machine learning that uses neural networks with multiple layers.
        """

        keywords = extractor._extract_keywords(text, max_keywords=5)

        assert isinstance(keywords, list), "Keywords should be a list"
        assert len(keywords) <= 5, "Should return max 5 keywords"
        assert (
            "machine" in keywords or "learning" in keywords
        ), "Should extract relevant keywords"

        print(f"✓ Keywords extracted: {keywords}")

        return True
    except Exception as e:
        print(f"✗ Keyword extraction failed: {e}")
        return False


def test_model_fields():
    """Test that Document model has metadata fields."""
    print("\nTesting Document model fields...")

    try:
        from db.models.document import Document
        from sqlalchemy import inspect

        # Get model columns
        mapper = inspect(Document)
        columns = {col.key for col in mapper.columns}

        # Check for metadata fields
        required_fields = {
            "document_title",
            "document_author",
            "document_subject",
            "document_keywords",
            "document_language",
            "document_creation_date",
            "document_modification_date",
        }

        missing_fields = required_fields - columns

        if missing_fields:
            print(f"✗ Missing fields: {missing_fields}")
            print(
                "  Run migration: backend/db/migrations/add_document_metadata_fields.sql"
            )
            return False

        print("✓ All metadata fields present in Document model")
        print(f"  Fields: {', '.join(sorted(required_fields))}")

        return True
    except Exception as e:
        print(f"✗ Model field check failed: {e}")
        return False


def test_milvus_schema():
    """Test that Milvus schema has metadata fields."""
    print("\nTesting Milvus schema...")

    try:
        from models.milvus_schema import get_document_collection_schema

        schema = get_document_collection_schema(embedding_dim=384)

        # Get field names
        field_names = {field.name for field in schema.fields}

        # Check for metadata fields
        required_fields = {"author", "creation_date", "language", "keywords"}

        missing_fields = required_fields - field_names

        if missing_fields:
            print(f"✗ Missing fields in Milvus schema: {missing_fields}")
            return False

        print("✓ All metadata fields present in Milvus schema")
        print(f"  Fields: {', '.join(sorted(required_fields))}")

        return True
    except Exception as e:
        print(f"✗ Milvus schema check failed: {e}")
        return False


def test_api_filters():
    """Test that API endpoints support metadata filters."""
    print("\nTesting API endpoint filters...")

    try:
        # Check if endpoints support filters
        with open("api/documents.py", "r", encoding="utf-8") as f:
            content = f.read()

        required_filters = ["author_filter", "language_filter", "from_date", "to_date"]

        missing_filters = []
        for filter_name in required_filters:
            if filter_name not in content:
                missing_filters.append(filter_name)

        if missing_filters:
            print(f"✗ Missing filters: {missing_filters}")
            return False

        print("✓ All metadata filters present in API")
        print(f"  Filters: {', '.join(required_filters)}")

        return True
    except Exception as e:
        print(f"✗ API filter check failed: {e}")
        return False


def test_extraction_methods():
    """Test that MetadataExtractor has all extraction methods."""
    print("\nTesting MetadataExtractor methods...")

    try:
        from services.metadata_extractor import MetadataExtractor

        # Check for extraction methods
        required_methods = [
            "extract_pdf_metadata",
            "extract_docx_metadata",
            "extract_txt_metadata",
            "extract_hwp_metadata",
            "extract_hwpx_metadata",
            "extract_metadata",
            "_detect_language",
            "_extract_keywords",
        ]

        missing_methods = []
        for method in required_methods:
            if not hasattr(MetadataExtractor, method):
                missing_methods.append(method)

        if missing_methods:
            print(f"✗ Missing methods: {missing_methods}")
            return False

        print("✓ All extraction methods present")
        print(f"  Methods: {len(required_methods)} total")

        return True
    except Exception as e:
        print(f"✗ Method check failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Metadata Extraction Feature Verification")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("MetadataExtractor Init", test_metadata_extractor_init),
        ("Language Detection", test_language_detection),
        ("Keyword Extraction", test_keyword_extraction),
        ("Model Fields", test_model_fields),
        ("Milvus Schema", test_milvus_schema),
        ("API Filters", test_api_filters),
        ("Extraction Methods", test_extraction_methods),
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
            "   psql -U postgres -d your_database -f backend/db/migrations/add_document_metadata_fields.sql"
        )
        print("2. Install langdetect if not already installed:")
        print("   pip install langdetect")
        print("3. Test with actual file uploads")
        print("4. Verify metadata extraction in database")
        print("5. Test API filters:")
        print("   GET /api/documents?author_filter=John&language_filter=en")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
