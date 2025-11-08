"""Tests for OAuth authentication system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from backend.core.tools.oauth import OAuthManager, OAuthError, OAuthCredential, OAuthState


class TestOAuthManager:
    """Test OAuth Manager functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock(spec=Session)
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.delete = Mock()
        return db
    
    @pytest.fixture
    def oauth_manager(self, mock_db):
        """Create OAuth manager instance."""
        return OAuthManager(mock_db)
    
    def test_generate_auth_url(self, oauth_manager, mock_db):
        """Test generating OAuth authorization URL."""
        # Generate auth URL
        result = oauth_manager.generate_auth_url(
            tool_id="test_tool",
            user_id="user123",
            auth_url="https://example.com/oauth/authorize",
            client_id="client123",
            redirect_uri="https://app.com/callback",
            scopes=["read", "write"]
        )
        
        # Verify result
        assert "auth_url" in result
        assert "state" in result
        assert "https://example.com/oauth/authorize" in result["auth_url"]
        assert "client_id=client123" in result["auth_url"]
        assert "scope=read+write" in result["auth_url"]
        
        # Verify state was stored
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, oauth_manager, mock_db):
        """Test successful token exchange."""
        # Mock OAuth state
        mock_state = Mock(spec=OAuthState)
        mock_state.user_id = "user123"
        mock_state.tool_id = "test_tool"
        mock_state.expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_state
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "access123",
            "refresh_token": "refresh123",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            # Exchange code for token
            result = await oauth_manager.exchange_code_for_token(
                code="auth_code",
                state="state123",
                token_url="https://example.com/oauth/token",
                client_id="client123",
                client_secret="secret123",
                redirect_uri="https://app.com/callback"
            )
            
            # Verify result
            assert result["access_token"] == "access123"
            assert result["refresh_token"] == "refresh123"
            
            # Verify state was deleted
            mock_db.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exchange_code_invalid_state(self, oauth_manager, mock_db):
        """Test token exchange with invalid state."""
        # Mock no state found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Attempt token exchange
        with pytest.raises(OAuthError) as exc_info:
            await oauth_manager.exchange_code_for_token(
                code="auth_code",
                state="invalid_state",
                token_url="https://example.com/oauth/token",
                client_id="client123",
                client_secret="secret123",
                redirect_uri="https://app.com/callback"
            )
        
        assert exc_info.value.error_code == "invalid_state"
    
    @pytest.mark.asyncio
    async def test_get_credentials_valid(self, oauth_manager, mock_db):
        """Test getting valid credentials."""
        # Mock credential
        mock_credential = Mock(spec=OAuthCredential)
        mock_credential.access_token = "access123"
        mock_credential.token_type = "Bearer"
        mock_credential.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_credential.refresh_token = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_credential
        
        # Get credentials
        result = await oauth_manager.get_credentials(
            user_id="user123",
            tool_id="test_tool",
            auto_refresh=False
        )
        
        # Verify result
        assert result is not None
        assert result["access_token"] == "access123"
        assert result["token_type"] == "Bearer"
    
    @pytest.mark.asyncio
    async def test_get_credentials_not_found(self, oauth_manager, mock_db):
        """Test getting credentials when none exist."""
        # Mock no credential found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Get credentials
        result = await oauth_manager.get_credentials(
            user_id="user123",
            tool_id="test_tool"
        )
        
        # Verify result
        assert result is None
    
    def test_revoke_credentials(self, oauth_manager, mock_db):
        """Test revoking credentials."""
        # Mock credential
        mock_credential = Mock(spec=OAuthCredential)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_credential
        
        # Revoke credentials
        oauth_manager.revoke_credentials(
            user_id="user123",
            tool_id="test_tool"
        )
        
        # Verify credential was deleted
        mock_db.delete.assert_called_once_with(mock_credential)
        mock_db.commit.assert_called_once()
    
    def test_cleanup_expired_states(self, oauth_manager, mock_db):
        """Test cleaning up expired OAuth states."""
        # Mock expired states
        expired_state1 = Mock(spec=OAuthState)
        expired_state2 = Mock(spec=OAuthState)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [
            expired_state1,
            expired_state2
        ]
        
        # Cleanup expired states
        oauth_manager.cleanup_expired_states()
        
        # Verify states were deleted
        assert mock_db.delete.call_count == 2
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
