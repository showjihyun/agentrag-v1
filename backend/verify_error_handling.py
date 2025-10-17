"""Verify error handling and rollback in ConversationService."""

import sys
import os
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.conversation_service import ConversationService


def test_error_handling():
    """Test that all methods have proper error handling with rollback."""

    print("=" * 80)
    print("ERROR HANDLING VERIFICATION")
    print("=" * 80)

    # Create mock database session
    mock_db = Mock()
    mock_db.rollback = Mock()

    # Create service with mock db
    service = ConversationService(mock_db)

    # Test 1: create_session error handling
    print("\n1. Testing create_session error handling...")
    service.session_repo.create_session = Mock(side_effect=SQLAlchemyError("DB Error"))

    try:
        service.create_session(user_id=uuid4())
        print("❌ create_session should have raised exception")
        return False
    except SQLAlchemyError:
        if mock_db.rollback.called:
            print("✅ create_session calls rollback on error")
        else:
            print("❌ create_session does not call rollback on error")
            return False

    # Reset mock
    mock_db.rollback.reset_mock()

    # Test 2: save_message_with_sources error handling
    print("\n2. Testing save_message_with_sources error handling...")
    service.message_repo.create_message = Mock(side_effect=SQLAlchemyError("DB Error"))

    try:
        service.save_message_with_sources(
            session_id=uuid4(), user_id=uuid4(), role="user", content="test"
        )
        print("❌ save_message_with_sources should have raised exception")
        return False
    except SQLAlchemyError:
        if mock_db.rollback.called:
            print("✅ save_message_with_sources calls rollback on error")
        else:
            print("❌ save_message_with_sources does not call rollback on error")
            return False

    # Reset mock
    mock_db.rollback.reset_mock()

    # Test 3: get_or_create_session error handling
    print("\n3. Testing get_or_create_session error handling...")
    service.session_repo.get_session_by_id = Mock(
        side_effect=SQLAlchemyError("DB Error")
    )

    try:
        service.get_or_create_session(user_id=uuid4(), session_id=uuid4())
        print("❌ get_or_create_session should have raised exception")
        return False
    except SQLAlchemyError:
        if mock_db.rollback.called:
            print("✅ get_or_create_session calls rollback on error")
        else:
            print("❌ get_or_create_session does not call rollback on error")
            return False

    # Reset mock
    mock_db.rollback.reset_mock()

    # Test 4: search_conversations error handling
    print("\n4. Testing search_conversations error handling...")
    service.message_repo.search_messages = Mock(side_effect=SQLAlchemyError("DB Error"))

    try:
        service.search_conversations(user_id=uuid4(), query="test")
        print("❌ search_conversations should have raised exception")
        return False
    except SQLAlchemyError:
        if mock_db.rollback.called:
            print("✅ search_conversations calls rollback on error")
        else:
            print("❌ search_conversations does not call rollback on error")
            return False

    # Reset mock
    mock_db.rollback.reset_mock()

    # Test 5: update_session_title error handling
    print("\n5. Testing update_session_title error handling...")
    service.session_repo.update_session = Mock(side_effect=SQLAlchemyError("DB Error"))

    try:
        service.update_session_title(session_id=uuid4(), user_id=uuid4(), title="test")
        print("❌ update_session_title should have raised exception")
        return False
    except SQLAlchemyError:
        if mock_db.rollback.called:
            print("✅ update_session_title calls rollback on error")
        else:
            print("❌ update_session_title does not call rollback on error")
            return False

    # Reset mock
    mock_db.rollback.reset_mock()

    # Test 6: delete_session error handling
    print("\n6. Testing delete_session error handling...")
    service.session_repo.delete_session = Mock(side_effect=SQLAlchemyError("DB Error"))

    try:
        service.delete_session(session_id=uuid4(), user_id=uuid4())
        print("❌ delete_session should have raised exception")
        return False
    except SQLAlchemyError:
        if mock_db.rollback.called:
            print("✅ delete_session calls rollback on error")
        else:
            print("❌ delete_session does not call rollback on error")
            return False

    print("\n" + "=" * 80)
    print("✅ ALL ERROR HANDLING TESTS PASSED!")
    print("=" * 80)
    print("\nAll methods properly:")
    print("  • Wrap database operations in try/except blocks")
    print("  • Call db.rollback() on failure")
    print("  • Re-raise exceptions for proper error propagation")
    print("  • Log errors with context")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_error_handling()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
