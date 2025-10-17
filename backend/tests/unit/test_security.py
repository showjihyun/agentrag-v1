"""Unit tests for security utilities."""

import pytest
from datetime import datetime, timedelta

from backend.core.security import SecurityManager
from backend.core.validators import (
    EmailValidator,
    PasswordValidator,
    UsernameValidator,
    QueryValidator,
)


class TestSecurityManager:
    """Test SecurityManager functionality."""

    def test_generate_token(self):
        """Test token generation."""
        manager = SecurityManager()

        token1 = manager.generate_token()
        token2 = manager.generate_token()

        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2  # Should be unique

    def test_hash_data(self):
        """Test data hashing."""
        manager = SecurityManager()

        hash1 = manager.hash_data("test data")
        hash2 = manager.hash_data("test data")
        hash3 = manager.hash_data("different data")

        assert hash1 == hash2  # Same input = same hash
        assert hash1 != hash3  # Different input = different hash
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        manager = SecurityManager()
        identifier = "test@example.com"

        # First attempts should be allowed
        for i in range(5):
            is_allowed, _ = manager.check_rate_limit(identifier, "login")
            assert is_allowed
            manager.record_attempt(identifier, "login")

        # 6th attempt should be blocked
        is_allowed, seconds = manager.check_rate_limit(identifier, "login")
        assert not is_allowed
        assert seconds is not None
        assert seconds > 0

    def test_reset_attempts(self):
        """Test resetting rate limit attempts."""
        manager = SecurityManager()
        identifier = "test@example.com"

        # Record max attempts
        for i in range(5):
            manager.record_attempt(identifier, "login")

        # Should be blocked
        is_allowed, _ = manager.check_rate_limit(identifier, "login")
        assert not is_allowed

        # Reset attempts
        manager.reset_attempts(identifier, "login")

        # Should be allowed again
        is_allowed, _ = manager.check_rate_limit(identifier, "login")
        assert is_allowed

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        manager = SecurityManager()

        # Test path traversal prevention
        assert manager.sanitize_filename("../../etc/passwd") == "passwd"
        assert manager.sanitize_filename("..\\..\\windows\\system32") == "system32"

        # Test dangerous character removal
        assert manager.sanitize_filename("file<>:name.txt") == "file___name.txt"

        # Test length limiting
        long_name = "a" * 300 + ".txt"
        sanitized = manager.sanitize_filename(long_name)
        assert len(sanitized) <= 255

    def test_validate_file_type(self):
        """Test file type validation."""
        manager = SecurityManager()

        # Valid types
        assert manager.validate_file_type("document.pdf")
        assert manager.validate_file_type("notes.txt")
        assert manager.validate_file_type("report.docx")

        # Invalid types
        assert not manager.validate_file_type("script.exe")
        assert not manager.validate_file_type("malware.bat")
        assert not manager.validate_file_type("file.unknown")

    def test_check_file_size(self):
        """Test file size validation."""
        manager = SecurityManager()

        # Valid sizes
        assert manager.check_file_size(1024)  # 1 KB
        assert manager.check_file_size(1024 * 1024)  # 1 MB
        assert manager.check_file_size(10 * 1024 * 1024)  # 10 MB

        # Invalid sizes
        assert not manager.check_file_size(
            100 * 1024 * 1024
        )  # 100 MB (exceeds default 50 MB)


class TestEmailValidator:
    """Test email validation."""

    def test_valid_emails(self):
        """Test valid email formats."""
        assert EmailValidator.is_valid("user@example.com")
        assert EmailValidator.is_valid("test.user@example.co.uk")
        assert EmailValidator.is_valid("user+tag@example.com")

    def test_invalid_emails(self):
        """Test invalid email formats."""
        assert not EmailValidator.is_valid("invalid")
        assert not EmailValidator.is_valid("@example.com")
        assert not EmailValidator.is_valid("user@")
        assert not EmailValidator.is_valid("user @example.com")


class TestPasswordValidator:
    """Test password validation."""

    def test_valid_passwords(self):
        """Test valid passwords."""
        is_valid, error = PasswordValidator.validate("Password123")
        assert is_valid
        assert error is None

        is_valid, error = PasswordValidator.validate("MySecure123Pass")
        assert is_valid
        assert error is None

    def test_too_short(self):
        """Test password too short."""
        is_valid, error = PasswordValidator.validate("Pass1")
        assert not is_valid
        assert "at least" in error

    def test_no_letter(self):
        """Test password without letter."""
        is_valid, error = PasswordValidator.validate("12345678")
        assert not is_valid
        assert "letter" in error

    def test_no_number(self):
        """Test password without number."""
        is_valid, error = PasswordValidator.validate("Password")
        assert not is_valid
        assert "number" in error


class TestUsernameValidator:
    """Test username validation."""

    def test_valid_usernames(self):
        """Test valid usernames."""
        is_valid, error = UsernameValidator.validate("user123")
        assert is_valid
        assert error is None

        is_valid, error = UsernameValidator.validate("test_user")
        assert is_valid
        assert error is None

    def test_too_short(self):
        """Test username too short."""
        is_valid, error = UsernameValidator.validate("ab")
        assert not is_valid
        assert "at least" in error

    def test_invalid_characters(self):
        """Test username with invalid characters."""
        is_valid, error = UsernameValidator.validate("user@name")
        assert not is_valid
        assert "can only contain" in error


class TestQueryValidator:
    """Test query validation."""

    def test_valid_queries(self):
        """Test valid queries."""
        is_valid, error = QueryValidator.validate("What is machine learning?")
        assert is_valid
        assert error is None

    def test_empty_query(self):
        """Test empty query."""
        is_valid, error = QueryValidator.validate("")
        assert not is_valid
        assert "empty" in error

    def test_too_long(self):
        """Test query too long."""
        long_query = "a" * 6000
        is_valid, error = QueryValidator.validate(long_query)
        assert not is_valid
        assert "at most" in error
