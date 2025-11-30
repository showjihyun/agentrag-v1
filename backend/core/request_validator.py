"""
Request Validation Utilities

Provides enhanced request validation with:
- Input sanitization
- Schema validation
- Security checks
- Custom validators
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

from fastapi import HTTPException, status, Request
from pydantic import BaseModel, validator, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Security Patterns
# ============================================================================

# SQL Injection patterns
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
    r"(--|#|/\*|\*/)",
    r"(\bOR\b\s+\d+\s*=\s*\d+)",
    r"(\bAND\b\s+\d+\s*=\s*\d+)",
    r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
]

# XSS patterns
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e/",
    r"\.%2e/",
]


# ============================================================================
# Validation Functions
# ============================================================================

def check_sql_injection(value: str) -> bool:
    """Check if value contains SQL injection patterns."""
    if not isinstance(value, str):
        return False
    
    value_upper = value.upper()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return True
    return False


def check_xss(value: str) -> bool:
    """Check if value contains XSS patterns."""
    if not isinstance(value, str):
        return False
    
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


def check_path_traversal(value: str) -> bool:
    """Check if value contains path traversal patterns."""
    if not isinstance(value, str):
        return False
    
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    return False


def sanitize_string(value: str, max_length: int = 10000) -> str:
    """Sanitize a string value."""
    if not isinstance(value, str):
        return value
    
    # Truncate
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Normalize whitespace
    value = ' '.join(value.split())
    
    return value


def sanitize_html(value: str) -> str:
    """Remove HTML tags from string."""
    if not isinstance(value, str):
        return value
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', value)
    
    # Decode HTML entities
    import html
    clean = html.unescape(clean)
    
    return clean


# ============================================================================
# Validators
# ============================================================================

class InputValidator:
    """Collection of input validators."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format."""
        # 3-50 chars, alphanumeric and underscore
        pattern = r'^[a-zA-Z0-9_]{3,50}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Validate password strength.
        
        Returns dict with:
        - valid: bool
        - score: int (0-5)
        - issues: list of issues
        """
        issues = []
        score = 0
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters")
        else:
            score += 1
        
        if len(password) >= 12:
            score += 1
        
        if re.search(r'[a-z]', password):
            score += 1
        else:
            issues.append("Password should contain lowercase letters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            issues.append("Password should contain uppercase letters")
        
        if re.search(r'\d', password):
            score += 1
        else:
            issues.append("Password should contain numbers")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            issues.append("Password should contain special characters")
        
        return {
            "valid": len(issues) == 0 or score >= 4,
            "score": min(score, 5),
            "issues": issues
        }
    
    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Validate UUID format."""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, value.lower()))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url, re.IGNORECASE))
    
    @staticmethod
    def validate_json_path(path: str) -> bool:
        """Validate JSON path format."""
        # Simple validation for common JSON path patterns
        pattern = r'^(\$|@)?(\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\]|\[\*\]|\[\'[^\']+\'\])*$'
        return bool(re.match(pattern, path))


# ============================================================================
# Request Validation Middleware
# ============================================================================

class RequestValidator:
    """
    Request validation utility.
    
    Validates incoming requests for security issues.
    """
    
    def __init__(
        self,
        check_sql: bool = True,
        check_xss: bool = True,
        check_path: bool = True,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        self.check_sql = check_sql
        self.check_xss = check_xss
        self.check_path = check_path
        self.max_body_size = max_body_size
    
    def validate_value(self, value: Any, field_name: str = "field") -> None:
        """Validate a single value."""
        if not isinstance(value, str):
            return
        
        if self.check_sql and check_sql_injection(value):
            logger.warning(f"SQL injection attempt detected in {field_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid characters in {field_name}"
            )
        
        if self.check_xss and check_xss(value):
            logger.warning(f"XSS attempt detected in {field_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content in {field_name}"
            )
        
        if self.check_path and check_path_traversal(value):
            logger.warning(f"Path traversal attempt detected in {field_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid path in {field_name}"
            )
    
    def validate_dict(self, data: Dict[str, Any], prefix: str = "") -> None:
        """Recursively validate a dictionary."""
        for key, value in data.items():
            field_name = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, str):
                self.validate_value(value, field_name)
            elif isinstance(value, dict):
                self.validate_dict(value, field_name)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        self.validate_value(item, f"{field_name}[{i}]")
                    elif isinstance(item, dict):
                        self.validate_dict(item, f"{field_name}[{i}]")
    
    async def validate_request(self, request: Request) -> None:
        """Validate an incoming request."""
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request body too large (max {self.max_body_size} bytes)"
            )
        
        # Validate query parameters
        for key, value in request.query_params.items():
            self.validate_value(value, f"query.{key}")
        
        # Validate path parameters
        for key, value in request.path_params.items():
            self.validate_value(str(value), f"path.{key}")


# ============================================================================
# Decorator
# ============================================================================

def validate_request(
    check_sql: bool = True,
    check_xss: bool = True,
    check_path: bool = True,
):
    """
    Decorator for request validation.
    
    Usage:
        @router.post("/items")
        @validate_request()
        async def create_item(request: Request, item: ItemCreate):
            ...
    """
    validator = RequestValidator(
        check_sql=check_sql,
        check_xss=check_xss,
        check_path=check_path,
    )
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args/kwargs
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                await validator.validate_request(request)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Pydantic Validators
# ============================================================================

def no_sql_injection(cls, v):
    """Pydantic validator to check for SQL injection."""
    if isinstance(v, str) and check_sql_injection(v):
        raise ValueError("Invalid characters detected")
    return v


def no_xss(cls, v):
    """Pydantic validator to check for XSS."""
    if isinstance(v, str) and check_xss(v):
        raise ValueError("Invalid content detected")
    return v


def sanitized_string(cls, v):
    """Pydantic validator to sanitize strings."""
    if isinstance(v, str):
        return sanitize_string(v)
    return v


# ============================================================================
# Safe Input Models
# ============================================================================

class SafeString(str):
    """String type that is automatically sanitized."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        
        # Check for malicious content
        if check_sql_injection(v):
            raise ValueError("Invalid characters")
        if check_xss(v):
            raise ValueError("Invalid content")
        
        # Sanitize
        return cls(sanitize_string(v))


class SafeEmail(str):
    """Email type with validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        
        v = v.lower().strip()
        
        if not InputValidator.validate_email(v):
            raise ValueError("Invalid email format")
        
        return cls(v)


class SafeURL(str):
    """URL type with validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        
        v = v.strip()
        
        if not InputValidator.validate_url(v):
            raise ValueError("Invalid URL format")
        
        # Check for malicious content
        if check_xss(v):
            raise ValueError("Invalid URL content")
        
        return cls(v)
