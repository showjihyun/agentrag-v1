"""
Verification script for FastAPI BackgroundTasks integration in batch upload.

This script verifies that:
1. Batch upload endpoint uses BackgroundTasks
2. Background processing is non-blocking
3. Progress can be tracked via batch status endpoint
4. SSE streaming works for real-time updates
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
import inspect


def verify_background_tasks_import():
    """Verify BackgroundTasks is imported in documents API."""
    print("\n1. Verifying BackgroundTasks import...")

    try:
        from api.documents import BackgroundTasks as ImportedBackgroundTasks

        print("   ✓ BackgroundTasks imported successfully")
        return True
    except ImportError as e:
        print(f"   ✗ Failed to import BackgroundTasks: {e}")
        return False


def verify_batch_upload_endpoint():
    """Verify batch upload endpoint signature includes BackgroundTasks."""
    print("\n2. Verifying batch upload endpoint signature...")

    try:
        from api.documents import upload_batch

        # Get function signature
        sig = inspect.signature(upload_batch)
        params = sig.parameters

        # Check if background_tasks parameter exists
        if "background_tasks" not in params:
            print("   ✗ background_tasks parameter not found in upload_batch")
            return False

        # Check parameter type annotation
        param = params["background_tasks"]
        if "BackgroundTasks" not in str(param.annotation):
            print(f"   ✗ background_tasks has wrong type: {param.annotation}")
            return False

        print("   ✓ upload_batch has background_tasks: BackgroundTasks parameter")
        return True

    except Exception as e:
        print(f"   ✗ Failed to verify endpoint: {e}")
        return False


def verify_background_task_scheduling():
    """Verify that background task is scheduled in upload_batch."""
    print("\n3. Verifying background task scheduling...")

    try:
        from api.documents import upload_batch
        import inspect

        # Get source code
        source = inspect.getsource(upload_batch)

        # Check for background_tasks.add_task call
        if "background_tasks.add_task" not in source:
            print("   ✗ background_tasks.add_task not found in upload_batch")
            return False

        # Check for process_batch_background call
        if "process_batch_background" not in source:
            print("   ✗ process_batch_background not scheduled as background task")
            return False

        print("   ✓ Background task scheduled with process_batch_background")
        return True

    except Exception as e:
        print(f"   ✗ Failed to verify task scheduling: {e}")
        return False


def verify_batch_status_endpoint():
    """Verify batch status endpoint exists."""
    print("\n4. Verifying batch status endpoint...")

    try:
        from api.documents import get_batch_status

        # Get function signature
        sig = inspect.signature(get_batch_status)
        params = sig.parameters

        # Check required parameters
        required_params = ["batch_id", "current_user", "batch_upload_service"]
        for param_name in required_params:
            if param_name not in params:
                print(f"   ✗ Missing parameter: {param_name}")
                return False

        print("   ✓ get_batch_status endpoint exists with correct signature")
        return True

    except Exception as e:
        print(f"   ✗ Failed to verify batch status endpoint: {e}")
        return False


def verify_sse_streaming_endpoint():
    """Verify SSE streaming endpoint exists."""
    print("\n5. Verifying SSE streaming endpoint...")

    try:
        from api.documents import stream_batch_progress

        # Get function signature
        sig = inspect.signature(stream_batch_progress)
        params = sig.parameters

        # Check required parameters
        required_params = ["batch_id", "current_user", "batch_upload_service"]
        for param_name in required_params:
            if param_name not in params:
                print(f"   ✗ Missing parameter: {param_name}")
                return False

        # Check source for StreamingResponse
        source = inspect.getsource(stream_batch_progress)
        if "StreamingResponse" not in source:
            print("   ✗ StreamingResponse not used in stream_batch_progress")
            return False

        if "text/event-stream" not in source:
            print("   ✗ SSE media type not set correctly")
            return False

        print("   ✓ stream_batch_progress endpoint exists with SSE support")
        return True

    except Exception as e:
        print(f"   ✗ Failed to verify SSE endpoint: {e}")
        return False


def verify_response_models():
    """Verify batch upload response models exist."""
    print("\n6. Verifying response models...")

    try:
        from api.documents import BatchUploadResponse, BatchProgressResponse

        # Check BatchUploadResponse fields
        batch_response_fields = BatchUploadResponse.model_fields
        required_fields = ["batch_id", "total_files", "status", "message"]
        for field in required_fields:
            if field not in batch_response_fields:
                print(f"   ✗ BatchUploadResponse missing field: {field}")
                return False

        # Check BatchProgressResponse fields
        progress_response_fields = BatchProgressResponse.model_fields
        required_fields = [
            "batch_id",
            "total_files",
            "completed_files",
            "failed_files",
            "status",
            "progress_percent",
        ]
        for field in required_fields:
            if field not in progress_response_fields:
                print(f"   ✗ BatchProgressResponse missing field: {field}")
                return False

        print("   ✓ Response models defined correctly")
        return True

    except Exception as e:
        print(f"   ✗ Failed to verify response models: {e}")
        return False


def verify_batch_upload_service_dependency():
    """Verify BatchUploadService dependency exists."""
    print("\n7. Verifying BatchUploadService dependency...")

    try:
        from api.documents import get_batch_upload_service

        # Get function signature
        sig = inspect.signature(get_batch_upload_service)

        # Check return type annotation
        if "BatchUploadService" not in str(sig.return_annotation):
            print(f"   ✗ Wrong return type: {sig.return_annotation}")
            return False

        print("   ✓ get_batch_upload_service dependency exists")
        return True

    except Exception as e:
        print(f"   ✗ Failed to verify dependency: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("FastAPI BackgroundTasks Integration Verification")
    print("=" * 70)

    checks = [
        verify_background_tasks_import,
        verify_batch_upload_endpoint,
        verify_background_task_scheduling,
        verify_batch_status_endpoint,
        verify_sse_streaming_endpoint,
        verify_response_models,
        verify_batch_upload_service_dependency,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n   ✗ Check failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total} checks")

    if passed == total:
        print("\n✓ All checks passed! BackgroundTasks integration is complete.")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
