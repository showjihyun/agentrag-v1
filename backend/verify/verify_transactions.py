#!/usr/bin/env python3
"""Verify database transactions in ConversationService."""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
import logging

import sys

sys.path.insert(0, "backend")

from config import settings
from backend.db.models.user import User
from backend.db.models.conversation import Session, Message, MessageSource
from backend.db.repositories.user_repository import UserRepository
from backend.services.conversation_service import ConversationService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_transaction_commit():
    """Test that successful operations are committed."""
    print("\n[1/4] Testing transaction commit...")

    db = SessionLocal()
    try:
        # Create test user
        user_repo = UserRepository(db)
        user = user_repo.create_user(
            email=f"test_commit_{uuid4()}@example.com",
            username=f"test_commit_{uuid4()}",
            password="test_password123",
        )
        db.commit()

        # Create conversation service
        conv_service = ConversationService(db)

        # Create session
        session = conv_service.create_session(user_id=user.id, title="Test Session")

        # Store IDs before closing session
        session_id = session.id
        user_id = user.id

        # Verify session was committed
        db.close()
        db = SessionLocal()

        from db.repositories.session_repository import SessionRepository

        session_repo = SessionRepository(db)
        retrieved_session = session_repo.get_session_by_id(session_id, user_id)

        assert retrieved_session is not None, "Session should be committed"
        assert retrieved_session.title == "Test Session", "Session title should match"

        print("✅ Transaction commit works correctly")
        return True

    except Exception as e:
        print(f"❌ Transaction commit test failed: {e}")
        return False
    finally:
        db.close()


def test_transaction_rollback():
    """Test that failed operations are rolled back."""
    print("\n[2/4] Testing transaction rollback...")

    db = SessionLocal()
    try:
        # Create test user
        user_repo = UserRepository(db)
        user = user_repo.create_user(
            email=f"test_rollback_{uuid4()}@example.com",
            username=f"test_rollback_{uuid4()}",
            password="test_password123",
        )
        db.commit()

        # Create conversation service
        conv_service = ConversationService(db)

        # Create session
        session = conv_service.create_session(user_id=user.id, title="Test Session")

        # Try to save message with invalid session_id (should fail and rollback)
        try:
            invalid_session_id = uuid4()
            conv_service.save_message_with_sources(
                session_id=invalid_session_id,  # Invalid session
                user_id=user.id,
                role="user",
                content="This should fail",
            )
            print("❌ Expected exception was not raised")
            return False
        except Exception:
            # Expected to fail
            pass

        # Store IDs before closing session
        session_id = session.id
        user_id = user.id

        # Verify original session still exists (rollback didn't affect it)
        db.close()
        db = SessionLocal()

        from db.repositories.session_repository import SessionRepository

        session_repo = SessionRepository(db)
        retrieved_session = session_repo.get_session_by_id(session_id, user_id)

        assert retrieved_session is not None, "Original session should still exist"

        print("✅ Transaction rollback works correctly")
        return True

    except Exception as e:
        print(f"❌ Transaction rollback test failed: {e}")
        return False
    finally:
        db.close()


def test_atomic_message_save():
    """Test that message + sources are saved atomically."""
    print("\n[3/4] Testing atomic message save...")

    db = SessionLocal()
    try:
        # Create test user
        user_repo = UserRepository(db)
        user = user_repo.create_user(
            email=f"test_atomic_{uuid4()}@example.com",
            username=f"test_atomic_{uuid4()}",
            password="test_password123",
        )
        db.commit()

        # Create conversation service
        conv_service = ConversationService(db)

        # Create session
        session = conv_service.create_session(user_id=user.id, title="Test Session")

        # Save message with sources
        sources = [
            {
                "document_id": str(uuid4()),
                "document_name": "test_doc.pdf",
                "chunk_id": "chunk_1",
                "score": 0.95,
                "text": "Test content",
            },
            {
                "document_id": str(uuid4()),
                "document_name": "test_doc2.pdf",
                "chunk_id": "chunk_2",
                "score": 0.85,
                "text": "More test content",
            },
        ]

        message = conv_service.save_message_with_sources(
            session_id=session.id,
            user_id=user.id,
            role="user",
            content="Test message",
            sources=sources,
            metadata={"query_mode": "balanced", "tokens_used": 100},
        )

        # Store IDs before closing session
        message_id = message.id
        session_id = session.id
        user_id = user.id

        # Verify message and sources were saved atomically
        db.close()
        db = SessionLocal()

        from db.repositories.message_repository import MessageRepository
        from db.repositories.message_source_repository import MessageSourceRepository

        message_repo = MessageRepository(db)
        source_repo = MessageSourceRepository(db)

        retrieved_message = message_repo.get_message_by_id(message_id)
        assert retrieved_message is not None, "Message should be saved"

        retrieved_sources = source_repo.get_message_sources(message_id)
        assert len(retrieved_sources) == 2, "Both sources should be saved"

        # Verify session stats were updated
        from db.repositories.session_repository import SessionRepository

        session_repo = SessionRepository(db)
        updated_session = session_repo.get_session_by_id(session_id, user_id)

        assert updated_session.message_count == 1, "Message count should be updated"
        assert updated_session.total_tokens == 100, "Token count should be updated"

        print("✅ Atomic message save works correctly")
        return True

    except Exception as e:
        print(f"❌ Atomic message save test failed: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def test_auto_title_generation():
    """Test that auto-title generation works in transaction."""
    print("\n[4/4] Testing auto-title generation in transaction...")

    db = SessionLocal()
    try:
        # Create test user
        user_repo = UserRepository(db)
        user = user_repo.create_user(
            email=f"test_title_{uuid4()}@example.com",
            username=f"test_title_{uuid4()}",
            password="test_password123",
        )
        db.commit()

        # Create conversation service
        conv_service = ConversationService(db)

        # Create session without title
        session = conv_service.create_session(user_id=user.id, title=None)

        assert session.title is None, "Session should have no title initially"

        # Store IDs before saving message
        session_id = session.id
        user_id = user.id

        # Save first user message (should auto-generate title)
        message = conv_service.save_message_with_sources(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content="What is the meaning of life, the universe, and everything?",
        )

        # Verify title was auto-generated
        db.close()
        db = SessionLocal()

        from db.repositories.session_repository import SessionRepository

        session_repo = SessionRepository(db)
        updated_session = session_repo.get_session_by_id(session_id, user_id)

        assert updated_session.title is not None, "Title should be auto-generated"
        assert (
            "meaning of life" in updated_session.title.lower()
        ), "Title should contain message content"

        print("✅ Auto-title generation works correctly")
        return True

    except Exception as e:
        print(f"❌ Auto-title generation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run all transaction tests."""
    print("=" * 60)
    print("Database Transaction Verification")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Transaction Commit", test_transaction_commit()))
    results.append(("Transaction Rollback", test_transaction_rollback()))
    results.append(("Atomic Message Save", test_atomic_message_save()))
    results.append(("Auto-Title Generation", test_auto_title_generation()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All transaction tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
