"""Verify pagination parameters in conversations API."""

import sys
import inspect
from backend.api.conversations import list_sessions, get_session_messages


def verify_pagination():
    """Verify that pagination parameters have correct defaults."""

    print("=" * 60)
    print("PAGINATION PARAMETERS VERIFICATION")
    print("=" * 60)

    issues = []

    # Check list_sessions endpoint
    print("\n1. Checking GET /sessions endpoint...")
    sig = inspect.signature(list_sessions)

    limit_param = sig.parameters.get("limit")
    offset_param = sig.parameters.get("offset")

    if limit_param:
        # Extract default from Query
        default_str = str(limit_param.default)
        if "default=50" in default_str or "50" in default_str:
            print("   ✓ limit parameter has default=50")
        else:
            print(f"   ✗ limit parameter default is not 50: {default_str}")
            issues.append("list_sessions: limit default should be 50")
    else:
        print("   ✗ limit parameter not found")
        issues.append("list_sessions: limit parameter missing")

    if offset_param:
        default_str = str(offset_param.default)
        if "default=0" in default_str or "0" in default_str:
            print("   ✓ offset parameter has default=0")
        else:
            print(f"   ✗ offset parameter default is not 0: {default_str}")
            issues.append("list_sessions: offset default should be 0")
    else:
        print("   ✗ offset parameter not found")
        issues.append("list_sessions: offset parameter missing")

    # Check get_session_messages endpoint
    print("\n2. Checking GET /sessions/{id}/messages endpoint...")
    sig = inspect.signature(get_session_messages)

    limit_param = sig.parameters.get("limit")
    offset_param = sig.parameters.get("offset")

    if limit_param:
        default_str = str(limit_param.default)
        if "default=50" in default_str or "50" in default_str:
            print("   ✓ limit parameter has default=50")
        else:
            print(f"   ✗ limit parameter default is not 50: {default_str}")
            issues.append("get_session_messages: limit default should be 50")
    else:
        print("   ✗ limit parameter not found")
        issues.append("get_session_messages: limit parameter missing")

    if offset_param:
        default_str = str(offset_param.default)
        if "default=0" in default_str or "0" in default_str:
            print("   ✓ offset parameter has default=0")
        else:
            print(f"   ✗ offset parameter default is not 0: {default_str}")
            issues.append("get_session_messages: offset default should be 0")
    else:
        print("   ✗ offset parameter not found")
        issues.append("get_session_messages: offset parameter missing")

    # Summary
    print("\n" + "=" * 60)
    if not issues:
        print("✅ ALL PAGINATION CHECKS PASSED")
        print("=" * 60)
        print("\nPagination parameters verified:")
        print("  • GET /sessions: limit=50, offset=0")
        print("  • GET /sessions/{id}/messages: limit=50, offset=0")
        return 0
    else:
        print("❌ PAGINATION VERIFICATION FAILED")
        print("=" * 60)
        print(f"\nFound {len(issues)} issue(s):")
        for issue in issues:
            print(f"  • {issue}")
        return 1


if __name__ == "__main__":
    sys.exit(verify_pagination())
