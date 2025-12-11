"""
API Key Authentication Middleware
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.orm import Session

from backend.core.security.api_key_manager import get_api_key_manager
from backend.db.database import SessionLocal
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[dict]:
    """
    Verify API key from Authorization header
    
    Args:
        request: FastAPI request
        credentials: HTTP Bearer credentials
        
    Returns:
        User info if valid, None if no API key provided
        
    Raises:
        HTTPException: If API key is invalid
    """
    # Skip if no credentials
    if not credentials:
        return None
    
    # Get API key from Bearer token
    api_key = credentials.credentials
    
    # Validate API key
    db = SessionLocal()
    try:
        manager = get_api_key_manager()
        user_info = await manager.validate_key(db, api_key)
        
        if not user_info:
            logger.warning(
                "api_key_authentication_failed",
                path=request.url.path,
                client=request.client.host if request.client else "unknown"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.debug(
            "api_key_authenticated",
            user_id=user_info["user_id"],
            key_id=user_info["key_id"],
            path=request.url.path
        )
        
        return user_info
        
    finally:
        db.close()


async def get_api_key_user(
    credentials: HTTPAuthorizationCredentials = security
) -> dict:
    """
    Dependency to get user from API key (required)
    
    Usage:
        @router.get("/protected")
        async def protected_endpoint(
            user_info: dict = Depends(get_api_key_user)
        ):
            # user_info contains user_id, user_email, key_id, scopes
            ...
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    db = SessionLocal()
    try:
        manager = get_api_key_manager()
        user_info = await manager.validate_key(db, credentials.credentials)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user_info
        
    finally:
        db.close()


def check_api_key_scope(required_scope: str):
    """
    Dependency to check if API key has required scope
    
    Usage:
        @router.post("/workflows/execute")
        async def execute_workflow(
            user_info: dict = Depends(get_api_key_user),
            _: None = Depends(check_api_key_scope("workflows:execute"))
        ):
            ...
    """
    async def _check_scope(user_info: dict = get_api_key_user):
        scopes = user_info.get("scopes", [])
        
        if required_scope not in scopes and "*" not in scopes:
            logger.warning(
                "api_key_insufficient_scope",
                user_id=user_info["user_id"],
                key_id=user_info["key_id"],
                required_scope=required_scope,
                available_scopes=scopes
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key does not have required scope: {required_scope}"
            )
        
        return None
    
    return _check_scope
