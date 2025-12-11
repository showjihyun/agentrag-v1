"""
Advanced Input Validation and Sanitization

Protects against SQL injection, XSS, and other injection attacks.
"""

import re
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, validator, Field
import bleach

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

# Dangerous patterns to detect
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
    r"(--|;|\/\*|\*\/)",
    r"(\bOR\b.*=.*)",
    r"(\bAND\b.*=.*)",
    r"('|\")(.*)(\\1)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
    r"<object",
    r"<embed",
]

COMMAND_INJECTION_PATTERNS = [
    r"[;&|`$()]",
    r"\$\{.*\}",
    r"\$\(.*\)",
]

# Allowed node types
ALLOWED_NODE_TYPES = {
    "start", "end",
    "llm", "agent",
    "http", "tool",
    "condition", "loop",
    "code", "transform",
    "delay", "human_approval"
}

# Dangerous Python imports/functions
DANGEROUS_PYTHON = [
    "os", "sys", "subprocess", "eval", "exec", "compile",
    "__import__", "open", "file", "input", "raw_input",
    "execfile", "reload", "globals", "locals", "vars"
]


class InputValidator:
    """Advanced input validation"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not value:
            return ""
        
        # Remove HTML tags
        value = bleach.clean(value, strip=True)
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value.strip()
    
    @staticmethod
    def check_sql_injection(value: str) -> bool:
        """
        Check for SQL injection patterns
        
        Args:
            value: Input string
            
        Returns:
            True if suspicious patterns found
        """
        value_upper = value.upper()
        
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(
                    "sql_injection_attempt_detected",
                    pattern=pattern,
                    value=value[:100]
                )
                return True
        
        return False
    
    @staticmethod
    def check_xss(value: str) -> bool:
        """
        Check for XSS patterns
        
        Args:
            value: Input string
            
        Returns:
            True if suspicious patterns found
        """
        for pattern in XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(
                    "xss_attempt_detected",
                    pattern=pattern,
                    value=value[:100]
                )
                return True
        
        return False
    
    @staticmethod
    def check_command_injection(value: str) -> bool:
        """
        Check for command injection patterns
        
        Args:
            value: Input string
            
        Returns:
            True if suspicious patterns found
        """
        for pattern in COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                logger.warning(
                    "command_injection_attempt_detected",
                    pattern=pattern,
                    value=value[:100]
                )
                return True
        
        return False
    
    @staticmethod
    def validate_code_safety(code: str) -> tuple[bool, Optional[str]]:
        """
        Validate Python code safety
        
        Args:
            code: Python code string
            
        Returns:
            (is_safe, error_message)
        """
        # Check for dangerous imports
        for dangerous in DANGEROUS_PYTHON:
            if dangerous in code:
                return False, f"Dangerous import/function detected: {dangerous}"
        
        # Check for file operations
        if any(op in code for op in ["open(", "file(", "read(", "write("]):
            return False, "File operations not allowed"
        
        # Check for network operations
        if any(net in code for net in ["socket", "urllib", "requests", "httpx"]):
            return False, "Network operations not allowed"
        
        # Check for system operations
        if any(sys in code for sys in ["system(", "popen(", "spawn("]):
            return False, "System operations not allowed"
        
        return True, None


class SecureWorkflowInput(BaseModel):
    """Secure workflow input validation"""
    
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    
    @validator('name')
    def validate_name(cls, v):
        """Validate workflow name"""
        # Sanitize
        v = InputValidator.sanitize_string(v, max_length=100)
        
        # Check length
        if len(v) < 3:
            raise ValueError("Name must be at least 3 characters")
        
        # Check for SQL injection
        if InputValidator.check_sql_injection(v):
            raise ValueError("Invalid characters in name")
        
        # Check for XSS
        if InputValidator.check_xss(v):
            raise ValueError("Invalid characters in name")
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description"""
        if v is None:
            return v
        
        # Sanitize
        v = InputValidator.sanitize_string(v, max_length=1000)
        
        # Check for XSS
        if InputValidator.check_xss(v):
            raise ValueError("Invalid characters in description")
        
        return v
    
    @validator('nodes')
    def validate_nodes(cls, v):
        """Validate nodes"""
        if not v:
            raise ValueError("At least one node required")
        
        if len(v) > 100:
            raise ValueError("Too many nodes (max 100)")
        
        for i, node in enumerate(v):
            # Validate node structure
            if 'type' not in node:
                raise ValueError(f"Node {i}: missing 'type' field")
            
            if 'data' not in node:
                raise ValueError(f"Node {i}: missing 'data' field")
            
            # Validate node type
            node_type = node['type']
            if node_type not in ALLOWED_NODE_TYPES:
                raise ValueError(f"Node {i}: invalid type '{node_type}'")
            
            # Special validation for code nodes
            if node_type == 'code':
                code = node.get('data', {}).get('code', '')
                is_safe, error = InputValidator.validate_code_safety(code)
                if not is_safe:
                    raise ValueError(f"Node {i}: {error}")
            
            # Validate HTTP nodes
            if node_type == 'http':
                url = node.get('data', {}).get('url', '')
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f"Node {i}: invalid URL")
        
        return v
    
    @validator('edges')
    def validate_edges(cls, v):
        """Validate edges"""
        if len(v) > 200:
            raise ValueError("Too many edges (max 200)")
        
        for i, edge in enumerate(v):
            # Validate edge structure
            if 'source' not in edge:
                raise ValueError(f"Edge {i}: missing 'source' field")
            
            if 'target' not in edge:
                raise ValueError(f"Edge {i}: missing 'target' field")
        
        return v


class SecureQueryInput(BaseModel):
    """Secure query input validation"""
    
    query: str = Field(..., min_length=1, max_length=5000)
    filters: Optional[Dict[str, Any]] = None
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query string"""
        # Sanitize
        v = InputValidator.sanitize_string(v, max_length=5000)
        
        # Check for SQL injection
        if InputValidator.check_sql_injection(v):
            raise ValueError("Invalid characters in query")
        
        return v
    
    @validator('filters')
    def validate_filters(cls, v):
        """Validate filters"""
        if v is None:
            return v
        
        # Limit filter complexity
        if len(v) > 20:
            raise ValueError("Too many filters (max 20)")
        
        # Validate filter values
        for key, value in v.items():
            if isinstance(value, str):
                if InputValidator.check_sql_injection(value):
                    raise ValueError(f"Invalid filter value for '{key}'")
        
        return v


class SecureFileUpload(BaseModel):
    """Secure file upload validation"""
    
    filename: str
    content_type: str
    size: int
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.txt', '.md',
        '.xlsx', '.xls', '.csv',
        '.pptx', '.ppt',
        '.jpg', '.jpeg', '.png', '.gif',
        '.json', '.yaml', '.yml'
    }
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/markdown',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/json',
        'application/x-yaml',
        'text/yaml'
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename"""
        # Sanitize
        v = InputValidator.sanitize_string(v, max_length=255)
        
        # Check for path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename")
        
        # Check extension
        import os
        ext = os.path.splitext(v)[1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not allowed: {ext}")
        
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate MIME type"""
        if v not in cls.ALLOWED_MIME_TYPES:
            raise ValueError(f"Content type not allowed: {v}")
        
        return v
    
    @validator('size')
    def validate_size(cls, v):
        """Validate file size"""
        if v > cls.MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {cls.MAX_FILE_SIZE / 1024 / 1024}MB)")
        
        if v <= 0:
            raise ValueError("Invalid file size")
        
        return v
