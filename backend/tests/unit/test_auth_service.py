"""
Unit tests for AuthService
"""

import pytest
from datetime import datetime, timedelta
from backend.services.auth_service import AuthService
from config import settings


class TestAuthService:
    """Test suite for AuthService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.auth_service = AuthService()

    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = self.auth_service.hash_password(password)

        # Check that hash is different from password
        assert hashed != password

        # Check that hash is a string
        assert isinstance(hashed, str)

        # Check that hash starts with bcrypt prefix
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = self.auth_service.hash_password(password)

        # Verify correct password
        assert self.auth_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = self.auth_service.hash_password(password)

        # Verify incorrect password
        assert self.auth_service.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test access token creation"""
        user_id = 1
        token = self.auth_service.create_access_token(user_id)

        # Check that token is a string
        assert isinstance(token, str)

        # Check that token has 3 parts (header.payload.signature)
        assert len(token.split(".")) == 3

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = 1
        token = self.auth_service.create_refresh_token(user_id)

        # Check that token is a string
        assert isinstance(token, str)

        # Check that token has 3 parts
        assert len(token.split(".")) == 3

    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        user_id = 1
        token = self.auth_service.create_access_token(user_id)

        # Verify token
        payload = self.auth_service.verify_token(token)

        # Check payload
        assert payload is not None
        assert payload["user_id"] == user_id
        assert "exp" in payload

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.here"

        # Verify token should return None
        payload = self.auth_service.verify_token(invalid_token)
        assert payload is None

    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        user_id = 1

        # Create token that expires immediately
        token = self.auth_service.create_access_token(
            user_id, expires_delta=timedelta(seconds=-1)
        )

        # Verify token should return None
        payload = self.auth_service.verify_token(token)
        assert payload is None

    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password"""
        valid_passwords = ["Password123!", "MyP@ssw0rd", "Str0ng!Pass", "Test1234!@#$"]

        for password in valid_passwords:
            is_valid, message = self.auth_service.validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid"

    def test_validate_password_strength_too_short(self):
        """Test password strength validation with short password"""
        short_password = "Pass1!"

        is_valid, message = self.auth_service.validate_password_strength(short_password)
        assert is_valid is False
        assert "at least 8 characters" in message.lower()

    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation without uppercase"""
        no_upper = "password123!"

        is_valid, message = self.auth_service.validate_password_strength(no_upper)
        assert is_valid is False
        assert "uppercase" in message.lower()

    def test_validate_password_strength_no_lowercase(self):
        """Test password strength validation without lowercase"""
        no_lower = "PASSWORD123!"

        is_valid, message = self.auth_service.validate_password_strength(no_lower)
        assert is_valid is False
        assert "lowercase" in message.lower()

    def test_validate_password_strength_no_digit(self):
        """Test password strength validation without digit"""
        no_digit = "Password!"

        is_valid, message = self.auth_service.validate_password_strength(no_digit)
        assert is_valid is False
        assert "digit" in message.lower()

    def test_validate_password_strength_no_special(self):
        """Test password strength validation without special character"""
        no_special = "Password123"

        is_valid, message = self.auth_service.validate_password_strength(no_special)
        assert is_valid is False
        assert "special character" in message.lower()

    def test_token_expiration_times(self):
        """Test that tokens have correct expiration times"""
        user_id = 1

        # Create access token
        access_token = self.auth_service.create_access_token(user_id)
        access_payload = self.auth_service.verify_token(access_token)

        # Create refresh token
        refresh_token = self.auth_service.create_refresh_token(user_id)
        refresh_payload = self.auth_service.verify_token(refresh_token)

        # Check that refresh token expires later than access token
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_different_users_different_tokens(self):
        """Test that different users get different tokens"""
        user1_token = self.auth_service.create_access_token(1)
        user2_token = self.auth_service.create_access_token(2)

        # Tokens should be different
        assert user1_token != user2_token

        # Verify tokens contain correct user IDs
        user1_payload = self.auth_service.verify_token(user1_token)
        user2_payload = self.auth_service.verify_token(user2_token)

        assert user1_payload["user_id"] == 1
        assert user2_payload["user_id"] == 2
