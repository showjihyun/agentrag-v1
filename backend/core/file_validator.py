"""
File validation utilities for secure file upload handling.

This module provides comprehensive file validation including:
- File size limits
- MIME type verification
- Extension validation
- Malicious content detection
"""

import logging
from typing import Tuple, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class FileValidator:
    """
    Comprehensive file validator for secure uploads.

    Features:
    - File size validation
    - MIME type verification (actual content, not just extension)
    - Extension whitelist
    - Filename length limits
    - Dangerous extension blocking
    - Basic malicious content detection
    """

    # Allowed MIME types and their corresponding extensions
    ALLOWED_MIME_TYPES = {
        "application/pdf": [".pdf"],
        "text/plain": [".txt"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
            ".docx"
        ],
        "application/msword": [".doc"],
        "application/x-hwp": [".hwp"],
        "application/haansofthwp": [".hwpx"],
        "application/vnd.hancom.hwp": [".hwp"],
    }

    # Maximum filename length
    MAX_FILENAME_LENGTH = 255

    # Dangerous extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        ".exe",
        ".bat",
        ".cmd",
        ".sh",
        ".ps1",
        ".vbs",
        ".js",
        ".jar",
        ".app",
        ".deb",
        ".rpm",
        ".dmg",
        ".pkg",
        ".scr",
        ".com",
        ".pif",
        ".msi",
        ".dll",
        ".so",
    }

    # Suspicious patterns in file content (first 1KB)
    SUSPICIOUS_PATTERNS = [
        b"<script",
        b"<?php",
        b"eval(",
        b"exec(",
        b"system(",
        b"passthru(",
        b"shell_exec(",
        b"base64_decode(",
    ]

    @classmethod
    async def validate_file(
        cls, file_content: bytes, filename: str, max_size_bytes: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive file validation.

        Args:
            file_content: File content as bytes
            filename: Original filename
            max_size_bytes: Maximum allowed file size

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file passes all validations
            - error_message: None if valid, error description if invalid
        """
        # 1. File size validation
        if len(file_content) == 0:
            return False, "File is empty"

        if len(file_content) > max_size_bytes:
            size_mb = len(file_content) / (1024 * 1024)
            max_mb = max_size_bytes / (1024 * 1024)
            return False, f"File too large: {size_mb:.2f}MB (max: {max_mb:.2f}MB)"

        # 2. Filename validation
        if not filename or not filename.strip():
            return False, "Filename is required"

        if len(filename) > cls.MAX_FILENAME_LENGTH:
            return (
                False,
                f"Filename too long: {len(filename)} chars (max: {cls.MAX_FILENAME_LENGTH})",
            )

        # 3. Extension validation
        file_ext = Path(filename).suffix.lower()

        if not file_ext:
            return False, "File must have an extension"

        if file_ext in cls.DANGEROUS_EXTENSIONS:
            return False, f"Dangerous file extension not allowed: {file_ext}"

        # 4. Check if extension is in allowed list
        allowed_extensions = set()
        for extensions in cls.ALLOWED_MIME_TYPES.values():
            allowed_extensions.update(extensions)

        if file_ext not in allowed_extensions:
            return False, f"File type not supported: {file_ext}"

        # 5. MIME type validation (if python-magic is available)
        try:
            import magic

            mime_type = magic.from_buffer(file_content, mime=True)

            if mime_type not in cls.ALLOWED_MIME_TYPES:
                return False, f"Invalid file type detected: {mime_type}"

            # Verify extension matches MIME type
            expected_extensions = cls.ALLOWED_MIME_TYPES[mime_type]
            if file_ext not in expected_extensions:
                return False, (
                    f"File extension {file_ext} doesn't match detected type {mime_type}. "
                    f"Expected one of: {', '.join(expected_extensions)}"
                )

            logger.debug(
                f"File validated: {filename} - MIME: {mime_type}, Size: {len(file_content)} bytes"
            )

        except ImportError:
            # python-magic not installed, skip MIME validation
            logger.warning(
                "python-magic not installed. MIME type validation skipped. "
                "Install with: pip install python-magic"
            )
        except Exception as e:
            logger.error(f"MIME type detection failed: {e}")
            return False, f"Failed to detect file type: {str(e)}"

        # 6. Basic malicious content detection
        # Check first 1KB for suspicious patterns
        content_sample = file_content[:1024]

        for pattern in cls.SUSPICIOUS_PATTERNS:
            if pattern in content_sample:
                logger.warning(
                    f"Suspicious pattern detected in file: {filename}",
                    extra={"pattern": pattern.decode("utf-8", errors="ignore")},
                )
                return False, "Potentially malicious content detected"

        # 7. Null byte injection check
        if b"\x00" in filename.encode("utf-8", errors="ignore"):
            return False, "Invalid characters in filename"

        # All validations passed
        return True, None

    @classmethod
    def get_allowed_extensions(cls) -> Set[str]:
        """
        Get set of all allowed file extensions.

        Returns:
            Set of allowed extensions (e.g., {'.pdf', '.txt', '.docx'})
        """
        extensions = set()
        for exts in cls.ALLOWED_MIME_TYPES.values():
            extensions.update(exts)
        return extensions

    @classmethod
    def is_extension_allowed(cls, filename: str) -> bool:
        """
        Quick check if file extension is allowed.

        Args:
            filename: Filename to check

        Returns:
            True if extension is allowed
        """
        file_ext = Path(filename).suffix.lower()
        return file_ext in cls.get_allowed_extensions()
