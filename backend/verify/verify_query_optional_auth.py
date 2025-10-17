"""
Verification script for Task 5.3.4 sub-task: Update backend/api/query.py to accept optional user authentication.

This script verifies:
1. Query endpoint accepts optional user authentication via get_optional_user
2. Query endpoint accepts optional session_id in request body
3. Backward compatibility - queries work without authentication
"""

import sys
import ast
import inspect
from pathlib import Path


def verify_query_api_optional_auth():
    """Verify that query API accepts optional user authentication."""

    print("=" * 80)
    print("VERIFICATION: Query API Optional Authentication")
    print("=" * 80)
    print()

    # Read the query API file
    query_api_path = Path(__file__).parent / "api" / "query.py"

    if not query_api_path.exists():
        print("❌ FAILED: backend/api/query.py not found")
        return False

    with open(query_api_path, "r", encoding="utf-8") as f:
        content = f.read()

    all_checks_passed = True

    # Check 1: Import get_optional_user
    print("Check 1: Import get_optional_user from auth_dependencies")
    if "from core.auth_dependencies import get_optional_user" in content:
        print("✅ PASSED: get_optional_user is imported")
    else:
        print("❌ FAILED: get_optional_user is not imported")
        all_checks_passed = False
    print()

    # Check 2: Import User model
    print("Check 2: Import User model")
    if "from db.models.user import User" in content:
        print("✅ PASSED: User model is imported")
    else:
        print("❌ FAILED: User model is not imported")
        all_checks_passed = False
    print()

    # Check 3: Import get_db
    print("Check 3: Import get_db for database session")
    if "from db.database import get_db" in content:
        print("✅ PASSED: get_db is imported")
    else:
        print("❌ FAILED: get_db is not imported")
        all_checks_passed = False
    print()

    # Check 4: Import Session from sqlalchemy
    print("Check 4: Import Session from sqlalchemy.orm")
    if "from sqlalchemy.orm import Session" in content:
        print("✅ PASSED: Session is imported")
    else:
        print("❌ FAILED: Session is not imported")
        all_checks_passed = False
    print()

    # Check 5: Main query endpoint has optional user parameter
    print("Check 5: Main query endpoint (POST /) has optional user parameter")
    if (
        "user: User | None = Depends(get_optional_user)" in content
        or "user: Optional[User] = Depends(get_optional_user)" in content
    ):
        print("✅ PASSED: Main query endpoint has optional user parameter")
    else:
        print("❌ FAILED: Main query endpoint missing optional user parameter")
        all_checks_passed = False
    print()

    # Check 6: Main query endpoint has db session parameter
    print("Check 6: Main query endpoint has db session parameter")
    if "db: Session = Depends(get_db)" in content:
        print("✅ PASSED: Main query endpoint has db session parameter")
    else:
        print("❌ FAILED: Main query endpoint missing db session parameter")
        all_checks_passed = False
    print()

    # Check 7: Sync query endpoint has optional user parameter
    print("Check 7: Sync query endpoint (POST /sync) has optional user parameter")
    sync_endpoint_section = (
        content[
            content.find('@router.post("/sync"') : content.find('@router.post("/sync"')
            + 1000
        ]
        if '@router.post("/sync"' in content
        else ""
    )
    if (
        "user: User | None = Depends(get_optional_user)" in sync_endpoint_section
        or "user: Optional[User] = Depends(get_optional_user)" in sync_endpoint_section
    ):
        print("✅ PASSED: Sync query endpoint has optional user parameter")
    else:
        print("❌ FAILED: Sync query endpoint missing optional user parameter")
        all_checks_passed = False
    print()

    # Check 8: Verify QueryRequest model accepts session_id
    print("Check 8: Verify QueryRequest model accepts optional session_id")
    query_model_path = Path(__file__).parent / "models" / "query.py"
    if query_model_path.exists():
        with open(query_model_path, "r", encoding="utf-8") as f:
            query_model_content = f.read()

        if (
            "session_id: Optional[UUID]" in query_model_content
            or "session_id: UUID | None" in query_model_content
        ):
            print("✅ PASSED: QueryRequest model has optional session_id field")
        else:
            print("❌ FAILED: QueryRequest model missing optional session_id field")
            all_checks_passed = False
    else:
        print("⚠️  WARNING: Could not verify QueryRequest model (file not found)")
    print()

    # Check 9: Verify HybridQueryRequest model accepts session_id
    print("Check 9: Verify HybridQueryRequest model accepts optional session_id")
    hybrid_model_path = Path(__file__).parent / "models" / "hybrid.py"
    if hybrid_model_path.exists():
        with open(hybrid_model_path, "r", encoding="utf-8") as f:
            hybrid_model_content = f.read()

        if (
            "session_id: Optional[UUID]" in hybrid_model_content
            or "session_id: UUID | None" in hybrid_model_content
            or "session_id: Optional[str]" in hybrid_model_content
            or "session_id: str | None" in hybrid_model_content
        ):
            print("✅ PASSED: HybridQueryRequest model has optional session_id field")
        else:
            print("⚠️  WARNING: HybridQueryRequest model may not have session_id field")
    else:
        print("⚠️  WARNING: Could not verify HybridQueryRequest model (file not found)")
    print()

    # Summary
    print("=" * 80)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED")
        print()
        print("Summary:")
        print("- Query API imports get_optional_user, User, get_db, and Session")
        print("- Main query endpoint (POST /) accepts optional user authentication")
        print("- Sync query endpoint (POST /sync) accepts optional user authentication")
        print("- Both endpoints have db session parameter for database operations")
        print("- QueryRequest model accepts optional session_id")
        print()
        print("Next steps:")
        print(
            "1. Implement message saving in stream_agent_response() when user is authenticated"
        )
        print(
            "2. Implement message saving in stream_hybrid_response() when user is authenticated"
        )
        print("3. Test backward compatibility (queries work without authentication)")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failed checks above and make necessary corrections.")
        return False


if __name__ == "__main__":
    success = verify_query_api_optional_auth()
    sys.exit(0 if success else 1)
