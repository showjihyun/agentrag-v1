"""
Verification script for Priority 1 Critical Fixes.

Tests:
1. Milvus collection load race condition fix
2. LLM timeout enforcement
3. Database transaction boundary documentation
4. Cache key collision prevention
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


async def verify_milvus_load_lock():
    """Verify Milvus collection load has race condition protection."""
    try:
        from services.milvus import MilvusManager
        import inspect

        # Check if _load_lock exists in __init__
        init_source = inspect.getsource(MilvusManager.__init__)
        if "_load_lock" not in init_source:
            return VerificationResult(
                "Milvus Load Lock", False, "_load_lock not initialized in __init__"
            )

        # Check if _ensure_collection_loaded is async
        if not asyncio.iscoroutinefunction(MilvusManager._ensure_collection_loaded):
            return VerificationResult(
                "Milvus Load Lock", False, "_ensure_collection_loaded is not async"
            )

        # Check if lock is used in _ensure_collection_loaded
        load_source = inspect.getsource(MilvusManager._ensure_collection_loaded)
        if "async with self._load_lock" not in load_source:
            return VerificationResult(
                "Milvus Load Lock", False, "Lock not used in _ensure_collection_loaded"
            )

        return VerificationResult(
            "Milvus Load Lock",
            True,
            "Race condition protection implemented with asyncio.Lock",
        )

    except Exception as e:
        return VerificationResult(
            "Milvus Load Lock", False, f"Error during verification: {str(e)}"
        )


async def verify_llm_timeout():
    """Verify LLM timeout enforcement."""
    try:
        from services.llm_manager import LLMManager
        import inspect

        # Check if generate method uses asyncio.wait_for
        generate_source = inspect.getsource(LLMManager.generate)

        if "asyncio.wait_for" not in generate_source:
            return VerificationResult(
                "LLM Timeout", False, "asyncio.wait_for not used in generate method"
            )

        if "asyncio.TimeoutError" not in generate_source:
            return VerificationResult(
                "LLM Timeout", False, "TimeoutError not handled in generate method"
            )

        return VerificationResult(
            "LLM Timeout", True, "Timeout enforcement implemented with asyncio.wait_for"
        )

    except Exception as e:
        return VerificationResult(
            "LLM Timeout", False, f"Error during verification: {str(e)}"
        )


async def verify_database_transaction_docs():
    """Verify database transaction boundary documentation."""
    try:
        from db.database import get_db
        import inspect

        # Check if get_db has comprehensive documentation
        docstring = inspect.getdoc(get_db)

        if not docstring:
            return VerificationResult(
                "Database Transaction Docs", False, "get_db has no docstring"
            )

        required_keywords = [
            "TRANSACTION BOUNDARY",
            "Repository",
            "Service",
            "commit",
            "rollback",
        ]

        missing_keywords = [kw for kw in required_keywords if kw not in docstring]

        if missing_keywords:
            return VerificationResult(
                "Database Transaction Docs",
                False,
                f"Missing keywords in documentation: {', '.join(missing_keywords)}",
            )

        return VerificationResult(
            "Database Transaction Docs",
            True,
            "Comprehensive transaction boundary documentation present",
        )

    except Exception as e:
        return VerificationResult(
            "Database Transaction Docs", False, f"Error during verification: {str(e)}"
        )


async def verify_cache_key_collision():
    """Verify cache key collision prevention."""
    try:
        from core.cache_manager import MultiLevelCache
        import inspect

        # Check if _generate_cache_key_with_data method exists
        if not hasattr(MultiLevelCache, "_generate_cache_key_with_data"):
            return VerificationResult(
                "Cache Key Collision",
                False,
                "_generate_cache_key_with_data method not found",
            )

        # Check if _generate_key uses colon separator
        generate_key_source = inspect.getsource(MultiLevelCache._generate_key)
        if (
            "namespace}:{key}" not in generate_key_source
            and 'namespace":"' not in generate_key_source
        ):
            return VerificationResult(
                "Cache Key Collision",
                False,
                "Namespace separator not found in _generate_key",
            )

        return VerificationResult(
            "Cache Key Collision", True, "Cache key collision prevention implemented"
        )

    except Exception as e:
        return VerificationResult(
            "Cache Key Collision", False, f"Error during verification: {str(e)}"
        )


async def run_all_verifications() -> List[VerificationResult]:
    """Run all verification tests."""
    results = []

    logger.info("=" * 60)
    logger.info("Backend Critical Fixes - Priority 1 Verification")
    logger.info("=" * 60)
    logger.info("")

    # Run all tests
    tests = [
        ("Milvus Load Lock", verify_milvus_load_lock),
        ("LLM Timeout", verify_llm_timeout),
        ("Database Transaction Docs", verify_database_transaction_docs),
        ("Cache Key Collision", verify_cache_key_collision),
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
        logger.info("✅ All Priority 1 critical fixes verified successfully!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
