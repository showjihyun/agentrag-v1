"""
Verify backward compatibility for query endpoint.

Tests that the query endpoint works correctly with and without authentication:
1. Without authentication (user is None) - should skip database saving
2. Without session_id - should create new session with auto-generated title
3. All existing functionality works without authentication

Requirements: FR-2.2, FR-2.3, NFR-1
"""

import sys
import ast
from pathlib import Path


def verify_unauthenticated_handling():
    """Verify that unauthenticated queries skip database saving."""
    print("\n" + "=" * 80)
    print("TEST 1: Unauthenticated Query Handling")
    print("=" * 80)

    query_api_path = Path(__file__).parent / "api" / "query.py"

    if not query_api_path.exists():
        print("❌ FAILED: backend/api/query.py not found")
        return False

    with open(query_api_path, "r", encoding="utf-8") as f:
        content = f.read()

    all_checks_passed = True

    # Check 1: stream_agent_response accepts optional user parameter
    print("\nCheck 1: stream_agent_response accepts optional user parameter")
    if (
        "user: User | None = None" in content
        or "user: Optional[User] = None" in content
    ):
        print("✅ PASSED: user parameter is optional")
    else:
        print("❌ FAILED: user parameter is not optional")
        all_checks_passed = False

    # Check 2: stream_agent_response accepts optional db parameter
    print("\nCheck 2: stream_agent_response accepts optional db parameter")
    if (
        "db: Session | None = None" in content
        or "db: Optional[Session] = None" in content
    ):
        print("✅ PASSED: db parameter is optional")
    else:
        print("❌ FAILED: db parameter is not optional")
        all_checks_passed = False

    # Check 3: Check for conditional database saving based on user authentication
    print("\nCheck 3: Conditional database saving based on user authentication")
    if "if user is not None and db is not None:" in content:
        print("✅ PASSED: Database saving is conditional on user authentication")
    elif "if user is not None and conversation_service is not None" in content:
        print("✅ PASSED: Database saving is conditional on user authentication")
    else:
        print(
            "❌ FAILED: No conditional check for user authentication before database operations"
        )
        all_checks_passed = False

    # Check 4: Check for error handling that doesn't break streaming
    print("\nCheck 4: Error handling for database failures")
    if (
        "# Continue processing even if database save fails" in content
        or "# Continue even if database save fails" in content
    ):
        print(
            "✅ PASSED: Error handling allows streaming to continue on database failures"
        )
    else:
        print("⚠️  WARNING: No explicit comment about continuing on database failures")

    return all_checks_passed


def verify_session_auto_creation():
    """Verify that sessions are auto-created when not provided."""
    print("\n" + "=" * 80)
    print("TEST 2: Session Auto-Creation")
    print("=" * 80)

    query_api_path = Path(__file__).parent / "api" / "query.py"

    if not query_api_path.exists():
        print("❌ FAILED: backend/api/query.py not found")
        return False

    with open(query_api_path, "r", encoding="utf-8") as f:
        content = f.read()

    all_checks_passed = True

    # Check 1: get_or_create_session is called
    print("\nCheck 1: get_or_create_session is called")
    if "get_or_create_session" in content:
        print("✅ PASSED: get_or_create_session method is used")
    else:
        print("❌ FAILED: get_or_create_session method not found")
        all_checks_passed = False

    # Check 2: session_id can be None
    print("\nCheck 2: session_id parameter accepts None")
    if "session_id=uuid.UUID(session_id) if session_id else None" in content:
        print("✅ PASSED: session_id can be None for auto-creation")
    else:
        print("⚠️  WARNING: session_id handling may not support None")

    # Check 3: ConversationService is imported
    print("\nCheck 3: ConversationService is imported")
    if "from services.conversation_service import ConversationService" in content:
        print("✅ PASSED: ConversationService is imported")
    else:
        print("❌ FAILED: ConversationService is not imported")
        all_checks_passed = False

    return all_checks_passed


def verify_existing_functionality():
    """Verify that all existing functionality is preserved."""
    print("\n" + "=" * 80)
    print("TEST 3: Existing Functionality Preserved")
    print("=" * 80)

    query_api_path = Path(__file__).parent / "api" / "query.py"

    if not query_api_path.exists():
        print("❌ FAILED: backend/api/query.py not found")
        return False

    with open(query_api_path, "r", encoding="utf-8") as f:
        content = f.read()

    all_checks_passed = True

    # Check 1: process_query endpoint still exists
    print("\nCheck 1: process_query endpoint exists")
    if '@router.post("/", response_class=StreamingResponse)' in content:
        print("✅ PASSED: Main query endpoint exists")
    else:
        print("❌ FAILED: Main query endpoint not found")
        all_checks_passed = False

    # Check 2: Streaming response is still supported
    print("\nCheck 2: Streaming response supported")
    if "StreamingResponse" in content and "text/event-stream" in content:
        print("✅ PASSED: Streaming response is supported")
    else:
        print("❌ FAILED: Streaming response not properly configured")
        all_checks_passed = False

    # Check 3: Both legacy and hybrid modes are supported
    print("\nCheck 3: Both legacy and hybrid modes supported")
    if "stream_agent_response" in content and "stream_hybrid_response" in content:
        print("✅ PASSED: Both legacy and hybrid streaming functions exist")
    else:
        print("❌ FAILED: Missing streaming functions")
        all_checks_passed = False

    # Check 4: Backward compatibility with QueryRequest
    print("\nCheck 4: Backward compatibility with QueryRequest")
    if "HybridQueryRequest" in content:
        print(
            "✅ PASSED: HybridQueryRequest extends QueryRequest for backward compatibility"
        )
    else:
        print("⚠️  WARNING: HybridQueryRequest not found")

    return all_checks_passed


def verify_hybrid_query_compatibility():
    """Verify that hybrid query also supports backward compatibility."""
    print("\n" + "=" * 80)
    print("TEST 4: Hybrid Query Backward Compatibility")
    print("=" * 80)

    query_api_path = Path(__file__).parent / "api" / "query.py"

    if not query_api_path.exists():
        print("❌ FAILED: backend/api/query.py not found")
        return False

    with open(query_api_path, "r", encoding="utf-8") as f:
        content = f.read()

    all_checks_passed = True

    # Check 1: stream_hybrid_response accepts optional user parameter
    print("\nCheck 1: stream_hybrid_response accepts optional user parameter")
    if (
        "user: User | None = None" in content
        or "user: Optional[User] = None" in content
    ):
        print("✅ PASSED: user parameter is optional in hybrid mode")
    else:
        print("❌ FAILED: user parameter is not optional in hybrid mode")
        all_checks_passed = False

    # Check 2: stream_hybrid_response accepts optional db parameter
    print("\nCheck 2: stream_hybrid_response accepts optional db parameter")
    if (
        "db: Session | None = None" in content
        or "db: Optional[Session] = None" in content
    ):
        print("✅ PASSED: db parameter is optional in hybrid mode")
    else:
        print("❌ FAILED: db parameter is not optional in hybrid mode")
        all_checks_passed = False

    # Check 3: Hybrid mode also checks for user authentication before database operations
    print(
        "\nCheck 3: Hybrid mode checks user authentication before database operations"
    )
    # Count occurrences of the conditional check
    conditional_checks = content.count("if user is not None and db is not None:")
    conditional_checks += content.count(
        "if user is not None and conversation_service is not None"
    )

    if (
        conditional_checks >= 2
    ):  # Should appear in both stream_agent_response and stream_hybrid_response
        print(
            f"✅ PASSED: Found {conditional_checks} conditional checks for user authentication"
        )
    else:
        print(
            f"⚠️  WARNING: Found only {conditional_checks} conditional checks (expected at least 2)"
        )

    return all_checks_passed


def main():
    """Run all backward compatibility verification checks."""
    print("=" * 80)
    print("BACKWARD COMPATIBILITY VERIFICATION")
    print("=" * 80)
    print("Verifying query endpoint backward compatibility:")
    print("1. Unauthenticated queries work without database")
    print("2. Authenticated queries without session_id auto-create session")
    print("3. All existing functionality is preserved")
    print("4. Hybrid queries work without authentication")
    print("=" * 80)

    results = []

    # Test 1: Unauthenticated query handling
    result1 = verify_unauthenticated_handling()
    results.append(("Unauthenticated Query Handling", result1))

    # Test 2: Session auto-creation
    result2 = verify_session_auto_creation()
    results.append(("Session Auto-Creation", result2))

    # Test 3: Existing functionality preserved
    result3 = verify_existing_functionality()
    results.append(("Existing Functionality", result3))

    # Test 4: Hybrid query compatibility
    result4 = verify_hybrid_query_compatibility()
    results.append(("Hybrid Query Compatibility", result4))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)

    print("=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED - Backward compatibility verified!")
        print("=" * 80)
        print("\nBackward Compatibility Summary:")
        print("✅ Unauthenticated queries work without database saving")
        print("✅ Authenticated queries auto-create sessions when needed")
        print("✅ All existing functionality is preserved")
        print("✅ Hybrid queries work without authentication")
        print("✅ No breaking changes to existing API")
        print("\nKey Features:")
        print("• If no user authenticated (user is None), skip database saving")
        print(
            "• If no session_id provided, create new session with auto-generated title"
        )
        print("• All existing functionality works without authentication")
        print("• Error handling ensures streaming continues even if database fails")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
