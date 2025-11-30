"""
Authentication API v2

Enhanced authentication with:
- Standardized responses
- Audit logging
- Rate limiting
- Enhanced security
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.db.database import get_db
from backend.db.repositories.user_repository import UserRepository
from backend.db.models.user import User
from backend.models.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from backend.services.auth_service import AuthService
from backend.core.auth_dependencies import get_current_user
from backend.core.api_response import ResponseBuilder, ErrorCode, ResponseTimer
from backend.core.rate_limiter_enhanced import rate_limit, RateLimitTier
from backend.core.audit_logger import get_audit_logger, AuditEventType
from backend.core.request_validator import InputValidator

logger = logging.getLogger(__name__)
audit = get_audit_logger()

router = APIRouter(prefix="/api/v2/auth", tags=["v2-auth"])


@router.post("/register")
@rate_limit(tier=RateLimitTier.ANONYMOUS, endpoint_key="/api/v2/auth/register")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user.
    
    Creates a new user account with enhanced validation.
    """
    with ResponseTimer() as timer:
        try:
            # Validate email
            if not InputValidator.validate_email(user_data.email):
                return ResponseBuilder.error(
                    code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    message="Invalid email format",
                    field="email",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Validate username
            if not InputValidator.validate_username(user_data.username):
                return ResponseBuilder.error(
                    code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    message="Username must be 3-50 characters, alphanumeric and underscore only",
                    field="username",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Validate password strength
            password_check = InputValidator.validate_password_strength(user_data.password)
            if not password_check["valid"]:
                return ResponseBuilder.error(
                    code=ErrorCode.VALIDATION_FAILED,
                    message="Password does not meet requirements",
                    field="password",
                    details={
                        "score": password_check["score"],
                        "issues": password_check["issues"]
                    },
                    request_id=getattr(request.state, "request_id", None)
                )
            
            user_repo = UserRepository(db)
            
            # Check if email exists
            if user_repo.get_user_by_email(user_data.email):
                audit.log(
                    event_type=AuditEventType.USER_CREATED,
                    action="Registration failed - email exists",
                    request=request,
                    user_email=user_data.email,
                    success=False,
                    error_message="Email already registered"
                )
                return ResponseBuilder.error(
                    code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                    message="Email already registered",
                    field="email",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Check if username exists
            if user_repo.get_user_by_username(user_data.username):
                return ResponseBuilder.error(
                    code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                    message="Username already taken",
                    field="username",
                    request_id=getattr(request.state, "request_id", None)
                )
            
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
            
            # Audit log
            audit.log(
                event_type=AuditEventType.USER_CREATED,
                action="User registered successfully",
                request=request,
                user_id=str(user.id),
                user_email=user.email,
                details={"username": user.username}
            )
            
            return ResponseBuilder.success(
                data={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": 86400,
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "username": user.username,
                        "full_name": user.full_name,
                    }
                },
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except IntegrityError:
            return ResponseBuilder.error(
                code=ErrorCode.RESOURCE_ALREADY_EXISTS,
                message="Email or username already exists",
                request_id=getattr(request.state, "request_id", None)
            )
        except Exception as e:
            logger.error(f"Registration failed: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Registration failed",
                request_id=getattr(request.state, "request_id", None)
            )


@router.post("/login")
@rate_limit(tier=RateLimitTier.ANONYMOUS, endpoint_key="/api/v2/auth/login")
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return tokens.
    """
    with ResponseTimer() as timer:
        try:
            user_repo = UserRepository(db)
            
            # Find user
            user = user_repo.get_user_by_email(credentials.email)
            
            if not user:
                audit.log_login_failed(
                    user_email=credentials.email,
                    request=request,
                    reason="User not found"
                )
                return ResponseBuilder.error(
                    code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                    message="Invalid email or password",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Verify password
            if not AuthService.verify_password(credentials.password, user.hashed_password):
                audit.log_login_failed(
                    user_email=credentials.email,
                    request=request,
                    reason="Invalid password"
                )
                return ResponseBuilder.error(
                    code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                    message="Invalid email or password",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Check if account is active
            if not user.is_active:
                audit.log_login_failed(
                    user_email=credentials.email,
                    request=request,
                    reason="Account inactive"
                )
                return ResponseBuilder.error(
                    code=ErrorCode.AUTH_ACCOUNT_INACTIVE,
                    message="Account is inactive",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Generate tokens
            access_token = AuthService.create_access_token(data={"sub": str(user.id)})
            refresh_token = AuthService.create_refresh_token(data={"sub": str(user.id)})
            
            # Update last login
            user_repo.update_last_login(user.id)
            
            # Audit log
            audit.log_login_success(
                user_id=str(user.id),
                user_email=user.email,
                request=request
            )
            
            return ResponseBuilder.success(
                data={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": 86400,
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "username": user.username,
                        "full_name": user.full_name,
                    }
                },
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except Exception as e:
            logger.error(f"Login failed: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Login failed",
                request_id=getattr(request.state, "request_id", None)
            )


@router.get("/me")
@rate_limit(tier=RateLimitTier.FREE)
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Get current user information.
    """
    with ResponseTimer() as timer:
        return ResponseBuilder.success(
            data={
                "id": str(current_user.id),
                "email": current_user.email,
                "username": current_user.username,
                "full_name": current_user.full_name,
                "is_active": current_user.is_active,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            },
            request_id=getattr(request.state, "request_id", None),
            duration_ms=timer.duration_ms
        )


@router.post("/logout")
@rate_limit(tier=RateLimitTier.FREE)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Logout current user.
    
    In a stateless JWT system, this mainly logs the event.
    For full logout, implement token blacklisting.
    """
    audit.log(
        event_type=AuditEventType.AUTH_LOGOUT,
        action="User logged out",
        request=request,
        user_id=str(current_user.id),
        user_email=current_user.email
    )
    
    return ResponseBuilder.success(
        data={"message": "Logged out successfully"},
        request_id=getattr(request.state, "request_id", None)
    )


@router.post("/change-password")
@rate_limit(tier=RateLimitTier.FREE, endpoint_key="/api/v2/auth/change-password")
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change user password.
    """
    with ResponseTimer() as timer:
        try:
            # Verify current password
            if not AuthService.verify_password(current_password, current_user.hashed_password):
                audit.log(
                    event_type=AuditEventType.AUTH_PASSWORD_CHANGE,
                    action="Password change failed - wrong current password",
                    request=request,
                    user_id=str(current_user.id),
                    success=False
                )
                return ResponseBuilder.error(
                    code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                    message="Current password is incorrect",
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Validate new password
            password_check = InputValidator.validate_password_strength(new_password)
            if not password_check["valid"]:
                return ResponseBuilder.error(
                    code=ErrorCode.VALIDATION_FAILED,
                    message="New password does not meet requirements",
                    details=password_check,
                    request_id=getattr(request.state, "request_id", None)
                )
            
            # Update password
            user_repo = UserRepository(db)
            user_repo.update_password(current_user.id, new_password)
            
            # Audit log
            audit.log(
                event_type=AuditEventType.AUTH_PASSWORD_CHANGE,
                action="Password changed successfully",
                request=request,
                user_id=str(current_user.id),
                user_email=current_user.email
            )
            
            return ResponseBuilder.success(
                data={"message": "Password changed successfully"},
                request_id=getattr(request.state, "request_id", None),
                duration_ms=timer.duration_ms
            )
            
        except Exception as e:
            logger.error(f"Password change failed: {e}", exc_info=True)
            return ResponseBuilder.error(
                code=ErrorCode.INTERNAL_ERROR,
                message="Password change failed",
                request_id=getattr(request.state, "request_id", None)
            )
