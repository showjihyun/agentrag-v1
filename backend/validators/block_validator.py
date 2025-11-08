"""Block validation logic."""

import re
import json
from typing import List, Dict, Any
from backend.models.agent_builder import BlockCreate, BlockUpdate


class BlockValidator:
    """Validator for Block operations."""
    
    # Valid block types
    VALID_BLOCK_TYPES = ["llm", "tool", "logic", "composite"]
    
    # Name constraints
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 255
    
    # Description constraints
    MAX_DESCRIPTION_LENGTH = 2000
    
    @classmethod
    def validate_create(cls, data: BlockCreate) -> List[str]:
        """
        Validate block creation data.
        
        Args:
            data: Block creation data
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate name
        name_errors = cls._validate_name(data.name)
        errors.extend(name_errors)
        
        # Validate description
        if data.description:
            desc_errors = cls._validate_description(data.description)
            errors.extend(desc_errors)
        
        # Validate block type
        if data.block_type not in cls.VALID_BLOCK_TYPES:
            errors.append(
                f"Invalid block type: {data.block_type}. "
                f"Must be one of: {', '.join(cls.VALID_BLOCK_TYPES)}"
            )
        
        # Validate input schema
        if data.input_schema:
            schema_errors = cls._validate_json_schema(data.input_schema, "input")
            errors.extend(schema_errors)
        else:
            errors.append("Input schema is required")
        
        # Validate output schema
        if data.output_schema:
            schema_errors = cls._validate_json_schema(data.output_schema, "output")
            errors.extend(schema_errors)
        else:
            errors.append("Output schema is required")
        
        # Validate configuration
        if data.configuration:
            config_errors = cls._validate_configuration(data.configuration, data.block_type)
            errors.extend(config_errors)
        
        # Validate implementation for logic blocks
        if data.block_type == "logic":
            if not data.implementation or len(data.implementation.strip()) == 0:
                errors.append("Logic blocks must have implementation code")
            else:
                impl_errors = cls._validate_implementation(data.implementation)
                errors.extend(impl_errors)
        
        return errors
    
    @classmethod
    def validate_update(cls, data: BlockUpdate) -> List[str]:
        """
        Validate block update data.
        
        Args:
            data: Block update data
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate name if provided
        if data.name is not None:
            name_errors = cls._validate_name(data.name)
            errors.extend(name_errors)
        
        # Validate description if provided
        if data.description is not None:
            desc_errors = cls._validate_description(data.description)
            errors.extend(desc_errors)
        
        # Validate input schema if provided
        if data.input_schema is not None:
            schema_errors = cls._validate_json_schema(data.input_schema, "input")
            errors.extend(schema_errors)
        
        # Validate output schema if provided
        if data.output_schema is not None:
            schema_errors = cls._validate_json_schema(data.output_schema, "output")
            errors.extend(schema_errors)
        
        # Validate configuration if provided
        if data.configuration is not None:
            # Note: We don't have block_type in update, so skip type-specific validation
            if not isinstance(data.configuration, dict):
                errors.append("Configuration must be a dictionary")
        
        # Validate implementation if provided
        if data.implementation is not None:
            if len(data.implementation.strip()) > 0:
                impl_errors = cls._validate_implementation(data.implementation)
                errors.extend(impl_errors)
        
        return errors
    
    @classmethod
    def _validate_name(cls, name: str) -> List[str]:
        """Validate block name."""
        errors = []
        
        if not name or len(name.strip()) == 0:
            errors.append("Name is required")
            return errors
        
        name = name.strip()
        
        if len(name) < cls.MIN_NAME_LENGTH:
            errors.append(f"Name must be at least {cls.MIN_NAME_LENGTH} characters")
        
        if len(name) > cls.MAX_NAME_LENGTH:
            errors.append(f"Name must not exceed {cls.MAX_NAME_LENGTH} characters")
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z0-9\s\-_()]+$', name):
            errors.append("Name contains invalid characters. Only alphanumeric, spaces, hyphens, underscores, and parentheses are allowed")
        
        return errors
    
    @classmethod
    def _validate_description(cls, description: str) -> List[str]:
        """Validate block description."""
        errors = []
        
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            errors.append(f"Description must not exceed {cls.MAX_DESCRIPTION_LENGTH} characters")
        
        return errors
    
    @classmethod
    def _validate_json_schema(cls, schema: Dict[str, Any], schema_type: str) -> List[str]:
        """
        Validate JSON Schema.
        
        Args:
            schema: JSON Schema to validate
            schema_type: Type of schema (input/output)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(schema, dict):
            errors.append(f"{schema_type.capitalize()} schema must be a dictionary")
            return errors
        
        # Check for required JSON Schema fields
        if "type" not in schema:
            errors.append(f"{schema_type.capitalize()} schema must have 'type' field")
        
        # Validate type
        valid_types = ["object", "array", "string", "number", "integer", "boolean", "null"]
        if "type" in schema and schema["type"] not in valid_types:
            errors.append(
                f"{schema_type.capitalize()} schema type must be one of: {', '.join(valid_types)}"
            )
        
        # If type is object, check for properties
        if schema.get("type") == "object":
            if "properties" not in schema:
                errors.append(f"{schema_type.capitalize()} schema of type 'object' should have 'properties' field")
        
        # If type is array, check for items
        if schema.get("type") == "array":
            if "items" not in schema:
                errors.append(f"{schema_type.capitalize()} schema of type 'array' should have 'items' field")
        
        # Try to validate as valid JSON Schema (basic check)
        try:
            json.dumps(schema)
        except Exception as e:
            errors.append(f"{schema_type.capitalize()} schema is not valid JSON: {str(e)}")
        
        return errors
    
    @classmethod
    def _validate_configuration(cls, configuration: Dict[str, Any], block_type: str) -> List[str]:
        """
        Validate block configuration based on block type.
        
        Args:
            configuration: Configuration dictionary
            block_type: Type of block
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(configuration, dict):
            errors.append("Configuration must be a dictionary")
            return errors
        
        # Type-specific validation
        if block_type == "llm":
            # LLM blocks should have llm_provider and llm_model
            if "llm_provider" not in configuration:
                errors.append("LLM blocks must have 'llm_provider' in configuration")
            if "llm_model" not in configuration:
                errors.append("LLM blocks must have 'llm_model' in configuration")
        
        elif block_type == "tool":
            # Tool blocks should have tool_id
            if "tool_id" not in configuration:
                errors.append("Tool blocks must have 'tool_id' in configuration")
        
        elif block_type == "composite":
            # Composite blocks should have workflow definition
            if "workflow" not in configuration:
                errors.append("Composite blocks must have 'workflow' in configuration")
        
        return errors
    
    @classmethod
    def _validate_implementation(cls, implementation: str) -> List[str]:
        """
        Validate block implementation code.
        
        Args:
            implementation: Python code string
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for dangerous imports/operations
        dangerous_patterns = [
            r'import\s+os',
            r'import\s+sys',
            r'import\s+subprocess',
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'file\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, implementation, re.IGNORECASE):
                errors.append(f"Implementation contains potentially dangerous operation: {pattern}")
        
        # Try to compile the code (basic syntax check)
        try:
            compile(implementation, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Implementation has syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Implementation validation failed: {str(e)}")
        
        return errors
    
    @classmethod
    def validate_test_input(cls, input_data: Dict[str, Any], input_schema: Dict[str, Any]) -> List[str]:
        """
        Validate test input against input schema.
        
        Args:
            input_data: Test input data
            input_schema: Input JSON Schema
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        required = input_schema.get("required", [])
        for field in required:
            if field not in input_data:
                errors.append(f"Missing required field: {field}")
        
        # Check field types (basic validation)
        properties = input_schema.get("properties", {})
        for field, value in input_data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                actual_type = type(value).__name__
                
                # Map Python types to JSON Schema types
                type_mapping = {
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean",
                    "list": "array",
                    "dict": "object",
                    "NoneType": "null"
                }
                
                json_type = type_mapping.get(actual_type, actual_type)
                
                if expected_type and json_type != expected_type:
                    # Allow integer for number type
                    if not (expected_type == "number" and json_type == "integer"):
                        errors.append(
                            f"Field '{field}' has wrong type. "
                            f"Expected: {expected_type}, Got: {json_type}"
                        )
        
        return errors
