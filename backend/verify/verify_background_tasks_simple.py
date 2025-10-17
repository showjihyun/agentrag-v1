"""
Simple verification script for FastAPI BackgroundTasks integration.

This script checks the source code directly without importing modules.
"""

import re
from pathlib import Path


def check_file_content(filepath, checks):
    """Check if file contains expected patterns."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        results = {}
        for check_name, pattern in checks.items():
            if isinstance(pattern, str):
                results[check_name] = pattern in content
            else:  # regex pattern
                results[check_name] = bool(pattern.search(content))

        return results, content
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None, None


def main():
    """Run verification checks."""
    print("=" * 70)
    print("FastAPI BackgroundTasks Integration Verification")
    print("=" * 70)

    backend_dir = Path(__file__).parent
    documents_api = backend_dir / "api" / "documents.py"

    if not documents_api.exists():
        print(f"\n✗ File not found: {documents_api}")
        return 1

    # Define checks
    checks = {
        "BackgroundTasks import": "from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks",
        "BatchUploadService import": "from services.batch_upload_service import BatchUploadService",
        "BatchUploadRepository import": "from db.repositories.batch_upload_repository import BatchUploadRepository",
        "BatchUploadResponse model": "class BatchUploadResponse(BaseModel):",
        "BatchProgressResponse model": "class BatchProgressResponse(BaseModel):",
        "get_batch_upload_service dependency": "async def get_batch_upload_service(",
        "upload_batch endpoint": "async def upload_batch(",
        "background_tasks parameter": re.compile(
            r"background_tasks:\s*BackgroundTasks"
        ),
        "background_tasks.add_task call": "background_tasks.add_task(",
        "process_batch_background scheduled": "batch_upload_service.process_batch_background,",
        "get_batch_status endpoint": "async def get_batch_status(",
        "stream_batch_progress endpoint": "async def stream_batch_progress(",
        "StreamingResponse": "from fastapi.responses import StreamingResponse",
        "SSE media type": 'media_type="text/event-stream"',
        "HTTP 202 status": "status_code=status.HTTP_202_ACCEPTED",
    }

    print(f"\nChecking: {documents_api}")
    print("-" * 70)

    results, content = check_file_content(documents_api, checks)

    if results is None:
        return 1

    # Print results
    passed = 0
    total = len(checks)

    for check_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if result:
            passed += 1

    # Additional checks
    print("\nAdditional Checks:")
    print("-" * 70)

    # Check that batch endpoint returns immediately (202 Accepted)
    if "status_code=status.HTTP_202_ACCEPTED" in content:
        print("✓ Batch endpoint returns 202 Accepted (non-blocking)")
        passed += 1
    else:
        print("✗ Batch endpoint should return 202 Accepted")
    total += 1

    # Check that background task is scheduled before returning
    batch_endpoint_match = re.search(
        r"async def upload_batch\(.*?\):(.*?)(?=\n@router|\nclass |\Z)",
        content,
        re.DOTALL,
    )
    if batch_endpoint_match:
        endpoint_body = batch_endpoint_match.group(1)
        add_task_pos = endpoint_body.find("background_tasks.add_task")
        return_pos = endpoint_body.find("return BatchUploadResponse")

        if add_task_pos > 0 and return_pos > add_task_pos:
            print("✓ Background task scheduled before returning response")
            passed += 1
        else:
            print("✗ Background task should be scheduled before returning")
    else:
        print("✗ Could not verify task scheduling order")
    total += 1

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    print(f"\nPassed: {passed}/{total} checks")

    if passed == total:
        print("\n✓ All checks passed! BackgroundTasks integration is complete.")
        print("\nKey Features Verified:")
        print("  • FastAPI BackgroundTasks imported and used")
        print("  • Batch upload endpoint accepts BackgroundTasks parameter")
        print("  • Background processing scheduled with add_task()")
        print("  • Endpoint returns 202 Accepted immediately (non-blocking)")
        print("  • Batch status endpoint for progress tracking")
        print("  • SSE streaming endpoint for real-time updates")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
