"""
Async User Repository with N+1 query prevention.

Provides optimized async database operations for User model
with eager loading support.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.db.models.user import User
from backend.db.async_database import AsyncBaseRepository
from backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class AsyncUserRepository(AsyncBaseRepository[User]):
    """
    Async repository for User operations with N+1 prevention.
    
    All methods support eager loading of relationships to prevent
    N+1 query problems.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    # ========================================================================
    # Query Methods with Eager Loading
    # ========================================================================
    
    async def get_by_id(
        self,
        user_id: UUID,
        load_relations: List[str] = None
    ) -> Optional[User]:
        """
        Get user by ID with optional eager loading.
        
        Args:
            user_id: User UUID
            load_relations: Relations to eager load (e.g., ['documents', 'sessions'])
        
        Example:
            # Load user with documents and sessions in single query
            user = await repo.get_by_id(
                user_id,
                load_relations=['documents', 'sessions']
            )
        """
        query = select(User).where(User.id == user_id)
        
        # Apply eager loading
        if load_relations:
            for relation in load_relations:
                if hasattr(User, relation):
                    query = query.options(selectinload(getattr(User, relation)))
        
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            logger.debug(f"Found user by id: {user_id}")
        else:
            logger.debug(f"User not found by id: {user_id}")
        
        return user
    
    async def get_by_email(
        self,
        email: str,
        load_relations: List[str] = None
    ) -> Optional[User]:
        """
        Get user by email with optional eager loading.
        
        Args:
            email: User email
            load_relations: Relations to eager load
        """
        query = select(User).where(User.email == email.lower())
        
        if load_relations:
            for relation in load_relations:
                if hasattr(User, relation):
                    query = query.options(selectinload(getattr(User, relation)))
        
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            logger.debug(f"Found user by email: {email}")
        else:
            logger.debug(f"User not found by email: {email}")
        
        return user
    
    async def get_by_username(
        self,
        username: str,
        load_relations: List[str] = None
    ) -> Optional[User]:
        """Get user by username with optional eager loading."""
        query = select(User).where(User.username == username)
        
        if load_relations:
            for relation in load_relations:
                if hasattr(User, relation):
                    query = query.options(selectinload(getattr(User, relation)))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_users(
        self,
        limit: int = 100,
        offset: int = 0,
        load_relations: List[str] = None
    ) -> List[User]:
        """Get all active users with pagination."""
        query = (
            select(User)
            .where(User.is_active == True)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        if load_relations:
            for relation in load_relations:
                if hasattr(User, relation):
                    query = query.options(selectinload(getattr(User, relation)))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ========================================================================
    # Create/Update Methods
    # ========================================================================
    
    async def create_user(
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
            
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)
            
            logger.info(f"Created user: {user.email} (id={user.id})")
            return user
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to create user {email}: {e}")
            raise
    
    async def update_user(
        self,
        user_id: UUID,
        **updates
    ) -> Optional[User]:
        """
        Update user information using bulk update for efficiency.
        
        Args:
            user_id: User UUID
            **updates: Fields to update
        
        Returns:
            Updated User object if found
        """
        allowed_fields = {
            "username", "full_name", "role", "is_active",
            "preferences", "query_count", "storage_used_bytes"
        }
        
        # Filter to allowed fields only
        valid_updates = {
            k: v for k, v in updates.items()
            if k in allowed_fields
        }
        
        if not valid_updates:
            return await self.get_by_id(user_id)
        
        # Add updated_at timestamp
        valid_updates["updated_at"] = datetime.utcnow()
        
        # Use bulk update for efficiency
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**valid_updates)
            .returning(User)
        )
        
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"Updated user: {user.email} (id={user_id})")
        
        return user
    
    async def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            .returning(User)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_password(
        self,
        user_id: UUID,
        new_password: str
    ) -> Optional[User]:
        """Update user's password."""
        password_hash = AuthService.hash_password(new_password)
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                password_hash=password_hash,
                updated_at=datetime.utcnow()
            )
            .returning(User)
        )
        
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"Updated password for user: {user.email}")
        
        return user
    
    # ========================================================================
    # Atomic Counter Updates (Prevents Race Conditions)
    # ========================================================================
    
    async def increment_query_count(self, user_id: UUID) -> Optional[User]:
        """
        Atomically increment user's query count.
        
        Uses SQL-level increment to prevent race conditions.
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                query_count=User.query_count + 1,
                updated_at=datetime.utcnow()
            )
            .returning(User)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_storage_used(
        self,
        user_id: UUID,
        bytes_delta: int
    ) -> Optional[User]:
        """
        Atomically update user's storage usage.
        
        Uses SQL-level arithmetic to prevent race conditions.
        Uses GREATEST to ensure storage doesn't go negative.
        """
        from sqlalchemy import func
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                storage_used_bytes=func.greatest(
                    User.storage_used_bytes + bytes_delta,
                    0
                ),
                updated_at=datetime.utcnow()
            )
            .returning(User)
        )
        
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.debug(
                f"Updated storage for user {user.email}: "
                f"{bytes_delta:+d} bytes (total: {user.storage_used_bytes})"
            )
        
        return user
    
    # ========================================================================
    # Soft Delete
    # ========================================================================
    
    async def soft_delete(self, user_id: UUID) -> bool:
        """
        Soft delete a user (set is_active to False).
        
        Returns:
            True if user was deleted, False if not found
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        
        result = await self.session.execute(stmt)
        
        if result.rowcount > 0:
            logger.info(f"Soft deleted user: {user_id}")
            return True
        
        logger.warning(f"Cannot delete user {user_id}: not found")
        return False
