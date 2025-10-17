"""
File Storage Service for handling file operations.

Provides secure file storage with user isolation, validation, and cleanup.
Supports local filesystem storage with future extensibility for S3/MinIO.
"""

import logging
import os
import re
import shutil
from pathlib import Path
from typing import Tuple, Optional
from uuid import UUID

from fastapi import UploadFile

logger = logging.getLogger(__name__)


class FileStorageError(Exception):
    """Custom exception for file storage errors."""

    pass


class FileStorageService:
    """
    Service for managing file storage operations.

    Features:
    - User-isolated storage (uploads/{user_id}/)
    - File validation (type and size)
    - Filename sanitization
    - Secure file operations
    - Cleanup on errors
    """

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".md": "text/markdown",
        ".hwp": "application/x-hwp",
        ".hwpx": "application/x-hwpx",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
        ".json": "application/json",
        # Image formats (OCR support)
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }

    # Maximum filename length
    MAX_FILENAME_LENGTH = 255

    def __init__(self, base_path: str = "./uploads"):
        """
        Initialize FileStorageService.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self._ensure_base_directory()

        logger.info(f"FileStorageService initialized with base_path: {self.base_path}")

    def _ensure_base_directory(self) -> None:
        """Ensure base storage directory exists."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Base directory ensured: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create base directory: {e}")
            raise FileStorageError(f"Failed to create base directory: {e}")

    def ensure_user_directory(self, user_id: UUID) -> str:
        """
        Ensure user-specific directory exists.

        Args:
            user_id: User's unique identifier

        Returns:
            str: Path to user directory

        Raises:
            FileStorageError: If directory creation fails
        """
        user_dir = self.base_path / str(user_id)

        try:
            user_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"User directory ensured: {user_dir}")
            return str(user_dir)
        except Exception as e:
            logger.error(f"Failed to create user directory for {user_id}: {e}")
            raise FileStorageError(f"Failed to create user directory: {e}")

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent security issues.

        Removes special characters, prevents path traversal,
        and limits filename length.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename

        Raises:
            ValueError: If filename is invalid
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Remove any path components first (prevent directory traversal)
        filename = os.path.basename(filename)

        # Get file extension
        name_parts = filename.rsplit(".", 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            ext = f".{ext.lower()}"
        else:
            name = filename
            ext = ""

        # Remove or replace special characters
        # Allow: alphanumeric, spaces, hyphens, underscores
        name = re.sub(r"[^\w\s\-]", "", name)

        # Replace spaces with underscores
        name = name.replace(" ", "_")

        # Remove multiple consecutive underscores
        name = re.sub(r"_+", "_", name)

        # Remove leading/trailing underscores
        name = name.strip("_")

        # Ensure name is not empty after sanitization
        if not name:
            name = "file"

        # Reconstruct filename
        sanitized = f"{name}{ext}"

        # Limit length
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            # Truncate name but keep extension
            max_name_length = self.MAX_FILENAME_LENGTH - len(ext)
            name = name[:max_name_length]
            sanitized = f"{name}{ext}"

        logger.debug(f"Sanitized filename: '{filename}' -> '{sanitized}'")
        return sanitized

    def validate_file_type(self, filename: str) -> bool:
        """
        Validate file type based on extension.

        Args:
            filename: Name of the file

        Returns:
            bool: True if file type is allowed
        """
        ext = Path(filename).suffix.lower()
        is_valid = ext in self.ALLOWED_EXTENSIONS

        if not is_valid:
            logger.warning(f"Invalid file type: {ext} (file: {filename})")

        return is_valid

    def validate_file_size(self, size: int, max_size: int) -> bool:
        """
        Validate file size against maximum limit.

        Args:
            size: File size in bytes
            max_size: Maximum allowed size in bytes

        Returns:
            bool: True if file size is within limit
        """
        is_valid = 0 < size <= max_size

        if not is_valid:
            logger.warning(
                f"Invalid file size: {size} bytes "
                f"(max: {max_size} bytes, {max_size / 1024 / 1024:.1f} MB)"
            )

        return is_valid

    def get_file_path(self, user_id: UUID, filename: str) -> str:
        """
        Get full file path for a user's file.

        Args:
            user_id: User's unique identifier
            filename: Name of the file

        Returns:
            str: Full path to the file
        """
        user_dir = self.base_path / str(user_id)
        file_path = user_dir / filename
        return str(file_path)

    async def save_file(self, file: UploadFile, user_id: UUID) -> Tuple[str, int]:
        """
        Save uploaded file to user's directory.

        Args:
            file: Uploaded file object
            user_id: User's unique identifier

        Returns:
            Tuple[str, int]: (file_path, file_size)

        Raises:
            FileStorageError: If file save fails
            ValueError: If file validation fails
        """
        try:
            # Validate file type
            if not self.validate_file_type(file.filename):
                allowed = ", ".join(self.ALLOWED_EXTENSIONS.keys())
                raise ValueError(f"File type not allowed. Supported types: {allowed}")

            # Sanitize filename
            safe_filename = self.sanitize_filename(file.filename)

            # Ensure user directory exists
            user_dir = self.ensure_user_directory(user_id)

            # Get full file path
            file_path = Path(user_dir) / safe_filename

            # Handle duplicate filenames
            if file_path.exists():
                # Add timestamp to make unique
                from datetime import datetime

                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                name_parts = safe_filename.rsplit(".", 1)
                if len(name_parts) == 2:
                    safe_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                else:
                    safe_filename = f"{safe_filename}_{timestamp}"
                file_path = Path(user_dir) / safe_filename

            # Read and save file
            file_size = 0
            with open(file_path, "wb") as f:
                # Read in chunks to handle large files
                chunk_size = 1024 * 1024  # 1MB chunks
                while chunk := await file.read(chunk_size):
                    file_size += len(chunk)
                    f.write(chunk)

            logger.info(
                f"File saved successfully: {file_path} "
                f"({file_size} bytes, {file_size / 1024 / 1024:.2f} MB)"
            )

            return str(file_path), file_size

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to save file: {e}", exc_info=True)
            raise FileStorageError(f"Failed to save file: {e}")

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if file was deleted successfully
        """
        try:
            path = Path(file_path)

            # Security check: ensure file is within base path
            if not path.is_relative_to(self.base_path):
                logger.error(f"Attempted to delete file outside base path: {file_path}")
                raise FileStorageError("Invalid file path")

            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"File deleted: {file_path}")

                # Clean up empty user directory
                user_dir = path.parent
                if user_dir != self.base_path and not any(user_dir.iterdir()):
                    user_dir.rmdir()
                    logger.debug(f"Empty user directory removed: {user_dir}")

                return True
            else:
                logger.warning(f"File not found or not a file: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get size of a file.

        Args:
            file_path: Path to the file

        Returns:
            Optional[int]: File size in bytes, or None if file doesn't exist
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                return path.stat().st_size
            return None
        except Exception as e:
            logger.error(f"Failed to get file size for {file_path}: {e}")
            return None

    def get_user_storage_used(self, user_id: UUID) -> int:
        """
        Calculate total storage used by a user.

        Args:
            user_id: User's unique identifier

        Returns:
            int: Total storage used in bytes
        """
        try:
            user_dir = self.base_path / str(user_id)

            if not user_dir.exists():
                return 0

            total_size = 0
            for file_path in user_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            logger.debug(
                f"User {user_id} storage: {total_size} bytes "
                f"({total_size / 1024 / 1024:.2f} MB)"
            )

            return total_size

        except Exception as e:
            logger.error(f"Failed to calculate storage for user {user_id}: {e}")
            return 0

    def cleanup_user_files(self, user_id: UUID) -> bool:
        """
        Delete all files for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            bool: True if cleanup was successful
        """
        try:
            user_dir = self.base_path / str(user_id)

            if user_dir.exists():
                shutil.rmtree(user_dir)
                logger.info(f"User directory cleaned up: {user_dir}")
                return True
            else:
                logger.debug(f"User directory does not exist: {user_dir}")
                return True

        except Exception as e:
            logger.error(f"Failed to cleanup user files for {user_id}: {e}")
            return False


# Singleton instance
_file_storage_service: Optional[FileStorageService] = None


def get_file_storage_service(base_path: str = "./uploads") -> FileStorageService:
    """
    Get or create FileStorageService singleton instance.

    Args:
        base_path: Base directory for file storage

    Returns:
        FileStorageService: Singleton instance
    """
    global _file_storage_service

    if _file_storage_service is None:
        _file_storage_service = FileStorageService(base_path)

    return _file_storage_service
