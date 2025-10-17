"""
Verification script for StaticRAGService implementation.

This script verifies that the StaticRAGService is correctly implemented
and can be instantiated with all required dependencies.
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def verify_imports():
    """Verify all required imports work."""
    print("✓ Verifying imports...")

    try:
        from backend.services.static_rag_service import StaticRAGService

        print("  ✓ StaticRAGService imported")
    except ImportError as e:
        print(f"  ✗ Failed to import StaticRAGService: {e}")
        return False

    try:
        from backend.models.hybrid import StaticRAGResponse

        print("  ✓ StaticRAGResponse imported")
    except ImportError as e:
        print(f"  ✗ Failed to import StaticRAGResponse: {e}")
        return False

    try:
        from backend.exceptions import StaticRAGException, HybridRAGException

        print("  ✓ Exceptions imported")
    except ImportError as e:
        print(f"  ✗ Failed to import exceptions: {e}")
        return False

    return True


def verify_model_structure():
    """Verify StaticRAGResponse model structure."""
    print("\n✓ Verifying StaticRAGResponse model...")

    try:
        from backend.models.hybrid import StaticRAGResponse
        from backend.models.query import SearchResult

        # Check required fields
        required_fields = [
            "response",
            "sources",
            "confidence_score",
            "processing_time",
            "cache_hit",
            "metadata",
        ]

        model_fields = StaticRAGResponse.model_fields

        for field in required_fields:
            if field in model_fields:
                print(f"  ✓ Field '{field}' present")
            else:
                print(f"  ✗ Field '{field}' missing")
                return False

        # Test model instantiation
        test_response = StaticRAGResponse(
            response="Test response",
            sources=[],
            confidence_score=0.85,
            processing_time=1.5,
            cache_hit=False,
            metadata={"test": "data"},
        )

        print(f"  ✓ Model instantiation successful")
        print(f"  ✓ Confidence score: {test_response.confidence_score}")
        print(f"  ✓ Processing time: {test_response.processing_time}s")

        return True

    except Exception as e:
        print(f"  ✗ Model verification failed: {e}")
        return False


def verify_service_structure():
    """Verify StaticRAGService class structure."""
    print("\n✓ Verifying StaticRAGService structure...")

    try:
        from backend.services.static_rag_service import StaticRAGService
        import inspect

        # Check required methods
        required_methods = [
            "process_query",
            "invalidate_cache",
            "get_stats",
            "_generate_cache_key",
            "_check_cache",
            "_cache_response",
            "_rank_and_filter_results",
            "_calculate_preliminary_confidence",
            "_build_context_prompt",
        ]

        service_methods = [
            name
            for name, _ in inspect.getmembers(
                StaticRAGService, predicate=inspect.isfunction
            )
        ]

        for method in required_methods:
            if method in service_methods:
                print(f"  ✓ Method '{method}' present")
            else:
                print(f"  ✗ Method '{method}' missing")
                return False

        # Check __init__ signature
        init_sig = inspect.signature(StaticRAGService.__init__)
        params = list(init_sig.parameters.keys())

        required_params = [
            "self",
            "embedding_service",
            "milvus_manager",
            "llm_manager",
            "cache_manager",
        ]

        for param in required_params:
            if param in params:
                print(f"  ✓ Init parameter '{param}' present")
            else:
                print(f"  ✗ Init parameter '{param}' missing")
                return False

        return True

    except Exception as e:
        print(f"  ✗ Service verification failed: {e}")
        return False


def verify_exception_hierarchy():
    """Verify exception hierarchy."""
    print("\n✓ Verifying exception hierarchy...")

    try:
        from backend.exceptions import (
            RAGException,
            HybridRAGException,
            StaticRAGException,
            RoutingException,
            EscalationException,
        )

        # Check inheritance
        assert issubclass(
            HybridRAGException, RAGException
        ), "HybridRAGException should inherit from RAGException"
        print("  ✓ HybridRAGException inherits from RAGException")

        assert issubclass(
            StaticRAGException, HybridRAGException
        ), "StaticRAGException should inherit from HybridRAGException"
        print("  ✓ StaticRAGException inherits from HybridRAGException")

        assert issubclass(
            RoutingException, HybridRAGException
        ), "RoutingException should inherit from HybridRAGException"
        print("  ✓ RoutingException inherits from HybridRAGException")

        assert issubclass(
            EscalationException, HybridRAGException
        ), "EscalationException should inherit from HybridRAGException"
        print("  ✓ EscalationException inherits from HybridRAGException")

        # Test exception raising
        try:
            raise StaticRAGException("Test error")
        except StaticRAGException as e:
            print(f"  ✓ StaticRAGException can be raised and caught: {e}")

        return True

    except Exception as e:
        print(f"  ✗ Exception verification failed: {e}")
        return False


def verify_cache_key_generation():
    """Verify cache key generation logic."""
    print("\n✓ Verifying cache key generation...")

    try:
        from backend.services.static_rag_service import StaticRAGService
        from unittest.mock import Mock

        # Create mock dependencies
        mock_embedding = Mock()
        mock_milvus = Mock()
        mock_llm = Mock()
        mock_cache = Mock()

        # Create service
        service = StaticRAGService(
            embedding_service=mock_embedding,
            milvus_manager=mock_milvus,
            llm_manager=mock_llm,
            cache_manager=mock_cache,
        )

        # Test cache key generation
        key1 = service._generate_cache_key("test query", "session_123", 5)
        key2 = service._generate_cache_key("test query", "session_123", 5)
        key3 = service._generate_cache_key("different query", "session_123", 5)

        assert key1 == key2, "Same inputs should generate same key"
        print(f"  ✓ Deterministic cache key generation")

        assert key1 != key3, "Different inputs should generate different keys"
        print(f"  ✓ Different inputs generate different keys")

        assert ":" in key1, "Cache key should contain separators"
        print(f"  ✓ Cache key format correct: {key1}")

        return True

    except Exception as e:
        print(f"  ✗ Cache key verification failed: {e}")
        return False


def verify_confidence_calculation():
    """Verify confidence calculation logic."""
    print("\n✓ Verifying confidence calculation...")

    try:
        from backend.services.static_rag_service import StaticRAGService
        from backend.services.milvus import SearchResult
        from unittest.mock import Mock

        # Create mock dependencies
        mock_embedding = Mock()
        mock_milvus = Mock()
        mock_llm = Mock()
        mock_cache = Mock()

        # Create service
        service = StaticRAGService(
            embedding_service=mock_embedding,
            milvus_manager=mock_milvus,
            llm_manager=mock_llm,
            cache_manager=mock_cache,
        )

        # Test with no sources
        confidence_no_sources = service._calculate_preliminary_confidence([])
        assert confidence_no_sources == 0.0, "No sources should give 0 confidence"
        print(f"  ✓ No sources: confidence = {confidence_no_sources}")

        # Test with good sources
        good_sources = [
            SearchResult(
                id="1",
                document_id="doc1",
                text="test",
                score=0.9,
                document_name="test.pdf",
                chunk_index=0,
            ),
            SearchResult(
                id="2",
                document_id="doc2",
                text="test",
                score=0.85,
                document_name="test2.pdf",
                chunk_index=0,
            ),
        ]

        confidence_good = service._calculate_preliminary_confidence(good_sources)
        assert 0.7 <= confidence_good <= 1.0, "Good sources should give high confidence"
        print(f"  ✓ Good sources: confidence = {confidence_good:.3f}")

        # Test with poor sources
        poor_sources = [
            SearchResult(
                id="1",
                document_id="doc1",
                text="test",
                score=0.5,
                document_name="test.pdf",
                chunk_index=0,
            )
        ]

        confidence_poor = service._calculate_preliminary_confidence(poor_sources)
        assert confidence_poor < 0.7, "Poor sources should give lower confidence"
        print(f"  ✓ Poor sources: confidence = {confidence_poor:.3f}")

        return True

    except Exception as e:
        print(f"  ✗ Confidence calculation verification failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("StaticRAGService Implementation Verification")
    print("=" * 60)

    checks = [
        ("Imports", verify_imports),
        ("Model Structure", verify_model_structure),
        ("Service Structure", verify_service_structure),
        ("Exception Hierarchy", verify_exception_hierarchy),
        ("Cache Key Generation", verify_cache_key_generation),
        ("Confidence Calculation", verify_confidence_calculation),
    ]

    results = []

    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n✗ {check_name} check failed with exception: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All verification checks passed!")
        print("\nStaticRAGService implementation is correct and ready for use.")
        return 0
    else:
        print(
            f"\n⚠️  {total - passed} check(s) failed. Please review the implementation."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
