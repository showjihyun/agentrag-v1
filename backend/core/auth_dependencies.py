"""Authentication dependencies for FastAPI endpoints."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Callable
from uuid import UUID
import logging

from backend.db.database import get_db
from backend.db.repositories.user_repository import UserRepository
from backend.db.models.user import User
from backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate user from JWT token.

    This dependency requires authentication and will raise 401 if:
    - No token is provided
    - Token is invalid or expired
    - User is not found in database
    - User is inactive

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object if authentication is successful

    Raises:
        HTTPException: 401 Unauthorized if authentication fails

    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    # Extract token
    token = credentials.credentials

    # Decode token
    payload = AuthService.decode_token(token)
    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        logger.warning("Token missing 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert to UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.warning(f"Invalid user ID format in token: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(user_id)

    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authenticated user: {user.email} (id={user.id})")
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Extract and validate user from JWT token, but allow requests without authentication.

    This dependency is for endpoints that work both with and without authentication.
    Returns None if no token is provided or if token is invalid.

    Args:
        credentials: Optional HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object if valid token is provided, None otherwise

    Usage:
        @app.get("/optional-auth")
        async def optional_auth_route(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.username}"}
            else:
                return {"message": "Hello guest"}
    """
    # No credentials provided - return None (guest access)
    if not credentials:
        logger.debug("No authentication credentials provided (guest access)")
        return None

    try:
        # Extract token
        token = credentials.credentials

        # Decode token
        payload = AuthService.decode_token(token)
        if not payload:
            logger.debug("Invalid or expired token (allowing guest access)")
            return None

        # Extract user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            logger.debug("Token missing 'sub' claim (allowing guest access)")
            return None

        # Convert to UUID
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            logger.debug(
                f"Invalid user ID format in token: {user_id_str} (allowing guest access)"
            )
            return None

        # Get user from database
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)

        if not user:
            logger.debug(f"User not found: {user_id} (allowing guest access)")
            return None

        # Check if user is active
        if not user.is_active:
            logger.debug(f"Inactive user: {user.email} (allowing guest access)")
            return None

        logger.debug(f"Authenticated user: {user.email} (id={user.id})")
        return user

    except Exception as e:
        # Log error but don't raise - allow guest access
        logger.debug(
            f"Error during optional authentication: {e} (allowing guest access)"
        )
        return None


def require_role(required_role: str) -> Callable:
    """
    Dependency factory to check if user has required role.

    This creates a dependency that checks if the authenticated user
    has the specified role. Must be used after get_current_user.

    Args:
        required_role: Required role (e.g., "admin", "premium")

    Returns:
        Dependency function that validates user role

    Raises:
        HTTPException: 403 Forbidden if user doesn't have required role

    Usage:
        @app.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_role("admin"))
        ):
            # Only admins can access this endpoint
            return {"message": "User deleted"}
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> None:
        """
        Check if current user has required role.

        Args:
            current_user: Authenticated user from get_current_user

        Raises:
            HTTPException: 403 Forbidden if user doesn't have required role
        """
        if current_user.role != required_role:
            logger.warning(
                f"User {current_user.email} (role={current_user.role}) "
                f"attempted to access endpoint requiring role={required_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires '{required_role}' role",
            )

        logger.debug(f"User {current_user.email} has required role: {required_role}")

    return role_checker
