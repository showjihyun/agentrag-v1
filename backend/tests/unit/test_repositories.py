"""Unit tests for repository layer."""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.db.models import (
    User,
    Document,
    Session as ConversationSession,
    Message,
    AnswerFeedback as Feedback,
)
from backend.db.repositories import (
    UserRepository,
    DocumentRepository,
    SessionRepository,
    MessageRepository,
    FeedbackRepository,
)


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user_repo(db_session):
    """Create UserRepository instance."""
    return UserRepository(db_session)


@pytest.fixture
def document_repo(db_session):
    """Create DocumentRepository instance."""
    return DocumentRepository(db_session)


@pytest.fixture
def session_repo(db_session):
    """Create SessionRepository instance."""
    return SessionRepository(db_session)


@pytest.fixture
def message_repo(db_session):
    """Create MessageRepository instance."""
    return MessageRepository(db_session)


@pytest.fixture
def feedback_repo(db_session):
    """Create FeedbackRepository instance."""
    return FeedbackRepository(db_session)


class TestUserRepository:
    """Test UserRepository operations."""

    def test_create_user(self, user_repo):
        """Test user creation."""
        user = user_repo.create_user(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User",
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.query_count == 0

    def test_get_user_by_email(self, user_repo):
        """Test retrieving user by email."""
        created_user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        found_user = user_repo.get_user_by_email("test@example.com")

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "test@example.com"

    def test_get_user_by_id(self, user_repo):
        """Test retrieving user by ID."""
        created_user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        found_user = user_repo.get_user_by_id(created_user.id)

        assert found_user is not None
        assert found_user.id == created_user.id

    def test_update_user(self, user_repo):
        """Test updating user information."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        updated_user = user_repo.update_user(user.id, full_name="Updated Name")

        assert updated_user.full_name == "Updated Name"

    def test_increment_query_count(self, user_repo):
        """Test incrementing query count."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        assert user.query_count == 0

        updated_user = user_repo.increment_query_count(user.id)
        assert updated_user.query_count == 1

        updated_user = user_repo.increment_query_count(user.id)
        assert updated_user.query_count == 2


class TestDocumentRepository:
    """Test DocumentRepository operations."""

    def test_create_document(self, user_repo, document_repo):
        """Test document creation."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        document = document_repo.create_document(
            user_id=user.id,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        assert document.id is not None
        assert document.user_id == user.id
        assert document.filename == "test.pdf"
        assert document.status == "pending"

    def test_get_user_documents(self, user_repo, document_repo):
        """Test retrieving user documents."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        # Create multiple documents
        for i in range(3):
            document_repo.create_document(
                user_id=user.id,
                filename=f"test{i}.pdf",
                file_path=f"/uploads/test{i}.pdf",
                file_size=1024,
                mime_type="application/pdf",
            )

        documents = document_repo.get_user_documents(user.id)

        assert len(documents) == 3

    def test_update_document_status(self, user_repo, document_repo):
        """Test updating document status."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        document = document_repo.create_document(
            user_id=user.id,
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )

        updated_doc = document_repo.update_document_status(document.id, "completed")

        assert updated_doc.status == "completed"
        assert updated_doc.processing_completed_at is not None


class TestSessionRepository:
    """Test SessionRepository operations."""

    def test_create_session(self, user_repo, session_repo):
        """Test session creation."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        session = session_repo.create_session(user_id=user.id, title="Test Session")

        assert session.id is not None
        assert session.user_id == user.id
        assert session.title == "Test Session"
        assert session.message_count == 0


class TestFeedbackRepository:
    """Test FeedbackRepository operations."""

    def test_create_feedback(
        self, user_repo, session_repo, message_repo, feedback_repo
    ):
        """Test feedback creation."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        session = session_repo.create_session(user_id=user.id, title="Test Session")

        message = message_repo.create_message(
            session_id=session.id,
            user_id=user.id,
            role="assistant",
            content="Test response",
        )

        feedback = feedback_repo.create_feedback(
            message_id=message.id,
            user_id=user.id,
            rating=5,
            feedback_text="Great answer!",
        )

        assert feedback.id is not None
        assert feedback.message_id == message.id
        assert feedback.rating == 5

    def test_get_feedback_stats(
        self, user_repo, session_repo, message_repo, feedback_repo
    ):
        """Test feedback statistics."""
        user = user_repo.create_user(
            email="test@example.com", username="testuser", password="password123"
        )

        session = session_repo.create_session(user_id=user.id, title="Test Session")

        # Create multiple feedback entries
        for rating in [5, 4, 5, 3, 5]:
            message = message_repo.create_message(
                session_id=session.id,
                user_id=user.id,
                role="assistant",
                content="Test response",
            )

            feedback_repo.create_feedback(
                message_id=message.id, user_id=user.id, rating=rating
            )

        stats = feedback_repo.get_feedback_stats()

        assert stats["total_feedback"] == 5
        assert stats["average_rating"] > 4.0
        assert stats["rating_distribution"][5] == 3
