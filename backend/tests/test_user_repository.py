"""Tests for UserRepository."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from backend.db.database import Base
from backend.db.models import User
from backend.db.repositories import UserRepository
from backend.services.auth_service import AuthService


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def user_repo(db_session):
    """Create a UserRepository instance."""
    return UserRepository(db_session)


def test_create_user(user_repo):
    """Test creating a new user."""
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
    assert user.role == "user"
    assert user.is_active is True
    assert user.query_count == 0
    assert user.storage_used_bytes == 0

    # Verify password is hashed
    assert user.password_hash != "password123"
    assert AuthService.verify_password("password123", user.password_hash)


def test_get_user_by_email(user_repo):
    """Test getting user by email."""
    # Create user
    created_user = user_repo.create_user(
        email="test@example.com", username="testuser", password="password123"
    )

    # Get user by email
    user = user_repo.get_user_by_email("test@example.com")

    assert user is not None
    assert user.id == created_user.id
    assert user.email == "test@example.com"

    # Test case insensitivity
    user_upper = user_repo.get_user_by_email("TEST@EXAMPLE.COM")
    assert user_upper is not None
    assert user_upper.id == created_user.id


def test_get_user_by_id(user_repo):
    """Test getting user by ID."""
    # Create user
    created_user = user_repo.create_user(
        email="test@example.com", username="testuser", password="password123"
    )

    # Get user by ID
    user = user_repo.get_user_by_id(created_user.id)

    assert user is not None
    assert user.id == created_user.id
    assert user.email == "test@example.com"


def test_get_user_by_id_not_found(user_repo):
    """Test getting non-existent user by ID."""
    user = user_repo.get_user_by_id(uuid4())
    assert user is None


def test_update_user(user_repo):
    """Test updating user information."""
    # Create user
    user = user_repo.create_user(
        email="test@example.com", username="testuser", password="password123"
    )

    # Update user
    updated_user = user_repo.update_user(
        user.id, full_name="Updated Name", role="premium"
    )

    assert updated_user is not None
    assert updated_user.full_name == "Updated Name"
    assert updated_user.role == "premium"


def test_update_last_login(user_repo):
    """Test updating last login timestamp."""
    # Create user
    user = user_repo.create_user(
        email="test@example.com", username="testuser", password="password123"
    )

    assert user.last_login_at is None

    # Update last login
    updated_user = user_repo.update_last_login(user.id)

    assert updated_user is not None
    assert updated_user.last_login_at is not None


def test_increment_query_count(user_repo):
    """Test incrementing query count."""
    # Create user
    user = user_repo.create_user(
        email="test@example.com", username="testuser", password="password123"
    )

    assert user.query_count == 0

    # Increment query count
    updated_user = user_repo.increment_query_count(user.id)

    assert updated_user is not None
    assert updated_user.query_count == 1

    # Increment again
    updated_user = user_repo.increment_query_count(user.id)
    assert updated_user.query_count == 2


def test_update_storage_used(user_repo):
    """Test updating storage usage."""
    # Create user
    user = user_repo.create_user(
        email="test@example.com", username="testuser", password="password123"
    )

    assert user.storage_used_bytes == 0

    # Add storage
    updated_user = user_repo.update_storage_used(user.id, 1000)

    assert updated_user is not None
    assert updated_user.storage_used_bytes == 1000

    # Add more storage
    updated_user = user_repo.update_storage_used(user.id, 500)
    assert updated_user.storage_used_bytes == 1500

    # Remove storage
    updated_user = user_repo.update_storage_used(user.id, -500)
    assert updated_user.storage_used_bytes == 1000


def test_delete_user(user_repo):
    """Test soft deleting a user."""
    # Create user
    user = user_repo.create_user(
        email="test@example.com", username="testuser", password="password123"
    )

    assert user.is_active is True

    # Delete user
    result = user_repo.delete_user(user.id)

    assert result is True

    # Verify user is inactive
    deleted_user = user_repo.get_user_by_id(user.id)
    assert deleted_user is not None
    assert deleted_user.is_active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
