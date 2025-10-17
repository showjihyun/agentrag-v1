"""
Simple verification script for authenticated document upload endpoint.

Checks the code structure without importing all dependencies.
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_file_content():
    """Verify the content of documents.py file."""
    logger.info("Verifying documents.py file content...")

    file_path = Path(__file__).parent / "api" / "documents.py"

    if not file_path.exists():
        logger.error(f"✗ File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Import get_current_user": "from core.auth_dependencies import get_current_user",
        "Import DocumentService": "from services.document_service import DocumentService",
        "Import User model": "from db.models.user import User",
        "get_document_service function": "async def get_document_service",
        "DocumentRepository in dependency": "DocumentRepository(db)",
        "UserRepository in dependency": "UserRepository(db)",
        "FileStorageService in dependency": "FileStorageService()",
        "current_user parameter": "current_user: User = Depends(get_current_user)",
        "document_service parameter": "document_service: DocumentService = Depends(get_document_service)",
        "Call upload_document": "document_service.upload_document",
        "Pass user_id": "user_id=current_user.id",
        "Handle DocumentServiceError": "DocumentServiceError",
        "Handle ValueError": "ValueError",
        "User metadata in response": '"user_id": str(current_user.id)',
    }

    results = []
    for check_name, check_string in checks.items():
        if check_string in content:
            logger.info(f"✓ {check_name}")
            results.append(True)
        else:
            logger.error(f"✗ {check_name} - not found: '{check_string}'")
            results.append(False)

    # Additional checks
    logger.info("\nAdditional checks:")

    # Check that old ingestion_service is not used in upload endpoint
    upload_start = content.find('@router.post("/upload"')
    if upload_start != -1:
        # Find the next endpoint or end of file
        next_endpoint = content.find("@router.", upload_start + 1)
        if next_endpoint == -1:
            next_endpoint = len(content)

        upload_endpoint = content[upload_start:next_endpoint]

        if "ingestion_service.ingest_document" in upload_endpoint:
            logger.warning(
                "⚠ Old ingestion_service.ingest_document still used in upload endpoint"
            )
            results.append(False)
        else:
            logger.info("✓ Old ingestion_service not used in upload endpoint")
            results.append(True)

        if "background" in upload_endpoint and "background: bool" in upload_endpoint:
            logger.warning("⚠ Old 'background' parameter still present")
        else:
            logger.info("✓ Old 'background' parameter removed")
            results.append(True)

    return all(results)


def verify_endpoint_structure():
    """Verify the structure of the upload endpoint."""
    logger.info("\nVerifying upload endpoint structure...")

    file_path = Path(__file__).parent / "api" / "documents.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find upload endpoint
    upload_start = content.find("async def upload_document(")
    if upload_start == -1:
        logger.error("✗ upload_document function not found")
        return False

    # Extract function signature (up to first colon after function def)
    sig_end = content.find("):", upload_start)
    if sig_end == -1:
        logger.error("✗ Could not find end of function signature")
        return False

    signature = content[upload_start : sig_end + 2]

    logger.info("Function signature found:")
    logger.info(signature[:200] + "..." if len(signature) > 200 else signature)

    # Check parameters
    required_params = [
        "file: UploadFile",
        "current_user: User",
        "document_service: DocumentService",
    ]

    results = []
    for param in required_params:
        if param in signature:
            logger.info(f"✓ Parameter present: {param}")
            results.append(True)
        else:
            logger.error(f"✗ Parameter missing: {param}")
            results.append(False)

    return all(results)


def main():
    """Run all verification checks."""
    logger.info("=" * 70)
    logger.info("Verifying Document Upload Endpoint with Authentication")
    logger.info("=" * 70)
    logger.info("")

    checks = [
        ("File Content", verify_file_content),
        ("Endpoint Structure", verify_endpoint_structure),
    ]

    results = []
    for check_name, check_func in checks:
        logger.info("")
        logger.info(f"Running: {check_name}")
        logger.info("-" * 70)
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"✗ {check_name} check failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((check_name, False))

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {check_name}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} checks passed")

    if passed == total:
        logger.info("")
        logger.info("✓ All checks passed!")
        logger.info("✓ Document upload endpoint is correctly updated to:")
        logger.info("  - Require authentication (get_current_user)")
        logger.info("  - Use DocumentService instead of DocumentIngestionService")
        logger.info("  - Pass user_id to service methods")
        return 0
    else:
        logger.error(
            f"\n✗ {total - passed} check(s) failed. Please review the implementation."
        )
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
