"""User repository for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime
import logging
from uuid import UUID

from backend.db.models import User
from backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class UserRepository:
    """Database operations for users."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "user",
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email (must be unique)
            username: Username (must be unique)
            password: Plain text password (will be hashed)
            full_name: Optional full name
            role: User role (default: "user")

        Returns:
            Created User object

        Raises:
            IntegrityError: If email or username already exists
        """
        try:
            # Hash password
            password_hash = AuthService.hash_password(password)

            # Create user
            user = User(
                email=email.lower(),
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
                is_active=True,
                query_count=0,
                storage_used_bytes=0,
                preferences={},
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Created user: {user.email} (id={user.id})")
            return user

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user {email}: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User object if found, None otherwise
        """
        user = self.db.query(User).filter(User.email == email.lower()).first()

        if user:
            logger.debug(f"Found user by email: {email}")
        else:
            logger.debug(f"User not found by email: {email}")

        return user

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User object if found, None otherwise
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if user:
            logger.debug(f"Found user by id: {user_id}")
        else:
            logger.debug(f"User not found by id: {user_id}")

        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User object if found, None otherwise
        """
        user = self.db.query(User).filter(User.username == username).first()

        if user:
            logger.debug(f"Found user by username: {username}")
        else:
            logger.debug(f"User not found by username: {username}")

        return user

    def update_user(self, user_id: UUID, **updates) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: User UUID
            **updates: Fields to update (e.g., full_name="John Doe")

        Returns:
            Updated User object if found, None otherwise
        """
        user = self.get_user_by_id(user_id)

        if not user:
            logger.warning(f"Cannot update user {user_id}: not found")
            return None

        # Update allowed fields
        allowed_fields = {
            "username",
            "full_name",
            "role",
            "is_active",
            "preferences",
            "query_count",
            "storage_used_bytes",
        }

        for key, value in updates.items():
            if key in allowed_fields and hasattr(user, key):
                setattr(user, key, value)
                logger.debug(f"Updated user {user_id} field {key}")

        # Update timestamp
        user.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Updated user: {user.email} (id={user_id})")
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    def update_last_login(self, user_id: UUID) -> Optional[User]:
        """
        Update user's last login timestamp.

        Args:
            user_id: User UUID

        Returns:
            Updated User object if found, None otherwise
        """
        user = self.get_user_by_id(user_id)

        if not user:
            logger.warning(f"Cannot update last login for user {user_id}: not found")
            return None

        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        logger.debug(f"Updated last login for user: {user.email}")
        return user

    def update_password(self, user_id: UUID, new_password: str) -> Optional[User]:
        """
        Update user's password.

        Args:
            user_id: User UUID
            new_password: New plain text password (will be hashed)

        Returns:
            Updated User object if found, None otherwise
        """
        user = self.get_user_by_id(user_id)

        if not user:
            logger.warning(f"Cannot update password for user {user_id}: not found")
            return None

        # Hash new password
        user.password_hash = AuthService.hash_password(new_password)
        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Updated password for user: {user.email}")
        return user

    def delete_user(self, user_id: UUID) -> bool:
        """
        Soft delete a user (set is_active to False).

        Args:
            user_id: User UUID

        Returns:
            True if user was deleted, False if not found
        """
        user = self.get_user_by_id(user_id)

        if not user:
            logger.warning(f"Cannot delete user {user_id}: not found")
            return False

        user.is_active = False
        user.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Soft deleted user: {user.email} (id={user_id})")
        return True

    def increment_query_count(self, user_id: UUID) -> Optional[User]:
        """
        Increment user's query count.

        Args:
            user_id: User UUID

        Returns:
            Updated User object if found, None otherwise
        """
        user = self.get_user_by_id(user_id)

        if not user:
            return None

        user.query_count += 1
        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        return user

    def update_storage_used(self, user_id: UUID, bytes_delta: int) -> Optional[User]:
        """
        Update user's storage usage.

        Args:
            user_id: User UUID
            bytes_delta: Change in storage (positive or negative)

        Returns:
            Updated User object if found, None otherwise
        """
        user = self.get_user_by_id(user_id)

        if not user:
            return None

        user.storage_used_bytes += bytes_delta

        # Ensure storage doesn't go negative
        if user.storage_used_bytes < 0:
            user.storage_used_bytes = 0

        user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)

        logger.debug(
            f"Updated storage for user {user.email}: "
            f"{bytes_delta:+d} bytes (total: {user.storage_used_bytes})"
        )

        return user
