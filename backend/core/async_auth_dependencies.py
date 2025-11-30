"""
Async Authentication dependencies for FastAPI endpoints.

Use these dependencies for async endpoints that use AsyncSession.
For sync endpoints, use auth_dependencies.py instead.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
import logging

from backend.db.async_database import get_async_db
from backend.db.models.user import User
from backend.services.auth_service import AuthService
from backend.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_async(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Async version of get_current_user.
    
    Use this for async endpoints that use AsyncSession.
    
    Usage:
        @router.get("/protected")
        async def protected_route(
            user: User = Depends(get_current_user_async),
            db: AsyncSession = Depends(get_async_db)
        ):
            return {"user_id": str(user.id)}
    """
    # DEBUG MODE: Use test user
    if settings.DEBUG:
        logger.debug("🔧 DEBUG mode enabled: Using default test user (async)")
        
        # Try to get existing test user
        result = await db.execute(
            select(User).where(User.email == "test@example.com")
        )
        test_user = result.scalar_one_or_none()
        
        # Create test user if doesn't exist
        if not test_user:
            logger.info("Creating default test user for DEBUG mode (async)")
            try:
                test_user = User(
                    email="test@example.com",
                    username="testuser",
                    password_hash=AuthService.hash_password("test1234"),
                    role="admin",
                    is_active=True,
                )
                db.add(test_user)
                await db.commit()
                await db.refresh(test_user)
                logger.info("✓ Test user created: test@example.com / test1234 (admin)")
            except Exception as e:
                logger.error(f"Failed to create test user: {e}")
                await db.rollback()
                # Try to get it again
                result = await db.execute(
                    select(User).where(User.email == "test@example.com")
                )
                test_user = result.scalar_one_or_none()
                if not test_user:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create or retrieve test user"
                    )
        
        return test_user
    
    # Production mode: Require credentials
    if not credentials:
        logger.warning("No authentication credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract and decode token
    token = credentials.credentials
    payload = AuthService.decode_token(token)
    
    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Authenticated user (async): {user.email}")
    return user


async def require_admin_async(
    current_user: User = Depends(get_current_user_async)
) -> User:
    """
    Async dependency to check if user has admin role.
    
    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            current_user: User = Depends(require_admin_async)
        ):
            return {"message": "User deleted"}
    """
    if current_user.role != "admin":
        logger.warning(
            f"User {current_user.email} (role={current_user.role}) "
            f"attempted to access admin-only endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires admin privileges",
        )
    
    return current_user


async def get_optional_user_async(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_async_db),
) -> Optional[User]:
    """
    Async version of get_optional_user.
    
    Returns None if no valid token is provided (guest access).
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = AuthService.decode_token(token)
        
        if not payload:
            return None
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            return None
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception as e:
        logger.debug(f"Optional auth error: {e}")
        return None
