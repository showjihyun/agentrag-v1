"""OAuth authentication system for tool integrations.

This module provides OAuth 2.0 authentication flow for tools that require it.
"""

import logging
import secrets
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx

from sqlalchemy.orm import Session

# Import OAuth models from models directory
from backend.db.models.oauth import OAuthCredential, OAuthState

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """Exception raised for OAuth-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class OAuthManager:
    """
    Manager for OAuth 2.0 authentication flows.
    
    Handles authorization URL generation, token exchange, token refresh,
    and credential storage.
    """
    
    def __init__(self, db: Session):
        """
        Initialize OAuthManager.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def generate_auth_url(
        self,
        tool_id: str,
        user_id: str,
        auth_url: str,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
        additional_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Generate OAuth authorization URL.
        
        Args:
            tool_id: Tool identifier
            user_id: User identifier
            auth_url: OAuth authorization endpoint
            client_id: OAuth client ID
            redirect_uri: Redirect URI after authorization
            scopes: List of OAuth scopes
            additional_params: Additional query parameters
            
        Returns:
            Dict with 'auth_url' and 'state'
        """
        # Generate state token
        state = secrets.token_urlsafe(32)
        
        # Store state in database
        oauth_state = OAuthState(
            state=state,
            user_id=user_id,
            tool_id=tool_id,
            redirect_uri=redirect_uri,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        self.db.add(oauth_state)
        self.db.commit()
        
        # Build authorization URL
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }
        
        if additional_params:
            params.update(additional_params)
        
        auth_url_with_params = f"{auth_url}?{urlencode(params)}"
        
        logger.info(f"Generated OAuth URL for tool {tool_id}, user {user_id}")
        
        return {
            "auth_url": auth_url_with_params,
            "state": state
        }
    
    async def exchange_code_for_token(
        self,
        code: str,
        state: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            state: State token
            token_url: OAuth token endpoint
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI
            
        Returns:
            Token response data
            
        Raises:
            OAuthError: If token exchange fails
        """
        # Verify state
        oauth_state = self.db.query(OAuthState).filter(
            OAuthState.state == state
        ).first()
        
        if not oauth_state:
            raise OAuthError("Invalid state token", "invalid_state")
        
        if oauth_state.expires_at < datetime.utcnow():
            self.db.delete(oauth_state)
            self.db.commit()
            raise OAuthError("State token expired", "expired_state")
        
        # Exchange code for token
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_message = error_data.get("error_description", "Token exchange failed")
                    raise OAuthError(error_message, error_data.get("error"))
                
                token_data = response.json()
                
                # Store credentials
                await self._store_credentials(
                    user_id=oauth_state.user_id,
                    tool_id=oauth_state.tool_id,
                    token_data=token_data
                )
                
                # Clean up state
                self.db.delete(oauth_state)
                self.db.commit()
                
                logger.info(
                    f"Successfully exchanged code for token: "
                    f"tool={oauth_state.tool_id}, user={oauth_state.user_id}"
                )
                
                return token_data
                
        except httpx.RequestError as e:
            raise OAuthError(f"Token exchange request failed: {str(e)}", "request_error")
    
    async def _store_credentials(
        self,
        user_id: str,
        tool_id: str,
        token_data: Dict[str, Any]
    ):
        """
        Store OAuth credentials in database.
        
        Args:
            user_id: User identifier
            tool_id: Tool identifier
            token_data: Token response data
        """
        # Calculate expiration
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        
        # Check if credentials already exist
        credential = self.db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.tool_id == tool_id
        ).first()
        
        if credential:
            # Update existing credentials
            credential.access_token = token_data["access_token"]
            credential.refresh_token = token_data.get("refresh_token")
            credential.token_type = token_data.get("token_type", "Bearer")
            credential.expires_at = expires_at
            credential.scope = token_data.get("scope")
            credential.updated_at = datetime.utcnow()
        else:
            # Create new credentials
            credential = OAuthCredential(
                id=f"{user_id}_{tool_id}_{secrets.token_urlsafe(8)}",
                user_id=user_id,
                tool_id=tool_id,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                expires_at=expires_at,
                scope=token_data.get("scope")
            )
            self.db.add(credential)
        
        self.db.commit()
    
    async def get_credentials(
        self,
        user_id: str,
        tool_id: str,
        auto_refresh: bool = True
    ) -> Optional[Dict[str, str]]:
        """
        Get OAuth credentials for a user and tool.
        
        Args:
            user_id: User identifier
            tool_id: Tool identifier
            auto_refresh: Automatically refresh expired tokens
            
        Returns:
            Dict with 'access_token' and 'token_type' or None
        """
        credential = self.db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.tool_id == tool_id
        ).first()
        
        if not credential:
            return None
        
        # Check if token is expired
        if credential.expires_at and credential.expires_at < datetime.utcnow():
            if auto_refresh and credential.refresh_token:
                # Attempt to refresh token
                try:
                    await self.refresh_token(user_id, tool_id)
                    # Reload credential
                    self.db.refresh(credential)
                except OAuthError as e:
                    logger.error(f"Failed to refresh token: {e.message}")
                    return None
            else:
                logger.warning(f"Token expired for user {user_id}, tool {tool_id}")
                return None
        
        return {
            "access_token": credential.access_token,
            "token_type": credential.token_type
        }
    
    async def refresh_token(
        self,
        user_id: str,
        tool_id: str,
        token_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Refresh OAuth access token.
        
        Args:
            user_id: User identifier
            tool_id: Tool identifier
            token_url: OAuth token endpoint (required if not stored)
            client_id: OAuth client ID (required if not stored)
            client_secret: OAuth client secret (required if not stored)
            
        Raises:
            OAuthError: If token refresh fails
        """
        credential = self.db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.tool_id == tool_id
        ).first()
        
        if not credential or not credential.refresh_token:
            raise OAuthError("No refresh token available", "no_refresh_token")
        
        if not all([token_url, client_id, client_secret]):
            raise OAuthError(
                "Token URL, client ID, and client secret required for refresh",
                "missing_config"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": credential.refresh_token,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_message = error_data.get("error_description", "Token refresh failed")
                    raise OAuthError(error_message, error_data.get("error"))
                
                token_data = response.json()
                
                # Update credentials
                await self._store_credentials(user_id, tool_id, token_data)
                
                logger.info(f"Successfully refreshed token for user {user_id}, tool {tool_id}")
                
        except httpx.RequestError as e:
            raise OAuthError(f"Token refresh request failed: {str(e)}", "request_error")
    
    def revoke_credentials(self, user_id: str, tool_id: str):
        """
        Revoke OAuth credentials.
        
        Args:
            user_id: User identifier
            tool_id: Tool identifier
        """
        credential = self.db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.tool_id == tool_id
        ).first()
        
        if credential:
            self.db.delete(credential)
            self.db.commit()
            logger.info(f"Revoked credentials for user {user_id}, tool {tool_id}")
    
    def cleanup_expired_states(self):
        """Clean up expired OAuth states."""
        expired_states = self.db.query(OAuthState).filter(
            OAuthState.expires_at < datetime.utcnow()
        ).all()
        
        for state in expired_states:
            self.db.delete(state)
        
        self.db.commit()
        logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")
