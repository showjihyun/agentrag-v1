"""Integration tests for repository layer with real database operations."""

import pytest
from datetime import datetime
from uuid import uuid4

from backend.db.database import get_db
from backend.db.repositories import (
    UserRepository,
    DocumentRepository,
    SessionRepository,
    MessageRepository,
    FeedbackRepository,
)


@pytest.fixture
def db():
    """Get database session for testing."""
    db_gen = get_db()
    db = next(db_gen)
    yield db
    db.close()


class TestUserDocumentIntegration:
    """Test user and document repository integration."""

    def test_user_document_workflow(self, db):
        """Test complete user document workflow."""
        user_repo = UserRepository(db)
        doc_repo = DocumentRepository(db)

        # Create user
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="Password123"
        )

        # Upload document
        document = doc_repo.create_document(
            user_id=user.id,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        # Update storage
        user_repo.update_storage_used(user.id, 1024)

        # Verify
        updated_user = user_repo.get_user_by_id(user.id)
        assert updated_user.storage_used_bytes == 1024

        # Get user documents
        docs = doc_repo.get_user_documents(user.id)
        assert len(docs) == 1
        assert docs[0].id == document.id


class TestConversationWorkflow:
    """Test conversation workflow integration."""

    def test_complete_conversation_flow(self, db):
        """Test complete conversation with feedback."""
        user_repo = UserRepository(db)
        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        feedback_repo = FeedbackRepository(db)

        # Create user
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="Password123"
        )

        # Create session
        session = session_repo.create_session(
            user_id=user.id, title="Test Conversation"
        )

        # Add user message
        user_message = message_repo.create_message(
            session_id=session.id, user_id=user.id, role="user", content="What is AI?"
        )

        # Add assistant message
        assistant_message = message_repo.create_message(
            session_id=session.id,
            user_id=user.id,
            role="assistant",
            content="AI stands for Artificial Intelligence...",
        )

        # Add feedback
        feedback = feedback_repo.create_feedback(
            message_id=assistant_message.id,
            user_id=user.id,
            rating=5,
            feedback_text="Very helpful!",
        )

        # Verify
        messages = message_repo.get_session_messages(session.id)
        assert len(messages) == 2

        user_feedback = feedback_repo.get_user_feedback(user.id)
        assert len(user_feedback) == 1
        assert user_feedback[0].rating == 5


class TestCascadeDelete:
    """Test cascade delete operations."""

    def test_user_deletion_cascades(self, db):
        """Test that deleting user cascades to related records."""
        user_repo = UserRepository(db)
        doc_repo = DocumentRepository(db)
        session_repo = SessionRepository(db)

        # Create user with documents and sessions
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="Password123"
        )

        doc_repo.create_document(
            user_id=user.id,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        session_repo.create_session(user_id=user.id, title="Test Session")

        # Verify records exist
        assert len(doc_repo.get_user_documents(user.id)) == 1
        assert len(session_repo.get_user_sessions(user.id)) == 1

        # Delete user (soft delete)
        user_repo.delete_user(user.id)

        # Verify user is inactive
        deleted_user = user_repo.get_user_by_id(user.id)
        assert not deleted_user.is_active
