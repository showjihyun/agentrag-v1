"""Response transformation utilities for tools.

This module provides utilities for transforming API responses into
standardized formats for workflow consumption.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
import json

logger = logging.getLogger(__name__)


class ResponseTransformer:
    """
    Utility class for transforming tool responses.
    
    Provides common transformation patterns for API responses.
    """
    
    @staticmethod
    def extract_json_path(data: Dict[str, Any], path: str) -> Any:
        """
        Extract value from nested JSON using dot notation.
        
        Args:
            data: JSON data
            path: Dot-separated path (e.g., "data.items.0.name")
            
        Returns:
            Extracted value or None if path not found
            
        Example:
            >>> data = {"data": {"items": [{"name": "test"}]}}
            >>> ResponseTransformer.extract_json_path(data, "data.items.0.name")
            "test"
        """
        try:
            keys = path.split(".")
            result = data
            
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key)
                elif isinstance(result, list):
                    try:
                        index = int(key)
                        result = result[index]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
                
                if result is None:
                    return None
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to extract JSON path '{path}': {e}")
            return None
    
    @staticmethod
    def map_fields(
        data: Dict[str, Any],
        field_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Map fields from source to target names.
        
        Args:
            data: Source data
            field_mapping: Dict mapping target field names to source paths
            
        Returns:
            Transformed data with mapped fields
            
        Example:
            >>> data = {"user": {"full_name": "John Doe", "email": "john@example.com"}}
            >>> mapping = {"name": "user.full_name", "contact": "user.email"}
            >>> ResponseTransformer.map_fields(data, mapping)
            {"name": "John Doe", "contact": "john@example.com"}
        """
        result = {}
        
        for target_field, source_path in field_mapping.items():
            value = ResponseTransformer.extract_json_path(data, source_path)
            if value is not None:
                result[target_field] = value
        
        return result
    
    @staticmethod
    def extract_array(
        data: Dict[str, Any],
        array_path: str,
        item_mapping: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract and transform an array from response.
        
        Args:
            data: Source data
            array_path: Path to array in source data
            item_mapping: Optional field mapping for each array item
            
        Returns:
            List of transformed items
            
        Example:
            >>> data = {"results": [{"id": 1, "title": "Test"}]}
            >>> ResponseTransformer.extract_array(
            ...     data,
            ...     "results",
            ...     {"name": "title"}
            ... )
            [{"name": "Test"}]
        """
        array = ResponseTransformer.extract_json_path(data, array_path)
        
        if not isinstance(array, list):
            logger.warning(f"Path '{array_path}' did not resolve to an array")
            return []
        
        if item_mapping:
            return [
                ResponseTransformer.map_fields(item, item_mapping)
                for item in array
            ]
        
        return array
    
    @staticmethod
    def flatten_nested(
        data: Dict[str, Any],
        separator: str = "_"
    ) -> Dict[str, Any]:
        """
        Flatten nested dictionary structure.
        
        Args:
            data: Nested dictionary
            separator: Separator for flattened keys
            
        Returns:
            Flattened dictionary
            
        Example:
            >>> data = {"user": {"name": "John", "age": 30}}
            >>> ResponseTransformer.flatten_nested(data)
            {"user_name": "John", "user_age": 30}
        """
        def _flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
            result = {}
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}{separator}{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        result.update(_flatten(value, new_key))
                    else:
                        result[new_key] = value
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{prefix}{separator}{i}"
                    if isinstance(item, (dict, list)):
                        result.update(_flatten(item, new_key))
                    else:
                        result[new_key] = item
            else:
                result[prefix] = obj
            
            return result
        
        return _flatten(data)
    
    @staticmethod
    def paginate_response(
        data: Dict[str, Any],
        items_path: str,
        next_token_path: Optional[str] = None,
        total_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract pagination information from response.
        
        Args:
            data: Response data
            items_path: Path to items array
            next_token_path: Path to next page token
            total_path: Path to total count
            
        Returns:
            Dict with items, next_token, and total
        """
        items = ResponseTransformer.extract_json_path(data, items_path) or []
        next_token = None
        total = None
        
        if next_token_path:
            next_token = ResponseTransformer.extract_json_path(data, next_token_path)
        
        if total_path:
            total = ResponseTransformer.extract_json_path(data, total_path)
        
        return {
            "items": items if isinstance(items, list) else [],
            "next_token": next_token,
            "total": total,
            "has_more": next_token is not None
        }
    
    @staticmethod
    def create_transformer(
        field_mapping: Optional[Dict[str, str]] = None,
        array_path: Optional[str] = None,
        custom_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """
        Create a reusable transformer function.
        
        Args:
            field_mapping: Field mapping for map_fields
            array_path: Array path for extract_array
            custom_fn: Custom transformation function
            
        Returns:
            Transformer function
        """
        def transformer(data: Dict[str, Any]) -> Dict[str, Any]:
            if custom_fn:
                return custom_fn(data)
            
            if array_path:
                return {
                    "items": ResponseTransformer.extract_array(
                        data,
                        array_path,
                        field_mapping
                    )
                }
            
            if field_mapping:
                return ResponseTransformer.map_fields(data, field_mapping)
            
            return data
        
        return transformer
    
    @staticmethod
    def extract_error(
        response_data: Dict[str, Any],
        error_paths: List[str] = None
    ) -> Optional[str]:
        """
        Extract error message from response.
        
        Args:
            response_data: Response data
            error_paths: List of possible error message paths
            
        Returns:
            Error message or None
        """
        if error_paths is None:
            error_paths = [
                "error.message",
                "error",
                "message",
                "error_description",
                "detail"
            ]
        
        for path in error_paths:
            error = ResponseTransformer.extract_json_path(response_data, path)
            if error:
                return str(error)
        
        return None
