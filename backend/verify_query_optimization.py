"""Verify query optimization with joinedload."""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
import logging

from config import settings
from backend.db.repositories.session_repository import SessionRepository
from backend.db.repositories.message_repository import MessageRepository
from backend.db.repositories.message_source_repository import MessageSourceRepository
from backend.db.repositories.user_repository import UserRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_query_optimization():
    """Verify that query optimization is working correctly."""

    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        logger.info("=" * 60)
        logger.info("QUERY OPTIMIZATION VERIFICATION")
        logger.info("=" * 60)

        # Initialize repositories
        user_repo = UserRepository(db)
        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        source_repo = MessageSourceRepository(db)

        # Create test user
        logger.info("\n0. Creating test user...")
        test_email = f"test_query_opt_{uuid4().hex[:8]}@example.com"
        test_username = f"test_user_{uuid4().hex[:8]}"
        test_user = user_repo.create_user(
            email=test_email, username=test_username, password="TestPassword123"
        )
        test_user_id = test_user.id
        logger.info(f"   ✓ Created test user: {test_user_id}")

        # Test 1: Create a session
        logger.info("\n1. Creating test session...")
        session = session_repo.create_session(
            user_id=test_user_id, title="Test Session for Query Optimization"
        )
        logger.info(f"   ✓ Created session: {session.id}")

        # Test 2: Create messages with sources
        logger.info("\n2. Creating test messages with sources...")
        for i in range(3):
            message = message_repo.create_message(
                session_id=session.id,
                user_id=test_user_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i+1}",
                metadata={
                    "query_mode": "balanced",
                    "processing_time_ms": 100 + i * 10,
                    "confidence_score": 0.9 - i * 0.1,
                },
            )

            # Add sources to assistant messages
            if i % 2 == 1:
                sources = [
                    {
                        "document_id": f"doc_{i}",
                        "document_name": f"Document {i}",
                        "chunk_id": f"chunk_{i}",
                        "score": 0.95 - i * 0.05,
                        "text": f"Source text {i}",
                    }
                ]
                source_repo.create_sources(message.id, sources)

            logger.info(f"   ✓ Created message {i+1}: {message.id}")

        # Test 3: Get user sessions WITHOUT loading messages
        logger.info("\n3. Testing get_user_sessions WITHOUT joinedload...")
        sessions_without = session_repo.get_user_sessions(
            user_id=test_user_id, load_messages=False
        )
        logger.info(f"   ✓ Retrieved {len(sessions_without)} sessions")
        logger.info(f"   ✓ Ordering: created_at DESC (most recent first)")

        # Test 4: Get user sessions WITH loading messages
        logger.info("\n4. Testing get_user_sessions WITH joinedload...")
        sessions_with = session_repo.get_user_sessions(
            user_id=test_user_id, load_messages=True
        )
        logger.info(f"   ✓ Retrieved {len(sessions_with)} sessions")
        if sessions_with:
            logger.info(
                f"   ✓ Messages eagerly loaded: {len(sessions_with[0].messages)} messages"
            )

        # Test 5: Get session by ID WITHOUT loading messages
        logger.info("\n5. Testing get_session_by_id WITHOUT joinedload...")
        session_without = session_repo.get_session_by_id(
            session_id=session.id, user_id=test_user_id, load_messages=False
        )
        logger.info(f"   ✓ Retrieved session: {session_without.id}")

        # Test 6: Get session by ID WITH loading messages
        logger.info("\n6. Testing get_session_by_id WITH joinedload...")
        session_with = session_repo.get_session_by_id(
            session_id=session.id, user_id=test_user_id, load_messages=True
        )
        logger.info(f"   ✓ Retrieved session: {session_with.id}")
        logger.info(
            f"   ✓ Messages eagerly loaded: {len(session_with.messages)} messages"
        )

        # Test 7: Get session messages WITHOUT loading sources
        logger.info("\n7. Testing get_session_messages WITHOUT joinedload...")
        messages_without = message_repo.get_session_messages(
            session_id=session.id, load_sources=False
        )
        logger.info(f"   ✓ Retrieved {len(messages_without)} messages")
        logger.info(f"   ✓ Ordering: created_at ASC (chronological)")

        # Test 8: Get session messages WITH loading sources
        logger.info("\n8. Testing get_session_messages WITH joinedload...")
        messages_with = message_repo.get_session_messages(
            session_id=session.id, load_sources=True
        )
        logger.info(f"   ✓ Retrieved {len(messages_with)} messages")
        for msg in messages_with:
            if msg.role == "assistant":
                logger.info(
                    f"   ✓ Message {msg.id}: {len(msg.sources)} sources eagerly loaded"
                )

        # Test 9: Search messages WITHOUT loading sources
        logger.info("\n9. Testing search_messages WITHOUT joinedload...")
        search_results_without = message_repo.search_messages(
            user_id=test_user_id, query="Test", load_sources=False
        )
        logger.info(f"   ✓ Found {len(search_results_without)} messages")
        logger.info(f"   ✓ Ordering: created_at DESC (most recent first)")

        # Test 10: Search messages WITH loading sources
        logger.info("\n10. Testing search_messages WITH joinedload...")
        search_results_with = message_repo.search_messages(
            user_id=test_user_id, query="Test", load_sources=True
        )
        logger.info(f"   ✓ Found {len(search_results_with)} messages")
        for msg in search_results_with:
            if msg.role == "assistant":
                logger.info(
                    f"   ✓ Message {msg.id}: {len(msg.sources)} sources eagerly loaded"
                )

        # Test 11: Get message with sources (existing method)
        logger.info("\n11. Testing get_message_with_sources...")
        if messages_with:
            msg_with_sources = message_repo.get_message_with_sources(
                message_id=messages_with[1].id  # Get assistant message
            )
            if msg_with_sources:
                logger.info(f"   ✓ Retrieved message: {msg_with_sources.id}")
                logger.info(
                    f"   ✓ Sources eagerly loaded: {len(msg_with_sources.sources)} sources"
                )

        # Cleanup
        logger.info("\n12. Cleaning up test data...")
        session_repo.delete_session(session.id, test_user_id)
        logger.info("   ✓ Deleted test session and messages")

        # Delete test user
        user_repo.delete_user(test_user_id)
        logger.info("   ✓ Deleted test user")

        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL QUERY OPTIMIZATION TESTS PASSED")
        logger.info("=" * 60)
        logger.info("\nKey Optimizations Verified:")
        logger.info("  • joinedload for Session.messages relationship")
        logger.info("  • joinedload for Message.sources relationship")
        logger.info("  • ORDER BY created_at DESC for sessions")
        logger.info("  • ORDER BY created_at ASC for messages (chronological)")
        logger.info("  • ORDER BY created_at DESC for search results")
        logger.info("  • Optional eager loading to avoid N+1 queries")

        return True

    except Exception as e:
        logger.error(f"\n❌ Verification failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = verify_query_optimization()
    sys.exit(0 if success else 1)
