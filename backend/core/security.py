"""Security utilities and middleware."""

import secrets
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    """Centralized security management."""

    # Rate limiting configuration
    RATE_LIMITS = {
        "login": {"max_attempts": 5, "window_minutes": 15},
        "register": {"max_attempts": 3, "window_minutes": 60},
        "query": {"max_attempts": 100, "window_minutes": 60},
        "upload": {"max_attempts": 20, "window_minutes": 60},
    }

    def __init__(self):
        """Initialize security manager."""
        self._failed_attempts: Dict[str, list] = {}

    def generate_token(self, length: int = 32) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(length)

    def hash_data(self, data: str) -> str:
        """Generate SHA-256 hash of data."""
        return hashlib.sha256(data.encode()).hexdigest()

    def check_rate_limit(
        self, identifier: str, action: str
    ) -> tuple[bool, Optional[int]]:
        """
        Check if action is rate limited.

        Args:
            identifier: User identifier (email, IP, etc.)
            action: Action type (login, register, query, upload)

        Returns:
            Tuple of (is_allowed, seconds_until_reset)
        """
        if action not in self.RATE_LIMITS:
            return True, None

        config = self.RATE_LIMITS[action]
        key = f"{action}:{identifier}"

        # Initialize if not exists
        if key not in self._failed_attempts:
            self._failed_attempts[key] = []

        # Clean old attempts
        cutoff = datetime.utcnow() - timedelta(minutes=config["window_minutes"])
        self._failed_attempts[key] = [
            attempt for attempt in self._failed_attempts[key] if attempt > cutoff
        ]

        # Check limit
        if len(self._failed_attempts[key]) >= config["max_attempts"]:
            oldest_attempt = min(self._failed_attempts[key])
            reset_time = oldest_attempt + timedelta(minutes=config["window_minutes"])
            seconds_until_reset = int((reset_time - datetime.utcnow()).total_seconds())

            logger.warning(
                f"Rate limit exceeded for {identifier} on {action}. "
                f"Reset in {seconds_until_reset}s"
            )
            return False, seconds_until_reset

        return True, None

    def record_attempt(self, identifier: str, action: str):
        """Record an attempt for rate limiting."""
        if action not in self.RATE_LIMITS:
            return

        key = f"{action}:{identifier}"

        if key not in self._failed_attempts:
            self._failed_attempts[key] = []

        self._failed_attempts[key].append(datetime.utcnow())

    def reset_attempts(self, identifier: str, action: str):
        """Reset attempts for an identifier."""
        key = f"{action}:{identifier}"
        if key in self._failed_attempts:
            del self._failed_attempts[key]

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Remove dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\0"]
        for char in dangerous_chars:
            filename = filename.replace(char, "_")

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:250] + ("." + ext if ext else "")

        return filename

    def validate_file_type(
        self, filename: str, allowed_extensions: Optional[list] = None
    ) -> bool:
        """
        Validate file type by extension.

        Args:
            filename: Filename to validate
            allowed_extensions: List of allowed extensions (default: pdf, txt, docx)

        Returns:
            True if file type is allowed
        """
        if allowed_extensions is None:
            allowed_extensions = ["pdf", "txt", "docx", "doc", "md"]

        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        is_valid = extension in allowed_extensions

        if not is_valid:
            logger.warning(f"Invalid file type: {extension} (file: {filename})")

        return is_valid

    def check_file_size(self, file_size: int, max_size_mb: int = 50) -> bool:
        """
        Check if file size is within limits.

        Args:
            file_size: File size in bytes
            max_size_mb: Maximum allowed size in MB

        Returns:
            True if file size is acceptable
        """
        max_bytes = max_size_mb * 1024 * 1024

        is_valid = file_size <= max_bytes

        if not is_valid:
            logger.warning(
                f"File size {file_size} bytes exceeds limit of {max_bytes} bytes"
            )

        return is_valid


# Global security manager instance
security_manager = SecurityManager()
