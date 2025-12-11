"""
Utilities

Common utility functions.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Any, Dict, Optional
import json
import hashlib


def generate_id() -> UUID:
    """Generate a new UUID."""
    return uuid4()


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase to snake_case."""
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()


def dict_to_camel_case(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all keys in dict to camelCase."""
    return {to_camel_case(k): v for k, v in d.items()}


def dict_to_snake_case(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all keys in dict to snake_case."""
    return {to_snake_case(k): v for k, v in d.items()}


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize object to JSON string."""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def safe_json_loads(s: str, default: Any = None) -> Any:
    """Safely deserialize JSON string."""
    try:
        return json.loads(s)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default if default is not None else {}


def generate_hash(data: Any) -> str:
    """Generate MD5 hash of data."""
    data_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(data_str.encode()).hexdigest()


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length."""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def get_nested(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Get nested value from dict using dot notation."""
    keys = path.split('.')
    value = d
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
        
        if value is None:
            return default
    
    return value


def set_nested(d: Dict[str, Any], path: str, value: Any) -> None:
    """Set nested value in dict using dot notation."""
    keys = path.split('.')
    current = d
    
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
