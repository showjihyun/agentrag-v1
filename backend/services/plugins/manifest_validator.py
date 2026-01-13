"""
Plugin manifest validation service.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import jsonschema
from jsonschema import validate, ValidationError

from backend.models.plugin import PluginManifest, ValidationResult, PluginCategory

logger = logging.getLogger(__name__)


class ManifestValidator:
    """Plugin manifest validator"""
    
    # JSON Schema for plugin manifest validation
    MANIFEST_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_-]+$",
                "minLength": 1,
                "maxLength": 255
            },
            "version": {
                "type": "string",
                "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9.-]+)?$"
            },
            "description": {
                "type": "string",
                "minLength": 10,
                "maxLength": 1000
            },
            "author": {
                "type": "string",
                "minLength": 1,
                "maxLength": 255
            },
            "license": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            },
            "category": {
                "type": "string",
                "enum": ["orchestration", "integration", "utility", "monitoring"]
            },
            "dependencies": {
                "type": "array",
                "items": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9_-]+$"
                },
                "uniqueItems": True
            },
            "permissions": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "uniqueItems": True
            },
            "configuration_schema": {
                "type": "object"
            },
            "supported_versions": {
                "type": "array",
                "items": {
                    "type": "string",
                    "pattern": "^\\d+\\.\\d+\\.\\d+$"
                }
            }
        },
        "required": ["name", "version", "description", "author", "license", "category"],
        "additionalProperties": False
    }
    
    def __init__(self):
        self.validator = jsonschema.Draft7Validator(self.MANIFEST_SCHEMA)
    
    def validate_manifest_file(self, manifest_path: str) -> ValidationResult:
        """Validate plugin manifest file"""
        try:
            # Check if file exists
            if not Path(manifest_path).exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Manifest file not found: {manifest_path}"]
                )
            
            # Load and parse JSON
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            return self.validate_manifest_data(manifest_data)
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid JSON in manifest file: {str(e)}"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Error reading manifest file: {str(e)}"]
            )
    
    def validate_manifest_data(self, manifest_data: Dict[str, Any]) -> ValidationResult:
        """Validate plugin manifest data"""
        errors = []
        warnings = []
        
        try:
            # Schema validation
            self.validator.validate(manifest_data)
            
            # Additional business logic validation
            additional_errors, additional_warnings = self._validate_business_rules(manifest_data)
            errors.extend(additional_errors)
            warnings.extend(additional_warnings)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
    
    def validate_manifest_object(self, manifest: PluginManifest) -> ValidationResult:
        """Validate PluginManifest object"""
        return self.validate_manifest_data(manifest.dict())
    
    def _validate_business_rules(self, manifest_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Validate business-specific rules"""
        errors = []
        warnings = []
        
        # Check for reserved plugin names
        reserved_names = ['system', 'core', 'admin', 'api', 'internal']
        if manifest_data.get('name', '').lower() in reserved_names:
            errors.append(f"Plugin name '{manifest_data['name']}' is reserved")
        
        # Validate version format more strictly
        version = manifest_data.get('version', '')
        if version:
            parts = version.split('.')
            if len(parts) >= 3:
                try:
                    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
                    if major < 0 or minor < 0 or patch < 0:
                        errors.append("Version numbers must be non-negative")
                except ValueError:
                    errors.append("Version must contain numeric components")
        
        # Check dependencies for circular references (basic check)
        dependencies = manifest_data.get('dependencies', [])
        plugin_name = manifest_data.get('name', '')
        if plugin_name in dependencies:
            errors.append("Plugin cannot depend on itself")
        
        # Validate permissions
        permissions = manifest_data.get('permissions', [])
        valid_permissions = [
            'file_system_read', 'file_system_write', 'network_access',
            'database_access', 'system_commands', 'user_data_access'
        ]
        for permission in permissions:
            if permission not in valid_permissions:
                warnings.append(f"Unknown permission: {permission}")
        
        # Check configuration schema
        config_schema = manifest_data.get('configuration_schema', {})
        if config_schema:
            schema_errors = self._validate_configuration_schema(config_schema)
            errors.extend(schema_errors)
        
        # Validate supported versions
        supported_versions = manifest_data.get('supported_versions', [])
        if not supported_versions:
            warnings.append("No supported system versions specified")
        
        # Check description quality
        description = manifest_data.get('description', '')
        if len(description) < 20:
            warnings.append("Description is very short, consider providing more details")
        
        return errors, warnings
    
    def _validate_configuration_schema(self, schema: Dict[str, Any]) -> List[str]:
        """Validate configuration schema is valid JSON Schema"""
        errors = []
        
        try:
            # Try to create a validator with the schema
            jsonschema.Draft7Validator(schema)
        except jsonschema.SchemaError as e:
            errors.append(f"Invalid configuration schema: {e.message}")
        except Exception as e:
            errors.append(f"Configuration schema validation error: {str(e)}")
        
        return errors
    
    def create_manifest_from_file(self, manifest_path: str) -> PluginManifest:
        """Create PluginManifest object from file"""
        validation_result = self.validate_manifest_file(manifest_path)
        
        if not validation_result.is_valid:
            raise ValueError(f"Invalid manifest: {validation_result.errors}")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        return PluginManifest(**manifest_data)
    
    def get_validation_schema(self) -> Dict[str, Any]:
        """Get the validation schema for external use"""
        return self.MANIFEST_SCHEMA.copy()