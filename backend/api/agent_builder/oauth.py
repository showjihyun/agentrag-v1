"""OAuth API endpoints for tool authentication."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.core.tools.oauth import OAuthManager, OAuthError
from backend.core.tools.registry import ToolRegistry
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])


class OAuthInitRequest(BaseModel):
    """Request to initiate OAuth flow."""
    tool_id: str
    redirect_uri: str


class OAuthInitResponse(BaseModel):
    """Response with OAuth authorization URL."""
    auth_url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response after OAuth callback."""
    success: bool
    message: str
    tool_id: Optional[str] = None


class OAuthStatusResponse(BaseModel):
    """OAuth credential status."""
    tool_id: str
    is_authenticated: bool
    expires_at: Optional[str] = None


@router.post("/init", response_model=OAuthInitResponse)
async def init_oauth_flow(
    request: OAuthInitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate OAuth authentication flow.
    
    Args:
        request: OAuth initialization request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Authorization URL and state token
    """
    # Get tool configuration
    tool_config = ToolRegistry.get_tool_config(request.tool_id)
    if not tool_config:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if not tool_config.oauth:
        raise HTTPException(status_code=400, detail="Tool does not support OAuth")
    
    # Get OAuth configuration from environment
    import os
    client_id = os.getenv(tool_config.oauth.client_id_env)
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth client ID not configured: {tool_config.oauth.client_id_env}"
        )
    
    # Initialize OAuth manager
    oauth_manager = OAuthManager(db)
    
    try:
        # Generate authorization URL
        result = oauth_manager.generate_auth_url(
            tool_id=request.tool_id,
            user_id=str(current_user.id),
            auth_url=tool_config.oauth.auth_url,
            client_id=client_id,
            redirect_uri=request.redirect_uri,
            scopes=tool_config.oauth.scopes
        )
        
        return OAuthInitResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to initiate OAuth flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    error: Optional[str] = Query(None, description="Error code"),
    error_description: Optional[str] = Query(None, description="Error description"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback.
    
    Args:
        code: Authorization code
        state: State token
        error: Error code (if authorization failed)
        error_description: Error description
        db: Database session
        
    Returns:
        Redirect to success/error page
    """
    # Check for errors
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        return RedirectResponse(
            url=f"/agent-builder/oauth/error?error={error}&description={error_description}"
        )
    
    # Initialize OAuth manager
    oauth_manager = OAuthManager(db)
    
    try:
        # Get state from database to retrieve tool_id
        from backend.core.tools.oauth import OAuthState
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        
        if not oauth_state:
            raise OAuthError("Invalid state token", "invalid_state")
        
        tool_id = oauth_state.tool_id
        
        # Get tool configuration
        tool_config = ToolRegistry.get_tool_config(tool_id)
        if not tool_config or not tool_config.oauth:
            raise OAuthError("Tool configuration not found", "invalid_tool")
        
        # Get OAuth credentials from environment
        import os
        client_id = os.getenv(tool_config.oauth.client_id_env)
        client_secret = os.getenv(tool_config.oauth.client_secret_env)
        
        if not client_id or not client_secret:
            raise OAuthError("OAuth credentials not configured", "missing_config")
        
        # Exchange code for token
        await oauth_manager.exchange_code_for_token(
            code=code,
            state=state,
            token_url=tool_config.oauth.token_url,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=oauth_state.redirect_uri
        )
        
        # Redirect to success page
        return RedirectResponse(
            url=f"/agent-builder/oauth/success?tool_id={tool_id}"
        )
        
    except OAuthError as e:
        logger.error(f"OAuth callback error: {e.message}")
        return RedirectResponse(
            url=f"/agent-builder/oauth/error?error={e.error_code}&description={e.message}"
        )
    except Exception as e:
        logger.error(f"Unexpected OAuth callback error: {e}")
        return RedirectResponse(
            url=f"/agent-builder/oauth/error?error=unexpected&description={str(e)}"
        )


@router.get("/status/{tool_id}", response_model=OAuthStatusResponse)
async def get_oauth_status(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get OAuth authentication status for a tool.
    
    Args:
        tool_id: Tool identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        OAuth status
    """
    oauth_manager = OAuthManager(db)
    
    try:
        credentials = await oauth_manager.get_credentials(
            user_id=str(current_user.id),
            tool_id=tool_id,
            auto_refresh=False
        )
        
        if credentials:
            # Get expiration time
            from backend.core.tools.oauth import OAuthCredential
            credential = db.query(OAuthCredential).filter(
                OAuthCredential.user_id == str(current_user.id),
                OAuthCredential.tool_id == tool_id
            ).first()
            
            expires_at = None
            if credential and credential.expires_at:
                expires_at = credential.expires_at.isoformat()
            
            return OAuthStatusResponse(
                tool_id=tool_id,
                is_authenticated=True,
                expires_at=expires_at
            )
        else:
            return OAuthStatusResponse(
                tool_id=tool_id,
                is_authenticated=False
            )
            
    except Exception as e:
        logger.error(f"Failed to get OAuth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/revoke/{tool_id}")
async def revoke_oauth(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke OAuth credentials for a tool.
    
    Args:
        tool_id: Tool identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    oauth_manager = OAuthManager(db)
    
    try:
        oauth_manager.revoke_credentials(
            user_id=str(current_user.id),
            tool_id=tool_id
        )
        
        return {"success": True, "message": "Credentials revoked"}
        
    except Exception as e:
        logger.error(f"Failed to revoke OAuth credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))
