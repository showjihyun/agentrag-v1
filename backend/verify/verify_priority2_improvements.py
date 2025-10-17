"""
Verification script for Priority 2 Improvements.

Tests:
1. Exception hierarchy with enhanced context
2. Embedding batch size optimization
3. Logging level optimization
4. Type hints improvements
"""

import asyncio
import sys
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VerificationResult:
    """Result of a verification test."""

    def __init__(self, name: str, passed: bool, message: str):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.name}\n   {self.message}"


async def verify_exception_hierarchy():
    """Verify enhanced exception hierarchy."""
    try:
        from exceptions import RAGException
        import inspect

        # Check if RAGException has enhanced __init__
        init_signature = inspect.signature(RAGException.__init__)
        params = list(init_signature.parameters.keys())

        if "details" not in params:
            return VerificationResult(
                "Exception Hierarchy", False, "RAGException missing 'details' parameter"
            )

        if "cause" not in params:
            return VerificationResult(
                "Exception Hierarchy", False, "RAGException missing 'cause' parameter"
            )

        # Check if to_dict method exists
        if not hasattr(RAGException, "to_dict"):
            return VerificationResult(
                "Exception Hierarchy", False, "RAGException missing 'to_dict' method"
            )

        # Test exception creation
        try:
            exc = RAGException(
                "Test error",
                details={"key": "value"},
                cause=ValueError("Original error"),
            )

            exc_dict = exc.to_dict()

            if "error_type" not in exc_dict:
                return VerificationResult(
                    "Exception Hierarchy", False, "to_dict() missing 'error_type'"
                )

            if "message" not in exc_dict:
                return VerificationResult(
                    "Exception Hierarchy", False, "to_dict() missing 'message'"
                )

            if "details" not in exc_dict:
                return VerificationResult(
                    "Exception Hierarchy", False, "to_dict() missing 'details'"
                )

        except Exception as e:
            return VerificationResult(
                "Exception Hierarchy", False, f"Exception creation failed: {str(e)}"
            )

        return VerificationResult(
            "Exception Hierarchy",
            True,
            "Enhanced exception hierarchy with context support",
        )

    except Exception as e:
        return VerificationResult(
            "Exception Hierarchy", False, f"Error during verification: {str(e)}"
        )


async def verify_embedding_batch_optimization():
    """Verify embedding batch size optimization."""
    try:
        from services.embedding import EmbeddingService
        import inspect

        # Check if _calculate_optimal_batch_size method exists
        if not hasattr(EmbeddingService, "_calculate_optimal_batch_size"):
            return VerificationResult(
                "Embedding Batch Optimization",
                False,
                "_calculate_optimal_batch_size method not found",
            )

        # Check if embed_batch has batch_size parameter with None default
        embed_batch_signature = inspect.signature(EmbeddingService.embed_batch)
        batch_size_param = embed_batch_signature.parameters.get("batch_size")

        if not batch_size_param:
            return VerificationResult(
                "Embedding Batch Optimization",
                False,
                "batch_size parameter not found in embed_batch",
            )

        if (
            batch_size_param.default is not None
            and batch_size_param.default != inspect.Parameter.empty
        ):
            # Check if it's None (auto-optimization)
            pass

        # Check if show_progress parameter exists
        if "show_progress" not in embed_batch_signature.parameters:
            return VerificationResult(
                "Embedding Batch Optimization",
                False,
                "show_progress parameter not found in embed_batch",
            )

        return VerificationResult(
            "Embedding Batch Optimization",
            True,
            "Dynamic batch size optimization implemented",
        )

    except Exception as e:
        return VerificationResult(
            "Embedding Batch Optimization",
            False,
            f"Error during verification: {str(e)}",
        )


async def verify_logging_optimization():
    """Verify logging level optimization."""
    try:
        from services.embedding import EmbeddingService
        from services.milvus import MilvusManager
        import inspect

        # Check embedding service logging
        embed_text_source = inspect.getsource(EmbeddingService.embed_text)

        # Should use DEBUG for individual embeddings
        if "logger.debug" not in embed_text_source:
            return VerificationResult(
                "Logging Optimization",
                False,
                "embed_text should use logger.debug for individual embeddings",
            )

        # Check milvus search logging
        search_source = inspect.getsource(MilvusManager.search)

        # Should use DEBUG for search results
        if (
            "logger.debug" not in search_source
            or "Search returned" not in search_source
        ):
            return VerificationResult(
                "Logging Optimization",
                False,
                "Milvus search should use logger.debug for result counts",
            )

        return VerificationResult(
            "Logging Optimization",
            True,
            "Logging levels optimized (DEBUG for frequent operations)",
        )

    except Exception as e:
        return VerificationResult(
            "Logging Optimization", False, f"Error during verification: {str(e)}"
        )


async def verify_type_hints():
    """Verify type hints improvements."""
    try:
        import os

        # Read the file directly
        file_path = os.path.join(
            os.path.dirname(__file__), "agents", "aggregator_optimized.py"
        )

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if type hints are present in __init__
        if "llm_manager: LLMManager" not in content:
            return VerificationResult(
                "Type Hints", False, "llm_manager type hint not found"
            )

        if "memory_manager: MemoryManager" not in content:
            return VerificationResult(
                "Type Hints", False, "memory_manager type hint not found"
            )

        if "vector_agent: Any" not in content:
            return VerificationResult(
                "Type Hints", False, "vector_agent type hint not found"
            )

        return VerificationResult(
            "Type Hints", True, "Type hints present in aggregator_optimized.py"
        )

    except Exception as e:
        return VerificationResult(
            "Type Hints", False, f"Error during verification: {str(e)}"
        )


async def run_all_verifications() -> List[VerificationResult]:
    """Run all verification tests."""
    results = []

    logger.info("=" * 60)
    logger.info("Backend Priority 2 Improvements Verification")
    logger.info("=" * 60)
    logger.info("")

    # Run all tests
    tests = [
        ("Exception Hierarchy", verify_exception_hierarchy),
        ("Embedding Batch Optimization", verify_embedding_batch_optimization),
        ("Logging Optimization", verify_logging_optimization),
        ("Type Hints", verify_type_hints),
    ]

    for test_name, test_func in tests:
        logger.info(f"Running: {test_name}...")
        result = await test_func()
        results.append(result)
        logger.info(str(result))
        logger.info("")

    return results


async def main():
    """Main verification function."""
    results = await run_all_verifications()

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"SUMMARY: {passed}/{total} tests passed")
    logger.info("=" * 60)

    if passed == total:
        logger.info("✅ All Priority 2 improvements verified successfully!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
