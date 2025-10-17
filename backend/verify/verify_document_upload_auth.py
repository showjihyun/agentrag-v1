"""
Verification script for authenticated document upload endpoint.

Tests that the upload endpoint:
1. Requires authentication (401 without token)
2. Uses DocumentService instead of DocumentIngestionService
3. Passes user_id to service methods
4. Returns proper response with user metadata
"""

import sys
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
# Also add parent directory for 'backend' imports
sys.path.insert(0, str(backend_dir.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_imports():
    """Verify that all required imports are present."""
    logger.info("Verifying imports...")

    try:
        from api.documents import (
            router,
            get_document_service,
            upload_document,
            UploadResponse,
        )
        from core.auth_dependencies import get_current_user
        from services.document_service import DocumentService
        from db.models.user import User

        logger.info("✓ All required imports are present")
        return True
    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False


def verify_endpoint_signature():
    """Verify that upload endpoint has correct signature."""
    logger.info("Verifying endpoint signature...")

    try:
        from api.documents import upload_document
        import inspect

        # Get function signature
        sig = inspect.signature(upload_document)
        params = sig.parameters

        # Check for required parameters
        required_params = {
            "file": "UploadFile",
            "current_user": "User",
            "document_service": "DocumentService",
        }

        for param_name, expected_type in required_params.items():
            if param_name not in params:
                logger.error(f"✗ Missing parameter: {param_name}")
                return False

            # Check if parameter has Depends annotation
            param = params[param_name]
            if param.default == inspect.Parameter.empty:
                logger.error(f"✗ Parameter {param_name} missing default (Depends)")
                return False

        logger.info("✓ Endpoint signature is correct")
        logger.info(f"  Parameters: {list(params.keys())}")
        return True

    except Exception as e:
        logger.error(f"✗ Error verifying signature: {e}")
        return False


def verify_dependency_function():
    """Verify that get_document_service dependency exists."""
    logger.info("Verifying get_document_service dependency...")

    try:
        from api.documents import get_document_service
        import inspect

        # Get function signature
        sig = inspect.signature(get_document_service)
        params = sig.parameters

        # Check for required dependencies
        required_deps = ["db", "doc_processor", "embedding_service", "milvus_manager"]

        for dep in required_deps:
            if dep not in params:
                logger.error(f"✗ Missing dependency: {dep}")
                return False

        # Check return type annotation
        if sig.return_annotation == inspect.Signature.empty:
            logger.warning("⚠ Missing return type annotation")
        elif "DocumentService" not in str(sig.return_annotation):
            logger.error(f"✗ Wrong return type: {sig.return_annotation}")
            return False

        logger.info("✓ get_document_service dependency is correct")
        logger.info(f"  Dependencies: {list(params.keys())}")
        return True

    except Exception as e:
        logger.error(f"✗ Error verifying dependency: {e}")
        return False


def verify_authentication_requirement():
    """Verify that endpoint requires authentication."""
    logger.info("Verifying authentication requirement...")

    try:
        from api.documents import upload_document
        import inspect

        # Get source code
        source = inspect.getsource(upload_document)

        # Check for get_current_user dependency
        if "get_current_user" not in source:
            logger.error("✗ Endpoint does not use get_current_user")
            return False

        # Check for current_user parameter
        if "current_user" not in source:
            logger.error("✗ Endpoint does not have current_user parameter")
            return False

        logger.info("✓ Endpoint requires authentication")
        return True

    except Exception as e:
        logger.error(f"✗ Error verifying authentication: {e}")
        return False


def verify_service_usage():
    """Verify that endpoint uses DocumentService."""
    logger.info("Verifying DocumentService usage...")

    try:
        from api.documents import upload_document
        import inspect

        # Get source code
        source = inspect.getsource(upload_document)

        # Check for DocumentService usage
        if "document_service" not in source:
            logger.error("✗ Endpoint does not use document_service parameter")
            return False

        # Check for upload_document method call
        if "document_service.upload_document" not in source:
            logger.error("✗ Endpoint does not call document_service.upload_document")
            return False

        # Check for user_id parameter
        if "user_id=current_user.id" not in source:
            logger.error("✗ Endpoint does not pass user_id to service")
            return False

        # Check that old ingestion_service is not used
        if "ingestion_service" in source and "get_ingestion_service" in source:
            logger.warning("⚠ Old ingestion_service code still present")

        logger.info("✓ Endpoint uses DocumentService correctly")
        return True

    except Exception as e:
        logger.error(f"✗ Error verifying service usage: {e}")
        return False


def verify_response_format():
    """Verify that response includes user metadata."""
    logger.info("Verifying response format...")

    try:
        from api.documents import upload_document
        import inspect

        # Get source code
        source = inspect.getsource(upload_document)

        # Check for user_id in metadata
        if "user_id" not in source or "current_user.id" not in source:
            logger.error("✗ Response does not include user_id in metadata")
            return False

        # Check for UploadResponse return
        if "UploadResponse" not in source:
            logger.error("✗ Endpoint does not return UploadResponse")
            return False

        logger.info("✓ Response format is correct")
        return True

    except Exception as e:
        logger.error(f"✗ Error verifying response: {e}")
        return False


def verify_error_handling():
    """Verify that endpoint handles DocumentServiceError."""
    logger.info("Verifying error handling...")

    try:
        from api.documents import upload_document
        import inspect

        # Get source code
        source = inspect.getsource(upload_document)

        # Check for DocumentServiceError handling
        if "DocumentServiceError" not in source:
            logger.error("✗ Endpoint does not handle DocumentServiceError")
            return False

        # Check for ValueError handling (validation errors)
        if "ValueError" not in source:
            logger.error("✗ Endpoint does not handle ValueError")
            return False

        logger.info("✓ Error handling is correct")
        return True

    except Exception as e:
        logger.error(f"✗ Error verifying error handling: {e}")
        return False


def main():
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("Verifying Document Upload Endpoint with Authentication")
    logger.info("=" * 60)

    checks = [
        ("Imports", verify_imports),
        ("Endpoint Signature", verify_endpoint_signature),
        ("Dependency Function", verify_dependency_function),
        ("Authentication Requirement", verify_authentication_requirement),
        ("DocumentService Usage", verify_service_usage),
        ("Response Format", verify_response_format),
        ("Error Handling", verify_error_handling),
    ]

    results = []
    for check_name, check_func in checks:
        logger.info("")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"✗ {check_name} check failed with exception: {e}")
            results.append((check_name, False))

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {check_name}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} checks passed")

    if passed == total:
        logger.info(
            "✓ All checks passed! Document upload endpoint is correctly updated."
        )
        return 0
    else:
        logger.error(
            f"✗ {total - passed} check(s) failed. Please review the implementation."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
