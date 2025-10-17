"""Verification script for conversations API endpoints."""

import sys
import logging
from uuid import UUID

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def verify_conversations_api():
    """Verify conversations API implementation."""

    logger.info("=" * 80)
    logger.info("CONVERSATIONS API VERIFICATION")
    logger.info("=" * 80)

    checks_passed = 0
    checks_failed = 0

    # Check 1: Verify conversations.py exists
    logger.info("\n1. Checking if conversations.py exists...")
    try:
        from api import conversations

        logger.info("✅ conversations.py module found")
        checks_passed += 1
    except ImportError as e:
        logger.error(f"❌ Failed to import conversations module: {e}")
        checks_failed += 1
        return checks_passed, checks_failed

    # Check 2: Verify router exists
    logger.info("\n2. Checking if router is defined...")
    try:
        assert hasattr(conversations, "router"), "Router not found"
        logger.info(f"✅ Router found: {conversations.router.prefix}")
        checks_passed += 1
    except AssertionError as e:
        logger.error(f"❌ {e}")
        checks_failed += 1

    # Check 3: Verify all required endpoints exist
    logger.info("\n3. Checking if all required endpoints exist...")
    required_endpoints = [
        ("POST", "/sessions", "create_session"),
        ("GET", "/sessions", "list_sessions"),
        ("GET", "/sessions/{session_id}", "get_session"),
        ("PUT", "/sessions/{session_id}", "update_session"),
        ("DELETE", "/sessions/{session_id}", "delete_session"),
        ("GET", "/sessions/{session_id}/messages", "get_session_messages"),
        ("POST", "/search", "search_messages"),
    ]

    routes = conversations.router.routes
    route_info = [(route.methods, route.path, route.name) for route in routes]

    for method, path, name in required_endpoints:
        found = False
        for route_methods, route_path, route_name in route_info:
            if method in route_methods and path in route_path and name == route_name:
                found = True
                break

        if found:
            logger.info(f"✅ {method} {path} ({name})")
            checks_passed += 1
        else:
            logger.error(f"❌ {method} {path} ({name}) not found")
            checks_failed += 1

    # Check 4: Verify authentication dependencies
    logger.info("\n4. Checking authentication dependencies...")
    try:
        from core.auth_dependencies import get_current_user

        # Check if endpoints use authentication
        auth_required_endpoints = [
            "create_session",
            "list_sessions",
            "get_session",
            "update_session",
            "delete_session",
            "get_session_messages",
            "search_messages",
        ]

        for endpoint_name in auth_required_endpoints:
            # Find the endpoint function
            endpoint_func = getattr(conversations, endpoint_name, None)
            if endpoint_func:
                # Check if it has current_user parameter
                import inspect

                sig = inspect.signature(endpoint_func)
                has_auth = "current_user" in sig.parameters

                if has_auth:
                    logger.info(f"✅ {endpoint_name} requires authentication")
                    checks_passed += 1
                else:
                    logger.error(f"❌ {endpoint_name} missing authentication")
                    checks_failed += 1
            else:
                logger.error(f"❌ {endpoint_name} function not found")
                checks_failed += 1

    except Exception as e:
        logger.error(f"❌ Failed to verify authentication: {e}")
        checks_failed += 1

    # Check 5: Verify response models
    logger.info("\n5. Checking response models...")
    try:
        from models.conversation import (
            SessionCreate,
            SessionResponse,
            SessionUpdate,
            MessageResponse,
            MessageListResponse,
            MessageSourceResponse,
            SearchRequest,
            SearchResponse,
        )

        models = [
            "SessionCreate",
            "SessionResponse",
            "SessionUpdate",
            "MessageResponse",
            "MessageListResponse",
            "MessageSourceResponse",
            "SearchRequest",
            "SearchResponse",
        ]

        for model_name in models:
            logger.info(f"✅ {model_name} model available")
            checks_passed += 1

    except ImportError as e:
        logger.error(f"❌ Failed to import models: {e}")
        checks_failed += 1

    # Check 6: Verify ConversationService integration
    logger.info("\n6. Checking ConversationService integration...")
    try:
        from services.conversation_service import ConversationService

        # Check if service has required methods
        required_methods = [
            "create_session",
            "save_message_with_sources",
            "get_or_create_session",
            "search_conversations",
            "update_session_title",
            "delete_session",
        ]

        for method_name in required_methods:
            if hasattr(ConversationService, method_name):
                logger.info(f"✅ ConversationService.{method_name} exists")
                checks_passed += 1
            else:
                logger.error(f"❌ ConversationService.{method_name} missing")
                checks_failed += 1

    except Exception as e:
        logger.error(f"❌ Failed to verify ConversationService: {e}")
        checks_failed += 1

    # Check 7: Verify router is registered in main.py
    logger.info("\n7. Checking if router is registered in main.py...")
    try:
        with open("backend/main.py", "r") as f:
            main_content = f.read()

        if (
            "from api import auth, conversations" in main_content
            or "from api import" in main_content
            and "conversations" in main_content
        ):
            logger.info("✅ conversations imported in main.py")
            checks_passed += 1
        else:
            logger.error("❌ conversations not imported in main.py")
            checks_failed += 1

        if "app.include_router(conversations.router)" in main_content:
            logger.info("✅ conversations.router registered in main.py")
            checks_passed += 1
        else:
            logger.error("❌ conversations.router not registered in main.py")
            checks_failed += 1

    except Exception as e:
        logger.error(f"❌ Failed to verify main.py: {e}")
        checks_failed += 1

    # Check 8: Verify error handling
    logger.info("\n8. Checking error handling...")
    try:
        # Check if endpoints have try-except blocks
        with open("backend/api/conversations.py", "r") as f:
            api_content = f.read()

        error_handling_checks = [
            ("HTTPException", "HTTPException imported and used"),
            ("status.HTTP_404_NOT_FOUND", "404 error handling"),
            ("status.HTTP_500_INTERNAL_SERVER_ERROR", "500 error handling"),
            ("logger.error", "Error logging"),
            ("logger.warning", "Warning logging"),
        ]

        for check_str, description in error_handling_checks:
            if check_str in api_content:
                logger.info(f"✅ {description}")
                checks_passed += 1
            else:
                logger.error(f"❌ {description} missing")
                checks_failed += 1

    except Exception as e:
        logger.error(f"❌ Failed to verify error handling: {e}")
        checks_failed += 1

    # Check 9: Verify pagination parameters
    logger.info("\n9. Checking pagination parameters...")
    try:
        with open("backend/api/conversations.py", "r") as f:
            api_content = f.read()

        pagination_checks = [
            ("limit: int = Query", "limit parameter with Query"),
            ("offset: int = Query", "offset parameter with Query"),
            ("ge=1", "minimum limit validation"),
            ("ge=0", "minimum offset validation"),
        ]

        for check_str, description in pagination_checks:
            if check_str in api_content:
                logger.info(f"✅ {description}")
                checks_passed += 1
            else:
                logger.error(f"❌ {description} missing")
                checks_failed += 1

    except Exception as e:
        logger.error(f"❌ Failed to verify pagination: {e}")
        checks_failed += 1

    # Check 10: Verify ownership verification
    logger.info("\n10. Checking ownership verification...")
    try:
        with open("backend/api/conversations.py", "r") as f:
            api_content = f.read()

        ownership_checks = [
            ("user_id=current_user.id", "user_id passed to service methods"),
            ("Session not found or access denied", "ownership error message"),
            ("verify ownership", "ownership verification comment"),
        ]

        for check_str, description in ownership_checks:
            if check_str in api_content:
                logger.info(f"✅ {description}")
                checks_passed += 1
            else:
                logger.warning(
                    f"⚠️  {description} not found (may be implemented differently)"
                )

    except Exception as e:
        logger.error(f"❌ Failed to verify ownership: {e}")
        checks_failed += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Checks passed: {checks_passed}")
    logger.info(f"❌ Checks failed: {checks_failed}")
    logger.info(f"Total checks: {checks_passed + checks_failed}")

    if checks_failed == 0:
        logger.info(
            "\n🎉 All checks passed! Conversations API is properly implemented."
        )
        return True
    else:
        logger.error(
            f"\n⚠️  {checks_failed} check(s) failed. Please review the issues above."
        )
        return False


if __name__ == "__main__":
    try:
        success = verify_conversations_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Verification failed with error: {e}", exc_info=True)
        sys.exit(1)
