"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from uuid import UUID

from backend.db.database import get_db
from backend.db.repositories.user_repository import UserRepository
from backend.db.models.user import User
from backend.models.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh,
    UserUpdate,
)
from backend.services.auth_service import AuthService
from backend.core.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Creates a new user account and returns authentication tokens.

    Args:
        user_data: User registration data (email, username, password)
        db: Database session

    Returns:
        TokenResponse with access token, refresh token, and user info

    Raises:
        409: Email or username already exists
        422: Validation error (invalid email, weak password, etc.)
    """
    user_repo = UserRepository(db)

    # Check if email already exists
    existing_user = user_repo.get_user_by_email(user_data.email)
    if existing_user:
        logger.warning(f"Registration failed: email already exists - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    # Check if username already exists
    existing_user = user_repo.get_user_by_username(user_data.username)
    if existing_user:
        logger.warning(
            f"Registration failed: username already exists - {user_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )

    try:
        # Create user
        user = user_repo.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
        )

        # Generate tokens
        access_token = AuthService.create_access_token(data={"sub": str(user.id)})
        refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

        # Update last login
        user_repo.update_last_login(user.id)

        logger.info(f"User registered successfully: {user.email} (id={user.id})")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=86400,  # 24 hours in seconds
            user=UserResponse.model_validate(user),
        )

    except IntegrityError as e:
        logger.error(f"Database integrity error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists",
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account",
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return tokens.

    Args:
        credentials: User login credentials (email, password)
        db: Database session

    Returns:
        TokenResponse with access token, refresh token, and user info

    Raises:
        401: Invalid credentials or inactive account
    """
    user_repo = UserRepository(db)

    # Get user by email
    user = user_repo.get_user_by_email(credentials.email)

    if not user:
        logger.warning(f"Login failed: user not found - {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Verify password
    if not AuthService.verify_password(credentials.password, user.password_hash):
        logger.warning(f"Login failed: invalid password - {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login failed: inactive account - {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
        )

    # Generate tokens
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})

    # Update last login
    user_repo.update_last_login(user.id)

    logger.info(f"User logged in successfully: {user.email} (id={user.id})")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours in seconds
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token
        db: Database session

    Returns:
        TokenResponse with new access token and user info

    Raises:
        401: Invalid or expired refresh token
    """
    # Decode refresh token
    payload = AuthService.decode_token(token_data.refresh_token)

    if not payload:
        logger.warning("Token refresh failed: invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Extract user ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        logger.warning("Token refresh failed: missing user ID in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.warning(f"Token refresh failed: invalid user ID format - {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # Get user from database
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(user_id)

    if not user:
        logger.warning(f"Token refresh failed: user not found - {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Token refresh failed: inactive account - {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
        )

    # Generate new access token (keep same refresh token)
    access_token = AuthService.create_access_token(data={"sub": str(user.id)})

    logger.info(f"Token refreshed successfully: {user.email} (id={user.id})")

    return TokenResponse(
        access_token=access_token,
        refresh_token=token_data.refresh_token,  # Return same refresh token
        token_type="bearer",
        expires_in=86400,  # 24 hours in seconds
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        UserResponse with user information

    Raises:
        401: Not authenticated or invalid token
    """
    logger.debug(f"Fetching user info: {current_user.email} (id={current_user.id})")

    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update current authenticated user information.

    Allows updating username, full_name, email, and password.
    Password change requires current_password for verification.

    Args:
        updates: Fields to update
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        UserResponse with updated user information

    Raises:
        400: Invalid current password or validation error
        401: Not authenticated
        409: Email or username already taken
    """
    user_repo = UserRepository(db)

    # Prepare update data
    update_data = {}

    # Update username if provided
    if updates.username is not None:
        # Check if username is already taken by another user
        existing_user = user_repo.get_user_by_username(updates.username)
        if existing_user and existing_user.id != current_user.id:
            logger.warning(
                f"Update failed: username already taken - {updates.username} "
                f"(user={current_user.email})"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
            )
        update_data["username"] = updates.username

    # Update full_name if provided
    if updates.full_name is not None:
        update_data["full_name"] = updates.full_name

    # Update email if provided
    if updates.email is not None:
        # Check if email is already taken by another user
        existing_user = user_repo.get_user_by_email(updates.email)
        if existing_user and existing_user.id != current_user.id:
            logger.warning(
                f"Update failed: email already taken - {updates.email} "
                f"(user={current_user.email})"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )
        update_data["email"] = updates.email.lower()

    # Update password if provided
    if updates.new_password is not None:
        # Verify current password
        if not updates.current_password:
            logger.warning(
                f"Password update failed: missing current password (user={current_user.email})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to change password",
            )

        if not AuthService.verify_password(
            updates.current_password, current_user.password_hash
        ):
            logger.warning(
                f"Password update failed: invalid current password (user={current_user.email})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Update password using repository method
        user_repo.update_password(current_user.id, updates.new_password)
        logger.info(f"Password updated successfully: {current_user.email}")

    # Update other fields if any
    if update_data:
        try:
            updated_user = user_repo.update_user(current_user.id, **update_data)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user",
                )
            logger.info(
                f"User updated successfully: {updated_user.email} (id={updated_user.id})"
            )
            return UserResponse.model_validate(updated_user)
        except IntegrityError as e:
            logger.error(f"Database integrity error during update: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already exists",
            )

    # If only password was updated, return current user
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
